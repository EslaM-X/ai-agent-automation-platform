"""Workflow layer: planner, approval gate, and execution.

This is the heart of the platform: a structured pipeline that turns an
objective into approved, executed, audited actions — explicitly not a raw
User -> LLM -> Answer call.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, List, Optional

from agents import Agent, build_agent
from knowledge import KnowledgeBase
from observability import AuditLog
from core import (
    AgentResult,
    AgentRole,
    Status,
    Task,
    WorkflowRun,
)


@dataclass
class WorkflowPlan:
    """Ordered steps produced by the planner."""

    steps: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"steps": self.steps}


class Planner:
    """Turns an objective into an ordered list of agent roles.

    Rules-based and deterministic: research first, then content, then QA.
    A production build can extend this with an LLM-based router; the contract
    (returns role names) stays the same.
    """

    def plan(self, objective: str) -> WorkflowPlan:
        return WorkflowPlan(
            steps=[AgentRole.RESEARCH.value, AgentRole.CONTENT.value, AgentRole.QA.value]
        )


class ApprovalGate:
    """Human-in-the-loop gate before irreversible actions.

    The gate is deliberately a callable with a clear interface so a real UI
    (or an explicit `approve_all=True` flag for tests) can drive it.
    """

    def __init__(self, approver: Optional[Callable[[AgentResult], bool]] = None):
        self._approver = approver

    def request(self, result: AgentResult) -> bool:
        if self._approver is not None:
            return self._approver(result)
        return False

    def approve(self, result: AgentResult) -> bool:
        return self.request(result)


class Executor:
    """Runs agent tasks for a plan, with approval gating and audit."""

    def __init__(self, agents: dict, approval_gate: Optional[ApprovalGate] = None, auto_approve: bool = False):
        self.agents: dict = agents
        self.approval_gate = approval_gate or ApprovalGate()
        self.auto_approve = auto_approve

    def execute(self, run: WorkflowRun, plan: WorkflowPlan, kb: Optional[KnowledgeBase] = None) -> WorkflowRun:
        run.status = Status.RUNNING
        run.log("plan", steps=plan.to_dict()["steps"])
        for role_name in plan.steps:
            run.log("dispatch", role=role_name)
            agent = self.agents[role_name]
            context = {}
            if kb is not None and role_name == AgentRole.RESEARCH.value:
                hits = kb.search(run.objective)
                context = {"sources": [d.to_dict() for d in hits]}
            task = Task(prompt=run.objective, role=AgentRole(role_name), context=context)
            result = agent.run(task)
            run.log("agent_result", **result.to_dict())
            if not result.passed_validation:
                run.status = Status.FAILED
                run.error = f"validation failed for {role_name}"
                return run
            if role_name == AgentRole.CONTENT.value:
                run.status = Status.AWAITING_APPROVAL
                approved = self.approval_gate.approve(result) or self.auto_approve
                run.log("approval", approved=approved)
                if not approved:
                    run.status = Status.REJECTED
                    run.error = "human rejected the content step"
                    return run
                run.status = Status.RUNNING
        run.status = Status.COMPLETED
        run.log("completed", at=time.time())
        return run
