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
        name: Name of the parameter to extract. If None, the function first attempts to
            find and return a DataFrame-like argument; if no DataFrame-like argument is
            found, it falls back to returning the first positional arg or kwarg.
        *args: Positional arguments passed to the function
        **kwargs: Keyword arguments passed to the function

    Returns:
        The value of the requested parameter

    Raises:
        ValueError: If the named parameter cannot be found in args or kwargs

    """
    if not name:
        first_dataframe_arg = _find_first_dataframe_argument(func, *args, **kwargs)
        if first_dataframe_arg is not None:
            return first_dataframe_arg[0]

        # Keep existing fallback behavior when no DataFrame-like argument is present.
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
    """Resolve the effective parameter name used for validation.

    Resolution order:
    1. Return the explicit ``name`` argument when provided.
    2. Find the first DataFrame-like argument via ``_find_first_dataframe_argument``.
    3. Fall back to the first positional parameter name if positional args were provided.
    4. Fall back to the first keyword argument name.

    Args:
        func: The function whose parameters to inspect.
        name: Explicit parameter name to use, or ``None`` for automatic resolution.
        *args: Positional arguments passed to the function.
        **kwargs: Keyword arguments passed to the function.

    Returns:
        The resolved parameter name, or ``None`` when no name can be determined.

    """
    if name:
        return name

    first_dataframe_arg = _find_first_dataframe_argument(func, *args, **kwargs)
    if first_dataframe_arg is not None:
        return first_dataframe_arg[1]

    if args:
        func_params_in_order = list(inspect.signature(func).parameters.keys())
        return func_params_in_order[0]

    return next(iter(kwargs.keys()), None)


def _find_first_dataframe_argument(func: Callable[..., Any], *args: Any, **kwargs: Any) -> tuple[Any, str] | None:
    """Find the first DataFrame-like argument using function signature order."""
    sig = inspect.signature(func)
    bound_args = sig.bind_partial(*args, **kwargs)

    for param_name, param in sig.parameters.items():
        if param_name not in bound_args.arguments:
            continue

        value = bound_args.arguments[param_name]

        if param.kind is inspect.Parameter.VAR_POSITIONAL:
            for item in value:
                if is_supported_dataframe(item):
                    return item, param_name
            continue

        if param.kind is inspect.Parameter.VAR_KEYWORD:
            for kwarg_name, kwarg_value in value.items():
                if is_supported_dataframe(kwarg_value):
                    return kwarg_value, kwarg_name
            continue

        if is_supported_dataframe(value):
            return value, param_name

    return None


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
