# ai-agent-automation-platform

> Production-oriented AI agent orchestration platform for knowledge-driven
> automation, workflow execution, content operations, and observability.

Not a `User → LLM → Answer` wrapper. The platform routes work through an
explicit pipeline with planning, specialized agents, human approval,
validation, execution, and a full audit trail — all testable offline.

**Part of [EslaM-X's engineering portfolio](https://github.com/EslaM-X/portfolio).**

---

## Pipeline

```
Trigger
  → Planner (research → content → qa)
  → Agent Router (specialized agents)
  → Research Agent → Content Agent → QA Agent
  → Approval Layer (human gate before irreversible action)
  → Execution → Observability / Audit Log
```

## Components

| Module | Responsibility |
| --- | --- |
| `orchestrator/` | Public entry point; wires planner, executor, audit |
| `agents/` | Specialized agents (research, content, qa, analytics) over a `Provider` interface |
| `workflow/` | Planner, ApprovalGate, Executor |
| `knowledge/` | Retrieval interface (in-memory keyword KB shipped; swap for a vector store) |
| `observability/` | Append-only audit log |
| `core/` | Shared, provider-agnostic types |

## Design decisions

- **Provider is the only seam to the outside world.** Tests inject a
  deterministic fake provider — no network, no keys, reproducible runs.
- **Human approval is explicit.** Content must pass an approval gate before the
  run completes; `auto_approve=True` exists only for tests/automation.
- **Validation before completion.** An agent that returns empty output fails the
  run instead of silently producing garbage.
- **Everything is audited.** Each dispatch, agent result, and approval decision
  lands in the audit log.

## Install

```bash
pip install -e ".[test]"        # test tooling
pip install -e ".[openai]"      # optional OpenAI-backed provider example
```

Requires Python ≥ 3.10.

## Run

```bash
python examples/run_workflow.py
```

## Test

```bash
python -m pytest tests/
```

## Repo layout

```
orchestrator/  core.py (types) + entry point
agents/        specialized agents
workflow/      planner, approval gate, executor
knowledge/     retrieval interface
observability/ audit log
examples/      runnable demo
tests/         offline test suite
docs/          architecture + methodology
```

## Honesty boundary

- The shipped `KnowledgeBase` is in-memory keyword search — a production vector
  store is a drop-in `KnowledgeBase` subclass, not a rewrite.
- Agent prompts are templates; quality depends on the provider, and that is
  stated rather than hidden.

---

## License

Apache-2.0. Copyright © 2026 EslaM-X. See [LICENSE](LICENSE).
