"""Tests for lazy validation mode."""

from typing import Any

import pandas as pd
import pytest

from daffy import df_in, df_out
from daffy.config import clear_config_cache


class TestLazyValidationDirect:
    """Test lazy validation behavior."""

    def test_lazy_false_raises_on_first_error(self) -> None:
        @df_in(columns=["c", "d"], lazy=False)
        def process(df: pd.DataFrame) -> pd.DataFrame:
            return df

        df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
        # Missing column "c" and "d" - should raise on first
        with pytest.raises(AssertionError) as exc_info:
            process(df)
        assert "Missing columns" in str(exc_info.value)
        # Should only mention the missing columns, not other errors
        assert "dtype" not in str(exc_info.value).lower()

    def test_lazy_true_collects_all_errors(self) -> None:
        columns: Any = {
            "a": {"dtype": "float64", "nullable": False},
            "b": {"dtype": "int64"},  # Wrong dtype
            "c": "object",  # Missing column
        }

        @df_in(columns=columns, lazy=True)
        def process(df: pd.DataFrame) -> pd.DataFrame:
            return df

        df = pd.DataFrame({"a": [1, None], "b": ["x", "y"]})
        with pytest.raises(AssertionError) as exc_info:
            process(df)
        error = str(exc_info.value)
        # Should contain all three types of errors
        assert "Missing columns" in error
        assert "wrong dtype" in error
        assert "null" in error

    def test_lazy_true_multiple_errors_separated_by_newlines(self) -> None:
        columns: Any = {
            "a": {"dtype": "str"},  # Wrong dtype
            "c": "int64",  # Missing column
        }

        @df_in(columns=columns, lazy=True)
        def process(df: pd.DataFrame) -> pd.DataFrame:
            return df

        df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
        with pytest.raises(AssertionError) as exc_info:
            process(df)
        error = str(exc_info.value)
        # Errors should be separated by double newlines
        assert "\n\n" in error

    def test_lazy_true_no_errors_passes(self) -> None:
        columns: Any = {"a": "int64", "b": "float64"}

        @df_in(columns=columns, lazy=True)
        def process(df: pd.DataFrame) -> pd.DataFrame:
            return df

        df = pd.DataFrame({"a": [1, 2], "b": [3.0, 4.0]})
        # Should not raise
        result = process(df)
        assert len(result) == 2

    def test_lazy_true_strict_mode_extra_columns(self) -> None:
        columns: Any = {"a": {"dtype": "str"}}  # Wrong dtype + extra column

        @df_in(columns=columns, strict=True, lazy=True)
        def process(df: pd.DataFrame) -> pd.DataFrame:
            return df

        df = pd.DataFrame({"a": [1, 2], "b": [3, 4], "extra": [5, 6]})
        with pytest.raises(AssertionError) as exc_info:
            process(df)
        error = str(exc_info.value)
        assert "wrong dtype" in error
        assert "unexpected column" in error

    def test_lazy_includes_check_violations(self) -> None:
        columns: Any = {
            "price": {"checks": {"gt": 0}},
            "missing": "int64",  # Missing column
        }

        @df_in(columns=columns, lazy=True)
        def process(df: pd.DataFrame) -> pd.DataFrame:
            return df

        df = pd.DataFrame({"price": [-1, 0, 5]})
        with pytest.raises(AssertionError) as exc_info:
            process(df)
        error = str(exc_info.value)
        assert "Missing columns" in error
        assert "failed check gt" in error


class TestLazyValidationDecorators:
    """Test lazy validation via decorators."""

    def test_df_in_lazy_false_default(self) -> None:
        @df_in(columns={"a": "str", "b": "int64"})
        def process(df: pd.DataFrame) -> pd.DataFrame:
            return df

        df = pd.DataFrame({"a": [1, 2]})  # Missing b, wrong dtype for a
        with pytest.raises(AssertionError) as exc_info:
            process(df)
        error = str(exc_info.value)
        # Default lazy=False should raise on first error (missing column)
        assert "Missing columns" in error

    def test_df_in_lazy_true_collects_errors(self) -> None:
        @df_in(columns={"a": "str", "b": "int64"}, lazy=True)
        def process(df: pd.DataFrame) -> pd.DataFrame:
            return df

        df = pd.DataFrame({"a": [1, 2]})  # Missing b, wrong dtype for a
        with pytest.raises(AssertionError) as exc_info:
            process(df)
        error = str(exc_info.value)
        # lazy=True should collect both errors
        assert "Missing columns" in error
        assert "wrong dtype" in error

    def test_df_out_lazy_true_collects_errors(self) -> None:
        @df_out(columns={"a": "str", "b": "int64"}, lazy=True)
        def process() -> pd.DataFrame:
            return pd.DataFrame({"a": [1, 2]})  # Missing b, wrong dtype for a

        with pytest.raises(AssertionError) as exc_info:
            process()
        error = str(exc_info.value)
        assert "Missing columns" in error
        assert "wrong dtype" in error

    def test_df_in_lazy_passes_when_valid(self) -> None:
        @df_in(columns={"a": "int64", "b": "float64"}, lazy=True)
        def process(df: pd.DataFrame) -> pd.DataFrame:
            return df

        df = pd.DataFrame({"a": [1, 2], "b": [1.0, 2.0]})
        result = process(df)
        assert len(result) == 2


class TestLazyValidationConfig:
    """Test lazy validation via pyproject.toml config."""

    def setup_method(self) -> None:
        clear_config_cache()

    def teardown_method(self) -> None:
        clear_config_cache()

    def test_lazy_defaults_to_false(self) -> None:
        from daffy.config import resolve_decorator_settings

        assert resolve_decorator_settings(None, None, None).lazy is False

    def test_lazy_param_overrides_config(self) -> None:
        from daffy.config import resolve_decorator_settings

        assert resolve_decorator_settings(None, True, None).lazy is True
        assert resolve_decorator_settings(None, False, None).lazy is False


class TestLazyValidationErrorMessages:
    """Test error message formatting in lazy mode."""

    def test_single_error_same_as_non_lazy(self) -> None:
        columns: Any = {"missing": "int64"}

        @df_in(columns=columns, lazy=True)
        def process_lazy(df: pd.DataFrame) -> pd.DataFrame:
            return df

        @df_in(columns=columns, lazy=False)
        def process_eager(df: pd.DataFrame) -> pd.DataFrame:
            return df

        df = pd.DataFrame({"a": [1, 2]})

        # Lazy mode with single error
        with pytest.raises(AssertionError) as lazy_exc:
            process_lazy(df)

        # Non-lazy mode
        with pytest.raises(AssertionError) as normal_exc:
            process_eager(df)

        # Error messages should have the same structure (minus function name)
        # Both should contain the same error type
        assert "Missing columns: ['missing']" in str(lazy_exc.value)
        assert "Missing columns: ['missing']" in str(normal_exc.value)

    def test_multiple_errors_readable_format(self) -> None:
        columns: Any = {
            "a": {"nullable": False},
            "b": {"unique": True},
            "c": "int64",
        }

        @df_in(columns=columns, lazy=True)
        def process(df: pd.DataFrame) -> pd.DataFrame:
            return df

        df = pd.DataFrame({"a": [1, None], "b": [1, 1]})
        with pytest.raises(AssertionError) as exc_info:
            process(df)
        error = str(exc_info.value)

        # Each error type should be on its own line(s)
        lines = error.split("\n\n")
        assert len(lines) == 3  # missing, nullable, unique
