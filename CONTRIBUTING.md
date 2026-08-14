# Contributing

Thanks for your interest. This project is designed so a first-time
contributor can land a small, reviewable change quickly.

## Ground rules

- **Provider-agnostic core.** `core/`, `workflow/`, `knowledge/`,
  `evaluation/`, and `observability/` must not import any specific LLM SDK.
- **Offline tests.** New features ship with tests that run without network or
  API keys (use a fake provider).
- **Small PRs.** One logical change per pull request.
- **Zero-dependency runtime.** New runtime code must not add dependencies;
  justify any exception explicitly.

## Getting started

1. Fork and clone.
2. `pip install -e ".[test]"`.
3. `python -m pytest tests/`.
4. `python examples/demo_60s.py` — the 60-second demo must keep working.

## First contribution in 6 steps

1. Pick an open issue (labels: `good first issue`, `help wanted`,
   `documentation`, `good first contribution`).
2. Read the [code of conduct](CODE_OF_CONDUCT.md) and this guide.
3. Run the test suite and keep it green.
4. Keep `ruff check` and `ruff format --check` clean.
5. Open your pull request (use the [PR template](.github/PULL_REQUEST_TEMPLATE.md)).
6. Get reviewed — then your name goes on the contributor wall.

## Pull requests

- Add or update a test with every change.
- Keep `examples/` runnable with zero configuration.
- Update `CHANGELOG.md`.
- Link the issue your PR closes.

## Labels you can grab

- `good first issue` / `good first contribution` — small, well-scoped.
- `help wanted` — maintainers would like contributions.
- `documentation` — docs-only, great starting point.
- `architecture` / `evaluation` / `security` — design-level work.

## Code of conduct

Be respectful and constructive. See `CODE_OF_CONDUCT.md`.
