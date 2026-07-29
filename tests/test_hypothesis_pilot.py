"""Property-based tests for mathematical invariants.

These tests verify relationships and invariants that unit tests don't typically cover.
Focus: properties that must always hold regardless of input values.
"""

from __future__ import annotations

import pandas as pd
from hypothesis import given, settings
from hypothesis import strategies as st

from daffy.checks import apply_check


class TestCheckInvariants:
    """Mathematical invariants that must hold across all checks."""

    @given(
        values=st.lists(st.floats(allow_nan=False, allow_infinity=False), min_size=1, max_size=100),
        threshold=st.floats(allow_nan=False, allow_infinity=False, min_value=-1000, max_value=1000),
    )
    def test_gt_ge_relationship(self, values: list[float], threshold: float) -> None:
        """Property: failures of gt(x) >= failures of ge(x) for same threshold."""
        series = pd.Series(values)

        gt_failures, _ = apply_check(series, "gt", threshold)
        ge_failures, _ = apply_check(series, "ge", threshold)

        assert gt_failures >= ge_failures

    @given(
        values=st.lists(st.floats(allow_nan=False, allow_infinity=False), min_size=1, max_size=100),
        threshold=st.floats(allow_nan=False, allow_infinity=False, min_value=-1000, max_value=1000),
    )
    def test_lt_le_relationship(self, values: list[float], threshold: float) -> None:
        """Property: failures of lt(x) >= failures of le(x) for same threshold."""
        series = pd.Series(values)

        lt_failures, _ = apply_check(series, "lt", threshold)
        le_failures, _ = apply_check(series, "le", threshold)

        assert lt_failures >= le_failures

    @given(
        values=st.lists(st.integers(min_value=-100, max_value=100), min_size=1, max_size=50),
        value_set=st.lists(st.integers(min_value=-100, max_value=100), min_size=1, max_size=20),
    )
    def test_isin_notin_complementary(self, values: list[int], value_set: list[int]) -> None:
        """Property: isin + notin failures = len(series) when checking same set."""
        series = pd.Series(values)

        isin_failures, _ = apply_check(series, "isin", value_set)
        notin_failures, _ = apply_check(series, "notin", value_set)

        assert isin_failures + notin_failures == len(values)

    @given(
        values=st.lists(st.integers(min_value=-100, max_value=100), min_size=1, max_size=50),
        target=st.integers(min_value=-100, max_value=100),
    )
    def test_eq_ne_complementary(self, values: list[int], target: int) -> None:
        """Property: eq + ne failures = len(series) for same target."""
        series = pd.Series(values)

        eq_failures, _ = apply_check(series, "eq", target)
        ne_failures, _ = apply_check(series, "ne", target)

        assert eq_failures + ne_failures == len(values)

    @given(
        values=st.lists(st.integers(min_value=-100, max_value=100), min_size=10, max_size=50),
    )
    def test_between_equivalent_to_ge_and_le(self, values: list[int]) -> None:
        """Property: between(a, b) fails iff value < a OR value > b."""
        series = pd.Series(values)
        lower, upper = -50, 50

        between_failures, _ = apply_check(series, "between", (lower, upper))

        # Count values outside the range
        expected_failures = sum(1 for v in values if v < lower or v > upper)

        assert between_failures == expected_failures


class TestCheckBoundaryInvariants:
    """Invariants for boundary conditions and special cases."""

    @settings(max_examples=10)
    @given(threshold=st.floats(allow_nan=False, allow_infinity=False, min_value=-1000, max_value=1000))
    def test_empty_series_passes_all_checks(self, threshold: float) -> None:
        """Property: empty series always passes all checks (no failures)."""
        empty_series = pd.Series([], dtype=float)

        for check_name, check_value in [
            ("gt", threshold),
            ("ge", threshold),
            ("lt", threshold),
            ("le", threshold),
            ("between", (threshold, threshold + 100)),
        ]:
            fail_count, samples = apply_check(empty_series, check_name, check_value)
            assert fail_count == 0
            assert not samples

    @given(
        n_failures=st.integers(min_value=10, max_value=100),
        max_samples=st.integers(min_value=1, max_value=10),
    )
    def test_max_samples_respected(self, n_failures: int, max_samples: int) -> None:
        """Property: returned samples never exceed max_samples."""
        series = pd.Series([-i for i in range(n_failures)])

        fail_count, samples = apply_check(series, "gt", 0, max_samples=max_samples)

        assert fail_count == n_failures
        assert len(samples) <= max_samples

    @given(
        values=st.lists(st.integers(min_value=0, max_value=20), min_size=5, max_size=30),
        allowed=st.lists(st.integers(min_value=0, max_value=20), min_size=1, max_size=10, unique=True),
        extra=st.integers(min_value=0, max_value=20),
    )
    def test_isin_expanding_set_reduces_failures(self, values: list[int], allowed: list[int], extra: int) -> None:
        """Property: expanding allowed set can only reduce or maintain failure count."""
        series = pd.Series(values)

        base_failures, _ = apply_check(series, "isin", allowed)
        expanded_failures, _ = apply_check(series, "isin", [*allowed, extra])

        assert expanded_failures <= base_failures
