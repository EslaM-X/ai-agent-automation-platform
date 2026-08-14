# Architecture

## Layering

```
Objective
   │
   ▼
Planner ──────────────▶ WorkflowPlan (ordered roles)
   │
   ▼
Executor
   ├── ToolPolicy ──────▶ permission check (deny-by-default)
   ├── RetryPolicy ─────▶ retry transient failures with backoff
   ├── ApprovalGate ────▶ human gate before irreversible work
   └── Checkpoint ──────▶ resume from the last completed step
   │
   ▼
Specialized agents ────▶ Research → Content → QA (Provider seam)
   │
   ▼
Evaluation ────────────▶ deterministic rule scoring (offline)
   │
   ▼
AuditLog ──────────────▶ append-only trace + operational summary
```

## Key interfaces

- **`Provider.complete(system, user, temperature) -> str`** — the only seam to
  the outside world. Swap OpenAI, local models, or a fake for tests.
- **`Agent.run(task) -> AgentResult`** — every agent returns a validated result
  with `passed_validation` and notes.
- **`ToolPolicy.allows(role) -> bool`** — the permission gate every dispatch
  passes through; unknown roles are denied.
- **`RetryPolicy.run(fn, sleep, retryable)`** — classifies and retries
  `TransientFailure`; permanent failures abort.
- **`KnowledgeBase.search(query, top_k) -> [Document]`** — retrieval is an
  interface, not an implementation.
- **`Evaluator.evaluate(run) -> EvaluationResult`** — deterministic, offline,
  rule-based quality scoring.
- **`AuditLog.record(...)` / `AuditLog.summarize(run)`** — append-only trace
  plus one-line operational status, metrics, and retry counts.

## State machine

```
pending → planning → running → awaiting_approval → approved → completed
                          │            │
                          ▼            ▼
                        failed      rejected
```

`failed` runs keep a checkpoint, so `Orchestrator.resume(run_id)` continues
from the last completed step without redoing work.

## Idempotency and execution state

- Every `run(objective, idempotency_key=...)` stores its audited run; a replay
  with the same key returns the original run object — no re-execution.
- `WorkflowRun` carries `checkpoint`, `attempts`, `retries`, `metrics`, and
  `plan`, all of which surface in `to_dict()` and `AuditLog.summarize()`.

## See also

- [Methodology](methodology.md)
- [Productization notes](productization.md)
- [Roadmap](../ROADMAP.md)
