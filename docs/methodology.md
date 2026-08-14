# Architecture

## Pipeline

```
Objective
  → Planner (research → content → qa)
  → Executor
      → Agent Router
          → Research Agent (with knowledge-base grounding)
          → Content Agent
              → Approval Gate (human)
              → QA Agent
  → Audit Log
```

## Key interfaces

- **`Provider.complete(system, user, temperature) -> str`** — the only seam to
  the outside world. Swap OpenAI, local models, or a fake for tests.
- **`Agent.run(task) -> AgentResult`** — every agent returns a validated result
  with `passed_validation` and notes.
- **`KnowledgeBase.search(query, top_k) -> [Document]`** — retrieval is an
  interface, not an implementation.
- **`AuditLog.record(...)`** — append-only trace of every workflow.

## State machine

```
pending → planning → running → awaiting_approval → approved → completed
                          │            │
                          ▼            ▼
                        failed      rejected
```

## See also

- `docs/methodology.md`
