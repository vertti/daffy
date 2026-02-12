# ROADMAP

Last updated: 2026-02-12

## Goals

- Keep Daffy focused on function-boundary DataFrame guardrails.
- Raise user trust by fixing contract mismatches first.
- Ship in small PRs with clear, automated verification.

## Non-Goals

- Do not turn Daffy into a pipeline/orchestration data-quality platform.
- Do not introduce heavy schema registry or external service dependencies.

## Delivery Rules (for every PR)

- Keep PR scope small and single-purpose.
- Include tests proving behavior change.
- Update docs and changelog if public behavior changes.
- Use these quality gates before merge:
  - `uv run pytest -q`
  - `uv run pytest --cov`
  - `uv run ruff check .`
  - `uv run ruff format --check .`
  - `uv run pyrefly check .`
- Tooling is managed by `mise`; run `mise install` before running the gates.

## PR Plan

### Milestone 0: Product Contract and Documentation Trust

- [x] PR-001: Backend Support Contract Alignment (shipped in v2.6.1)
  - Value: Removes user confusion and support churn.
  - Scope:
    - Decide and codify support matrix in one source of truth (README + docs + error messages).
    - Align messaging around pandas/polars/modin/pyarrow support and import behavior.
  - Tests:
    - Update/add assertions in `tests/test_optional_dependencies.py`.
    - Add docs consistency checks where practical (or explicit snapshot tests for key messages).
  - Verify:
    - `uv run pytest tests/test_optional_dependencies.py -q`
  - Done when:
    - Public docs and runtime behavior no longer conflict.

- [x] PR-002: Pydantic Install Path and Packaging Clarity (shipped in v2.6.1)
  - Value: Prevents failed install guidance.
  - Scope:
    - Either add proper optional dependency extras for Pydantic or update all install hints to the actual supported install path.
    - Update `daffy/pydantic_types.py` message and docs examples.
  - Tests:
    - Add/adjust tests in `tests/test_pydantic_types.py`.
  - Verify:
    - `uv run pytest tests/test_pydantic_types.py -q`
  - Done when:
    - Error hints are executable as written.

- [x] PR-003: API Docs Signature and Examples Sync (shipped in v2.6.1)
  - Value: Reduces misuse and issue volume.
  - Scope:
    - Update `docs/api.md`, `README.md`, and advanced docs to match real decorator signatures and supported check names.
    - Remove stale examples (for example, obsolete `nullable=`/`unique=` decorator parameters).
  - Tests:
    - Add a small doc example smoke test module for critical snippets.
  - Verify:
    - `uv run pytest tests/test_type_compatibility.py -q`
  - Done when:
    - Public examples reflect current API.

### Milestone 1: Correctness and Predictability

- [ ] PR-004: Config File Discovery Behavior Fix
  - Value: Makes project-level config work from nested directories.
  - Scope:
    - Implement parent-directory search for `pyproject.toml` or update docs to match intentional CWD-only behavior.
    - Keep caching semantics explicit and tested.
  - Tests:
    - Expand `tests/test_config.py` to cover nested cwd parent lookup behavior.
  - Verify:
    - `uv run pytest tests/test_config.py -q`
  - Done when:
    - Config resolution behavior is deterministic and documented accurately.

- [ ] PR-005: `df_in` Auto-Parameter Selection Hardening
  - Value: Prevents false failures when first argument is not a DataFrame.
  - Scope:
    - Improve unnamed parameter selection logic to find the first DataFrame-like argument.
    - Preserve explicit `name=...` behavior as highest priority.
  - Tests:
    - Add targeted cases to `tests/test_df_in.py` and `tests/test_utils.py`.
  - Verify:
    - `uv run pytest tests/test_df_in.py tests/test_utils.py -q`
  - Done when:
    - Common multi-argument patterns work without requiring `name=...`.

- [ ] PR-006: Strict Validation of Invalid Column Specs (Opt-In)
  - Value: Catches silent typos early without breaking legacy users by default.
  - Scope:
    - Add an opt-in strict-spec mode (decorator flag or config) that errors on invalid column keys/spec types.
    - Keep current silent-ignore behavior as default for backwards compatibility.
  - Tests:
    - Add tests in `tests/validators/test_spec_parser.py` and `tests/test_df_in.py`.
  - Verify:
    - `uv run pytest tests/validators/test_spec_parser.py tests/test_df_in.py -q`
  - Done when:
    - Users can opt into typo-safe schema specs.

### Milestone 2: Developer Experience

- [ ] PR-007: Typed Exception Class (`DaffyValidationError`)
  - Value: Easier error handling in apps and APIs.
  - Scope:
    - Introduce a dedicated exception type (subclass of `AssertionError` for compatibility).
    - Include structured fields (validator type, function name, parameter/return context).
  - Tests:
    - Add error type assertions across `tests/test_df_in.py`, `tests/test_df_out.py`, `tests/test_lazy_validation.py`.
  - Verify:
    - `uv run pytest tests/test_df_in.py tests/test_df_out.py tests/test_lazy_validation.py -q`
  - Done when:
    - Consumers can catch Daffy-specific failures cleanly.

- [ ] PR-008: Check Argument Validation and Better Error Messages
  - Value: Faster debugging for invalid check payloads.
  - Scope:
    - Validate check argument shapes/types (`between`, `str_length`, `isin`, `notnull`) before execution.
    - Return explicit guidance in raised errors.
  - Tests:
    - Extend `tests/test_checks.py` and `tests/test_custom_checks.py`.
  - Verify:
    - `uv run pytest tests/test_checks.py tests/test_custom_checks.py -q`
  - Done when:
    - Invalid check configs fail with actionable messages.

### Milestone 3: Performance (Measured, No Premature Optimization)

- [ ] PR-009: Row Validation Fast Path and Adapter Reuse
  - Value: Improves valid-data row validation throughput.
  - Scope:
    - Reuse `TypeAdapter`/compiled validator path.
    - Keep current early-termination behavior unchanged for error-heavy datasets.
  - Tests/Benchmarks:
    - Keep functional tests in `tests/test_df_in_row_validation.py` and `tests/test_df_out_row_validation.py`.
    - Add micro-benchmark script under `scripts/` for repeatable comparisons.
  - Verify:
    - `uv run pytest tests/test_df_in_row_validation.py tests/test_df_out_row_validation.py -q`
  - Done when:
    - Benchmark shows meaningful improvement on valid large DataFrames.

- [ ] PR-010: Pipeline Build Caching for Repeated Calls
  - Value: Reduces overhead for hot paths with stable schemas.
  - Scope:
    - Cache resolved pipeline components keyed by decorator config + column signature.
    - Keep cache bounded and safe.
  - Tests/Benchmarks:
    - Add tests in `tests/validators/test_builder.py`.
    - Add benchmark scenario validating repeated-call speedup.
  - Verify:
    - `uv run pytest tests/validators/test_builder.py -q`
  - Done when:
    - Repeated validations show lower overhead without behavior drift.

## Suggested Execution Order

1. PR-001, PR-002, PR-003
2. PR-004, PR-005, PR-006
3. PR-007, PR-008
4. PR-009, PR-010

## Release Cadence Suggestion

- `v2.7.x`: Milestone 0 + Milestone 1
- `v2.8.x`: Milestone 2
- `v2.9.x`: Milestone 3
