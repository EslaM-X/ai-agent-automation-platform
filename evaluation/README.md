# Evaluation Harness

Deterministic, offline evaluation of the governed agent platform — the same
harness that runs in CI as a **regression gate**.

It drives the **real** `Orchestrator` with case-defined `CaseProvider`
instances (no LLM, no network, no mocked orchestrator) and asserts expected
behavior across seven dimensions:

| Dimension | What it proves |
| --- | --- |
| `correctness` | The run reached the expected status, plan, and evaluation result |
| `policy` | Deny-by-default tool permissions block disallowed roles and allow the rest |
| `safety` | Approval discipline: the gate is exercised exactly once at the content step and the run reflects the approver's decision; invalid output fails closed; transient failures are retried while permanent ones abort |
| `execution` | Step order, checkpoint advancement, attempt/retry accounting, resume without redoing completed work |
| `auditability` | Every dispatch, agent result, approval, and evaluation is mirrored in the audit log |
| `idempotency` | A replay with the same key returns the original run and never re-executes provider calls |

## Layout

```
evaluation/
├── cases/            JSON scenarios (basic, approval, failure, idempotency)
├── evaluators/       dimension checkers against real WorkflowRun objects
├── metrics.py        aggregates case results into per-dimension rates
├── runner.py         runs the suite, writes benchmarks/latest.json, --gate
├── report.py         human-readable console report
└── README.md
```

## Run

```bash
python -m evaluation.runner           # run + print + write benchmarks/latest.json
python -m evaluation.runner --gate    # also fail if behavior regressed vs baseline
```

The `--gate` mode compares every case result and dimension rate against the
committed `benchmarks/baseline.json` and exits non-zero on any regression. CI
runs it on every push and pull request.

## Adding a case

1. Add a scenario to the right file under `cases/` (or a new `cases/*.json`).
2. Give it a unique `id`, a deterministic `provider` (replies / raise_once /
   raise_always), a `config`, and an `expect` block.
3. List the dimensions it exercises in `checks`.
4. Run locally, then refresh the baseline only when the new behavior is
   intended: `python -m evaluation.runner --out benchmarks/baseline.json`.

## Honesty boundary

- Rates are computed from actual runs — the report never claims a number that
  was not measured.
- `raise_once` / `raise_always` model transient vs permanent failures with the
  platform's real taxonomy (`core/errors.py`).
- Checkers return `None` (not counted) when a case does not assert a behavior;
  a case only counts toward a dimension when it actually exercises it.
