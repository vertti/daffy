# CLAUDE.md

## Project Overview

Daffy is a decorator-first runtime DataFrame validation library.

- Primary API: `@df_in`, `@df_out`, `@df_log`
- Core promise: fast boundary checks with clear failures
- Positioning: function-level guardrails, not pipeline orchestration

## Working Agreements

- Keep PRs small and single-purpose.
- Prefer backwards-compatible changes unless explicitly doing a breaking release.
- Add tests for every behavior change.
- If public behavior changes, update docs and `CHANGELOG.md` in the same PR.

## Source of Truth

- Roadmap and sequencing: `ROADMAP.md`
- API behavior: `daffy/decorators.py`, `daffy/validators/*`
- Packaging and dependency metadata: `pyproject.toml`
- Optional dependency scenarios: `TESTING_OPTIONAL_DEPS.md`, `scripts/test_isolated_deps.py`

## Local Commands

Tooling is managed by `mise`. Run this first:

```bash
mise install
```

Then run commands with `uv run`:

```bash
uv run pytest
uv run pytest --cov
uv run ruff format
uv run ruff check
uv run pyrefly check .
```

## Quality Gates Before Merge

Run all of:

```bash
uv run pytest -q
uv run pytest --cov
uv run ruff check .
uv run ruff format --check .
uv run pyrefly check .
uv run skylos . --gate --strict --no-upload
```

Notes:

- Coverage threshold is defined in `pyproject.toml` (`fail_under = 95`).
- For optional dependency isolation testing, follow `TESTING_OPTIONAL_DEPS.md`.

## Design Constraints

- Python compatibility: 3.10+
- Narwhals-based runtime abstractions
- Keep default validation overhead low
- Avoid silent behavior changes in decorators

## PR Checklist

1. Add/adjust tests first.
2. Implement minimal change for the targeted outcome.
3. Run quality gates.
4. Update docs/examples affected by the change.
5. Add changelog entry if user-visible.
