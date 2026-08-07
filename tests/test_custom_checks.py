"""Tests for custom check functions (callable checks)."""

import pandas as pd
import pytest

from daffy import df_in
from daffy.checks import apply_check


class TestCustomCheckFunctions:
    def test_custom_check_passes(self) -> None:
        series = pd.Series([1, 2, 3, 4, 5])
        fail_count, samples = apply_check(series, "positive", lambda s: s > 0)
        assert fail_count == 0
        assert samples == []

    def test_custom_check_fails(self) -> None:
        series = pd.Series([1, -2, 3, -4, 5])
        fail_count, samples = apply_check(series, "positive", lambda s: s > 0)
        assert fail_count == 2
        assert -2 in samples
        assert -4 in samples

    def test_custom_check_with_mean(self) -> None:
        series = pd.Series([1, 2, 3, 100])  # 100 is outlier (mean ~26.5)
        fail_count, samples = apply_check(series, "no_outliers", lambda s: s < s.mean() * 3)
        assert fail_count == 1
        assert samples == [100]

    def test_custom_check_all_fail(self) -> None:
        series = pd.Series([-1, -2, -3])
        fail_count, _samples = apply_check(series, "positive", lambda s: s > 0)
        assert fail_count == 3

    def test_custom_check_empty_series(self) -> None:
        series = pd.Series([], dtype=float)
        fail_count, samples = apply_check(series, "positive", lambda s: s > 0)
        assert fail_count == 0
        assert samples == []

    def test_custom_check_with_pandas_float_nan(self) -> None:
        """NaN compares as False in Pandas float columns, so it fails the custom check natively."""
        series = pd.Series([1, None, 3])
        fail_count, _samples = apply_check(series, "positive", lambda s: s > 0)
        assert fail_count == 1

    def test_custom_check_max_samples(self) -> None:
        series = pd.Series([-1, -2, -3, -4, -5, -6, -7, -8, -9, -10])
        fail_count, samples = apply_check(series, "positive", lambda s: s > 0, max_samples=3)
        assert fail_count == 10
        assert len(samples) == 3

    def test_custom_check_string_validation(self) -> None:
        series = pd.Series(["hello", "world", "hi"])
        fail_count, samples = apply_check(series, "long_enough", lambda s: s.str.len_chars() >= 4)
        assert fail_count == 1
        assert samples == ["hi"]


class TestCustomCheckWithDecorator:
    def test_decorator_with_custom_check(self) -> None:
        @df_in(columns={"price": {"checks": {"positive": lambda s: s > 0}}})
        def process(df: pd.DataFrame) -> pd.DataFrame:
            return df

        df = pd.DataFrame({"price": [1, 2, 3]})
        result = process(df)
        assert len(result) == 3

    def test_decorator_with_custom_check_fails(self) -> None:
        @df_in(columns={"price": {"checks": {"no_negatives": lambda s: s >= 0}}})
        def process(df: pd.DataFrame) -> pd.DataFrame:
            return df

        df = pd.DataFrame({"price": [1, -2, 3]})
        with pytest.raises(AssertionError) as exc_info:
            process(df)
        assert "no_negatives" in str(exc_info.value)
        assert "-2" in str(exc_info.value)

    def test_decorator_mixed_builtin_and_custom_checks(self) -> None:
        @df_in(
            columns={
                "price": {
                    "checks": {
                        "gt": 0,  # built-in
                        "reasonable": lambda s: s < 10000,  # custom
                    }
                }
            }
        )
        def process(df: pd.DataFrame) -> pd.DataFrame:
            return df

        # Both pass
        df = pd.DataFrame({"price": [100, 200, 300]})
        result = process(df)
        assert len(result) == 3

        # Built-in fails
        df = pd.DataFrame({"price": [0, 100, 200]})
        with pytest.raises(AssertionError) as exc_info:
            process(df)
        assert "gt" in str(exc_info.value)

        # Custom fails
        df = pd.DataFrame({"price": [100, 50000]})
        with pytest.raises(AssertionError) as exc_info:
            process(df)
        assert "reasonable" in str(exc_info.value)

    def test_decorator_custom_check_with_dtype(self) -> None:
        @df_in(
            columns={
                "score": {
                    "dtype": "int64",
                    "checks": {"valid_range": lambda s: (s >= 0) & (s <= 100)},
                }
            }
        )
        def process(df: pd.DataFrame) -> pd.DataFrame:
            return df

        df = pd.DataFrame({"score": [50, 75, 100]})
        result = process(df)
        assert len(result) == 3

    def test_custom_check_error_shows_check_name(self) -> None:
        @df_in(columns={"value": {"checks": {"my_custom_validation": lambda s: s != 999}}})
        def process(df: pd.DataFrame) -> pd.DataFrame:
            return df

        df = pd.DataFrame({"value": [1, 999, 3]})
        with pytest.raises(AssertionError) as exc_info:
            process(df)
        assert "my_custom_validation" in str(exc_info.value)


class TestCustomCheckErrorHandling:
    def test_callable_raises_exception(self) -> None:
        series = pd.Series([1, 2, 3])

        def bad_check(s: pd.Series) -> pd.Series:  # type: ignore[type-arg]
            raise RuntimeError("Something went wrong")

        with pytest.raises(ValueError, match=r"bad_check.*raised an error"):
            apply_check(series, "bad_check", bad_check)

    def test_callable_returns_wrong_type(self) -> None:
        series = pd.Series([1, 2, 3])

        with pytest.raises(TypeError) as exc_info:
            apply_check(series, "wrong_type", lambda s: [True, True, True])
        assert "wrong_type" in str(exc_info.value)
        assert "Series-like object" in str(exc_info.value)
        assert "list" in str(exc_info.value)

    def test_callable_returns_scalar(self) -> None:
        series = pd.Series([1, 2, 3])

        with pytest.raises(TypeError) as exc_info:
            apply_check(series, "scalar_check", lambda s: True)
        assert "scalar_check" in str(exc_info.value)
        assert "Series-like object" in str(exc_info.value)

    def test_callable_with_attribute_error(self) -> None:
        series = pd.Series([1, 2, 3])

        with pytest.raises(ValueError, match=r"attr_error.*raised an error"):
            apply_check(series, "attr_error", lambda s: s.nonexistent_method())

    def test_decorator_with_failing_callable(self) -> None:
        @df_in(columns={"value": {"checks": {"bad": lambda s: s.nonexistent()}}})
        def process(df: pd.DataFrame) -> pd.DataFrame:
            return df

        df = pd.DataFrame({"value": [1, 2, 3]})
        with pytest.raises(ValueError, match=r"bad.*raised an error"):
            process(df)
