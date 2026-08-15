"""Human-readable report for the evaluation harness."""

from __future__ import annotations


def _pct(rate: float | None) -> str:
    if rate is None:
        return "  n/a"
    return f"{rate * 100:5.1f}%"


def print_suite(suite: dict) -> None:
    dims = suite["dimensions"]
    print()
    print("== AI Agent Automation Platform - Evaluation Harness ==")
    print(f"cases       : {suite['cases_passed']}/{suite['cases_total']} passed")
    width = max(len(d) for d in dims)
    for dim in sorted(dims):
        m = dims[dim]
        if not m["checked"]:
            print(f"  {dim:<{width}}  -")
            continue
        print(f"  {dim:<{width}}  {m['passed']:>3}/{m['checked']:<3}  {_pct(m['rate'])}")
    failed = [c for c in suite["cases"] if not c["passed"]]
    if failed:
        print()
        print("failed cases:")
        for case in failed:
            print(f"  [{case['id']}] {case['objective']}")
            for f in case["checks"]:
                if not f["passed"]:
                    print(f"    - {f['checker']}: {f['notes']}")
    print()
