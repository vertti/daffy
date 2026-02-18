"""Tests for utility functions."""

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
