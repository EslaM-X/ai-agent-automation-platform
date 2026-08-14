"""Orchestrator: the public entry point that ties the pipeline together."""

from __future__ import annotations

from collections.abc import Callable

from agents import Provider, build_agent
from core import AgentResult, AgentRole, Status, WorkflowRun
from knowledge import KnowledgeBase
from observability import AuditLog
from workflow import ApprovalGate, Executor, Planner


class Orchestrator:
    """Coordinates planning, execution, approval, and audit.

    Example:
        orc = Orchestrator(provider, auto_approve=True)
        run = orc.run("Summarize our Q3 results")
        print(run.to_dict())
    """

    def __init__(
        self,
        provider: Provider,
        approver: Callable[[AgentResult], bool] | None = None,
        auto_approve: bool = False,
        kb: KnowledgeBase | None = None,
    ):
        self.provider = provider
        self.agents: dict = {role.value: build_agent(role, provider) for role in AgentRole}
        self.planner = Planner()
        self.audit = AuditLog()
        gate = ApprovalGate(approver)
        self.executor = Executor(self.agents, approval_gate=gate, auto_approve=auto_approve)
        self.kb = kb

    def run(self, objective: str) -> WorkflowRun:
        run = WorkflowRun(objective=objective, status=Status.PLANNING)
        run.log("objective", objective=objective)
        plan = self.planner.plan(objective)
        run.log("planned", steps=plan.to_dict()["steps"])
        self.executor.execute(run, plan, kb=self.kb)
        self.audit.observe(run)
        return run
