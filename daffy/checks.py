"""Value check implementations for column validation.

All check functions return a mask where True indicates a FAILING value.
This convention allows consistent handling: count failures and sample them.

Null handling follows the backend rather than being normalised here: a comparison
against a null yields "unknown" on backends with three-valued logic, and unknown is
not a violation. Use `nullable=False` or the `notnull` check to constrain nulls.
"""

from __future__ import annotations

from typing import Any, Literal, get_args

import narwhals as nw

CheckName = Literal[
    "gt",
    "ge",
    "lt",
    "le",
    "between",
    "eq",
    "ne",
    "isin",
    "notin",
    "notnull",
    "str_regex",
    "str_startswith",
    "str_endswith",
    "str_contains",
    "str_length",
]

BUILTIN_CHECK_NAMES: frozenset[str] = frozenset(get_args(CheckName))

CheckViolation = tuple[str, str, int, list[Any]]


def _nw_series(series: Any) -> nw.Series[Any]:
    """Wrap native series in Narwhals."""
    return nw.from_native(series, series_only=True)


def _failing_mask(valid_mask: nw.Series[Any]) -> nw.Series[Any]:
    """Turn a validity mask into a failure mask, leaving each backend's null semantics intact.

    A null comparison result means "unknown", not "failed", so it is not counted as a
    violation. Resolving it before inverting also keeps pandas object-dtype masks (which
    hold `None` rather than a null-aware boolean) from reaching `~`, where they raise a
    TypeError.
    """
    return ~valid_mask.fill_null(True).cast(nw.Boolean())


def _evaluate_mask(nws: nw.Series[Any], fail_mask: nw.Series[Any], max_samples: int) -> tuple[int, list[Any]]:
    """Count failures and sample failing values from a boolean mask (True = failing)."""
    nw_mask = fail_mask.fill_null(False)
    fail_count = int(nw_mask.sum())
    if fail_count == 0:
        return 0, []
    samples = nws.filter(nw_mask).head(max_samples).to_list()
    return fail_count, samples


def apply_check(series_or_nws: Any, check_name: str, check_value: Any, max_samples: int = 5) -> tuple[int, list[Any]]:
    """Apply a single check to a series.

    Check value can be:
    - A value for built-in checks (e.g., {"gt": 0})
    - A callable for custom checks (e.g., {"no_outliers": lambda s: s < s.mean() * 10})
      The callable receives a Narwhals Series and should return a boolean Series (True = valid)

    Returns:
        Tuple of (fail_count, sample_failing_values)

    """
    nws = series_or_nws if isinstance(series_or_nws, nw.Series) else _nw_series(series_or_nws)

    # Handle custom callable checks
    if callable(check_value):
        try:
            result = check_value(nws)
        except Exception as e:
            # Catch any exception from user code (Exception excludes KeyboardInterrupt/SystemExit)
            raise ValueError(f"Custom check '{check_name}' raised an error: {e}") from e

        # Validate return type - must be Series-like with boolean values
        try:
            nw_result = _nw_series(result)
        except Exception:  # noqa: BLE001 - intentionally catch any conversion failure
            # Any conversion failure means the return type is wrong
            raise TypeError(
                f"Custom check '{check_name}' must return a Series-like object, got {type(result).__name__}"
            ) from None

        # Custom checks return True for VALID values, but we need True for INVALID.
        return _evaluate_mask(nws, _failing_mask(nw_result), max_samples)

    # Built-in checks: each lambda returns a mask where True = FAILING value.
    # _failing_mask inverts a validity mask (e.g. x > 0) into "not greater than 0".
    check_masks = {
        "gt": lambda: _failing_mask(nws > check_value),
        "ge": lambda: _failing_mask(nws >= check_value),
        "lt": lambda: _failing_mask(nws < check_value),
        "le": lambda: _failing_mask(nws <= check_value),
        "between": lambda: _failing_mask((nws >= check_value[0]) & (nws <= check_value[1])),
        "eq": lambda: nws != check_value,
        "ne": lambda: nws == check_value,
        "isin": lambda: _failing_mask(nws.is_in(check_value)),
        "notin": lambda: nws.is_in(check_value),
        "notnull": lambda: nws.is_null(),  # noqa: PLW0108
        "str_regex": lambda: _failing_mask(nws.str.contains(check_value)),
        "str_startswith": lambda: _failing_mask(nws.str.starts_with(check_value)),
        "str_endswith": lambda: _failing_mask(nws.str.ends_with(check_value)),
        "str_contains": lambda: _failing_mask(nws.str.contains(check_value, literal=True)),
        "str_length": lambda: _failing_mask(
            (nws.str.len_chars() >= check_value[0]) & (nws.str.len_chars() <= check_value[1])
        ),
    }

    if check_name not in check_masks:
        raise ValueError(f"Unknown check: {check_name}")

    return _evaluate_mask(nws, check_masks[check_name](), max_samples)


def validate_checks(
    nws: nw.Series[Any], column: str, checks: dict[str, Any], max_samples: int = 5
) -> list[CheckViolation]:
    """Run all checks on a column.

    Returns:
        List of (column, check_name, fail_count, sample_values) tuples for failures.

    """
    violations: list[CheckViolation] = []

    for check_name, check_value in checks.items():
        fail_count, samples = apply_check(nws, check_name, check_value, max_samples)
        if fail_count > 0:
            violations.append((column, check_name, fail_count, samples))

    return violations
