from typing import Any

import pandas as pd
import polars as pl
import pytest

from daffy import df_in
from daffy.utils import get_parameter_name
from tests.conftest import IntoDataFrame, cars, extended_cars


def test_wrong_input_type_unnamed() -> None:
    @df_in()
    def test_fn(my_input: Any) -> Any:
        return my_input

    with pytest.raises(AssertionError) as excinfo:
        test_fn("foobar")

    assert "Wrong parameter type" in str(excinfo.value)


def test_wrong_input_type_named() -> None:
    @df_in(name="my_input")
    def test_fn(my_input: Any) -> Any:
        return my_input

    with pytest.raises(AssertionError) as excinfo:
        test_fn(my_input="foobar")

    assert "Wrong parameter type" in str(excinfo.value)
    assert "got str instead" in str(excinfo.value)


@pytest.mark.parametrize("df", [pd.DataFrame(cars), pl.DataFrame(cars)])
def test_correct_input_with_columns(df: IntoDataFrame) -> None:
    @df_in(columns=["Brand", "Price"])
    def test_fn(my_input: Any) -> Any:
        return my_input

    test_fn(df)


@pytest.mark.parametrize("df", [pd.DataFrame(cars), pl.DataFrame(cars)])
def test_correct_input_with_no_column_constraints(df: IntoDataFrame) -> None:
    @df_in()
    def test_fn(my_input: Any) -> Any:
        return my_input

    test_fn(df)


def test_dfin_with_no_inputs() -> None:
    @df_in()
    def test_fn() -> Any:
        return

    with pytest.raises(AssertionError) as excinfo:
        test_fn()

    assert "Wrong parameter type" in str(excinfo.value)
    assert "got NoneType instead" in str(excinfo.value)


@pytest.mark.parametrize("df", [pd.DataFrame(cars), pl.DataFrame(cars)])
def test_df_in_unnamed_selects_first_dataframe_like_parameter(df: IntoDataFrame) -> None:
    @df_in(columns=["Brand", "Price"])
    def test_fn(metadata: str, table: IntoDataFrame, retries: int) -> IntoDataFrame:
        return table

    result = test_fn("context", df, 3)
    assert result is df


@pytest.mark.parametrize("df", [pd.DataFrame(cars), pl.DataFrame(cars)])
def test_df_in_unnamed_selects_dataframe_like_parameter_with_kwargs(df: IntoDataFrame) -> None:
    @df_in(columns=["Brand", "Price"])
    def test_fn(metadata: str, table: IntoDataFrame) -> IntoDataFrame:
        return table

    result = test_fn(metadata="context", table=df)
    assert result is df


@pytest.mark.parametrize("df", [pd.DataFrame(cars), pl.DataFrame(cars)])
def test_correct_named_input_with_columns(df: IntoDataFrame) -> None:
    @df_in(name="_df", columns=["Brand", "Price"])
    def test_fn(my_input: Any, _df: IntoDataFrame) -> IntoDataFrame:
        return _df

    test_fn("foo", _df=df)


@pytest.mark.parametrize("df", [pd.DataFrame(cars), pl.DataFrame(cars)])
def test_correct_named_input_with_columns_strict(df: IntoDataFrame) -> None:
    @df_in(name="_df", columns=["Brand", "Price"], strict=True)
    def test_fn(my_input: Any, _df: IntoDataFrame) -> IntoDataFrame:
        return _df

    test_fn("foo", _df=df)


@pytest.mark.parametrize("df", [pd.DataFrame(cars), pl.DataFrame(cars)])
def test_correct_named_input_with_columns_strict_no_name(df: IntoDataFrame) -> None:
    @df_in(columns=["Brand", "Price"], strict=True)
    def test_fn(_df: IntoDataFrame) -> IntoDataFrame:
        return _df

    test_fn(_df=df)


@pytest.mark.parametrize("df", [pd.DataFrame(cars), pl.DataFrame(cars)])
def test_in_allow_extra_columns(df: IntoDataFrame) -> None:
    @df_in(name="_df", columns=["Brand"])
    def test_fn(my_input: Any, _df: IntoDataFrame) -> IntoDataFrame:
        return _df

    test_fn("foo", _df=df)


@pytest.mark.parametrize("df", [pd.DataFrame(cars), pl.DataFrame(cars)])
def test_in_strict_extra_columns(df: IntoDataFrame) -> None:
    @df_in(name="_df", columns=["Brand"], strict=True)
    def test_fn(my_input: Any, _df: IntoDataFrame) -> IntoDataFrame:
        return _df

    with pytest.raises(AssertionError) as excinfo:
        test_fn("foo", _df=df)

    assert "DataFrame in function 'test_fn' parameter '_df' contained unexpected column(s): Price" in str(excinfo.value)


def test_correct_input_with_columns_and_dtypes_pandas(basic_pandas_df: pd.DataFrame) -> None:
    @df_in(columns={"Brand": "object", "Price": "int64"})
    def test_fn(my_input: Any) -> Any:
        return my_input

    test_fn(basic_pandas_df)


def test_correct_input_with_columns_and_dtypes_polars(basic_polars_df: pl.DataFrame) -> None:
    @df_in(columns={"Brand": pl.datatypes.String, "Price": pl.datatypes.Int64})
    def test_fn(my_input: Any) -> Any:
        return my_input

    test_fn(basic_polars_df)


def test_dtype_mismatch_pandas(basic_pandas_df: pd.DataFrame) -> None:
    @df_in(columns={"Brand": "object", "Price": "float64"})
    def test_fn(my_input: Any) -> Any:
        return my_input

    with pytest.raises(AssertionError) as excinfo:
        test_fn(basic_pandas_df)

    assert (
        "Column Price in function 'test_fn' parameter 'my_input' has wrong dtype. Was int64, expected float64"
        in str(excinfo.value)
    )


def test_dtype_mismatch_polars(basic_polars_df: pl.DataFrame) -> None:
    @df_in(columns={"Brand": pl.datatypes.String, "Price": pl.datatypes.Float64})
    def test_fn(my_input: Any) -> Any:
        return my_input

    with pytest.raises(AssertionError) as excinfo:
        test_fn(basic_polars_df)

    assert (
        "Column Price in function 'test_fn' parameter 'my_input' has wrong dtype. Was int64, expected Float64"
        in str(excinfo.value)
    )


@pytest.mark.parametrize("df", [pd.DataFrame(cars), pl.DataFrame(cars)])
def test_df_in_missing_column(df: Any) -> None:
    @df_in(columns=["Brand", "Price"])
    def test_fn(my_input: Any) -> Any:
        return my_input

    with pytest.raises(AssertionError) as excinfo:
        test_fn(df[["Brand"]])
    assert "Missing columns: ['Price'] in function 'test_fn' parameter 'my_input'. Got columns: ['Brand']" in str(
        excinfo.value
    )


@pytest.mark.parametrize("df", [pd.DataFrame(cars), pl.DataFrame(cars)])
def test_df_in_missing_multiple_columns(df: Any) -> None:
    @df_in(columns=["Brand", "Price", "Extra"])
    def test_fn(my_input: Any) -> Any:
        return my_input

    with pytest.raises(AssertionError) as excinfo:
        test_fn(df[["Brand"]])
    assert (
        "Missing columns: ['Price', 'Extra'] in function 'test_fn' parameter 'my_input'. Got columns: ['Brand']"
        in str(excinfo.value)
    )


@pytest.mark.parametrize(
    ("basic_df", "extended_df"),
    [(pd.DataFrame(cars), pd.DataFrame(extended_cars)), (pl.DataFrame(cars), pl.DataFrame(extended_cars))],
)
def test_multiple_named_inputs_with_names_in_function_call(basic_df: IntoDataFrame, extended_df: IntoDataFrame) -> None:
    @df_in(name="cars", columns=["Brand", "Price"], strict=True)
    @df_in(name="ext_cars", columns=["Brand", "Price", "Year"], strict=True)
    def test_fn(cars: IntoDataFrame, ext_cars: IntoDataFrame) -> int:
        return len(cars) + len(ext_cars)

    test_fn(cars=basic_df, ext_cars=extended_df)


@pytest.mark.parametrize(
    ("basic_df", "extended_df"),
    [(pd.DataFrame(cars), pd.DataFrame(extended_cars)), (pl.DataFrame(cars), pl.DataFrame(extended_cars))],
)
def test_multiple_named_inputs_without_names_in_function_call(
    basic_df: IntoDataFrame, extended_df: IntoDataFrame
) -> None:
    @df_in(name="cars", columns=["Brand", "Price"], strict=True)
    @df_in(name="ext_cars", columns=["Brand", "Price", "Year"], strict=True)
    def test_fn(cars: pd.DataFrame, ext_cars: pd.DataFrame) -> int:
        return len(cars) + len(ext_cars)

    test_fn(basic_df, extended_df)


@pytest.mark.parametrize(
    ("basic_df", "extended_df"),
    [(pd.DataFrame(cars), pd.DataFrame(extended_cars)), (pl.DataFrame(cars), pl.DataFrame(extended_cars))],
)
def test_multiple_named_inputs_with_some_of_names_in_function_call(
    basic_df: IntoDataFrame, extended_df: IntoDataFrame
) -> None:
    @df_in(name="cars", columns=["Brand", "Price"], strict=True)
    @df_in(name="ext_cars", columns=["Brand", "Price", "Year"], strict=True)
    def test_fn(cars: IntoDataFrame, ext_cars: IntoDataFrame) -> int:
        return len(cars) + len(ext_cars)

    test_fn(basic_df, ext_cars=extended_df)


def test_regex_column_pattern(basic_pandas_df: pd.DataFrame) -> None:
    # Create a DataFrame with numbered price columns
    df = basic_pandas_df.copy()
    df["Price_1"] = df["Price"] * 1
    df["Price_2"] = df["Price"] * 2
    df["Price_3"] = df["Price"] * 3

    @df_in(columns=["Brand", "r/Price_[0-9]/"])
    def test_fn(my_input: Any) -> Any:
        return my_input

    # This should pass since we have Price_1, Price_2, and Price_3 columns
    result = test_fn(df)
    assert "Price_1" in result.columns
    assert "Price_2" in result.columns
    assert "Price_3" in result.columns


def test_regex_column_pattern_missing(basic_pandas_df: pd.DataFrame) -> None:
    @df_in(columns=["Brand", "r/NonExistent_[0-9]/"])
    def test_fn(my_input: Any) -> Any:
        return my_input

    # This should fail since we don't have any columns matching the pattern
    with pytest.raises(AssertionError) as excinfo:
        test_fn(basic_pandas_df)

    assert "Missing columns: ['r/NonExistent_[0-9]/']" in str(excinfo.value)


def test_regex_column_pattern_with_strict(basic_pandas_df: pd.DataFrame) -> None:
    # Create a DataFrame with numbered price columns
    df = basic_pandas_df.copy()
    df["Price_1"] = df["Price"] * 1
    df["Price_2"] = df["Price"] * 2

    @df_in(columns=["Brand", "r/Price_[0-9]/"], strict=True)
    def test_fn(my_input: Any) -> Any:
        return my_input

    # This should pass, because "Price" is unexpected but "Price_1" and "Price_2" match the regex
    with pytest.raises(AssertionError) as excinfo:
        test_fn(df)

    assert "DataFrame in function 'test_fn' parameter 'my_input' contained unexpected column(s): Price" in str(
        excinfo.value
    )


def test_regex_column_with_dtype_pandas(basic_pandas_df: pd.DataFrame) -> None:
    # Create a DataFrame with numbered price columns
    df = basic_pandas_df.copy()
    df["Price_1"] = df["Price"] * 1
    df["Price_2"] = df["Price"] * 2

    @df_in(columns={"Brand": "object", "r/Price_[0-9]/": "int64"})
    def test_fn(my_input: Any) -> Any:
        return my_input

    # This should pass since Price_1 and Price_2 are int64
    result = test_fn(df)
    assert "Price_1" in result.columns
    assert "Price_2" in result.columns


def test_regex_column_with_dtype_mismatch_pandas(basic_pandas_df: pd.DataFrame) -> None:
    # Create a DataFrame with numbered price columns
    df = basic_pandas_df.copy()
    df["Price_1"] = df["Price"] * 1
    df["Price_2"] = df["Price"] * 2.0  # Make this a float

    @df_in(columns={"Brand": "object", "r/Price_[0-9]/": "int64"})
    def test_fn(my_input: Any) -> Any:
        return my_input

    # This should fail since Price_2 is float64, not int64
    with pytest.raises(AssertionError) as excinfo:
        test_fn(df)

    assert (
        "Column Price_2 in function 'test_fn' parameter 'my_input' has wrong dtype. Was float64, expected int64"
        in str(excinfo.value)
    )


def test_regex_column_with_dtype_polars(basic_polars_df: pl.DataFrame) -> None:
    # Create a DataFrame with numbered price columns
    # Polars DataFrames are immutable, so we don't need to copy
    df = basic_polars_df.with_columns([pl.col("Price").alias("Price_1"), pl.col("Price").alias("Price_2")])

    @df_in(columns={"Brand": pl.datatypes.String, "r/Price_[0-9]/": pl.datatypes.Int64})
    def test_fn(my_input: Any) -> Any:
        return my_input

    # This should pass since Price_1 and Price_2 are Int64
    result = test_fn(df)
    assert "Price_1" in result.columns
    assert "Price_2" in result.columns


@pytest.mark.parametrize(
    ("basic_df", "extended_df"),
    [(pd.DataFrame(cars), pd.DataFrame(extended_cars)), (pl.DataFrame(cars), pl.DataFrame(extended_cars))],
)
def test_multiple_parameters_error_identification(basic_df: IntoDataFrame, extended_df: IntoDataFrame) -> None:
    """Test that we can identify which parameter has the issue when multiple dataframes are used."""

    @df_in(name="cars", columns=["Brand", "Price"], strict=True)
    @df_in(name="ext_cars", columns=["Brand", "Price", "Year", "NonExistent"], strict=True)
    def test_fn(cars: IntoDataFrame, ext_cars: IntoDataFrame) -> int:
        return len(cars) + len(ext_cars)

    # Test missing column in second parameter
    with pytest.raises(AssertionError) as excinfo:
        test_fn(cars=basic_df, ext_cars=extended_df)

    assert "Missing columns: ['NonExistent'] in function 'test_fn' parameter 'ext_cars'" in str(excinfo.value)


def test_check_columns_handles_invalid_column_type_in_list() -> None:
    """Invalid column types in list spec are silently ignored."""
    columns: Any = ["A", 123]

    @df_in(columns=columns)
    def process(df: pd.DataFrame) -> pd.DataFrame:
        return df

    df = pd.DataFrame({"A": [1, 2], "B": [3, 4]})
    result = process(df)
    assert len(result) == 2


def test_check_columns_handles_invalid_column_key_in_dict() -> None:
    """Invalid column keys in dict spec are silently ignored."""
    columns: Any = {"A": "int64", 123: "int64"}

    @df_in(columns=columns)
    def process(df: pd.DataFrame) -> pd.DataFrame:
        return df

    df = pd.DataFrame({"A": [1, 2], "B": [3, 4]})
    result = process(df)
    assert len(result) == 2


def test_check_columns_handles_invalid_column_key_with_constraints() -> None:
    """Invalid column keys with constraints in dict spec are silently ignored."""
    columns: Any = {"A": {"nullable": False}, 123: {"nullable": False}}

    @df_in(columns=columns)
    def process(df: pd.DataFrame) -> pd.DataFrame:
        return df

    df = pd.DataFrame({"A": [1, 2], "B": [3, 4]})
    result = process(df)
    assert len(result) == 2


def test_get_parameter_name_returns_none_when_no_params() -> None:
    def func_with_no_params() -> None:
        pass

    result = get_parameter_name(func_with_no_params, None)
    assert result is None


def test_get_parameter_name_returns_none_when_no_args_or_kwargs() -> None:
    def some_func(param: str) -> str:
        return param

    result = get_parameter_name(some_func, None)
    assert result is None


def test_missing_column_in_dict_specification() -> None:
    @df_in(columns={"A": "int64", "MissingCol": "int64"})
    def process(df: pd.DataFrame) -> pd.DataFrame:
        return df

    df = pd.DataFrame({"A": [1, 2]})
    with pytest.raises(AssertionError) as excinfo:
        process(df)

    assert "Missing columns: ['MissingCol']" in str(excinfo.value)


def test_missing_regex_pattern_in_dict_specification() -> None:
    @df_in(columns={"A": "int64", "r/Missing_[0-9]/": "int64"})
    def process(df: pd.DataFrame) -> pd.DataFrame:
        return df

    df = pd.DataFrame({"A": [1, 2]})
    with pytest.raises(AssertionError) as excinfo:
        process(df)

    assert "Missing columns: ['r/Missing_[0-9]/']" in str(excinfo.value)


def test_dict_columns_all_present_no_error() -> None:
    @df_in(columns={"A": "int64", "B": "int64"})
    def test_fn(df: pd.DataFrame) -> pd.DataFrame:
        return df

    df = pd.DataFrame({"A": [1, 2], "B": [3, 4]})
    result = test_fn(df)
    assert result is not None


def test_function_name_appears_in_missing_columns_exception() -> None:
    @df_in(columns=["Brand", "NonExistentColumn"])
    def my_test_function(df: pd.DataFrame) -> pd.DataFrame:
        return df

    df = pd.DataFrame({"Brand": ["Toyota", "Honda"]})

    with pytest.raises(AssertionError) as excinfo:
        my_test_function(df)

    # Should include function name in the exception message
    assert "my_test_function" in str(excinfo.value)
    assert "Missing columns: ['NonExistentColumn']" in str(excinfo.value)


def test_function_name_appears_in_dtype_mismatch_exception() -> None:
    @df_in(columns={"Brand": "object", "Price": "float64"})
    def another_test_function(df: pd.DataFrame) -> pd.DataFrame:
        return df

    df = pd.DataFrame({"Brand": ["Toyota"], "Price": [100]})  # Price is int64, not float64

    with pytest.raises(AssertionError) as excinfo:
        another_test_function(df)

    # Should include function name in the exception message
    assert "another_test_function" in str(excinfo.value)
    assert "Column Price" in str(excinfo.value)
    assert "wrong dtype" in str(excinfo.value)
