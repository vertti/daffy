"""Narwhals utilities for DataFrame type checking."""

from __future__ import annotations

from typing import Any

import narwhals as nw
from narwhals.exceptions import NarwhalsError


class UnsupportedDataFrameError(Exception):
    """A supported DataFrame type that Narwhals cannot work with, e.g. duplicate column names."""


def to_nw_dataframe(obj: Any) -> Any | None:
    """Convert to a Narwhals DataFrame, or return None if the object is not one.

    Raises:
        UnsupportedDataFrameError: If the object is a DataFrame that Narwhals rejects.
            Duplicate column names are the common case, and they arrive as
            `DuplicateError`, which is a ValueError - not the TypeError raised for
            "this is not a DataFrame at all".

    """
    try:
        return nw.from_native(obj, eager_only=True)
    except TypeError:
        return None
    except NarwhalsError as e:
        raise UnsupportedDataFrameError(str(e)) from e


def is_supported_dataframe(obj: Any) -> bool:
    """Check if object is a supported eager DataFrame type.

    A DataFrame Narwhals cannot work with is still a DataFrame, so this answers True
    for it; converting is what surfaces the problem.
    """
    try:
        return to_nw_dataframe(obj) is not None
    except UnsupportedDataFrameError:
        return True
