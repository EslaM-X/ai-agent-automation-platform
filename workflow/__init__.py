"""Workflow layer: planner, approval gate, and execution.

This is the heart of the platform: a structured pipeline that turns an
objective into approved, executed, audited actions — explicitly not a raw
User -> LLM -> Answer call.

Execution is hardened for production: every dispatch is permission-checked
against a ToolPolicy, transient failures are retried with backoff, runs keep
a checkpoint so they can be resumed, and each step records duration metrics.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass, field

from core import (
    AgentResult,
    AgentRole,
    Status,
    Task,
    WorkflowRun,
)
from core.errors import WorkflowError
from core.policy import DEFAULT_POLICY, ToolPolicy
from knowledge import KnowledgeBase
from workflow.retry import RetryExhausted, RetryPolicy


@dataclass
class WorkflowPlan:
    """Ordered steps produced by the planner."""

    steps: list[str] = field(default_factory=list)

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

    def __init__(self, approver: Callable[[AgentResult], bool] | None = None):
        self._approver = approver

    def request(self, result: AgentResult) -> bool:
        if self._approver is not None:
            return self._approver(result)
        return False

    def approve(self, result: AgentResult) -> bool:
        return self.request(result)


class Executor:
    """Runs agent tasks for a plan, with permission, retry, and audit.

    A run is resumable: `run.checkpoint` records how many plan steps have
    completed, and `execute(..., resume_from=N)` continues from there instead
    of restarting the whole pipeline.
    """

    def __init__(
        self,
        agents: dict,
        approval_gate: ApprovalGate | None = None,
        auto_approve: bool = False,
        retry_policy: RetryPolicy | None = None,
        policy: ToolPolicy | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ):
        self.agents: dict = agents
        self.approval_gate = approval_gate or ApprovalGate()
        self.auto_approve = auto_approve
        self.retry_policy = retry_policy or RetryPolicy()
        self.policy = policy or DEFAULT_POLICY
        self._sleep = sleep

    def execute(
        self,
        run: WorkflowRun,
        plan: WorkflowPlan,
        kb: KnowledgeBase | None = None,
        resume_from: int = 0,
    ) -> WorkflowRun:
        run.plan = plan.to_dict()["steps"]
        run.status = Status.RUNNING
        run.log("plan", steps=run.plan)
        steps = plan.steps
        for idx in range(max(resume_from, run.checkpoint), len(steps)):
            role_name = steps[idx]
            role = AgentRole(role_name)
            if not self.policy.allows(role):
                run.status = Status.FAILED
                run.error = f"permission denied for role {role_name}"
                run.log("permission_denied", role=role_name)
                return run
            run.log("dispatch", role=role_name, step_index=idx)
            agent = self.agents[role_name]
            context = {}
            if kb is not None and role == AgentRole.RESEARCH:
                hits = kb.search(run.objective)
                context = {"sources": [d.to_dict() for d in hits]}
            task = Task(
                prompt=run.objective,
                role=role,
                context=context,
                id=self._task_id(run, idx, role),
            )
            t0 = time.time()
            try:
                result, attempts = self.retry_policy.run(
                    lambda a=agent, t=task: a.run(t), sleep=self._sleep
                )
            except WorkflowError as exc:
                attempts_used = exc.attempts if isinstance(exc, RetryExhausted) else 1
                run.attempts += attempts_used
                run.retries += max(0, attempts_used - 1)
                run.status = Status.FAILED
                run.error = f"{exc} for role {role_name}"
                run.log("failed", role=role_name, error=str(exc), attempts=attempts_used)
                return run
            run.attempts += attempts
            run.retries += max(0, attempts - 1)
            run.metrics[f"{role_name}.attempts"] = float(attempts)
            run.metrics[f"{role_name}.duration"] = round(time.time() - t0, 4)
            run.log("agent_result", **result.to_dict())
            if not result.passed_validation:
                run.status = Status.FAILED
                run.error = f"validation failed for {role_name}"
                return run
            if role == AgentRole.CONTENT:
                run.status = Status.AWAITING_APPROVAL
                approved = self.approval_gate.approve(result) or self.auto_approve
                run.log("approval", approved=approved)
                if not approved:
                    run.status = Status.REJECTED
                    run.error = "human rejected the content step"
                    return run
                run.status = Status.RUNNING
            run.checkpoint = idx + 1
        run.status = Status.COMPLETED
        run.log(
            "completed",
            at=time.time(),
            attempts=run.attempts,
            retries=run.retries,
            checkpoint=run.checkpoint,
        )
        return run

    @staticmethod
    def _task_id(run: WorkflowRun, idx: int, role: AgentRole) -> str:
        return f"{run.id}-{idx}-{role.value}"
