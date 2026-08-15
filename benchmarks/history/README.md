# Benchmark history

Versioned snapshots of the evaluation harness results (`evaluation/runner.py`)
over time. Each file is the record for one released version: what the harness
measured at that commit, and whether the regression gate passed.

## Current history

| Version | Commit | Cases | Pass rate | Execution count | Gate |
| --- | --- | --- | --- | --- | --- |
| [0.3.0](0.3.0.json) | `0ba5ce4` | 17 | 1.0 | 49 | pass |

## Snapshot format

Every snapshot is derived from the committed `baseline.json` at that version
and adds the provenance fields the baseline does not carry. The core fields
(`cases_total`, `cases_passed`, `cases_failed`, `dimensions`, `_source_files`)
are copied verbatim from the baseline so comparisons stay structurally
identical:

| Field | Meaning |
| --- | --- |
| `schema` | `ai-agent-evaluation-harness/v1` (same as baseline) |
| `version` | Released version (from `pyproject.toml`) |
| `commit` | Full commit SHA of the snapshot |
| `timestamp` | Commit timestamp (ISO-8601) |
| `gate_result` | `pass` if `--gate` exited 0 against the baseline, else `fail` |
| `cases_total` / `cases_passed` / `cases_failed` | Case counts (from baseline) |
| `pass_rate` | `cases_passed / cases_total` |
| `execution_count` | Sum of `execution.attempts` across all cases (how many times the platform actually ran) |
| `deterministic_hash` | SHA-256 of the committed `baseline.json` — a re-run producing the same hash proves determinism |
| `dimensions` | Per-dimension `{checked, passed, rate}` (copied from baseline) |
| `_source_files` | Case source files (copied from baseline) |

## Adding a snapshot after a release

Only add a snapshot when a version is **actually released and its baseline
committed** — never backfill or fabricate points.

1. Release the version and commit the new `baseline.json` with it.
2. Record the new commit and its timestamp.
3. Copy the fields from the committed `baseline.json` into
   `history/<version>.json` and fill in the provenance fields.
4. Compute `execution_count` as the sum of `execution.attempts` notes across
   all cases.
5. Compute `deterministic_hash` as the SHA-256 of the committed `baseline.json`.
6. Update the table in this file, the table in `../README.md`, and the
   changelog.

The regression gate itself stays the enforcement mechanism: a new version must
prove `--gate` passes at its commit before it can be recorded as a `pass`.
