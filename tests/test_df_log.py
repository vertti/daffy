import logging
from unittest.mock import call

import pandas as pd
import polars as pl
import pytest
from pytest_mock import MockerFixture

from daffy import df_log
from tests.conftest import IntoDataFrame, cars


@pytest.mark.parametrize(("df"), [pd.DataFrame(cars), pl.DataFrame(cars)])
def test_log_df(df: IntoDataFrame, mocker: MockerFixture) -> None:
    @df_log()
    def test_fn(foo_df: IntoDataFrame) -> IntoDataFrame:
        return foo_df

    mock_log = mocker.patch("daffy.decorators.logging.log")
    test_fn(df)

    mock_log.assert_has_calls(
        [
            call(
                logging.DEBUG,
                ("Function test_fn parameters contained a DataFrame: columns: ['Brand', 'Price']"),
            ),
            call(
                logging.DEBUG,
                "Function test_fn returned a DataFrame: columns: ['Brand', 'Price']",
            ),
        ]
    )


def test_log_df_with_dtypes(basic_pandas_df: pd.DataFrame, mocker: MockerFixture) -> None:
    @df_log(include_dtypes=True)
    def test_fn(foo_df: pd.DataFrame) -> pd.DataFrame:
        return basic_pandas_df

    mock_log = mocker.patch("daffy.decorators.logging.log")
    test_fn(basic_pandas_df)

    # Narwhals provides unified dtype representation across pandas/polars
    mock_log.assert_has_calls(
        [
            call(
                logging.DEBUG,
                (
                    "Function test_fn parameters contained a DataFrame: "
                    "columns: ['Brand', 'Price'] with dtypes [String, Int64]"
                ),
            ),
            call(
                logging.DEBUG,
                "Function test_fn returned a DataFrame: columns: ['Brand', 'Price'] with dtypes [String, Int64]",
            ),
        ]
    )


def test_log_df_with_dtypes_polars(basic_polars_df: pl.DataFrame, mocker: MockerFixture) -> None:
    @df_log(include_dtypes=True)
    def test_fn(foo_df: pl.DataFrame) -> pl.DataFrame:
        return basic_polars_df

    mock_log = mocker.patch("daffy.decorators.logging.log")
    test_fn(basic_polars_df)

    mock_log.assert_has_calls(
        [
            call(
                logging.DEBUG,
                (
                    "Function test_fn parameters contained a DataFrame: "
                    "columns: ['Brand', 'Price'] with dtypes [String, Int64]"
                ),
            ),
            call(
                logging.DEBUG,
                "Function test_fn returned a DataFrame: columns: ['Brand', 'Price'] with dtypes [String, Int64]",
            ),
        ]
    )


def test_log_non_df(mocker: MockerFixture) -> None:
    @df_log()
    def test_fn(foo: str) -> int:
        return 123

    mock_log = mocker.patch("daffy.decorators.logging.log")
    test_fn("foo")

    mock_log.assert_not_called()
