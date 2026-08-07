"""Utility functions for DAFFY DataFrame Column Validator."""

from __future__ import annotations

import inspect
import logging
from typing import TYPE_CHECKING, Any

from daffy.dataframe_types import get_available_library_names
from daffy.narwhals_compat import UnsupportedDataFrameError, is_supported_dataframe, to_nw_dataframe

if TYPE_CHECKING:
    from collections.abc import Callable

_POSITIONAL_KINDS = (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)


def assert_is_dataframe(obj: Any, context: str, nw_df: Any = None) -> Any:
    """Verify that an object is a supported DataFrame (Pandas, Polars, Modin, or PyArrow).

    Args:
        obj: Object to validate
        context: Context string for the error message (e.g., "parameter type", "return type")
        nw_df: Narwhals view of obj when the caller already has one, to skip re-converting

    Returns:
        The Narwhals view of the DataFrame, so callers do not convert it a second time.

    Raises:
        AssertionError: If obj is not a DataFrame

    """
    if nw_df is None:
        try:
            nw_df = to_nw_dataframe(obj)
        except UnsupportedDataFrameError as e:
            raise AssertionError(f"Cannot validate this DataFrame ({context}): {e}") from None
    if nw_df is None:
        libs_str = " or ".join(get_available_library_names())
        raise AssertionError(f"Wrong {context}. Expected {libs_str} DataFrame, got {type(obj).__name__} instead.")
    return nw_df


def _find_dataframe(obj: Any) -> tuple[Any, bool]:
    """Return (Narwhals view or None, whether obj is a DataFrame at all).

    A DataFrame Narwhals cannot convert counts as found, so the caller stops searching
    and lets `assert_is_dataframe` report why it is unusable.
    """
    try:
        nw_df = to_nw_dataframe(obj)
    except UnsupportedDataFrameError:
        return None, True
    return nw_df, nw_df is not None


class ParameterResolver:
    """Efficiently resolves parameter values from function arguments without repeated introspection."""

    def __init__(self, func: Callable[..., Any]) -> None:
        sig = inspect.signature(func)
        self.params = list(sig.parameters.values())
        self.param_names = [p.name for p in self.params]

        # Only these can be filled positionally. Indexing param_names by position would
        # run past the *args slot into keyword-only names and report the wrong parameter.
        self.positional_names = [p.name for p in self.params if p.kind in _POSITIONAL_KINDS]

        # Precompute lists for faster lookup during resolve
        self.param_kinds = [p.kind for p in self.params]
        self.param_defaults = [p.default for p in self.params]

        self.var_pos_name = next((p.name for p in self.params if p.kind is inspect.Parameter.VAR_POSITIONAL), None)
        self.var_kw_name = next((p.name for p in self.params if p.kind is inspect.Parameter.VAR_KEYWORD), None)

    def resolve(self, name: str | None, *args: Any, **kwargs: Any) -> tuple[Any, str | None, Any]:  # noqa: C901, PLR0911, PLR0912
        """Extract a parameter value and its name from function arguments.

        Returns (value, parameter name, Narwhals view). The Narwhals view is None unless
        searching for the DataFrame already produced one, in which case callers reuse it
        instead of converting the same frame again.
        """
        if not name:
            # 1. Search positional arguments
            for i, arg in enumerate(args):
                nw_df, is_frame = _find_dataframe(arg)
                if is_frame:
                    if i < len(self.positional_names):
                        return arg, self.positional_names[i], nw_df
                    return arg, self.var_pos_name, nw_df

            # 2. Search keyword arguments
            for kw_name, kw_val in kwargs.items():
                nw_df, is_frame = _find_dataframe(kw_val)
                if is_frame:
                    # If it's explicitly in the signature, return that name.
                    # Otherwise, if it's passed as kwargs but VAR_KEYWORD exists, return kw_name.
                    return kw_val, kw_name, nw_df

            # 3. Fallback to first argument if no dataframe found
            value = args[0] if args else next(iter(kwargs.values()), None)
            if args:
                param_name = self.param_names[0] if self.param_names else None
            else:
                param_name = next(iter(kwargs.keys()), None)
            return value, param_name, None

        if name in kwargs:
            return kwargs[name], name, None

        try:
            parameter_location = self.param_names.index(name)
        except ValueError:
            raise ValueError(
                f"Parameter '{name}' not found in function signature. Available: {self.param_names}"
            ) from None

        kind = self.param_kinds[parameter_location]
        default = self.param_defaults[parameter_location]

        if kind == inspect.Parameter.KEYWORD_ONLY:
            if default is not inspect.Parameter.empty:
                return default, name, None
            raise ValueError(f"Required keyword-only parameter '{name}' not provided in arguments.")

        if parameter_location >= len(args):
            if default is not inspect.Parameter.empty:
                return default, name, None
            raise ValueError(
                f"Parameter '{name}' not found in function arguments. "
                f"Expected at position {parameter_location}, but only {len(args)} positional arguments provided."
            )

        return args[parameter_location], name, None


def describe_dataframe(df: Any, include_dtypes: bool = False) -> str:
    nw_df = to_nw_dataframe(df)
    if nw_df is None:
        raise UnsupportedDataFrameError(f"not a supported DataFrame, got {type(df).__name__}")
    result = f"columns: {nw_df.columns}"
    if include_dtypes:
        result += f" with dtypes {list(nw_df.schema.values())}"
    return result


def _log_dataframe(level: int, func_name: str, df: Any, include_dtypes: bool, context: str) -> None:
    if not is_supported_dataframe(df):
        return
    try:
        description = describe_dataframe(df, include_dtypes)
    except UnsupportedDataFrameError as e:
        # df_log only logs. A frame it cannot describe must not break the function.
        logging.warning(f"Function {func_name} {context}, but it could not be described: {e}")  # noqa: LOG015, G004
        return
    logging.log(level, f"Function {func_name} {context}: {description}")  # noqa: LOG015, G004


def log_dataframe_input(level: int, func_name: str, df: Any, include_dtypes: bool) -> None:
    _log_dataframe(level, func_name, df, include_dtypes, "parameters contained a DataFrame")


def log_dataframe_output(level: int, func_name: str, df: Any, include_dtypes: bool) -> None:
    _log_dataframe(level, func_name, df, include_dtypes, "returned a DataFrame")
