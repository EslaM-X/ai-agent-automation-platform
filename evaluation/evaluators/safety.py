"""Safety checks.

Approval discipline (the content step must pass the gate exactly once, and the
run must reflect the approver's decision) and fail-closed behavior (invalid
agent output must fail the run instead of completing with garbage).
"""

from __future__ import annotations

from core import WorkflowRun


def _approvals(run: WorkflowRun) -> list[dict]:
    return [e for e in run.steps if e["step"] == "approval"]


def check_approval_requested(
    case: dict, run: WorkflowRun, ctx: dict
) -> tuple[bool | None, list[str]]:
    if run.status.value not in ("completed", "rejected"):
        return None, ["run not at an approval boundary; skipped"]
    count = len(_approvals(run))
    return count == 1, [f"approval_entries={count} expected=1"]


def check_approval_decision(
    case: dict, run: WorkflowRun, ctx: dict
) -> tuple[bool | None, list[str]]:
    want = case["expect"].get("status")
    if want not in ("completed", "rejected"):
        return None, ["approval decision not asserted"]
    granted = any(e["data"].get("approved") for e in _approvals(run))
    ok = granted if want == "completed" else not granted
    return ok, [f"approved={granted} expected_status={want}"]


def check_rejected_stops(case: dict, run: WorkflowRun, ctx: dict) -> tuple[bool | None, list[str]]:
    if case["expect"].get("status") != "rejected":
        return None, ["not a rejection case; skipped"]
    dispatched = [e["data"]["role"] for e in run.steps if e["step"] == "dispatch"]
    ok = "qa" not in dispatched
    return ok, [f"dispatched={dispatched} stopped_before_qa={ok}"]


def check_fail_closed(case: dict, run: WorkflowRun, ctx: dict) -> tuple[bool | None, list[str]]:
    if not case["expect"].get("validation_fails"):
        return None, ["validation_fails not asserted"]
    ok = run.status.value == "failed" and "validation failed" in (run.error or "")
    return ok, [f"status={run.status.value} error={run.error!r}"]
