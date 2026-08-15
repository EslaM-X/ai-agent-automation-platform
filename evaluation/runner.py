"""Evaluation harness runner.

Drives the REAL platform with deterministic, case-defined providers and asserts
expected behavior per dimension (correctness, policy, safety, execution,
auditability, idempotency). No LLM, no network, no mocked Orchestrator.

Usage:
    python -m evaluation.runner                 # run, print report, write latest.json
    python -m evaluation.runner --gate          # also fail on regression vs baseline.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from agents import AgentRole
from core.errors import PermanentFailure, TransientFailure
from core.policy import ToolPolicy
from evaluation import Rule, RuleEvaluator
from evaluation.evaluators import CHECKERS
from evaluation.metrics import summarize
from knowledge import KnowledgeBase
from orchestrator import Orchestrator
from workflow.retry import RetryPolicy

ROOT = Path(__file__).resolve().parent.parent
CASES_DIR = ROOT / "evaluation" / "cases"
BENCHMARKS_DIR = ROOT / "benchmarks"
BASELINE = BENCHMARKS_DIR / "baseline.json"
LATEST = BENCHMARKS_DIR / "latest.json"

_ROLE_HINTS = ("research", "content", "qa", "analytics")


class CaseProvider:
    """Deterministic provider driven by case JSON (same contract as test fakes)."""

    def __init__(
        self,
        replies: dict[str, str] | None = None,
        raise_once: dict[str, str] | None = None,
        raise_always: dict[str, str] | None = None,
    ):
        self.replies = replies or {}
        self.raise_once = raise_once or {}
        self.raise_always = raise_always or {}
        self.calls: list[str] = []
        self._fired_once: set[str] = set()

    def complete(self, system: str, user: str, temperature: float = 0.2) -> str:
        lowered = system.lower()
        for role in _ROLE_HINTS:
            if role not in lowered:
                continue
            self.calls.append(role)
            if role in self.raise_always:
                raise self._failure(self.raise_always[role], role)
            if role in self.raise_once and role not in self._fired_once:
                self._fired_once.add(role)
                raise self._failure(self.raise_once[role], role)
            return self.replies.get(role, "OK")
        return "OK"

    @staticmethod
    def _failure(kind: str, role: str) -> TransientFailure | PermanentFailure:
        if kind == "transient":
            return TransientFailure(f"transient failure for {role}")
        return PermanentFailure(f"permanent failure for {role}")


def _build_orchestrator(provider: CaseProvider, cfg: dict) -> Orchestrator:
    approver = None
    if cfg.get("approver_accepts") is not None:
        approver = lambda _r: bool(cfg.get("approver_accepts"))
    policy = None
    if cfg.get("policy") is not None:
        policy = ToolPolicy({AgentRole(role) for role in cfg["policy"]})
    evaluator = None
    if cfg.get("evaluator_rules"):
        evaluator = RuleEvaluator(
            [Rule(rule["kind"], rule["value"]) for rule in cfg["evaluator_rules"]]
        )
    kb = None
    doc = cfg.get("kb_doc")
    if doc:
        kb = KnowledgeBase()
        kb.add(doc["text"], source=doc.get("source", ""))
    return Orchestrator(
        provider,
        approver=approver,
        auto_approve=bool(cfg.get("auto_approve", True)),
        kb=kb,
        retry_policy=RetryPolicy(
            max_attempts=int(cfg.get("retry_max_attempts", 3)),
            base_delay=float(cfg.get("retry_base_delay", 0.0)),
        ),
        policy=policy,
        evaluator=evaluator,
    )


def load_cases(cases_dir: Path) -> list[dict]:
    cases: list[dict] = []
    for path in sorted(cases_dir.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        for case in payload.get("cases", []):
            case["_source"] = path.name
            cases.append(case)
    return cases


def run_case(case: dict) -> dict:
    cfg = case["config"]
    provider = CaseProvider(**case.get("provider", {}))
    orc = _build_orchestrator(provider, cfg)
    objective = case["objective"]
    run = orc.run(objective, idempotency_key=cfg.get("idempotency_key"))
    ctx: dict = {"provider": provider, "orchestrator": orc, "first_run": run}
    if cfg.get("resume"):
        ctx["resumed_run"] = orc.resume(run.id)
    if cfg.get("replay"):
        ctx["replay_run"] = orc.run(objective, idempotency_key=cfg.get("idempotency_key"))

    wanted = set(case.get("checks", []))
    results: list[dict] = []
    dimensions: dict[str, dict] = {}
    for name, dim, fn in CHECKERS:
        if dim not in wanted:
            continue
        try:
            outcome, notes = fn(case, run, ctx)
        except Exception as exc:  # noqa: BLE001 - a broken checker must not kill the suite
            outcome, notes = False, [f"checker raised {exc!r}"]
        if outcome is None:
            continue
        results.append({"checker": name, "dimension": dim, "passed": bool(outcome), "notes": notes})
        state = dimensions.setdefault(dim, {"checked": False, "passed": True})
        state["checked"] = True
        if not outcome:
            state["passed"] = False

    return {
        "id": case["id"],
        "group": case.get("group", ""),
        "source": case.get("_source", ""),
        "objective": objective,
        "status": run.status.value,
        "passed": not any(not r["passed"] for r in results),
        "checks": results,
        "dimensions": dimensions,
    }


def run_suite(cases_dir: Path = CASES_DIR) -> dict:
    cases = load_cases(cases_dir)
    results = [run_case(case) for case in cases]
    suite = summarize(results)
    suite["_source_files"] = sorted({c["source"] for c in results})
    return suite


def compare_to_baseline(suite: dict, baseline: dict) -> list[dict]:
    """List of regressions vs the committed baseline (empty == gate passes)."""
    by_id = {c["id"]: c for c in suite["cases"]}
    regressions: list[dict] = []
    for base_case in baseline.get("cases", []):
        current = by_id.get(base_case["id"])
        if current is None:
            continue
        if base_case.get("passed") and not current["passed"]:
            regressions.append(
                {
                    "kind": "case",
                    "id": base_case["id"],
                    "baseline": "pass",
                    "now": "fail",
                    "failures": [
                        {
                            "checker": f["checker"],
                            "notes": f["notes"],
                        }
                        for f in current["checks"]
                        if not f["passed"]
                    ],
                }
            )
    for dim, base in baseline.get("dimensions", {}).items():
        if not base.get("checked"):
            continue
        current = suite["dimensions"].get(dim, {})
        now_rate = current.get("rate") or 0.0
        if now_rate < base["rate"]:
            regressions.append(
                {
                    "kind": "dimension",
                    "dimension": dim,
                    "baseline_rate": base["rate"],
                    "now_rate": now_rate,
                }
            )
    return regressions


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the evaluation harness.")
    parser.add_argument("--gate", action="store_true", help="fail on regression vs baseline")
    parser.add_argument("--baseline", type=Path, default=BASELINE, help="baseline file")
    parser.add_argument("--out", type=Path, default=LATEST, help="output JSON file")
    args = parser.parse_args(argv)

    suite = run_suite()

    from evaluation.report import print_suite

    print_suite(suite)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(suite, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"report written: {args.out}")

    if not args.gate:
        return 0
    if not args.baseline.exists():
        print(f"ERROR: baseline not found at {args.baseline}; run once to generate it.")
        return 1
    baseline = json.loads(args.baseline.read_text(encoding="utf-8"))
    regressions = compare_to_baseline(suite, baseline)
    if regressions:
        print(f"REGRESSION GATE: FAIL ({len(regressions)} regression(s))")
        for item in regressions:
            print(f"  - {item}")
        return 1
    print("REGRESSION GATE: PASS (matches committed baseline)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
