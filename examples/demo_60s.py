"""The 60-second demo: build your first governed AI workflow.

Runs offline with a deterministic provider - no API keys, no network. It
shows the full production pipeline: planning, specialized agents, human
approval, execution, evaluation, retries, and the audit trail.

    python examples/demo_60s.py

Output is structured so it can be recorded as a 15-30s demo clip
(see docs/demo-recording.md).
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.errors import TransientFailure
from evaluation import Rule, RuleEvaluator
from knowledge import KnowledgeBase
from orchestrator import Orchestrator
from workflow.retry import RetryPolicy


class FakeProvider:
    """Deterministic provider: one flaky first call, then stable replies."""

    def __init__(self):
        self._research_calls = 0

    def complete(self, system: str, user: str, temperature: float = 0.2) -> str:
        if "research agent" in system.lower():
            self._research_calls += 1
            if self._research_calls == 1:
                raise TransientFailure("research endpoint timed out (retried)")
            return "Facts: Q3 revenue up 12%, costs flat, churn down."
        if "content agent" in system.lower():
            return "Draft: Q3 was strong across revenue and retention."
        if "qa agent" in system.lower():
            return "QA: no blocking issues on the Q3 draft; recommend a follow-up on margins."
        return "OK"


def banner(text: str) -> None:
    print()
    print("=" * 62)
    print(text)
    print("=" * 62)


def main() -> None:
    t0 = time.time()
    banner("STEP 1/4  Build the platform (no keys, no network)")
    kb = KnowledgeBase()
    kb.add(
        "Q3 revenue grew 12% while costs stayed flat; churn declined for the "
        "third consecutive quarter.",
        source="finance/q3.md",
    )
    provider = FakeProvider()
    orc = Orchestrator(
        provider,
        approver=lambda r: True,
        kb=kb,
        retry_policy=RetryPolicy(max_attempts=3, base_delay=0.1),
        evaluator=RuleEvaluator(
            rules=[
                Rule("contains", "Q3"),
                Rule("min_length", 20),
                Rule("not_contains", "ERROR"),
            ]
        ),
    )
    print("  ok - Orchestrator ready with retry policy, tool policy, and evaluator.")

    banner("STEP 2/4  Run a governed workflow (idempotency key)")
    run = orc.run("Summarize the Q3 business results", idempotency_key="q3-summary")
    replay = orc.run("Summarize the Q3 business results", idempotency_key="q3-summary")
    assert replay.id == run.id
    print(f"  run id      : {run.id}")
    print(f"  status      : {run.status.value}")
    print(f"  attempts    : {run.attempts} (research retried once after a transient failure)")
    print(f"  checkpoint  : {run.checkpoint} of {len(run.plan)} steps")
    print("  idempotent  : replay returned the SAME run without re-executing")

    banner("STEP 3/4  Results + evaluation")
    for step in run.steps:
        if step["step"] == "agent_result":
            print(f"  [{step['data']['role']:>8}] {step['data']['output']}")
    for step in run.steps:
        if step["step"] == "evaluation":
            print(f"  evaluation  : score={step['data']['score']} passed={step['data']['passed']}")

    banner("STEP 4/4  Operational summary")
    summary = orc.audit.summarize(run)
    for key, value in summary.items():
        print(f"  {key:<13}: {value}")
    print()
    print(f"  total wall time: {time.time() - t0:.2f}s - done, no LLM required.")
    print()


if __name__ == "__main__":
    main()
