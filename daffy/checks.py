"""Value check implementations for column validation.

All check functions return a mask where True indicates a FAILING value.
This convention allows consistent handling: count failures and sample them.
"""

from __future__ import annotations

from typing import Any, Literal

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

CheckViolation = tuple[str, str, int, list[Any]]


def _nw_series(series: Any) -> nw.Series[Any]:
    """Wrap native series in Narwhals."""
    return nw.from_native(series, series_only=True)


def apply_check(series: Any, check_name: str, check_value: Any, max_samples: int = 5) -> tuple[int, list[Any]]:
    """Apply a single check to a series.

    Check value can be:
    - A value for built-in checks (e.g., {"gt": 0})
    - A callable for custom checks (e.g., {"no_outliers": lambda s: s < s.mean() * 10})
      The callable receives a Narwhals Series and should return a boolean Series (True = valid)

    Returns:
        Tuple of (fail_count, sample_failing_values)

    """
    nws = _nw_series(series)

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
        # Invert the result and treat nulls as failures (fill_null(True)).
        nw_mask = (~nw_result).fill_null(True)
        fail_count = int(nw_mask.sum())
        if fail_count == 0:
            return 0, []
        samples = nws.filter(nw_mask).head(max_samples).to_list()
        return fail_count, samples

    # Built-in checks: each lambda returns a mask where True = FAILING value.
    # The ~ operator inverts comparison results (e.g., ~(x > 0) means "not greater than 0").
    check_masks = {
        "gt": lambda: ~(nws > check_value),
        "ge": lambda: ~(nws >= check_value),
        "lt": lambda: ~(nws < check_value),
        "le": lambda: ~(nws <= check_value),
        "between": lambda: ~((nws >= check_value[0]) & (nws <= check_value[1])),
        "eq": lambda: nws != check_value,
        "ne": lambda: nws == check_value,
        "isin": lambda: ~nws.is_in(check_value),
        "notin": lambda: nws.is_in(check_value),
        "notnull": lambda: nws.is_null(),  # noqa: PLW0108
        "str_regex": lambda: ~nws.str.contains(f"^(?:{check_value})"),
        "str_startswith": lambda: ~nws.str.starts_with(check_value),
        "str_endswith": lambda: ~nws.str.ends_with(check_value),
        "str_contains": lambda: ~nws.str.contains(check_value, literal=True),
        "str_length": lambda: ~((nws.str.len_chars() >= check_value[0]) & (nws.str.len_chars() <= check_value[1])),
    }

    if check_name not in check_masks:
        raise ValueError(f"Unknown check: {check_name}")

    nw_mask = check_masks[check_name]().fill_null(True)
    fail_count = int(nw_mask.sum())
    if fail_count == 0:
        return 0, []

    samples = nws.filter(nw_mask).head(max_samples).to_list()
    return fail_count, samples


def validate_checks(df: Any, column: str, checks: dict[str, Any], max_samples: int = 5) -> list[CheckViolation]:
    """Run all checks on a column.

    Returns:
        List of (column, check_name, fail_count, sample_values) tuples for failures.

    """
    violations: list[CheckViolation] = []
    series = df[column]

    for check_name, check_value in checks.items():
        fail_count, samples = apply_check(series, check_name, check_value, max_samples)
        if fail_count > 0:
            violations.append((column, check_name, fail_count, samples))

    return violations
