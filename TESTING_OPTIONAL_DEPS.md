# Testing Optional Dependencies

This document describes how to test daffy's optional dependency support for DataFrame libraries (Pandas, Polars, Modin, PyArrow).

## Background

Daffy supports optional dependencies: you can install it with pandas, polars, pyarrow, modin, or combinations of these. This testing setup ensures that supported combinations work correctly.

## Automated Testing

### CI Pipeline

The GitHub Actions workflow includes three separate jobs:

1. **Standard tests** - Run with both pandas and polars installed (full functionality)
2. **Pytest optional dependency tests** - Run pytest tests that work with available libraries (always pass locally and in CI)
3. **Isolation scenario tests** - Test each scenario in true isolation using built wheels:
   - `pandas-only` - Only pandas is available
   - `polars-only` - Only polars is available
   - `pyarrow-only` - Only pyarrow is available
   - `modin-only` - Modin is available (with pandas as dependency)
   - `both` - Both libraries available
   - `none` - No DataFrame libraries (should fail gracefully)

### Simple Pytest Tests

The file `tests/test_optional_dependencies.py` contains tests that:

- Verify library detection flags work correctly
- Test that error messages reflect available libraries
- Ensure decorators work with whatever is installed

These tests are designed to always pass regardless of which DataFrame libraries are installed. They run as part of the regular test suite and should succeed when you run `uv run pytest` locally.

## Manual Testing

### Using the Test Script

The `scripts/test_isolated_deps.py` script allows manual testing of different scenarios:

**Note:** The pandas-only and polars-only tests will likely "fail" in local development environments because both libraries are typically installed. These tests are designed to work in CI environments with truly isolated environments using built wheel packages. The test failure messages will explain this.

```bash
# First build a wheel to avoid dev dependencies
uv build --wheel

# Test with pandas only
WHEEL=$(ls dist/daffy-*.whl | head -n1)
uv run --no-project --with "pandas>=1.5.1" --with "$WHEEL" python scripts/test_isolated_deps.py pandas

# Test with polars only
WHEEL=$(ls dist/daffy-*.whl | head -n1)
uv run --no-project --with "polars>=1.7.0" --with "$WHEEL" python scripts/test_isolated_deps.py polars

# Test with both
WHEEL=$(ls dist/daffy-*.whl | head -n1)
uv run --no-project --with "pandas>=1.5.1" --with "polars>=1.7.0" --with "$WHEEL" python scripts/test_isolated_deps.py both

# Test with pyarrow only
WHEEL=$(ls dist/daffy-*.whl | head -n1)
uv run --no-project --with "pyarrow>=14.0.0" --with "$WHEEL" python scripts/test_isolated_deps.py pyarrow

# Test with modin only (modin installs pandas as a dependency)
WHEEL=$(ls dist/daffy-*.whl | head -n1)
uv run --no-project --with "modin[ray]>=0.30.0" --with "$WHEEL" python scripts/test_isolated_deps.py modin

# Test with neither (should fail gracefully)
WHEEL=$(ls dist/daffy-*.whl | head -n1)
uv run --no-project --with "$WHEEL" python scripts/test_isolated_deps.py none
```

### Expected Behaviors

#### Pandas Only

- `HAS_PANDAS = True`, `HAS_POLARS = False`
- Only pandas DataFrames are accepted
- Error messages mention "Pandas DataFrame"

#### Polars Only

- `HAS_PANDAS = False`, `HAS_POLARS = True`
- Only polars DataFrames are accepted
- Error messages mention "Polars DataFrame"

#### Both Libraries

- `HAS_PANDAS = True`, `HAS_POLARS = True`
- Both DataFrame types work
- Error messages mention available DataFrame types

#### PyArrow Only

- `HAS_PYARROW = True` (other `HAS_*` flags False)
- PyArrow tables are accepted as DataFrame inputs/outputs
- Error messages mention "PyArrow DataFrame"

#### Modin Only

- `HAS_MODIN = True`
- `HAS_PANDAS = True` is expected because Modin depends on pandas
- Other backend flags (`HAS_POLARS`, `HAS_PYARROW`) should be False in this scenario
- Modin DataFrames are accepted as DataFrame inputs/outputs
- Error messages mention "Modin DataFrame"

#### No Libraries

- Import should fail with: `ImportError: No supported DataFrame library found...`

## Implementation Details

The optional dependency support works through:

1. **Module detection** in `daffy/dataframe_types.py` using `importlib.util.find_spec`
2. **Narwhals runtime compatibility checks** in `daffy/narwhals_compat.py`
3. **Conditional type hints** using `TYPE_CHECKING` for static analysis
4. **Dynamic error messages** that reflect available libraries

## Adding New Tests

When adding tests for optional dependencies:

1. Use the simple approach in `test_optional_dependencies.py`
2. Check `HAS_PANDAS`, `HAS_POLARS`, `HAS_MODIN`, and `HAS_PYARROW` flags to conditionally run tests
3. Use `pytest.mark.skipif` for tests requiring specific libraries
4. Test error message content to ensure it reflects available libraries

## Development Workflow

When working on optional dependency features:

1. Run standard tests: `uv run pytest`
2. Test specific scenarios: `uv run python scripts/test_isolated_deps.py <scenario>`
3. Verify CI passes with all dependency combinations
4. Ensure mypy type checking works: `uv run mypy daffy`
