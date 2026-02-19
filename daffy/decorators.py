"""Decorators for DAFFY DataFrame Column Validator."""

from __future__ import annotations

import logging
from functools import wraps
from typing import TYPE_CHECKING, Any, TypeVar, overload

if TYPE_CHECKING:
    from collections.abc import Callable

    from pydantic import BaseModel

    from daffy.dataframe_types import IntoDataFrameT
    from daffy.validation import ColumnsDef

from daffy.config import get_allow_empty, get_lazy, get_strict, get_strict_specs
from daffy.utils import (
    assert_is_dataframe,
    get_parameter,
    get_parameter_name,
    log_dataframe_input,
    log_dataframe_output,
)
from daffy.validators.builder import build_validation_pipeline
from daffy.validators.context import ValidationContext


def _validate_composite_unique(composite_unique: list[list[str]] | None) -> None:
    """Validate composite_unique parameter structure at decorator time."""
    if composite_unique is None:
        return

    if not isinstance(composite_unique, list):
        raise TypeError(f"composite_unique must be a list, got {type(composite_unique).__name__}")

    for i, combo in enumerate(composite_unique):
        if not isinstance(combo, list):
            raise TypeError(f"composite_unique[{i}] must be a list, got {type(combo).__name__}")
        if len(combo) < 2:
            raise ValueError(f"composite_unique[{i}] must have at least 2 columns, got {len(combo)}")
        for j, col in enumerate(combo):
            if not isinstance(col, str):
                raise TypeError(f"composite_unique[{i}][{j}] must be a string, got {type(col).__name__}")


def _validate_shape_constraints(
    min_rows: int | None,
    max_rows: int | None,
    exact_rows: int | None,
) -> None:
    """Validate shape constraint parameters at decorator time."""
    if min_rows is not None and min_rows < 0:
        raise ValueError(f"min_rows must be >= 0, got {min_rows}")
    if max_rows is not None and max_rows < 0:
        raise ValueError(f"max_rows must be >= 0, got {max_rows}")
    if exact_rows is not None and exact_rows < 0:
        raise ValueError(f"exact_rows must be >= 0, got {exact_rows}")
    if min_rows is not None and max_rows is not None and min_rows > max_rows:
        raise ValueError(f"min_rows ({min_rows}) cannot be greater than max_rows ({max_rows})")


# Type variables for preserving return types
LogReturnT = TypeVar("LogReturnT")  # Return type for df_log
InReturnT = TypeVar("InReturnT")  # Return type for df_in


def _run_validations(
    df: Any,
    func_name: str,
    columns: ColumnsDef,
    strict: bool | None,
    lazy: bool | None,
    composite_unique: list[list[str]] | None,
    row_validator: type[BaseModel] | None,
    min_rows: int | None,
    max_rows: int | None,
    exact_rows: int | None,
    allow_empty: bool | None,
    param_name: str | None,
    is_return_value: bool,
) -> None:
    """Run all validations on a DataFrame using the validation pipeline."""
    ctx = ValidationContext(
        df=df,
        func_name=func_name,
        param_name=param_name,
        is_return_value=is_return_value,
    )

    pipeline = build_validation_pipeline(
        columns=columns,
        strict=get_strict(strict),
        strict_specs=get_strict_specs(),
        lazy=get_lazy(lazy),
        composite_unique=composite_unique,
        row_validator=row_validator,
        min_rows=min_rows,
        max_rows=max_rows,
        exact_rows=exact_rows,
        allow_empty=get_allow_empty(allow_empty),
        df_columns=list(ctx.columns),
    )
    pipeline.run(ctx)


def df_out(
    columns: ColumnsDef = None,
    strict: bool | None = None,
    lazy: bool | None = None,
    composite_unique: list[list[str]] | None = None,
    row_validator: type[BaseModel] | None = None,
    min_rows: int | None = None,
    max_rows: int | None = None,
    exact_rows: int | None = None,
    allow_empty: bool | None = None,
) -> Callable[[Callable[..., IntoDataFrameT]], Callable[..., IntoDataFrameT]]:
    """Decorate a function that returns a DataFrame (Pandas, Polars, Modin, or PyArrow).

    Document the return value of a function. The return value will be validated in runtime.

    Args:
        columns (Union[Sequence[str], Dict[str, Any]], optional): Sequence or dict that describes expected columns
            of the DataFrame.
            Sequence can contain regex patterns in format "r/pattern/" (e.g., "r/Col[0-9]+/").
            Dict can use regex patterns as keys in format "r/pattern/" to validate dtypes for matching columns.
            Defaults to None.
        strict (bool, optional): If True, columns must match exactly with no extra columns.
            If None, uses the value from [tool.daffy] strict setting in pyproject.toml.
        lazy (bool, optional): If True, collect all validation errors before raising.
            If None, uses the value from [tool.daffy] lazy setting in pyproject.toml.
        composite_unique (list[list[str]], optional): List of column name lists that must be unique together.
            E.g., [["first_name", "last_name"]] ensures the combination is unique.
        row_validator (type[BaseModel], optional): Pydantic model for validating row data.
            Requires pydantic >= 2.4.0. Defaults to None.
        min_rows (int, optional): Minimum number of rows required. Defaults to None (no minimum).
        max_rows (int, optional): Maximum number of rows allowed. Defaults to None (no maximum).
        exact_rows (int, optional): Exact number of rows required. Defaults to None (no constraint).
        allow_empty (bool, optional): Whether empty DataFrames (0 rows) are allowed.
            If None, uses the value from [tool.daffy] allow_empty setting in pyproject.toml.

    Returns:
        Callable: Decorated function with preserved DataFrame return type

    """
    _validate_composite_unique(composite_unique)
    _validate_shape_constraints(min_rows, max_rows, exact_rows)

    def wrapper_df_out(func: Callable[..., IntoDataFrameT]) -> Callable[..., IntoDataFrameT]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> IntoDataFrameT:
            result = func(*args, **kwargs)
            assert_is_dataframe(result, "return type")
            _run_validations(
                result,
                getattr(func, "__name__", "<unknown>"),
                columns,
                strict,
                lazy,
                composite_unique,
                row_validator,
                min_rows,
                max_rows,
                exact_rows,
                allow_empty,
                param_name=None,
                is_return_value=True,
            )
            return result

        return wrapper

    return wrapper_df_out


@overload
def df_in(
    columns: ColumnsDef,
    /,
    *,
    strict: bool | None = ...,
    lazy: bool | None = ...,
    composite_unique: list[list[str]] | None = ...,
    row_validator: type[BaseModel] | None = ...,
    min_rows: int | None = ...,
    max_rows: int | None = ...,
    exact_rows: int | None = ...,
    allow_empty: bool | None = ...,
) -> Callable[[Callable[..., InReturnT]], Callable[..., InReturnT]]: ...


@overload
def df_in(
    name: str | None = ...,
    columns: ColumnsDef = ...,
    strict: bool | None = ...,
    lazy: bool | None = ...,
    composite_unique: list[list[str]] | None = ...,
    row_validator: type[BaseModel] | None = ...,
    min_rows: int | None = ...,
    max_rows: int | None = ...,
    exact_rows: int | None = ...,
    allow_empty: bool | None = ...,
) -> Callable[[Callable[..., InReturnT]], Callable[..., InReturnT]]: ...


def df_in(
    name: str | ColumnsDef | None = None,
    columns: ColumnsDef = None,
    strict: bool | None = None,
    lazy: bool | None = None,
    composite_unique: list[list[str]] | None = None,
    row_validator: type[BaseModel] | None = None,
    min_rows: int | None = None,
    max_rows: int | None = None,
    exact_rows: int | None = None,
    allow_empty: bool | None = None,
) -> Callable[[Callable[..., InReturnT]], Callable[..., InReturnT]]:
    """Decorate a function parameter that is a DataFrame (Pandas, Polars, Modin, or PyArrow).

    Document the contents of an input parameter. The parameter will be validated in runtime.

    Args:
        name (Optional[str], optional): Name of the parameter that contains a DataFrame. Defaults to None.
            Alternatively, a column specification (list or dict) may be passed as the first positional
            argument as a shorthand for ``columns=`` — e.g. ``@df_in(["col1", "col2"])``.
        columns (Union[Sequence[str], Dict[str, Any]], optional): Sequence or dict that describes expected columns
            of the DataFrame.
            Sequence can contain regex patterns in format "r/pattern/" (e.g., "r/Col[0-9]+/").
            Dict can use regex patterns as keys in format "r/pattern/" to validate dtypes for matching columns.
            Defaults to None.
        strict (bool, optional): If True, columns must match exactly with no extra columns.
            If None, uses the value from [tool.daffy] strict setting in pyproject.toml.
        lazy (bool, optional): If True, collect all validation errors before raising.
            If None, uses the value from [tool.daffy] lazy setting in pyproject.toml.
        composite_unique (list[list[str]], optional): List of column name lists that must be unique together.
            E.g., [["first_name", "last_name"]] ensures the combination is unique.
        row_validator (type[BaseModel], optional): Pydantic model for validating row data.
            Requires pydantic >= 2.4.0. Defaults to None.
        min_rows (int, optional): Minimum number of rows required. Defaults to None (no minimum).
        max_rows (int, optional): Maximum number of rows allowed. Defaults to None (no maximum).
        exact_rows (int, optional): Exact number of rows required. Defaults to None (no constraint).
        allow_empty (bool, optional): Whether empty DataFrames (0 rows) are allowed.
            If None, uses the value from [tool.daffy] allow_empty setting in pyproject.toml.

    Returns:
        Callable: Decorated function with preserved return type

    """
    if name is not None and not isinstance(name, str):
        if columns is not None:
            raise TypeError(
                "Cannot pass columns as both the first positional argument and the 'columns' keyword argument"
            )
        columns = name
        name = None

    _validate_composite_unique(composite_unique)
    _validate_shape_constraints(min_rows, max_rows, exact_rows)

    def wrapper_df_in(func: Callable[..., InReturnT]) -> Callable[..., InReturnT]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> InReturnT:
            df = get_parameter(func, name, *args, **kwargs)
            param_name = get_parameter_name(func, name, *args, **kwargs)
            assert_is_dataframe(df, "parameter type")
            _run_validations(
                df,
                getattr(func, "__name__", "<unknown>"),
                columns,
                strict,
                lazy,
                composite_unique,
                row_validator,
                min_rows,
                max_rows,
                exact_rows,
                allow_empty,
                param_name=param_name,
                is_return_value=False,
            )
            return func(*args, **kwargs)

        return wrapper

    return wrapper_df_in


def df_log(
    level: int = logging.DEBUG, include_dtypes: bool = False
) -> Callable[[Callable[..., LogReturnT]], Callable[..., LogReturnT]]:
    """Decorate a function that consumes or produces a Pandas DataFrame or both.

    Logs the columns of the consumed and/or produced DataFrame.

    Args:
        level (int, optional): Level of the logging messages produced. Defaults to logging.DEBUG.
        include_dtypes (bool, optional): When set to True, will log also the dtypes of each column. Defaults to False.

    Returns:
        Callable: Decorated function with preserved return type.

    """

    def wrapper_df_log(func: Callable[..., LogReturnT]) -> Callable[..., LogReturnT]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> LogReturnT:
            func_name = getattr(func, "__name__", "<unknown>")
            log_dataframe_input(level, func_name, get_parameter(func, None, *args, **kwargs), include_dtypes)
            result = func(*args, **kwargs)
            log_dataframe_output(level, func_name, result, include_dtypes)
            return result

        return wrapper

    return wrapper_df_log
