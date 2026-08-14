"""Tests for the v0.2 production features.

Everything runs offline with a deterministic provider: retries, permission
gating, idempotency, checkpoint/resume, evaluation, and run metrics.
"""

import pytest

from agents import AgentRole
from core import Status
from core.errors import PermanentFailure, TransientFailure
from core.policy import ToolPolicy
from evaluation import Rule, RuleEvaluator
from orchestrator import Orchestrator
from workflow.retry import RetryPolicy


class CallRecordingProvider:
    """Fake provider that records every complete() call."""

    def __init__(self, replies=None, raises=None):
        self.replies = replies or {
            "research": "RESEARCH: found 3 key facts.",
            "content": "CONTENT: draft is ready.",
            "qa": "QA: no blocking issues found.",
            "analytics": "ANALYTICS: trend is positive.",
        }
        self.raises = raises or {}
        self.calls: list[str] = []

    def complete(self, system: str, user: str, temperature: float = 0.2) -> str:
        lowered = system.lower()
        for role, reply in self.replies.items():
            if role in lowered:
                self.calls.append(role)
                exc = self.raises.get(role)
                if exc is not None:
                    raise exc
                return reply
        return "OK"


@pytest.fixture
def provider():
    return CallRecordingProvider()


def make_orchestrator(provider, **kwargs):
    return Orchestrator(provider, auto_approve=True, **kwargs)


def test_transient_failure_is_retried_then_succeeds():
    provider = CallRecordingProvider()
    original = provider.complete
    attempts = {"n": 0}

    def flaky(system, user, temperature=0.2):
        if "research agent" in system.lower() and attempts["n"] == 0:
            attempts["n"] += 1
            raise TransientFailure("backend timed out")
        attempts["n"] += 1
        return original(system, user, temperature)

    provider.complete = flaky
    orc = make_orchestrator(provider, retry_policy=RetryPolicy(max_attempts=3, base_delay=0))
    run = orc.run("Retry me")
    assert run.status == Status.COMPLETED
    assert run.attempts == 4  # 3 roles; research failed once then retried
    assert run.retries == 1
    assert run.metrics["research.attempts"] == 2


def test_retries_exhausted_fails_run():
    def always_fail(system, user, temperature=0.2):
        raise TransientFailure("always down")

    provider = CallRecordingProvider()
    provider.complete = always_fail
    orc = make_orchestrator(provider, retry_policy=RetryPolicy(max_attempts=2, base_delay=0))
    run = orc.run("Doomed")
    assert run.status == Status.FAILED
    assert "always down" in run.error
    assert run.attempts == 2
    assert run.retries == 1
    assert any(e["step"] == "failed" for e in run.steps)


def test_permanent_failure_is_not_retried():
    def reject(system, user, temperature=0.2):
        raise PermanentFailure("prompt rejected")

    provider = CallRecordingProvider()
    provider.complete = reject
    orc = make_orchestrator(provider, retry_policy=RetryPolicy(max_attempts=3, base_delay=0))
    run = orc.run("No retries")
    assert run.status == Status.FAILED
    assert run.attempts == 1
    assert run.retries == 0


def test_policy_denies_disallowed_role(provider):
    policy = ToolPolicy({AgentRole.RESEARCH})
    orc = make_orchestrator(provider, policy=policy)
    run = orc.run("Blocked content")
    assert run.status == Status.FAILED
    assert "permission denied" in run.error
    assert any(e["step"] == "permission_denied" for e in run.steps)


def test_policy_can_be_extended(provider):
    policy = ToolPolicy({AgentRole.RESEARCH, AgentRole.CONTENT})
    policy.grant(AgentRole.QA)
    orc = make_orchestrator(provider, policy=policy)
    run = orc.run("Granted")
    assert run.status == Status.COMPLETED


def test_idempotency_key_returns_original_run(provider):
    orc = make_orchestrator(provider)
    first = orc.run("Summarize Q3", idempotency_key="q3")
    replay = orc.run("Summarize Q3", idempotency_key="q3")
    assert replay.id == first.id
    assert len(provider.calls) == 3  # executed once, not twice


def test_resume_continues_from_checkpoint():
    class ResumeProvider(CallRecordingProvider):
        def __init__(self):
            super().__init__()
            self.fail_once = True

        def complete(self, system, user, temperature=0.2):
            lowered = system.lower()
            for role, reply in self.replies.items():
                if role in lowered:
                    self.calls.append(role)
                    if role == "qa" and self.fail_once:
                        self.fail_once = False
                        raise PermanentFailure("qa transient outage")
                    return reply
            return "OK"

    provider = ResumeProvider()
    orc = make_orchestrator(provider)
    failed = orc.run("Resume me")
    assert failed.status == Status.FAILED
    assert provider.calls.count("research") == 1
    assert provider.calls.count("content") == 1
    resumed = orc.resume(failed.id)
    assert resumed.status == Status.COMPLETED
    assert provider.calls.count("research") == 1  # not re-run
    assert provider.calls.count("content") == 1
    assert provider.calls.count("qa") == 2
    assert resumed.checkpoint == 3


def test_resume_unknown_run_raises():
    orc = make_orchestrator(CallRecordingProvider())
    with pytest.raises(KeyError):
        orc.resume("does-not-exist")


def test_rule_evaluator_scores_and_records():
    provider = CallRecordingProvider()
    rules = [
        Rule("contains", "no blocking issues"),
        Rule("not_contains", "ERROR"),
        Rule("min_length", 5),
    ]
    orc = make_orchestrator(provider, evaluator=RuleEvaluator(rules))
    run = orc.run("Evaluate me")
    assert run.status == Status.COMPLETED
    evals = [e for e in run.steps if e["step"] == "evaluation"]
    assert len(evals) == 1
    assert evals[0]["data"]["passed"] is True
    assert evals[0]["data"]["score"] == 1.0


def test_rule_evaluator_can_fail():
    provider = CallRecordingProvider()
    rules = [Rule("contains", "this text is definitely absent")]
    orc = make_orchestrator(provider, evaluator=RuleEvaluator(rules))
    run = orc.run("Evaluate fail")
    evals = [e for e in run.steps if e["step"] == "evaluation"]
    assert evals[0]["data"]["passed"] is False
    assert evals[0]["data"]["score"] == 0.0


def test_run_carries_metrics_and_summary(provider):
    orc = make_orchestrator(provider)
    run = orc.run("Metrics")
    for role in ("research", "content", "qa"):
        assert f"{role}.duration" in run.metrics
        assert f"{role}.attempts" in run.metrics
    summary = orc.audit.summarize(run)
    assert summary["status"] == "completed"
    assert summary["checkpoint"] == 3
    assert summary["attempts"] == 3
    assert summary["retries"] == 0
    assert "metrics" in summary


def test_research_agent_retries_via_workflow_level():
    provider = CallRecordingProvider()
    original = provider.complete
    fired = {"n": 0}

    def flaky(system, user, temperature=0.2):
        if "research agent" in system.lower() and fired["n"] == 0:
            fired["n"] += 1
            raise TransientFailure("rate limited")
        return original(system, user, temperature)

    provider.complete = flaky
    orc = make_orchestrator(provider, retry_policy=RetryPolicy(max_attempts=3, base_delay=0))
    run = orc.run("Flaky")
    assert run.status == Status.COMPLETED
    assert run.retries == 1
