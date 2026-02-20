"""Column specification parsing."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Sequence


@dataclass
class ParsedColumnSpec:
    """Parsed column specification ready for validators."""

    required_columns: list[str] = field(default_factory=list)
    optional_columns: list[str] = field(default_factory=list)
    dtype_constraints: dict[str, Any] = field(default_factory=dict)
    non_nullable_columns: list[str] = field(default_factory=list)
    unique_columns: list[str] = field(default_factory=list)
    checks_by_column: dict[str, dict[str, Any]] = field(default_factory=dict)

    @property
    def all_columns(self) -> list[str]:
        """All columns (required + optional) for strict mode."""
        return self.required_columns + self.optional_columns


def _get_col_name(col_spec: Any) -> str | None:
    """Get column name from specification, or None if invalid.

    Handles:
    - Plain strings: "column_name" -> "column_name"
    - Regex tuples: ("column_name", compiled_pattern) -> "column_name" (only if first element is str)
    - Invalid types (int, etc): None (skip silently for backwards compatibility)
    """
    if isinstance(col_spec, str):
        return col_spec
    if isinstance(col_spec, tuple) and len(col_spec) >= 1 and isinstance(col_spec[0], str):
        return col_spec[0]
    return None


def _parse_dict_constraints(col_name: str, constraints: dict[str, Any], result: ParsedColumnSpec) -> None:
    """Parse a dict constraint specification for a column."""
    is_required = constraints.get("required", True)
    if is_required:
        result.required_columns.append(col_name)
    else:
        result.optional_columns.append(col_name)

    if "dtype" in constraints:
        result.dtype_constraints[col_name] = constraints["dtype"]
    if constraints.get("nullable") is False:
        result.non_nullable_columns.append(col_name)
    if constraints.get("unique") is True:
        result.unique_columns.append(col_name)
    if "checks" in constraints:
        result.checks_by_column[col_name] = constraints["checks"]


def _parse_list_spec(columns: Sequence[Any], result: ParsedColumnSpec, strict_specs: bool) -> None:
    """Parse a list column specification."""
    for index, c in enumerate(columns):
        col_name = _get_col_name(c)
        if col_name is None:
            if strict_specs:
                raise TypeError(
                    "Invalid column spec at index "
                    f"{index}: expected str or regex column pattern, got {type(c).__name__}"
                )
            continue
        result.required_columns.append(col_name)


def _parse_dict_spec(columns: dict[Any, Any], result: ParsedColumnSpec, strict_specs: bool) -> None:
    """Parse a dict column specification."""
    for index, (col_spec, value) in enumerate(columns.items()):
        col_name = _get_col_name(col_spec)
        if col_name is None:
            if strict_specs:
                raise TypeError(
                    "Invalid column key at index "
                    f"{index}: expected str or regex column pattern, got {type(col_spec).__name__}"
                )
            continue  # Skip invalid column types

        if isinstance(value, dict):
            _parse_dict_constraints(col_name, value, result)
        else:
            result.required_columns.append(col_name)
            result.dtype_constraints[col_name] = value


def parse_column_spec(columns: Sequence[Any] | dict[Any, Any] | None, strict_specs: bool = False) -> ParsedColumnSpec:
    """Parse user-provided column specification into validator-ready format.

    Handles:
    - List: ["col1", "col2"] → required columns
    - String: "col1" → single required column (not split into characters)
    - Dict with dtype: {"col1": "int64"} → required + dtype check
    - Dict with constraints: {"col1": {"dtype": ..., "nullable": False, "required": False, ...}}

    Invalid column types (like integers) are silently ignored for backwards compatibility
    unless strict_specs=True, in which case a TypeError is raised with the offending
    index and type name.
    """
    result = ParsedColumnSpec()

    if columns is None:
        return result

    if isinstance(columns, dict):
        _parse_dict_spec(columns, result, strict_specs)
    elif isinstance(columns, str):
        # Treat a single string as a single column name, not a character sequence
        _parse_list_spec([columns], result, strict_specs)
    else:
        _parse_list_spec(columns, result, strict_specs)

    return result
