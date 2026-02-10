"""DataFrame type handling for DAFFY - supports Pandas, Polars, Modin, and PyArrow."""

from __future__ import annotations

from importlib.util import find_spec

from narwhals.typing import IntoDataFrame, IntoDataFrameT

# Re-export narwhals types for use throughout daffy
__all__ = [
    "HAS_MODIN",
    "HAS_PANDAS",
    "HAS_POLARS",
    "HAS_PYARROW",
    "IntoDataFrame",
    "IntoDataFrameT",
    "get_available_library_names",
]


def _module_available(module_name: str) -> bool:
    """Check if an optional dependency can be imported without importing it eagerly."""
    return find_spec(module_name) is not None


# Check which DataFrame libraries are available (for error messages and early failure)
HAS_PANDAS = _module_available("pandas")
HAS_POLARS = _module_available("polars")
HAS_MODIN = _module_available("modin")
HAS_PYARROW = _module_available("pyarrow")

# Fail early if no supported DataFrame library is available
if not (HAS_PANDAS or HAS_POLARS or HAS_MODIN or HAS_PYARROW):  # pragma: no cover
    raise ImportError(
        "No supported DataFrame library found. Install at least one supported library: "
        "pip install pandas or pip install polars or pip install modin or pip install pyarrow"
    )


def get_available_library_names() -> list[str]:
    """Get list of available DataFrame library names for error messages.

    Returns:
        list[str]: List of available library names (e.g., ["Pandas", "Polars", "PyArrow"])

    """
    available_libs = []
    if HAS_PANDAS:
        available_libs.append("Pandas")
    if HAS_POLARS:
        available_libs.append("Polars")
    if HAS_MODIN:
        available_libs.append("Modin")
    if HAS_PYARROW:
        available_libs.append("PyArrow")
    return available_libs
