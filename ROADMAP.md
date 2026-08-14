# Roadmap

The product tiers below are deliberately **unpriced**. Pricing is set after
real usage exists — the numbers must come from the data, not from a guess.

## North star

> 100 real users running governed AI workflows, then a sustainable
> free + hosted model around the runtime.

Signal that matters, in order:

1. A stranger installs, runs `demo_60s.py`, and understands value in < 5 min.
2. 10 external users. 3. 100 users. 4. External contributors and PRs.
5. Companies evaluating it. 6. Monetization or sponsorship.

## Free

- The OSS runtime (this repository): planning, agents, approval gate,
  execution, retries, idempotency, resume, evaluation, audit.
- Community support via [Discussions](https://github.com/EslaM-X/ai-agent-automation-platform/discussions).

## Pro (hosted execution)

- Hosted run execution and storage.
- Advanced observability: dashboards, run tracing, per-agent metrics.
- Retry/evaluation history retained beyond the local audit log.

## Team

- Everything in Pro.
- RBAC and team workspaces.
- Persistent, long-running workflows.

## Enterprise

- Everything in Team.
- SSO and compliance tooling.
- Private deployment.
- Dedicated support.

## Sequencing (what gets built, and when)

1. **Traction first** — demo clip, quickstart, issue templates, labels,
   contributor funnel. (Done in v0.2.)
2. **First 10 external users** — driven by the launch posts in
   `docs/launch-campaign.md`.
3. **Semantic evaluator** — optional LLM-backed evaluation behind the same
   `Evaluator` interface; deterministic rules stay the default.
4. **Persistent run store** — swap the in-memory audit log for a documented
   persistent store behind the same interface.
5. **Hosted tier** — only after usage data justifies it.

## Explicitly out of scope (for now)

- New agent roles added without a demonstrated need.
- New repositories or parallel projects. This project is the flagship.
- Cosmetic features with no function.
