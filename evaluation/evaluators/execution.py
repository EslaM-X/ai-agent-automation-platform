"""Execution, auditability, and idempotency checks.

Execution: step order, checkpoint advancement, and attempt/retry accounting.
Auditability: every dispatch, agent result, approval, and evaluation recorded
in the run must be mirrored in the audit log. Idempotency: a replay with the
same key returns the original run and never re-executes provider calls.
"""

from __future__ import annotations

from core import WorkflowRun

_AUDITABLE_STEPS = (
    "dispatch",
    "agent_result",
    "approval",
    "evaluation",
    "failed",
    "permission_denied",
)


def check_step_order(case: dict, run: WorkflowRun, ctx: dict) -> tuple[bool | None, list[str]]:
    if case["expect"].get("resume"):
        return None, ["resumed runs legitimately re-dispatch the failed step; skipped"]
    if run.status.value != "completed":
        return None, ["run not completed; step order skipped"]
    dispatched = [e["data"]["role"] for e in run.steps if e["step"] == "dispatch"]
    plan = case["expect"].get("plan") or []
    return dispatched == plan, [f"dispatch_order={dispatched}"]


def check_checkpoint(case: dict, run: WorkflowRun, ctx: dict) -> tuple[bool | None, list[str]]:
    want = case["expect"].get("checkpoint")
    if want is None:
        return None, ["checkpoint not asserted"]
    return run.checkpoint == want, [f"checkpoint={run.checkpoint} expected={want}"]


def check_attempts(case: dict, run: WorkflowRun, ctx: dict) -> tuple[bool | None, list[str]]:
    want = case["expect"].get("attempts")
    if want is None:
        return None, ["attempts not asserted"]
    return run.attempts == want, [f"attempts={run.attempts} expected={want}"]


def check_retries(case: dict, run: WorkflowRun, ctx: dict) -> tuple[bool | None, list[str]]:
    want = case["expect"].get("retries")
    if want is None:
        return None, ["retries not asserted"]
    return run.retries == want, [f"retries={run.retries} expected={want}"]


def check_resume(case: dict, run: WorkflowRun, ctx: dict) -> tuple[bool | None, list[str]]:
    if not case["expect"].get("resume"):
        return None, ["resume not asserted"]
    resumed = ctx["resumed_run"]
    calls = ctx["provider"].calls
    ok = (
        resumed.status.value == "completed"
        and calls.count("research") == 1
        and calls.count("content") == 1
    )
    return ok, [
        (
            f"resumed_status={resumed.status.value} "
            f"research_calls={calls.count('research')} "
            f"content_calls={calls.count('content')} "
            f"qa_calls={calls.count('qa')}"
        )
    ]


def check_audit(case: dict, run: WorkflowRun, ctx: dict) -> tuple[bool | None, list[str]]:
    entries = ctx["orchestrator"].audit.for_workflow(run.id)
    log_steps = {e.step for e in entries}
    missing = [
        e["step"] for e in run.steps if e["step"] in _AUDITABLE_STEPS and e["step"] not in log_steps
    ]
    return not missing, [f"audit_entries={len(entries)} missing={missing}"]


def check_replay(case: dict, run: WorkflowRun, ctx: dict) -> tuple[bool | None, list[str]]:
    if not case["config"].get("replay"):
        return None, ["replay not asserted"]
    same = ctx["replay_run"].id == run.id
    return same, [f"replay_returns_same_id={same}"]


def check_calls(case: dict, run: WorkflowRun, ctx: dict) -> tuple[bool | None, list[str]]:
    want = case["expect"].get("provider_calls")
    if want is None:
        return None, ["provider_calls not asserted"]
    got = len(ctx["provider"].calls)
    return got == want, [f"provider_calls={got} expected={want}"]
