"""Tests for pattern matching utilities."""

import pytest

from daffy.patterns import compile_regex_pattern, match_column_with_regex


def test_invalid_regex_pattern_raises_error() -> None:
    with pytest.raises(ValueError, match="Invalid regex pattern"):
        compile_regex_pattern("r/[invalid/")


def test_empty_regex_pattern_raises_error() -> None:
    with pytest.raises(ValueError, match="cannot be empty"):
        compile_regex_pattern("r//")


class TestColumnPatternsAreAppliedAsWritten:
    """Column patterns match anywhere in the name unless the caller anchors them."""

    def test_matches_without_leading_anchor(self) -> None:
        pattern = compile_regex_pattern(r"r/Price_\d+/")
        columns = ["Price_1", "Total_Price_2", "Brand"]
        assert match_column_with_regex(pattern, columns) == ["Price_1", "Total_Price_2"]

    def test_caller_start_anchor_is_honoured(self) -> None:
        pattern = compile_regex_pattern(r"r/^Price_\d+/")
        columns = ["Price_1", "Total_Price_2", "Brand"]
        assert match_column_with_regex(pattern, columns) == ["Price_1"]

    def test_caller_full_match_anchors_are_honoured(self) -> None:
        pattern = compile_regex_pattern(r"r/^Price_\d+$/")
        columns = ["Price_1", "Price_1_eur", "Brand"]
        assert match_column_with_regex(pattern, columns) == ["Price_1"]

    def test_matches_nothing_when_no_column_contains_the_pattern(self) -> None:
        pattern = compile_regex_pattern(r"r/Price_\d+/")
        assert match_column_with_regex(pattern, ["Brand", "Model"]) == []
