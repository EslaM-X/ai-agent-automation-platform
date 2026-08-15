"""Metric aggregation for the evaluation harness.

Numbers are computed from the actual case results produced by the runner — the
report never claims a rate that was not measured.
"""

from __future__ import annotations

from evaluation.evaluators import DIMENSIONS


def compute_dimensions(case_results: list[dict]) -> dict:
    """Aggregate per-case dimension results into per-dimension rates.

    A case counts toward a dimension when at least one checker of that
    dimension was asserted; it passes the dimension when every asserted
    checker of that dimension passed.
    """
    counts = {d: {"checked": 0, "passed": 0} for d in DIMENSIONS}
    for result in case_results:
        for dim, state in result["dimensions"].items():
            if not state["checked"]:
                continue
            counts[dim]["checked"] += 1
            if state["passed"]:
                counts[dim]["passed"] += 1
    metrics: dict[str, dict] = {}
    for dim in DIMENSIONS:
        c = counts[dim]
        checked = c["checked"]
        metrics[dim] = {
            "checked": checked,
            "passed": c["passed"],
            "rate": round(c["passed"] / checked, 4) if checked else None,
        }
    return metrics


def summarize(case_results: list[dict]) -> dict:
    """Top-level suite summary used by both the report and the baseline."""
    passed = sum(1 for r in case_results if r["passed"])
    return {
        "schema": "ai-agent-evaluation-harness/v1",
        "cases_total": len(case_results),
        "cases_passed": passed,
        "cases_failed": len(case_results) - passed,
        "dimensions": compute_dimensions(case_results),
        "cases": case_results,
    }
