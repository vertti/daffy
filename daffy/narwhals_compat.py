"""Narwhals utilities for DataFrame type checking."""

from __future__ import annotations

from typing import Any

import narwhals as nw


def to_nw_dataframe(obj: Any) -> Any | None:
    """Convert to a Narwhals DataFrame, or return None if the object is not one."""
    try:
        return nw.from_native(obj, eager_only=True)
    except TypeError:
        return None


def is_supported_dataframe(obj: Any) -> bool:
    """Check if object is a supported eager DataFrame type."""
    return to_nw_dataframe(obj) is not None
