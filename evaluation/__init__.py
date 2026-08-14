"""Workflow evaluation.

The platform can evaluate outputs with no LLM in the loop: an Evaluator
applies deterministic rules (required content, forbidden content, minimum
length) and returns a score. That is what keeps the whole test suite offline
and makes quality signals reproducible — a deliberate counterweight to
LLM-only quality checks.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from core import WorkflowRun


@dataclass
class EvaluationResult:
    """Score for one run, between 0.0 and 1.0, with per-rule notes."""

    score: float
    passed: bool
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"score": self.score, "passed": self.passed, "notes": self.notes}


class Evaluator(Protocol):
    def evaluate(self, run: WorkflowRun) -> EvaluationResult: ...


@dataclass
class Rule:
    """One deterministic check against the final agent output.

    kind:
      "contains"      -> value (str) must appear
      "not_contains"  -> value (str) must not appear
      "min_length"    -> value (int) maximum length of output
    """

    kind: str
    value: str | int


def _final_output(run: WorkflowRun) -> str:
    """Last non-empty agent output recorded in the run (QA preferred)."""
    fallback = ""
    for step in reversed(run.steps):
        if step["step"] != "agent_result":
            continue
        output = step["data"].get("output", "")
        if not output:
            continue
        fallback = output
        if step["data"].get("role") == "qa":
            return output
    return fallback


class RuleEvaluator:
    """Scores a run's final output against deterministic rules."""

    def __init__(self, rules: list[Rule] | None = None, threshold: float = 1.0):
        self.rules = rules or []
        self.threshold = threshold

    def evaluate(self, run: WorkflowRun) -> EvaluationResult:
        if not run.steps:
            return EvaluationResult(0.0, False, ["no steps recorded"])
        output = _final_output(run)
        if not self.rules:
            passed_count = 1 if output else 0
            score = 1.0 if output else 0.0
            return EvaluationResult(score, passed_count == 1, ["output present"])
        notes: list[str] = []
        passed = 0
        for rule in self.rules:
            if rule.kind == "contains":
                ok = str(rule.value) in output
            elif rule.kind == "not_contains":
                ok = str(rule.value) not in output
            elif rule.kind == "min_length":
                ok = len(output) >= int(rule.value)
            else:
                ok = True
                notes.append(f"unknown rule {rule.kind!r} ignored")
                continue
            notes.append(f"{rule.kind}:{rule.value} -> {'pass' if ok else 'fail'}")
            if ok:
                passed += 1
        score = passed / len(self.rules) if self.rules else 0.0
        return EvaluationResult(round(score, 3), score >= self.threshold, notes)
