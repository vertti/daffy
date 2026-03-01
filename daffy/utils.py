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


def resolve_parameter(
    func: Callable[..., Any], name: str | None = None, *args: Any, **kwargs: Any
) -> tuple[Any, str | None]:
    """Extract a parameter value and its name from function arguments in a single pass.

    Combines the work of get_parameter and get_parameter_name to avoid
    duplicate signature introspection.
    """
    if not name:
        first_dataframe_arg = _find_first_dataframe_argument(func, *args, **kwargs)
        if first_dataframe_arg is not None:
            return first_dataframe_arg

        value = args[0] if args else next(iter(kwargs.values()), None)
        if args:
            param_name: str | None = next(iter(inspect.signature(func).parameters.keys()))
        else:
            param_name = next(iter(kwargs.keys()), None)
        return value, param_name

    if name in kwargs:
        return kwargs[name], name

    func_params_in_order = list(inspect.signature(func).parameters.keys())

    if name not in func_params_in_order:
        raise ValueError(f"Parameter '{name}' not found in function signature. Available: {func_params_in_order}")

    parameter_location = func_params_in_order.index(name)

    if parameter_location >= len(args):
        raise ValueError(
            f"Parameter '{name}' not found in function arguments. "
            f"Expected at position {parameter_location}, but only {len(args)} positional arguments provided."
        )

    return args[parameter_location], name


def get_parameter(func: Callable[..., Any], name: str | None = None, *args: Any, **kwargs: Any) -> Any:
    """Extract a parameter value from function arguments."""
    return resolve_parameter(func, name, *args, **kwargs)[0]


def get_parameter_name(func: Callable[..., Any], name: str | None = None, *args: Any, **kwargs: Any) -> str | None:
    """Resolve the effective parameter name used for validation."""
    return resolve_parameter(func, name, *args, **kwargs)[1]


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
