"""Pattern matching utilities for DAFFY DataFrame Column Validator."""

from __future__ import annotations

import re
from functools import lru_cache

# Regex column pattern format delimiters
_REGEX_PREFIX = "r/"
_REGEX_SUFFIX = "/"

RegexColumnDef = tuple[str, re.Pattern[str]]


def is_regex_string(column: str) -> bool:
    return column.startswith(_REGEX_PREFIX) and column.endswith(_REGEX_SUFFIX)


@lru_cache(maxsize=128)
def compile_regex_pattern(pattern_string: str) -> RegexColumnDef:
    r"""Compile a regex pattern from r/pattern/ format.

    Args:
        pattern_string: Pattern in format "r/pattern/" (e.g., "r/col_\\d+/")

    Returns:
        Tuple of (original pattern string, compiled regex pattern)

    Raises:
        ValueError: If the regex pattern is invalid or empty

    """
    if not is_regex_string(pattern_string):
        raise ValueError(f"Regex pattern must be in 'r/.../' format (got {pattern_string!r})")
    pattern_str = pattern_string[len(_REGEX_PREFIX) : -len(_REGEX_SUFFIX)]
    if not pattern_str:
        raise ValueError("Regex pattern cannot be empty (got 'r//')")
    try:
        compiled_pattern = re.compile(pattern_str)
    except re.error as e:
        raise ValueError(f"Invalid regex pattern '{pattern_str}': {e}") from e
    return (pattern_string, compiled_pattern)


def match_column_with_regex(column_pattern: RegexColumnDef, df_columns: list[str]) -> list[str]:
    """Find DataFrame columns matching a regex pattern.

    The pattern is applied as written - it matches anywhere in the column name unless
    anchored by the caller, the same way `str_regex` treats value patterns.
    """
    _, pattern = column_pattern
    return [col for col in df_columns if pattern.search(col)]
