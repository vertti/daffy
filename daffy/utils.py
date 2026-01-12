"""Utility functions for DAFFY DataFrame Column Validator."""

from __future__ import annotations

import inspect
import logging
from typing import TYPE_CHECKING, Any

import narwhals as nw

from daffy.dataframe_types import get_available_library_names
from daffy.narwhals_compat import is_supported_dataframe

if TYPE_CHECKING:
    from collections.abc import Callable


def assert_is_dataframe(obj: Any, context: str) -> None:
    """Verify that an object is a supported DataFrame (Pandas, Polars, Modin, or PyArrow).

    Args:
        obj: Object to validate
        context: Context string for the error message (e.g., "parameter type", "return type")

    Raises:
        AssertionError: If obj is not a DataFrame

    """
    if not is_supported_dataframe(obj):
        libs_str = " or ".join(get_available_library_names())
        raise AssertionError(f"Wrong {context}. Expected {libs_str} DataFrame, got {type(obj).__name__} instead.")


def get_parameter(func: Callable[..., Any], name: str | None = None, *args: Any, **kwargs: Any) -> Any:
    """Extract a parameter value from function arguments.

    Args:
        func: The function whose parameters to inspect
        name: Name of the parameter to extract. If None, returns first positional arg or kwarg.
        *args: Positional arguments passed to the function
        **kwargs: Keyword arguments passed to the function

    Returns:
        The value of the requested parameter

    Raises:
        ValueError: If the named parameter cannot be found in args or kwargs

    """
    if not name:
        # Return first arg/kwarg or None - let downstream code handle validation
        return args[0] if args else next(iter(kwargs.values()), None)

    if name in kwargs:
        return kwargs[name]

    func_params_in_order = list(inspect.signature(func).parameters.keys())

    if name not in func_params_in_order:
        raise ValueError(f"Parameter '{name}' not found in function signature. Available: {func_params_in_order}")

    parameter_location = func_params_in_order.index(name)

    if parameter_location >= len(args):
        raise ValueError(
            f"Parameter '{name}' not found in function arguments. "
            f"Expected at position {parameter_location}, but only {len(args)} positional arguments provided."
        )

    return args[parameter_location]


def get_parameter_name(func: Callable[..., Any], name: str | None = None, *args: Any, **kwargs: Any) -> str | None:
    if name:
        return name

    if args:
        func_params_in_order = list(inspect.signature(func).parameters.keys())
        return func_params_in_order[0]

    return next(iter(kwargs.keys()), None)


def describe_dataframe(df: Any, include_dtypes: bool = False) -> str:
    nw_df = nw.from_native(df, eager_only=True)
    result = f"columns: {nw_df.columns}"
    if include_dtypes:
        result += f" with dtypes {list(nw_df.schema.values())}"
    return result


def _log_dataframe(level: int, func_name: str, df: Any, include_dtypes: bool, context: str) -> None:
    if is_supported_dataframe(df):
        logging.log(level, f"Function {func_name} {context}: {describe_dataframe(df, include_dtypes)}")  # noqa: LOG015, G004


def log_dataframe_input(level: int, func_name: str, df: Any, include_dtypes: bool) -> None:
    _log_dataframe(level, func_name, df, include_dtypes, "parameters contained a DataFrame")


def log_dataframe_output(level: int, func_name: str, df: Any, include_dtypes: bool) -> None:
    _log_dataframe(level, func_name, df, include_dtypes, "returned a DataFrame")
