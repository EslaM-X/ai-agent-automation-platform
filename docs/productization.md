# Productization notes (v0.2)

What v0.2 adds over the v0.1 engineering lab, and why each piece exists.

## The gap v0.2 closes

v0.1 was a correct architecture with one major limitation stated honestly in
the changelog: "single-run orchestration; no retries or distributed execution
yet." v0.2 turns that into a platform a stranger can install, run, and trust
in minutes:

| Concern | v0.1 | v0.2 |
| --- | --- | --- |
| Transient provider failures | run failed | **retried with exponential backoff** |
| Failure classification | none | `TransientFailure` vs `PermanentFailure` |
| What an agent may do | anything | **`ToolPolicy` (deny-by-default)** |
| Re-running an objective | re-executes | **idempotency keys, replay returns the original run** |
| Interrupted run | restart from scratch | **checkpoint + `resume()`** |
| Quality signal | none | **offline rule-based `RuleEvaluator`** |
| Operations | audit trail only | **per-step duration/attempt metrics + `summarize()`** |

## Design constraints kept from v0.1

- Zero runtime dependencies (`dependencies = []`).
- Python >= 3.10.
- The entire test suite runs offline with a deterministic provider.
- The provider remains the only seam to the outside world.

## Failures are data

Failures are classified, retried, and audited — they are never silent.

- `TransientFailure` (timeout, rate limit, backend hiccup): retried with
  exponential backoff; the run records exactly how many attempts were used.
- `PermanentFailure` (bad request, rejected prompt): aborts immediately.
- `RetryExhausted` carries the underlying cause and attempt count so the run's
  `attempts`/`retries` accounting is precise.

## Permissions: deny-by-default

A `ToolPolicy` is an explicit allowlist of `AgentRole`s. The shipped roles are
granted; any future role is denied until explicitly granted. This keeps the
platform conservative about what an agent is allowed to do — the same posture
a production gate needs.

## Idempotency and resume

- `run(objective, idempotency_key="...")` maps the key to exactly one audited
  run; replays return the original object and never re-execute.
- `resume(run_id)` continues a failed run from its `checkpoint`. The in-memory
  registry is per-process; a persistent store can implement the same
  `Orchestrator.get`/`resume` surface.

## Evaluation without an LLM

`RuleEvaluator` scores the final agent output against deterministic rules
(contains / not_contains / min_length). This is deliberate: quality signals
must be reproducible, and they must run in CI and in the offline test suite.
A semantic evaluator can be added behind the same `Evaluator` protocol.

## Observability

Every dispatch, agent result, approval, retry, failure, and evaluation lands
in the audit trail. `AuditLog.summarize(run)` gives a one-line operational
summary: status, checkpoint, attempts, retries, event count, and per-step
durations.

## Roadmap

See [ROADMAP.md](../ROADMAP.md) for the product tiers (free runtime, hosted
execution, teams, enterprise) — deliberately unpriced until real usage
informs the numbers.
