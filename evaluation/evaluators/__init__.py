"""Dimension checkers for the evaluation harness.

Every checker inspects a real ``WorkflowRun`` produced by the real
``Orchestrator`` (never a mocked API) and returns ``(outcome, notes)`` where
``outcome`` is ``True``/``False`` when the case asserts that behavior, or
``None`` when the case does not assert it (skipped, not counted).
"""

from __future__ import annotations

from collections.abc import Callable

from evaluation.evaluators import correctness, execution, policy, safety

# (checker name, dimension, callable). Dimensions map 1:1 to the metrics the
# harness reports and the regression gate compares against a committed baseline.
CHECKERS: list[tuple[str, str, Callable[..., tuple[bool | None, list[str]]]]] = [
    ("correctness.status", "correctness", correctness.check_status),
    ("correctness.plan", "correctness", correctness.check_plan),
    ("correctness.evaluation", "correctness", correctness.check_evaluation),
    ("correctness.error", "correctness", correctness.check_error),
    ("policy.allowed", "policy", policy.check_allowed),
    ("policy.denied", "policy", policy.check_denied),
    ("safety.approval_requested", "safety", safety.check_approval_requested),
    ("safety.approval_decision", "safety", safety.check_approval_decision),
    ("safety.rejected_stops", "safety", safety.check_rejected_stops),
    ("safety.fail_closed", "safety", safety.check_fail_closed),
    ("execution.step_order", "execution", execution.check_step_order),
    ("execution.checkpoint", "execution", execution.check_checkpoint),
    ("execution.attempts", "execution", execution.check_attempts),
    ("execution.retries", "execution", execution.check_retries),
    ("execution.resume", "execution", execution.check_resume),
    ("auditability.audit", "auditability", execution.check_audit),
    ("idempotency.replay", "idempotency", execution.check_replay),
    ("idempotency.calls", "idempotency", execution.check_calls),
]

DIMENSIONS: list[str] = sorted({d for _, d, _ in CHECKERS})

__all__ = ["CHECKERS", "DIMENSIONS"]
