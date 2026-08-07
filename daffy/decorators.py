"""Decorators for DAFFY DataFrame Column Validator."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from functools import wraps
from typing import TYPE_CHECKING, Any, ParamSpec, TypeVar, overload

if TYPE_CHECKING:
    from collections.abc import Callable

    from pydantic import BaseModel

    from daffy.dataframe_types import IntoDataFrameT
    from daffy.validation import ColumnsDef

from daffy.checks import BUILTIN_CHECK_NAMES
from daffy.config import resolve_decorator_settings
from daffy.utils import (
    ParameterResolver,
    assert_is_dataframe,
    log_dataframe_input,
    log_dataframe_output,
)
from daffy.validators.builder import build_validation_pipeline
from daffy.validators.context import ValidationContext
from daffy.validators.spec_parser import assert_known_constraints


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


_BOOLEAN_CONSTRAINTS = ("nullable", "unique", "required")


def _validate_check_names(column: str, checks: Any) -> None:
    """Reject unknown built-in check names.

    Mirrors `apply_check`: a callable check value is a custom check and may carry any
    name, so only non-callable values are matched against the built-ins.
    """
    if not isinstance(checks, dict):
        return

    for check_name, check_value in checks.items():
        if callable(check_value) or check_name in BUILTIN_CHECK_NAMES:
            continue
        valid = ", ".join(sorted(BUILTIN_CHECK_NAMES))
        raise ValueError(
            f"Unknown check '{check_name}' for column '{column}'. "
            f"Pass a callable to define a custom check, or use one of: {valid}"
        )


def _validate_column_spec(columns: ColumnsDef) -> None:
    """Reject unusable column specs at decoration time.

    Everything here used to be accepted and then quietly do nothing, which is the worst
    outcome for a validation library: the decorator reads as a guarantee while no
    validation runs. Catching it at decoration puts the error next to the mistake.
    """
    if not isinstance(columns, Mapping):
        return

    for column, spec in columns.items():
        if not isinstance(spec, dict):
            continue

        assert_known_constraints(str(column), spec)

        for key in _BOOLEAN_CONSTRAINTS:
            if key in spec and not isinstance(spec[key], bool):
                raise TypeError(
                    f"Constraint '{key}' for column '{column}' must be True or False, "
                    f"got {type(spec[key]).__name__}: {spec[key]!r}"
                )

        _validate_check_names(str(column), spec.get("checks"))


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


# Type variables for preserving signatures. ParamSpec keeps the decorated function's
# parameters visible to type checkers - with a bare `...` every call site of a
# decorated function silently loses argument checking.
LogParams = ParamSpec("LogParams")
InParams = ParamSpec("InParams")
OutParams = ParamSpec("OutParams")
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
    nw_df: Any = None,
) -> None:
    """Run all validations on a DataFrame using the validation pipeline."""
    ctx = ValidationContext(
        df=df,
        func_name=func_name,
        param_name=param_name,
        is_return_value=is_return_value,
        nw_df=nw_df,
    )

    settings = resolve_decorator_settings(strict, lazy, allow_empty)
    pipeline = build_validation_pipeline(
        columns=columns,
        strict=settings.strict,
        strict_specs=settings.strict_specs,
        lazy=settings.lazy,
        composite_unique=composite_unique,
        row_validator=row_validator,
        min_rows=min_rows,
        max_rows=max_rows,
        exact_rows=exact_rows,
        allow_empty=settings.allow_empty,
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
) -> Callable[[Callable[OutParams, IntoDataFrameT]], Callable[OutParams, IntoDataFrameT]]:
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

    Note:
        When ``[tool.daffy] strict_specs = true`` is set in pyproject.toml, invalid column
        keys or spec types raise ``TypeError`` instead of being silently ignored.

    Returns:
        Callable: Decorated function with preserved DataFrame return type

    """
    _validate_column_spec(columns)
    _validate_composite_unique(composite_unique)
    _validate_shape_constraints(min_rows, max_rows, exact_rows)

    def wrapper_df_out(func: Callable[OutParams, IntoDataFrameT]) -> Callable[OutParams, IntoDataFrameT]:
        @wraps(func)
        def wrapper(*args: OutParams.args, **kwargs: OutParams.kwargs) -> IntoDataFrameT:
            result = func(*args, **kwargs)
            nw_df = assert_is_dataframe(result, "return type")
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
                nw_df=nw_df,
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
) -> Callable[[Callable[InParams, InReturnT]], Callable[InParams, InReturnT]]: ...


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
) -> Callable[[Callable[InParams, InReturnT]], Callable[InParams, InReturnT]]: ...


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
) -> Callable[[Callable[InParams, InReturnT]], Callable[InParams, InReturnT]]:
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

    Note:
        When ``[tool.daffy] strict_specs = true`` is set in pyproject.toml, invalid column
        keys or spec types raise ``TypeError`` instead of being silently ignored.

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

    _validate_column_spec(columns)
    _validate_composite_unique(composite_unique)
    _validate_shape_constraints(min_rows, max_rows, exact_rows)

    def wrapper_df_in(func: Callable[InParams, InReturnT]) -> Callable[InParams, InReturnT]:
        resolver = ParameterResolver(func)

        @wraps(func)
        def wrapper(*args: InParams.args, **kwargs: InParams.kwargs) -> InReturnT:
            df, param_name, resolved_nw_df = resolver.resolve(name, *args, **kwargs)
            nw_df = assert_is_dataframe(df, "parameter type", resolved_nw_df)
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
                nw_df=nw_df,
            )
            return func(*args, **kwargs)

        return wrapper

    return wrapper_df_in


def df_log(
    level: int = logging.DEBUG, include_dtypes: bool = False
) -> Callable[[Callable[LogParams, LogReturnT]], Callable[LogParams, LogReturnT]]:
    """Decorate a function that consumes or produces a Pandas DataFrame or both.

    Logs the columns of the consumed and/or produced DataFrame.

    Args:
        level (int, optional): Level of the logging messages produced. Defaults to logging.DEBUG.
        include_dtypes (bool, optional): When set to True, will log also the dtypes of each column. Defaults to False.

    Returns:
        Callable: Decorated function with preserved return type.

    """

    def wrapper_df_log(func: Callable[LogParams, LogReturnT]) -> Callable[LogParams, LogReturnT]:
        resolver = ParameterResolver(func)

        @wraps(func)
        def wrapper(*args: LogParams.args, **kwargs: LogParams.kwargs) -> LogReturnT:
            func_name = getattr(func, "__name__", "<unknown>")
            df, _, _ = resolver.resolve(None, *args, **kwargs)
            log_dataframe_input(level, func_name, df, include_dtypes)
            result = func(*args, **kwargs)
            log_dataframe_output(level, func_name, result, include_dtypes)
            return result

        return wrapper

    return wrapper_df_log
