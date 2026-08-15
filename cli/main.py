"""Command-line interface for ai-agent-automation-platform.

Thin interface over the existing evaluation harness and persisted execution
state. No business logic lives here:

- ``evaluate``  -> ``evaluation.runner.run_suite`` + ``evaluation.report.print_suite``
- ``gate``      -> ``evaluation.runner.compare_to_baseline`` (exit code = gate result)
- ``inspect``   -> reads persisted execution state (``benchmarks/latest.json`` + history)

Usage:
    agent-platform evaluate
    agent-platform gate
    agent-platform inspect [--case CASE_ID] [--history]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from evaluation.report import print_suite
from evaluation.runner import (
    BASELINE,
    CASES_DIR,
    LATEST,
    compare_to_baseline,
    run_suite,
)

BENCHMARKS_DIR = LATEST.parent
HISTORY_DIR = BENCHMARKS_DIR / "history"


def _write_report(suite: dict, out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(suite, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _cmd_evaluate(args: argparse.Namespace) -> int:
    suite = run_suite(args.cases)
    print_suite(suite)
    _write_report(suite, args.out)
    print(f"report written: {args.out}")
    return 0


def _cmd_gate(args: argparse.Namespace) -> int:
    suite = run_suite(args.cases)
    print_suite(suite)
    _write_report(suite, args.out)
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


def _cmd_inspect(args: argparse.Namespace) -> int:
    if not args.latest.exists():
        print(f"ERROR: no execution state at {args.latest}; run `agent-platform evaluate` first.")
        return 1
    suite = json.loads(args.latest.read_text(encoding="utf-8"))

    if args.history:
        _print_history()
        print()

    print(f"execution state: {args.latest}")
    print(f"cases          : {suite['cases_passed']}/{suite['cases_total']} passed")
    for dim, m in sorted(suite["dimensions"].items()):
        if not m["checked"]:
            continue
        rate = f"{m['rate'] * 100:.1f}%" if m["rate"] is not None else "n/a"
        print(f"  {dim:<18} {m['passed']:>3}/{m['checked']:<3} {rate}")

    if args.case:
        for case in suite["cases"]:
            if case["id"] != args.case:
                continue
            print(f"\ncase [{case['id']}] {case['objective']}  ({case['source']})")
            print(f"  status : {case['status']}")
            for chk in case["checks"]:
                mark = "PASS" if chk["passed"] else "FAIL"
                print(f"  [{mark}] {chk['checker']} ({chk['dimension']})")
                for note in chk["notes"]:
                    print(f"           - {note}")
            return 0
        print(f"\nERROR: no case with id {args.case!r}")
        return 1

    failed = [c for c in suite["cases"] if not c["passed"]]
    if failed:
        print("\nfailed cases:")
        for case in failed:
            print(f"  [{case['id']}] {case['objective']}")
    return 0


def _print_history() -> None:
    if not HISTORY_DIR.exists():
        print("history: (none)")
        return
    print("history (versioned reports):")
    for path in sorted(HISTORY_DIR.glob("*.json")):
        report = json.loads(path.read_text(encoding="utf-8"))
        print(f"  {path.name:<16} {report['cases_passed']}/{report['cases_total']} passed")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agent-platform", description=__doc__.split("\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)

    ev = sub.add_parser("evaluate", help="run the full evaluation harness (writes latest report)")
    ev.add_argument(
        "--cases", type=Path, default=CASES_DIR, help="cases directory (default: evaluation/cases)"
    )
    ev.add_argument(
        "--out",
        type=Path,
        default=LATEST,
        help="report output path (default: benchmarks/latest.json)",
    )
    ev.set_defaults(func=_cmd_evaluate)

    ga = sub.add_parser("gate", help="run evaluation and fail if behavior regressed vs baseline")
    ga.add_argument(
        "--cases", type=Path, default=CASES_DIR, help="cases directory (default: evaluation/cases)"
    )
    ga.add_argument(
        "--baseline",
        type=Path,
        default=BASELINE,
        help="baseline file (default: benchmarks/baseline.json)",
    )
    ga.add_argument(
        "--out",
        type=Path,
        default=LATEST,
        help="report output path (default: benchmarks/latest.json)",
    )
    ga.set_defaults(func=_cmd_gate)

    ins = sub.add_parser(
        "inspect", help="inspect persisted execution state (latest report + history)"
    )
    ins.add_argument(
        "--latest",
        type=Path,
        default=LATEST,
        help="execution state file (default: benchmarks/latest.json)",
    )
    ins.add_argument("--case", type=str, default=None, help="show full detail for one case id")
    ins.add_argument("--history", action="store_true", help="also list versioned history reports")
    ins.set_defaults(func=_cmd_inspect)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
