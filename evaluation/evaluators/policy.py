"""Tool-policy checks.

Permission gating must be deny-by-default: a role that is not on the allowlist
blocks the run with a `permission_denied` audit entry, while an allowlisted
plan executes end to end.
"""

from __future__ import annotations

from core import WorkflowRun


def _has_step(run: WorkflowRun, step: str) -> bool:
    return any(e["step"] == step for e in run.steps)


def check_allowed(case: dict, run: WorkflowRun, ctx: dict) -> tuple[bool | None, list[str]]:
    if case["expect"].get("permission_denied"):
        return None, ["denied case; allowed-role check skipped"]
    dispatched = [e["data"]["role"] for e in run.steps if e["step"] == "dispatch"]
    plan = case["expect"].get("plan") or []
    return dispatched == plan, [f"dispatched={dispatched}"]


def check_denied(case: dict, run: WorkflowRun, ctx: dict) -> tuple[bool | None, list[str]]:
    if not case["expect"].get("permission_denied"):
        return None, ["permission_denied not asserted"]
    ok = (
        run.status.value == "failed"
        and "permission denied" in (run.error or "")
        and _has_step(run, "permission_denied")
    )
    return ok, [
        (
            f"status={run.status.value} error={run.error!r} "
            f"audited={_has_step(run, 'permission_denied')}"
        )
    ]
