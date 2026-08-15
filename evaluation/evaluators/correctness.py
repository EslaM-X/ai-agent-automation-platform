"""Correctness checks.

These assert that a real WorkflowRun reached the outcome the case expects:
final status, plan order, evaluation result, and the error text. Each checker
returns (True/False/None, notes); None means the case did not assert it.
"""

from __future__ import annotations

from typing import Any

from core import WorkflowRun


def _expected(case: dict, key: str, default: Any = None) -> Any:
    return case["expect"].get(key, default)


def check_status(case: dict, run: WorkflowRun, ctx: dict) -> tuple[bool | None, list[str]]:
    want = _expected(case, "status")
    if want is None:
        return None, ["status not asserted"]
    got = run.status.value
    return got == want, [f"status={got} expected={want}"]


def check_plan(case: dict, run: WorkflowRun, ctx: dict) -> tuple[bool | None, list[str]]:
    want = _expected(case, "plan")
    if want is None:
        return None, ["plan not asserted"]
    return run.plan == want, [f"plan={run.plan}"]


def check_evaluation(case: dict, run: WorkflowRun, ctx: dict) -> tuple[bool | None, list[str]]:
    want = _expected(case, "evaluation_passed")
    if want is None:
        return None, ["evaluation not asserted"]
    evals = [e for e in run.steps if e["step"] == "evaluation"]
    got = bool(evals and evals[-1]["data"]["passed"])
    return got == want, [f"evaluation_passed={got} expected={want}"]


def check_error(case: dict, run: WorkflowRun, ctx: dict) -> tuple[bool | None, list[str]]:
    needle = _expected(case, "error_contains")
    if needle is None:
        return None, ["error not asserted"]
    got = needle in (run.error or "")
    return got, [f"error={run.error!r} expected_contains={needle!r}"]
