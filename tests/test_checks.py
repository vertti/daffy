"""Tests for value checks."""

import narwhals as nw
import pandas as pd
import pytest

from daffy.checks import apply_check, validate_checks


class TestComparisonChecks:
    def test_gt_passes(self) -> None:
        series = pd.Series([1, 2, 3])
        fail_count, samples = apply_check(series, "gt", 0)
        assert fail_count == 0
        assert samples == []

    def test_gt_fails(self) -> None:
        series = pd.Series([0, 1, 2, 3])
        fail_count, samples = apply_check(series, "gt", 0)
        assert fail_count == 1
        assert samples == [0]

    def test_ge_passes(self) -> None:
        series = pd.Series([0, 1, 2])
        fail_count, _samples = apply_check(series, "ge", 0)
        assert fail_count == 0

    def test_ge_fails(self) -> None:
        series = pd.Series([-1, 0, 1])
        fail_count, samples = apply_check(series, "ge", 0)
        assert fail_count == 1
        assert samples == [-1]

    def test_lt_passes(self) -> None:
        series = pd.Series([1, 2, 3])
        fail_count, _samples = apply_check(series, "lt", 10)
        assert fail_count == 0

    def test_lt_fails(self) -> None:
        series = pd.Series([5, 10, 15])
        fail_count, samples = apply_check(series, "lt", 10)
        assert fail_count == 2
        assert 10 in samples
        assert 15 in samples

    def test_le_passes(self) -> None:
        series = pd.Series([1, 5, 10])
        fail_count, _samples = apply_check(series, "le", 10)
        assert fail_count == 0

    def test_le_fails(self) -> None:
        series = pd.Series([5, 10, 15])
        fail_count, samples = apply_check(series, "le", 10)
        assert fail_count == 1
        assert samples == [15]

    def test_null_values_treated_as_failures(self) -> None:
        series = pd.Series([1, None, 3])
        fail_count, _samples = apply_check(series, "gt", 0)
        assert fail_count == 1

    def test_unknown_check_raises(self) -> None:
        series = pd.Series([1, 2, 3])
        with pytest.raises(ValueError, match="Unknown check"):
            apply_check(series, "unknown", 0)


class TestBetweenCheck:
    def test_between_passes(self) -> None:
        series = pd.Series([0, 50, 100])
        fail_count, _samples = apply_check(series, "between", (0, 100))
        assert fail_count == 0

    def test_between_fails_below(self) -> None:
        series = pd.Series([-1, 50, 100])
        fail_count, samples = apply_check(series, "between", (0, 100))
        assert fail_count == 1
        assert samples == [-1]

    def test_between_fails_above(self) -> None:
        series = pd.Series([0, 50, 101])
        fail_count, samples = apply_check(series, "between", (0, 100))
        assert fail_count == 1
        assert samples == [101]

    def test_between_inclusive(self) -> None:
        series = pd.Series([0, 100])
        fail_count, _samples = apply_check(series, "between", (0, 100))
        assert fail_count == 0


class TestEqualityChecks:
    def test_eq_passes(self) -> None:
        series = pd.Series(["active", "active", "active"])
        fail_count, _samples = apply_check(series, "eq", "active")
        assert fail_count == 0

    def test_eq_fails(self) -> None:
        series = pd.Series(["active", "inactive", "active"])
        fail_count, samples = apply_check(series, "eq", "active")
        assert fail_count == 1
        assert samples == ["inactive"]

    def test_ne_passes(self) -> None:
        series = pd.Series(["active", "pending", "closed"])
        fail_count, _samples = apply_check(series, "ne", "deleted")
        assert fail_count == 0

    def test_ne_fails(self) -> None:
        series = pd.Series(["active", "deleted", "closed"])
        fail_count, samples = apply_check(series, "ne", "deleted")
        assert fail_count == 1
        assert samples == ["deleted"]


class TestIsinCheck:
    def test_isin_passes(self) -> None:
        series = pd.Series(["active", "pending", "closed"])
        fail_count, _samples = apply_check(series, "isin", ["active", "pending", "closed"])
        assert fail_count == 0

    def test_isin_fails(self) -> None:
        series = pd.Series(["active", "deleted", "unknown"])
        fail_count, samples = apply_check(series, "isin", ["active", "pending", "closed"])
        assert fail_count == 2
        assert "deleted" in samples
        assert "unknown" in samples

    def test_isin_with_numbers(self) -> None:
        series = pd.Series([1, 2, 3, 99])
        fail_count, samples = apply_check(series, "isin", [1, 2, 3])
        assert fail_count == 1
        assert samples == [99]


class TestNotinCheck:
    def test_notin_passes(self) -> None:
        series = pd.Series(["a", "b", "c"])
        fail_count, _samples = apply_check(series, "notin", ["x", "y", "z"])
        assert fail_count == 0

    def test_notin_fails(self) -> None:
        series = pd.Series(["a", "b", "x"])
        fail_count, samples = apply_check(series, "notin", ["x", "y", "z"])
        assert fail_count == 1
        assert samples == ["x"]

    def test_notin_with_numbers(self) -> None:
        series = pd.Series([1, 2, 3])
        fail_count, samples = apply_check(series, "notin", [3, 4, 5])
        assert fail_count == 1
        assert samples == [3]

    def test_notin_all_forbidden(self) -> None:
        series = pd.Series(["x", "y", "z"])
        fail_count, _samples = apply_check(series, "notin", ["x", "y", "z"])
        assert fail_count == 3


class TestNotnullCheck:
    def test_notnull_passes(self) -> None:
        series = pd.Series([1, 2, 3])
        fail_count, _samples = apply_check(series, "notnull", True)
        assert fail_count == 0

    def test_notnull_fails(self) -> None:
        series = pd.Series([1, None, 3, None])
        fail_count, _samples = apply_check(series, "notnull", True)
        assert fail_count == 2


class TestStrRegexCheck:
    def test_str_regex_passes(self) -> None:
        series = pd.Series(["abc123", "def456", "ghi789"])
        fail_count, _samples = apply_check(series, "str_regex", r"^[a-z]+\d+$")
        assert fail_count == 0

    def test_str_regex_fails(self) -> None:
        series = pd.Series(["abc123", "ABC456", "123def"])
        fail_count, samples = apply_check(series, "str_regex", r"^[a-z]+\d+$")
        assert fail_count == 2
        assert "ABC456" in samples
        assert "123def" in samples

    def test_str_regex_email_pattern(self) -> None:
        series = pd.Series(["test@example.com", "invalid", "user@domain.org"])
        fail_count, samples = apply_check(series, "str_regex", r"^[^@]+@[^@]+\.[^@]+$")
        assert fail_count == 1
        assert samples == ["invalid"]


class TestStrStartswithCheck:
    def test_str_startswith_passes(self) -> None:
        series = pd.Series(["hello", "hi", "hey"])
        fail_count, _samples = apply_check(series, "str_startswith", "h")
        assert fail_count == 0

    def test_str_startswith_fails(self) -> None:
        series = pd.Series(["hello", "world"])
        fail_count, samples = apply_check(series, "str_startswith", "h")
        assert fail_count == 1
        assert samples == ["world"]

    def test_str_startswith_prefix(self) -> None:
        series = pd.Series(["pre_name", "pre_value", "other"])
        fail_count, samples = apply_check(series, "str_startswith", "pre_")
        assert fail_count == 1
        assert samples == ["other"]


class TestStrEndswithCheck:
    def test_str_endswith_passes(self) -> None:
        series = pd.Series(["test.py", "main.py"])
        fail_count, _samples = apply_check(series, "str_endswith", ".py")
        assert fail_count == 0

    def test_str_endswith_fails(self) -> None:
        series = pd.Series(["test.py", "readme.md"])
        fail_count, samples = apply_check(series, "str_endswith", ".py")
        assert fail_count == 1
        assert samples == ["readme.md"]


class TestStrContainsCheck:
    def test_str_contains_passes(self) -> None:
        series = pd.Series(["hello world", "world peace"])
        fail_count, _samples = apply_check(series, "str_contains", "world")
        assert fail_count == 0

    def test_str_contains_fails(self) -> None:
        series = pd.Series(["hello", "goodbye"])
        fail_count, _samples = apply_check(series, "str_contains", "world")
        assert fail_count == 2

    def test_str_contains_literal_not_regex(self) -> None:
        # Ensure . is treated as literal, not regex wildcard
        series = pd.Series(["a.b", "axb"])
        fail_count, samples = apply_check(series, "str_contains", ".")
        assert fail_count == 1
        assert samples == ["axb"]

    def test_str_contains_at_symbol(self) -> None:
        series = pd.Series(["user@example.com", "no-at-here"])
        fail_count, samples = apply_check(series, "str_contains", "@")
        assert fail_count == 1
        assert samples == ["no-at-here"]


class TestStrLengthCheck:
    def test_str_length_passes(self) -> None:
        series = pd.Series(["ab", "abc", "abcd"])
        fail_count, _samples = apply_check(series, "str_length", (2, 4))
        assert fail_count == 0

    def test_str_length_fails_too_short(self) -> None:
        series = pd.Series(["a", "abc"])
        fail_count, samples = apply_check(series, "str_length", (2, 4))
        assert fail_count == 1
        assert samples == ["a"]

    def test_str_length_fails_too_long(self) -> None:
        series = pd.Series(["abc", "abcdef"])
        fail_count, samples = apply_check(series, "str_length", (2, 4))
        assert fail_count == 1
        assert samples == ["abcdef"]

    def test_str_length_inclusive(self) -> None:
        series = pd.Series(["ab", "abcd"])
        fail_count, _samples = apply_check(series, "str_length", (2, 4))
        assert fail_count == 0

    def test_str_length_exact(self) -> None:
        # Can use same min/max for exact length
        series = pd.Series(["abc", "ab", "abcd"])
        fail_count, _samples = apply_check(series, "str_length", (3, 3))
        assert fail_count == 2


class TestMaxSamples:
    def test_max_samples_limits_returned_values(self) -> None:
        series = pd.Series([0, -1, -2, -3, -4, -5, -6, -7, -8, -9])
        fail_count, samples = apply_check(series, "gt", 0, max_samples=3)
        assert fail_count == 10
        assert len(samples) == 3

    def test_max_samples_default_is_five(self) -> None:
        series = pd.Series([0, -1, -2, -3, -4, -5, -6, -7, -8, -9])
        fail_count, samples = apply_check(series, "gt", 0)
        assert fail_count == 10
        assert len(samples) == 5

    def test_max_samples_one(self) -> None:
        series = pd.Series([-1, -2, -3])
        fail_count, samples = apply_check(series, "gt", 0, max_samples=1)
        assert fail_count == 3
        assert len(samples) == 1


class TestEdgeCases:
    def test_empty_series_passes(self) -> None:
        series = pd.Series([], dtype=float)
        fail_count, samples = apply_check(series, "gt", 0)
        assert fail_count == 0
        assert samples == []

    def test_single_value_passes(self) -> None:
        series = pd.Series([5])
        fail_count, samples = apply_check(series, "gt", 0)
        assert fail_count == 0
        assert samples == []

    def test_single_value_fails(self) -> None:
        series = pd.Series([-1])
        fail_count, samples = apply_check(series, "gt", 0)
        assert fail_count == 1
        assert samples == [-1]

    def test_all_null_series_fails_notnull(self) -> None:
        series = pd.Series([None, None, None])
        fail_count, _samples = apply_check(series, "notnull", True)
        assert fail_count == 3

    def test_all_null_series_comparison_check(self) -> None:
        series = pd.Series([None, None, None])
        fail_count, _samples = apply_check(series, "gt", 0)
        assert fail_count == 3


class TestValidateChecks:
    def test_single_check_passes(self) -> None:
        df = pd.DataFrame({"price": [1, 2, 3]})

        nws = nw.from_native(df, eager_only=True)["price"]
        violations = validate_checks(nws, "price", {"gt": 0})
        assert violations == []

    def test_single_check_fails(self) -> None:
        df = pd.DataFrame({"price": [0, 1, 2]})

        nws = nw.from_native(df, eager_only=True)["price"]
        violations = validate_checks(nws, "price", {"gt": 0})
        assert len(violations) == 1
        col, check, count, samples = violations[0]
        assert col == "price"
        assert check == "gt"
        assert count == 1
        assert samples == [0]

    def test_multiple_checks_all_pass(self) -> None:
        df = pd.DataFrame({"score": [50, 60, 70]})

        nws = nw.from_native(df, eager_only=True)["score"]
        violations = validate_checks(nws, "score", {"gt": 0, "lt": 100})
        assert violations == []

    def test_multiple_checks_one_fails(self) -> None:
        df = pd.DataFrame({"score": [50, 60, 150]})

        nws = nw.from_native(df, eager_only=True)["score"]
        violations = validate_checks(nws, "score", {"gt": 0, "lt": 100})
        assert len(violations) == 1
        assert violations[0][1] == "lt"
