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

## Diagram

Source: [diagrams/ai-agent-platform.mmd](diagrams/ai-agent-platform.mmd)
(rendered inline for GitHub; edit the `.mmd`, regenerate with `mmdc`).

```mermaid
flowchart TB
    subgraph TRUST["Trust boundary - untrusted input"]
        USER["User / Task<br/>objective + idempotency_key"]
    end

    ORCH["Orchestrator<br/>orchestrator/__init__.py - run / resume"]
    IDEM["Idempotency registry<br/>key -> cached WorkflowRun"]
    PLAN["Planner<br/>workflow/__init__.py - research -> content -> qa"]
    POLICY["ToolPolicy<br/>core/policy.py - deny-by-default"]
    AGENTS["Specialized agents<br/>agents/__init__.py<br/>research / content / qa / analytics<br/>over Provider (sole seam to the outside)"]
    VALID["Output validation<br/>empty output -> fail closed"]
    RETRY["RetryPolicy<br/>workflow/retry.py<br/>TransientFailure vs PermanentFailure<br/>core/errors.py"]
    GATE["ApprovalGate<br/>workflow/__init__.py<br/>content step - human or auto_approve"]
    EXEC["Executor<br/>workflow/__init__.py<br/>checkpoint / attempts / validation"]
    EVAL["RuleEvaluator<br/>evaluation/__init__.py<br/>contains / not_contains / min_length"]
    AUDIT["AuditLog<br/>observability/__init__.py<br/>append-only, every step"]

    HARNESS["Evaluation Harness<br/>evaluation/runner.py<br/>drives the REAL Orchestrator<br/>with deterministic CaseProvider"]
    CASES["17 cases<br/>evaluation/cases/*.json<br/>basic / approval / failure / idempotency"]
    BASELINE["benchmarks/baseline.json<br/>committed, deterministic"]
    CI_GATE["Regression Gate<br/>CI step: python -m evaluation.runner --gate"]

    USER --> ORCH
    ORCH --> IDEM
    IDEM -- "key seen: replay stored run, no re-execution" --> ORCH
    ORCH --> PLAN
    PLAN --> POLICY
    POLICY -- "role denied: permission_denied + failed" --> AUDIT
    POLICY -- "allowed" --> AGENTS
    AGENTS --> VALID
    VALID -- "invalid: fail closed" --> AUDIT
    VALID -- "valid" --> RETRY
    RETRY -- "transient: backoff and retry; permanent: abort" --> AGENTS
    RETRY -- "exhausted: audited error (after N attempts)" --> AUDIT
    AGENTS --> GATE
    GATE -- "rejected: stopped at checkpoint 2" --> AUDIT
    GATE -- "approved" --> EXEC
    EXEC --> EVAL
    EVAL --> AUDIT
    ORCH -- "failure: checkpoint saved, resume(run_id) continues" --> AUDIT

    HARNESS --> CASES
    HARNESS --> BASELINE
    BASELINE --> CI_GATE
    CI_GATE -- "regression: CI fails" --> HARNESS
```

## Evidence map (diagram -> code)

| Component | Module | What it proves | Evidence |
| --- | --- | --- | --- |
| Orchestrator | `orchestrator/__init__.py` `run`/`resume` | idempotency replay, resume from checkpoint | `tests/test_platform.py` |
| Planner | `workflow/__init__.py` `Planner` | plan is research -> content -> qa | `EVAL-001..017` plan assertions |
| ToolPolicy | `core/policy.py` | deny-by-default for unknown roles | `EVAL-005` permission_denied |
| Agents | `agents/__init__.py` | specialized roles over a single `Provider` seam | `tests/test_productization.py` |
| RetryPolicy | `workflow/retry.py` | transient retried, permanent aborts, exhausted fails | `EVAL-011/012/013` |
| ApprovalGate | `workflow/__init__.py` | content gate exercised once, decision reflected | `EVAL-007..010` |
| RuleEvaluator | `evaluation/__init__.py` | deterministic offline scoring | `EVAL-003/004` |
| AuditLog | `observability/__init__.py` | every step mirrored in audit | `auditability` 13/13 |
| Harness + gate | `evaluation/runner.py` + `.github/workflows/ci.yml` | real runs vs committed baseline | `benchmarks/baseline.json` 17/17 |

## See also

- [Methodology](methodology.md)
- [Productization notes](productization.md)
- [Roadmap](../ROADMAP.md)
