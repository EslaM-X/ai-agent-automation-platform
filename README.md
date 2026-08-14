# ai-agent-automation-platform

> Governed AI agent orchestration: **Plan -> Specialized Agents -> Human Approval -> Execute -> Audit** — offline-testable, retry-hardened, idempotent, and permission-gated.

Not a `User -> LLM -> Answer` wrapper. The platform routes work through an explicit pipeline with planning, specialized agents, a human approval gate, validation, deterministic evaluation, and a full audit trail — and the entire test suite runs with **no LLM, no API keys, no network**.

**Part of [EslaM-X's engineering portfolio](https://github.com/EslaM-X/portfolio).**

---

## Build your first governed AI workflow in 60 seconds

```bash
git clone https://github.com/EslaM-X/ai-agent-automation-platform.git
cd ai-agent-automation-platform
pip install -e .
python examples/demo_60s.py
```

That is the whole demo: a governed workflow runs (planning -> research -> content -> QA -> approval -> evaluation), a transient failure is retried automatically, the run is **idempotent**, and the full operational summary prints at the end. No keys, no network.

```text
  [research] Facts: Q3 revenue up 12%, costs flat, churn down.
  [ content] Draft: Q3 was strong across revenue and retention.
  [      qa] QA: no blocking issues on the Q3 draft; recommend a follow-up on margins.
  evaluation  : score=1.0 passed=True
  status       : completed
  attempts     : 4
  retries      : 1
  idempotency_key: q3-summary
```

Run the whole test suite in a few seconds more:

```bash
python -m pytest tests/ -q    # 22 tests, fully offline
```

A 15-30 second recording guide for this demo is in [docs/demo-recording.md](docs/demo-recording.md).

---

## Why this exists

AI agents keep gaining autonomy, but autonomy without control is a liability.
This platform adds the parts that production systems need and demos usually
skip:

- **Human approval before irreversible work** — a real gate, not a flag.
- **Tool permissions** — a `ToolPolicy` decides which agent roles may run;
  unknown roles are denied by default.
- **Retries with backoff** — transient failures are classified and retried;
  permanent failures abort with a clear audited error.
- **Idempotency** — replay an objective with the same key and you get the
  original run back. No duplicate work, no duplicate side effects.
- **Resumable runs** — a failed run continues from its checkpoint instead of
  restarting the whole pipeline.
- **Deterministic evaluation** — rule-based scoring that runs offline, so
  quality signals are reproducible, not LLM-dependent.
- **Observability** — every dispatch, approval, retry, and duration lands in
  an audit trail plus an operational summary.

## Pipeline

```
Trigger
  -> Planner (research -> content -> qa)
  -> Agent Router (specialized agents)
  -> Research Agent -> Content Agent -> QA Agent
  -> Approval Layer (human gate before irreversible action)
  -> Execution -> Evaluation -> Observability / Audit Log
```

## Components

| Module | Responsibility |
| --- | --- |
| `orchestrator/` | Public entry point; wires planner, executor, audit, retries, policy, idempotency, resume |
| `agents/` | Specialized agents (research, content, qa, analytics) over a `Provider` interface |
| `workflow/` | Planner, ApprovalGate, Executor, RetryPolicy |
| `knowledge/` | Retrieval interface (in-memory keyword KB shipped; swap for a vector store) |
| `evaluation/` | Offline rule-based evaluation of run outputs |
| `observability/` | Append-only audit log + operational summaries |
| `core/` | Shared, provider-agnostic types, failure taxonomy, tool policy |

## Design decisions

- **Provider is the only seam to the outside world.** Tests inject a
  deterministic fake provider - no network, no keys, reproducible runs.
- **Human approval is explicit.** Content must pass an approval gate before
  the run completes; `auto_approve=True` exists only for tests/automation.
- **Validation before completion.** An agent that returns empty output fails
  the run instead of silently producing garbage.
- **Failures are classified.** `TransientFailure` is retried with exponential
  backoff; `PermanentFailure` aborts immediately. Both are audited.
- **Deny-by-default permissions.** A role must be explicitly granted by the
  `ToolPolicy` before it can be dispatched.
- **Replays never re-execute.** An idempotency key maps to one audited run.
- **Everything is audited.** Each dispatch, agent result, approval decision,
  retry, and evaluation lands in the audit log.

## Install

```bash
pip install -e ".[test]"        # test tooling
pip install -e ".[openai]"      # optional OpenAI-backed provider example
```

Requires Python >= 3.10.

## Run

```bash
python examples/demo_60s.py        # 60-second governed workflow demo
python examples/run_workflow.py    # minimal end-to-end example
```

## Test

```bash
python -m pytest tests/ -v
```

The suite is fully offline: 22 tests covering orchestration, approval,
retries, permissions, idempotency, resume, evaluation, and observability.

## Repo layout

```
orchestrator/  public entry point (idempotency, resume, policy, evaluation)
agents/        specialized agents over a Provider interface
workflow/      planner, approval gate, executor, retry policy
knowledge/     retrieval interface
evaluation/    offline rule-based evaluation
observability/ audit log + summaries
examples/      runnable demos (60s quickstart, minimal run)
tests/         offline test suite (22 tests)
docs/          architecture, methodology, productization, demo recording
```

## Documentation

- [Productization notes](docs/productization.md) - what v0.2 adds and why
- [Architecture](docs/architecture.md)
- [Methodology](docs/methodology.md)
- [Roadmap](ROADMAP.md) - free / hosted tiers, evaluation, contributor funnel

## Contributing

Want to contribute? The repository is designed so a first-time contributor
can land a small, reviewable change quickly.

1. Pick an open issue (labels like `good first issue` or `help wanted`).
2. Read [CONTRIBUTING.md](CONTRIBUTING.md) and the [code of conduct](CODE_OF_CONDUCT.md).
3. Run the test suite and keep it green: `python -m pytest tests/`.
4. Keep `ruff check` and `ruff format --check` clean.
5. Open your pull request - maintainers review and merge.
6. Your name goes on the contributor wall.

## Honesty boundary

- The shipped `KnowledgeBase` is in-memory keyword search - a production vector
  store is a drop-in `KnowledgeBase` subclass, not a rewrite.
- Agent prompts are templates; quality depends on the provider, and that is
  stated rather than hidden.
- Evaluation is rule-based and deterministic by design; a semantic evaluator
  can be added behind the same `Evaluator` interface.

---

## License

Apache-2.0. Copyright (c) 2026 EslaM-X. See [LICENSE](LICENSE).
