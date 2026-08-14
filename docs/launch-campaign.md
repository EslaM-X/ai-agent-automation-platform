# Launch campaign

Five posts, one idea, published in order. The posts sell an idea, not a
"look at my GitHub". Every post ends at the same funnel:

```
Post → Demo clip → GitHub → Quickstart → User → Star → Issue/PR → Contributor
```

## Post 1 — the thesis

> AI agents don't need more autonomy. They need better control.
>
> PLAN → APPROVE → EXECUTE → AUDIT
>
> Most agent frameworks optimize for how *smart* the agent is. This one
> optimizes for how *accountable* it is. High-impact actions can require
> human approval. Every retry, every decision, every execution lands in an
> audit trail.
>
> Open source, offline-testable, no API keys to run the tests:
> [repo]

## Post 2 — the differentiator

> I built an open-source agent runtime where high-impact actions can require
> human approval.
>
> Not a `User → LLM → Answer` wrapper. A pipeline:
> Planner → specialized agents → approval gate → execution → audit log.
> The human is a stage in the pipeline, not a bystander.
>
> [demo clip] [repo]

## Post 3 — failure handling

> What happens when an AI agent fails halfway through a workflow?
>
> Most frameworks: the run dies and you start over.
> This runtime: failures are classified. Transient failures are retried with
> exponential backoff. Permanent failures abort with a clear audited error.
> And a failed run resumes from its checkpoint — it doesn't restart.
>
> [repo]

## Post 4 — testing without an LLM

> Why my agent tests don't require an external LLM.
>
> The provider is the only seam to the outside world. Inject a deterministic
> fake provider and the entire pipeline — planning, approval, retries,
> evaluation, audit — runs offline, reproducibly, in CI.
>
> 22 tests, zero API keys, ~0.1s. That is how you build agent software you
> can actually ship.
>
> [repo]

## Post 5 — the story

> I turned an AI agent architecture experiment into an open-source developer
> tool.
>
> The version you can install today: governed workflows, retries, idempotency,
> tool permissions, deterministic evaluation, full audit trail.
>
> Build your first workflow in 60 seconds: [quickstart]
>
> [repo]

## Funnel checklist

- [ ] Demo clip recorded (see `docs/demo-recording.md`).
- [ ] GitHub pinned + description set.
- [ ] Issue templates and labels live.
- [ ] Quickstart verified in a fresh clone.
- [ ] First external user → ask for the missing step that blocks them.
- [ ] First external PR → respond within 24h, celebrate publicly.
