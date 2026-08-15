# Benchmarks

Committed, reproducible numbers produced by the evaluation harness
(`evaluation/runner.py`) against the real platform.

| File | Committed | Purpose |
| --- | --- | --- |
| `baseline.json` | yes | The regression baseline: `python -m evaluation.runner --gate` fails CI if behavior moves away from it |
| `latest.json` | no (gitignored) | Most recent local run, written by the runner for inspection |

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
