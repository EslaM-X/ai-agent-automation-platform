"""Orchestrator: the public entry point that ties the pipeline together.

Production features beyond v0.1:
- idempotency keys (a replayed objective returns the original audited run),
- resumable runs (failed runs continue from their checkpoint),
- a tool policy that gates which roles may be dispatched,
- deterministic evaluation hooks recorded into the audit trail,
- per-step duration and retry metrics surfaced on every run.
"""

from __future__ import annotations

from collections.abc import Callable

from agents import Provider, build_agent
from core import AgentResult, AgentRole, Status, WorkflowRun
from core.policy import DEFAULT_POLICY, ToolPolicy
from evaluation import Evaluator
from knowledge import KnowledgeBase
from observability import AuditLog
from workflow import ApprovalGate, Executor, Planner, WorkflowPlan
from workflow.retry import RetryPolicy


class Orchestrator:
    """Coordinates planning, execution, approval, and audit.

    Example:
        orc = Orchestrator(provider, auto_approve=True)
        run = orc.run("Summarize our Q3 results")
        print(run.to_dict())

        orc = Orchestrator(provider, auto_approve=True)
        run = orc.run("Summarize our Q3 results", idempotency_key="q3-summary")
        replay = orc.run("Summarize our Q3 results", idempotency_key="q3-summary")
        assert replay.id == run.id  # no re-execution
    """

    def __init__(
        self,
        provider: Provider,
        approver: Callable[[AgentResult], bool] | None = None,
        auto_approve: bool = False,
        kb: KnowledgeBase | None = None,
        retry_policy: RetryPolicy | None = None,
        policy: ToolPolicy | None = None,
        evaluator: Evaluator | None = None,
    ):
        self.provider = provider
        self.agents: dict = {role.value: build_agent(role, provider) for role in AgentRole}
        self.planner = Planner()
        self.audit = AuditLog()
        gate = ApprovalGate(approver)
        self.executor = Executor(
            self.agents,
            approval_gate=gate,
            auto_approve=auto_approve,
            retry_policy=retry_policy,
            policy=policy or DEFAULT_POLICY,
        )
        self.kb = kb
        self.evaluator = evaluator
        self._runs: dict[str, WorkflowRun] = {}
        self._completed: dict[str, WorkflowRun] = {}

    def run(self, objective: str, idempotency_key: str | None = None) -> WorkflowRun:
        if idempotency_key is not None:
            cached = self._completed.get(idempotency_key)
            if cached is not None:
                return cached
        run = WorkflowRun(
            objective=objective,
            status=Status.PLANNING,
            idempotency_key=idempotency_key,
        )
        run.log("objective", objective=objective)
        plan = self.planner.plan(objective)
        self.executor.execute(run, plan, kb=self.kb)
        if self.evaluator is not None:
            evaluation = self.evaluator.evaluate(run)
            run.log("evaluation", **evaluation.to_dict())
        self.audit.observe(run)
        self._runs[run.id] = run
        if idempotency_key is not None:
            self._completed[idempotency_key] = run
        return run

    def resume(self, run_id: str) -> WorkflowRun:
        """Continue a failed run from its checkpoint without redoing work.

        Requires a reference to the run object; because the default audit log
        is in-memory, resuming across processes needs a persistent store.
        """
        run = self._runs.get(run_id)
        if run is None:
            raise KeyError(f"unknown run {run_id}")
        if run.status in (Status.COMPLETED, Status.REJECTED, Status.CANCELLED):
            return run
        plan = WorkflowPlan(steps=run.plan or self.planner.plan(run.objective).steps)
        self.executor.execute(run, plan, kb=self.kb)
        self.audit.observe(run)
        return run

    def get(self, run_id: str) -> WorkflowRun | None:
        return self._runs.get(run_id)
