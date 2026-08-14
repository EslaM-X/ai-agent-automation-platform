# Changelog

All notable changes to `ai-agent-automation-platform`.

## [Unreleased]

## [v0.1.0] — 2026-08-14

Initial release.

### Added
- Orchestrator entry point (`run(objective) -> WorkflowRun`).
- Specialized agents: research, content, QA, analytics over a `Provider` interface.
- Workflow layer: `Planner`, `ApprovalGate`, `Executor`.
- Knowledge base interface (in-memory keyword search shipped).
- Append-only audit log and observability.
- Offline test suite (10 tests) using a deterministic fake provider.
- Example CLI.

### Known limitations
- Knowledge base is keyword search, not semantic retrieval.
- Agent prompts are templates; output quality depends on the provider.
- Single-run orchestration; no retries or distributed execution yet.
