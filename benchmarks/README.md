# Benchmarks

Committed, reproducible numbers produced by the evaluation harness
(`evaluation/runner.py`) against the real platform.

| File | Committed | Purpose |
| --- | --- | --- |
| `baseline.json` | yes | The regression baseline: `python -m evaluation.runner --gate` fails CI if behavior moves away from it |
| `latest.json` | no (gitignored) | Most recent local run, written by the runner for inspection |
| `history/` | yes | One snapshot per released version — how the results changed over time |

## History

`history/` records one snapshot per released version (see
[`history/README.md`](history/README.md)). Each snapshot stores the version,
commit, timestamp, case counts, per-dimension rates, execution count, the
deterministic hash of its `baseline.json`, and the gate result — so a
regression is provable against the previous version instead of being a
claim. The current history:

| Version | Commit | Cases | Pass rate | Gate |
| --- | --- | --- | --- | --- |
| [0.3.0](history/0.3.0.json) | `0ba5ce4` | 17 | 1.0 | pass |

## Refreshing the baseline

Only commit a new `baseline.json` when a behavior change is **intended**. The
output is deterministic (no timestamps, no sleeping, no randomness), so a diff
against the committed file is always a real behavioral signal:

```bash
python -m evaluation.runner --out benchmarks/baseline.json
```

then review the diff and commit it together with the change that caused it.

## Current numbers

Generated from this repository's cases on an offline run — no LLM, no network.
See `benchmarks/baseline.json` for the exact per-dimension figures.

Snapshot policy: only released versions with a committed baseline are recorded
in `history/`. One real point is worth more than a fabricated graph.
