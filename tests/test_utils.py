"""Tests for utility functions."""

import logging
from typing import Any

import pandas as pd
import pytest

from daffy import df_in, df_log, df_out
from daffy.utils import ParameterResolver


def test_get_parameter_name_not_in_signature() -> None:
    def func(a: int, b: int) -> None:
        pass

    with pytest.raises(ValueError, match="not found in function signature"):
        ParameterResolver(func).resolve("nonexistent", 1, 2)[0]


def test_get_parameter_not_provided() -> None:
    def func(a: int, b: int, c: int) -> None:
        pass

    with pytest.raises(ValueError, match="not found in function arguments"):
        ParameterResolver(func).resolve("c", 1, 2)[0]


def test_get_parameter_unnamed_selects_first_dataframe_like_argument() -> None:
    def func(meta: str, df: pd.DataFrame, count: int) -> None:
        pass

    dataframe = pd.DataFrame({"a": [1, 2]})
    result = ParameterResolver(func).resolve(None, "metadata", dataframe, 5)[0]
    assert result is dataframe


def test_get_parameter_name_unnamed_selects_dataframe_parameter_name() -> None:
    def func(meta: str, df: pd.DataFrame, count: int) -> None:
        pass

    dataframe = pd.DataFrame({"a": [1, 2]})
    result = ParameterResolver(func).resolve(None, "metadata", dataframe, 5)[1]
    assert result == "df"


def test_get_parameter_unnamed_falls_back_when_no_dataframe_like_argument() -> None:
    def func(meta: str, count: int) -> None:
        pass

    result = ParameterResolver(func).resolve(None, "metadata", 5)[0]
    assert result == "metadata"


def test_get_parameter_unnamed_selects_dataframe_in_varargs() -> None:
    def func(meta: str, *items: Any) -> None:
        pass

    dataframe = pd.DataFrame({"a": [1, 2]})
    result = ParameterResolver(func).resolve(None, "metadata", 1, dataframe, 2)[0]
    assert result is dataframe

    parameter_name = ParameterResolver(func).resolve(None, "metadata", 1, dataframe, 2)[1]
    assert parameter_name == "items"


def test_get_parameter_unnamed_skips_non_dataframe_varargs_then_uses_later_param() -> None:
    def func(meta: str, *items: Any, table: pd.DataFrame | None = None) -> None:
        pass

    dataframe = pd.DataFrame({"a": [1, 2]})
    result = ParameterResolver(func).resolve(None, "metadata", 1, 2, table=dataframe)[0]
    assert result is dataframe

    parameter_name = ParameterResolver(func).resolve(None, "metadata", 1, 2, table=dataframe)[1]
    assert parameter_name == "table"


def test_get_parameter_unnamed_selects_dataframe_in_varkwargs() -> None:
    def func(meta: str, **options: Any) -> None:
        pass

    dataframe = pd.DataFrame({"a": [1, 2]})
    result = ParameterResolver(func).resolve(None, "metadata", payload=dataframe)[0]
    assert result is dataframe

    parameter_name = ParameterResolver(func).resolve(None, "metadata", payload=dataframe)[1]
    assert parameter_name == "payload"


def test_get_parameter_unnamed_falls_back_when_varkwargs_have_no_dataframe() -> None:
    def func(meta: str, **options: Any) -> None:
        pass

    result = ParameterResolver(func).resolve(None, "metadata", retries=3, verbose=True)[0]
    assert result == "metadata"

    parameter_name = ParameterResolver(func).resolve(None, "metadata", retries=3, verbose=True)[1]
    assert parameter_name == "meta"


class TestDuplicateColumnNames:
    """Narwhals rejects duplicate column names with DuplicateError, a ValueError.

    That used to escape every decorator uncaught, turning @df_log - which only logs -
    into something that broke a working function.
    """

    @staticmethod
    def _duplicated() -> pd.DataFrame:
        return pd.DataFrame([[1, 2]], columns=["A", "A"])

    def test_df_in_reports_it_as_a_validation_error(self) -> None:
        @df_in(["A"])
        def process(df: Any) -> Any:
            return df

        with pytest.raises(AssertionError, match="Cannot validate this DataFrame"):
            process(self._duplicated())

    def test_df_out_reports_it_as_a_validation_error(self) -> None:
        @df_out(["A"])
        def produce() -> Any:
            return TestDuplicateColumnNames._duplicated()

        with pytest.raises(AssertionError, match="Cannot validate this DataFrame"):
            produce()

    def test_df_log_does_not_break_the_function(self, caplog: pytest.LogCaptureFixture) -> None:
        @df_log()
        def summarize(df: Any) -> Any:
            return df.iloc[:, [0]]

        with caplog.at_level(logging.WARNING):
            result = summarize(self._duplicated())

        assert result.shape == (1, 1)
        assert "could not be described" in caplog.text


class TestParameterNamesPastVarargs:
    """param_names includes keyword-only names, so indexing it by position misreports."""

    def test_frame_in_varargs_is_named_as_varargs(self) -> None:
        @df_in(columns=["missing"])
        def process(first: Any, *rest: Any, flag: bool = False) -> Any:
            return rest

        with pytest.raises(AssertionError, match=r"parameter 'rest'"):
            process(1, 2, pd.DataFrame({"x": [1]}))

    def test_frame_in_varargs_only_signature(self) -> None:
        @df_in(columns=["missing"])
        def process(*frames: Any, **opts: Any) -> Any:
            return frames

        with pytest.raises(AssertionError, match=r"parameter 'frames'"):
            process(1, pd.DataFrame({"x": [1]}))
