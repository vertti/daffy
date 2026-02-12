"""Documentation contract tests for public API examples."""

from __future__ import annotations

from inspect import signature
from pathlib import Path
from typing import get_args

from daffy.checks import CheckName
from daffy.decorators import df_in, df_log, df_out

ROOT_DIR = Path(__file__).resolve().parents[1]
API_DOC = (ROOT_DIR / "docs" / "api.md").read_text(encoding="utf-8")
README_DOC = (ROOT_DIR / "README.md").read_text(encoding="utf-8")


def _section(text: str, start_heading: str, end_heading: str | None = None) -> str:
    start_index = text.index(start_heading)
    if end_heading is None:
        return text[start_index:]
    end_index = text.index(end_heading, start_index)
    return text[start_index:end_index]


def test_api_reference_df_in_parameters_match_signature() -> None:
    section = _section(API_DOC, "## @df_in", "## @df_out")
    for parameter_name in signature(df_in).parameters:
        assert f"`{parameter_name}`" in section


def test_api_reference_df_out_parameters_match_signature() -> None:
    section = _section(API_DOC, "## @df_out", "## @df_log")
    for parameter_name in signature(df_out).parameters:
        assert f"`{parameter_name}`" in section


def test_api_reference_df_log_parameters_match_signature() -> None:
    section = _section(API_DOC, "## @df_log", "## Column Specifications")
    for parameter_name in signature(df_log).parameters:
        assert f"`{parameter_name}`" in section


def test_api_reference_lists_all_builtin_checks() -> None:
    section = _section(API_DOC, "## Value Checks", "## Configuration")
    for check_name in get_args(CheckName):
        assert f"`{check_name}`" in section


def test_readme_examples_do_not_use_removed_top_level_nullable_or_unique_args() -> None:
    assert "nullable={" not in README_DOC
    assert "unique=[" not in README_DOC
