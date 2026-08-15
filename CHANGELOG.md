# Changelog

All notable changes to `ai-agent-automation-platform`.

## [v0.3.0] — 2026-08-15

Evaluation harness release: the platform now ships with a deterministic,
offline harness that proves its own guarantees and gates CI against a
committed baseline.

### Added
- Evaluation harness (`evaluation/runner.py`, `evaluation/evaluators/`,
  `evaluation/metrics.py`, `evaluation/report.py`): drives the real
  `Orchestrator` with case-defined providers (no LLM, no network) and asserts
  behavior across six dimensions - correctness, policy, safety, execution,
  auditability, idempotency.
- 17 scenario cases in `evaluation/cases/` (basic, approval, failure recovery,
  idempotency), including transient-vs-permanent failures, exhausted retries,
  resume-without-redo, validation fail-closed, and replay semantics.
- Regression gate: `python -m evaluation.runner --gate` compares every case
  and dimension rate against the committed `benchmarks/baseline.json` and
  fails on any regression; wired into CI on every push/PR.
- `benchmarks/` with a committed, deterministic baseline and a gitignored
  `latest.json` for local inspection.
- `docs/` pointers and README section documenting the harness and how to
  refresh the baseline only for intended behavior changes.

### Changed
- Package version 0.2.0 -> 0.3.0.
- CI now runs the harness gate in addition to tests, lint, and the demo smoke
  test.

## [v0.2.0] — 2026-08-14

Productization release: the engineering lab becomes an installable,
trustable platform for strangers.

### Added
- Retry policy with exponential backoff for transient failures; permanent
  failures abort with an audited error (`RetryExhausted` carries attempt counts).
- Failure taxonomy: `TransientFailure` vs `PermanentFailure` (`core/errors.py`).
- Tool permissions: `ToolPolicy` with deny-by-default for unknown roles.
- Idempotency keys: `run(objective, idempotency_key=...)` replays return the
  original audited run without re-execution.
- Resumable runs: `Orchestrator.resume(run_id)` continues a failed run from
  its checkpoint without redoing completed steps.
- Deterministic offline evaluation: `RuleEvaluator` (contains /
  not_contains / min_length) via the new `evaluation/` package.
- Observability: per-step duration/attempt metrics on `WorkflowRun` and
  `AuditLog.summarize()` operational summaries.
- 60-second demo: `examples/demo_60s.py` (retry, idempotency, evaluation,
  summary in one offline run).
- Contributor experience: issue templates (bug/feature/evaluation), PR
  template, discussion template, roadmap.
- Corrected `docs/architecture.md` (previously contained robotics-project
  content) and fixed doc cross-references.
- CI now smoke-tests the demo and lints `evaluation/`.

### Changed
- Test suite grew from 10 to 22 tests, all offline with a deterministic
  provider.
- `WorkflowRun` carries execution state: `checkpoint`, `attempts`, `retries`,
  `idempotency_key`, `metrics`, `plan`.

### Known limitations
- Run registry and audit log are in-memory (per-process); a persistent store
  can implement the same interfaces.
- Knowledge base is keyword search, not semantic retrieval.
- Evaluation is rule-based by design; a semantic evaluator can be added
  behind the same `Evaluator` protocol.
- Agent prompts are templates; output quality depends on the provider.

## [v0.1.0] — 2026-08-14

Initial release.

### Added
- Orchestrator entry point (`run(objective) -> WorkflowRun`).
- Specialized agents: research, content, QA, analytics over a `Provider` interface.
- Workflow layer: `Planner`, `ApprovalGate`, `Executor`.
- Knowledge base interface (in-memory keyword search shipped).
- Append-only audit log and observability.
- Offline test suite (10 tests) using a deterministic fake provider.
- Example CLI.

### Known limitations
- Knowledge base is keyword search, not semantic retrieval.
- Agent prompts are templates; output quality depends on the provider.
- Single-run orchestration; no retries or distributed execution yet.
