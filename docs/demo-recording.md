# Recording the 60-second demo

A 15-30 second clip of `examples/demo_60s.py` is the single highest-converting
asset for the project. This guide keeps the recording honest and reproducible.

## Recommended stack

- **VHS** (terminal recording to GIF/SVG) or **asciinema** + **agg**.
  Any is fine; what matters is that the clip shows a *real* run, not an
  animation.

## Steps

1. Fresh clone in a clean directory:
   ```bash
   git clone https://github.com/EslaM-X/ai-agent-automation-platform.git
   cd ai-agent-automation-platform
   pip install -e .
   ```
2. Start the recorder (e.g. `vhs`, or `asciinema rec demo.cast`), then run:
   ```bash
   python examples/demo_60s.py
   python -m pytest tests/ -q
   ```
3. Stop the recorder. The whole thing takes ~10 seconds and prints every
   stage of the pipeline, a retry, the evaluation result, and the operational
   summary.

## What the clip should show (in order)

1. Clone + install (a few seconds).
2. The workflow run: plan -> research -> content -> QA -> approval.
3. The automatic retry (`research endpoint timed out (retried)`).
4. The evaluation line (`score=1.0 passed=True`).
5. The operational summary with `status: completed`.

## Captions that convert

Keep on-screen text minimal. Recommended caption: *"Governed AI agents:
plan, approve, execute, audit. Offline-testable, no API keys."*

## Placements

- Top of the README (linked from the quickstart).
- The first issue/PR, the first article, and the launch posts in
  `docs/launch-campaign.md`.

## Honesty rules

- Never splice different runs together and present them as one.
- Never hide the retry - it is a feature, not a bug.
- The demo uses a deterministic fake provider by design; say so in the post
  that carries the clip.
