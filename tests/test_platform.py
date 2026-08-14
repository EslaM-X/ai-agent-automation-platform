"""End-to-end tests using a deterministic fake provider (no LLM, no network).

The whole platform is testable offline: the provider is the only seam that
touches the outside world.
"""

import pytest

from agents import AgentRole, ResearchAgent
from core import Status
from knowledge import KnowledgeBase
from orchestrator import Orchestrator
from workflow import ApprovalGate, Planner


class FakeProvider:
    """Deterministic provider that echoes a fixed template."""

    def __init__(self, replies=None):
        self.replies = replies or {
            "research": "RESEARCH: found 3 key facts.",
            "content": "CONTENT: draft is ready.",
            "qa": "QA: no blocking issues found.",
            "analytics": "ANALYTICS: trend is positive.",
        }

    def complete(self, system: str, user: str, temperature: float = 0.2) -> str:
        lowered = system.lower()
        for role, reply in self.replies.items():
            if role in lowered:
                return reply
        return "OK"


@pytest.fixture
def provider():
    return FakeProvider()


def test_research_agent_validates(provider):
    agent = ResearchAgent(provider)
    task = type("T", (), {"id": "t1", "prompt": "summary", "role": AgentRole.RESEARCH})()
    result = agent.run(task)
    assert result.passed_validation is True
    assert result.role == AgentRole.RESEARCH
    assert "RESEARCH" in result.output


def test_planner_orders_roles():
    plan = Planner().plan("anything")
    assert plan.steps == ["research", "content", "qa"]


def test_approval_gate_default_rejects():
    gate = ApprovalGate()
    assert gate.approve(None) is False


def test_approval_gate_with_approver():
    gate = ApprovalGate(approver=lambda r: True)
    assert gate.approve(None) is True


def test_orchestrator_auto_approve_completes(provider):
    orc = Orchestrator(provider, auto_approve=True)
    run = orc.run("Summarize Q3")
    assert run.status == Status.COMPLETED
    assert len(run.steps) >= 5


def test_orchestrator_rejects_without_approval(provider):
    orc = Orchestrator(provider, auto_approve=False)
    run = orc.run("Summarize Q3")
    assert run.status == Status.REJECTED
    assert "rejected" in run.error


def test_orchestrator_with_approver_callback(provider):
    orc = Orchestrator(provider, approver=lambda r: True, auto_approve=False)
    run = orc.run("Summarize Q3")
    assert run.status == Status.COMPLETED


def test_knowledge_base_search():
    kb = KnowledgeBase()
    kb.add("The launch date is January 1st.", source="docs")
    kb.add("Budget for Q1 is 50k.", source="finance")
    hits = kb.search("budget")
    assert len(hits) == 1
    assert "50k" in hits[0].text


def test_audit_log_records_run(provider):
    orc = Orchestrator(provider, auto_approve=True)
    run = orc.run("Audit me")
    entries = orc.audit.for_workflow(run.id)
    assert len(entries) >= 1
    assert any(e.step == "agent_result" for e in entries)


def test_workflow_run_to_dict(provider):
    orc = Orchestrator(provider, auto_approve=True)
    run = orc.run("Serialize")
    d = run.to_dict()
    assert d["status"] == "completed"
    assert d["objective"] == "Serialize"
