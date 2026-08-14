"""Example: run a workflow end-to-end with a deterministic fake provider.

Shows the full pipeline: plan -> research -> content -> approval -> QA -> audit.
No network or LLM key needed.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from orchestrator import Orchestrator


class FakeProvider:
    def complete(self, system: str, user: str, temperature: float = 0.2) -> str:
        if "research agent" in system.lower():
            return "Facts: Q3 revenue up 12%, costs flat, churn down."
        if "content agent" in system.lower():
            return "Draft: Q3 was strong across revenue and retention."
        if "qa agent" in system.lower():
            return "QA: no blocking issues; recommend a follow-up on margins."
        return "OK"


def main():
    provider = FakeProvider()
    orc = Orchestrator(provider, approver=lambda r: True)
    run = orc.run("Summarize the Q3 business results")
    print(run.to_dict())
    print()
    print("AUDIT LOG")
    print(orc.audit.export_json())


if __name__ == "__main__":
    main()
