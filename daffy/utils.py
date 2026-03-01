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


class ParameterResolver:
    """Efficiently resolves parameter values from function arguments without repeated introspection."""

    def __init__(self, func: Callable[..., Any]) -> None:
        sig = inspect.signature(func)
        self.params = list(sig.parameters.values())
        self.param_names = [p.name for p in self.params]
        self.var_pos_name = next((p.name for p in self.params if p.kind is inspect.Parameter.VAR_POSITIONAL), None)
        self.var_kw_name = next((p.name for p in self.params if p.kind is inspect.Parameter.VAR_KEYWORD), None)

    def resolve(self, name: str | None, *args: Any, **kwargs: Any) -> tuple[Any, str | None]:  # noqa: C901, PLR0911, PLR0912
        """Extract a parameter value and its name from function arguments."""
        if not name:
            # 1. Search positional arguments
            for i, arg in enumerate(args):
                if is_supported_dataframe(arg):
                    if i < len(self.param_names):
                        return arg, self.param_names[i]
                    return arg, self.var_pos_name

            # 2. Search keyword arguments
            for kw_name, kw_val in kwargs.items():
                if is_supported_dataframe(kw_val):
                    # If it's explicitly in the signature, return that name.
                    # Otherwise, if it's passed as kwargs but VAR_KEYWORD exists, return kw_name.
                    return kw_val, kw_name

            # 3. Fallback to first argument if no dataframe found
            value = args[0] if args else next(iter(kwargs.values()), None)
            if args:
                param_name = self.param_names[0] if self.param_names else None
            else:
                param_name = next(iter(kwargs.keys()), None)
            return value, param_name

        if name in kwargs:
            return kwargs[name], name

        try:
            parameter_location = self.param_names.index(name)
        except ValueError:
            raise ValueError(
                f"Parameter '{name}' not found in function signature. Available: {self.param_names}"
            ) from None

        param = self.params[parameter_location]
        if param.kind == inspect.Parameter.KEYWORD_ONLY:
            if param.default is not inspect.Parameter.empty:
                return param.default, name
            raise ValueError(f"Required keyword-only parameter '{name}' not provided in arguments.")

        if parameter_location >= len(args):
            if param.default is not inspect.Parameter.empty:
                return param.default, name
            raise ValueError(
                f"Parameter '{name}' not found in function arguments. "
                f"Expected at position {parameter_location}, but only {len(args)} positional arguments provided."
            )

        return args[parameter_location], name


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
