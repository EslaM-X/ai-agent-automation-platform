# Architecture

## Layering

```
Task
  │
  ▼
Policy ──────────▶ target pose
  │
  ▼
Controller ─────▶ Action (linear, angular velocity)
  │
  ▼
Simulator ──────▶ State (pose, velocities, contact)
  │
  ▼
Metrics ────────▶ EpisodeReport
  │
  ▼
Validation ─────▶ ExperimentSummary / sim2sim report
```

## Invariants

- **Policy/planner/controller/metrics are pure** — no physics imports, fully
  unit-testable without any engine.
- **Simulators are interchangeable** — `reset()`, `step(action) -> State`,
  `state` and `name` are the entire contract.
- **Metrics are backend-agnostic** — derived from the state history alone, so
  comparing backends is meaningful.
- **Determinism** — the only randomness is the per-seed goal jitter; the same
  seed yields the same report on the same backend.

## Why three backends

| Backend | Motion model | Contact model | Value |
| --- | --- | --- | --- |
| `kinematic` | exact unicycle | analytic circles | reference, fast, portable |
| `mujoco` | MuJoCo free-joint integration | MuJoCo solver | real physics, reproducible |
| `pybullet` | Bullet rigid-body | Bullet contact | real physics, independent |

The kinematic backend is the **reference**. Physics backends are real — their
numbers can and do differ, and sim-to-sim exists to *measure* that difference.

## See also

- [Methodology](methodology.md)
- [Validation](validation.md)
