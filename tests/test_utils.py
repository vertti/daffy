"""Tests for utility functions."""

from typing import Any

import pandas as pd
import pytest

from daffy.utils import get_parameter, get_parameter_name


def test_get_parameter_name_not_in_signature() -> None:
    def func(a: int, b: int) -> None:
        pass

    with pytest.raises(ValueError, match="not found in function signature"):
        get_parameter(func, "nonexistent", 1, 2)


def test_get_parameter_not_provided() -> None:
    def func(a: int, b: int, c: int) -> None:
        pass

    with pytest.raises(ValueError, match="not found in function arguments"):
        get_parameter(func, "c", 1, 2)


def test_get_parameter_unnamed_selects_first_dataframe_like_argument() -> None:
    def func(meta: str, df: pd.DataFrame, count: int) -> None:
        pass

    dataframe = pd.DataFrame({"a": [1, 2]})
    result = get_parameter(func, None, "metadata", dataframe, 5)
    assert result is dataframe


def test_get_parameter_name_unnamed_selects_dataframe_parameter_name() -> None:
    def func(meta: str, df: pd.DataFrame, count: int) -> None:
        pass

    dataframe = pd.DataFrame({"a": [1, 2]})
    result = get_parameter_name(func, None, "metadata", dataframe, 5)
    assert result == "df"


def test_get_parameter_unnamed_falls_back_when_no_dataframe_like_argument() -> None:
    def func(meta: str, count: int) -> None:
        pass

    result = get_parameter(func, None, "metadata", 5)
    assert result == "metadata"


def test_get_parameter_unnamed_selects_dataframe_in_varargs() -> None:
    def func(meta: str, *items: Any) -> None:
        pass

    dataframe = pd.DataFrame({"a": [1, 2]})
    result = get_parameter(func, None, "metadata", 1, dataframe, 2)
    assert result is dataframe

    parameter_name = get_parameter_name(func, None, "metadata", 1, dataframe, 2)
    assert parameter_name == "items"


def test_get_parameter_unnamed_skips_non_dataframe_varargs_then_uses_later_param() -> None:
    def func(meta: str, *items: Any, table: pd.DataFrame | None = None) -> None:
        pass

    dataframe = pd.DataFrame({"a": [1, 2]})
    result = get_parameter(func, None, "metadata", 1, 2, table=dataframe)
    assert result is dataframe

    parameter_name = get_parameter_name(func, None, "metadata", 1, 2, table=dataframe)
    assert parameter_name == "table"


def test_get_parameter_unnamed_selects_dataframe_in_varkwargs() -> None:
    def func(meta: str, **options: Any) -> None:
        pass

    dataframe = pd.DataFrame({"a": [1, 2]})
    result = get_parameter(func, None, "metadata", payload=dataframe)
    assert result is dataframe

    parameter_name = get_parameter_name(func, None, "metadata", payload=dataframe)
    assert parameter_name == "payload"


def test_get_parameter_unnamed_falls_back_when_varkwargs_have_no_dataframe() -> None:
    def func(meta: str, **options: Any) -> None:
        pass

    result = get_parameter(func, None, "metadata", retries=3, verbose=True)
    assert result == "metadata"

    parameter_name = get_parameter_name(func, None, "metadata", retries=3, verbose=True)
    assert parameter_name == "meta"
