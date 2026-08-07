"""Tests for value checks."""

from typing import Any, ClassVar

import narwhals as nw
import pandas as pd
import polars as pl
import pyarrow as pa
import pytest

from daffy.checks import BUILTIN_CHECK_NAMES, apply_check, validate_checks


def numeric_with_null(backend: str) -> Any:
    """Build [1, null, 3] on the requested backend."""
    return {
        "pandas-float": lambda: pd.Series([1.0, None, 3.0]),
        "pandas-nullable-int": lambda: pd.Series([1, None, 3], dtype="Int64"),
        "polars": lambda: pl.Series([1, None, 3]),
        "pyarrow": lambda: pa.chunked_array([[1, None, 3]]),
    }[backend]()


def strings_with_null(backend: str) -> Any:
    """Build ["ab1x", null, "ab2x"] on the requested backend."""
    return {
        "pandas-object": lambda: pd.Series(["ab1x", None, "ab2x"]),
        "pandas-string": lambda: pd.Series(["ab1x", None, "ab2x"], dtype="string"),
        "polars": lambda: pl.Series(["ab1x", None, "ab2x"]),
        "pyarrow": lambda: pa.chunked_array([["ab1x", None, "ab2x"]]),
    }[backend]()


NUMERIC_BACKENDS = ["pandas-float", "pandas-nullable-int", "polars", "pyarrow"]
STRING_BACKENDS = ["pandas-object", "pandas-string", "polars", "pyarrow"]

# Backends whose nulls are three-valued: a comparison against null yields "unknown",
# which is not a violation. Pandas float NaN is the exception - it compares as False,
# so NaN fails comparisons natively.
THREE_VALUED_NUMERIC = ["pandas-nullable-int", "polars", "pyarrow"]


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

    def test_pandas_float_nan_fails_comparison(self) -> None:
        """NaN compares as False in Pandas float columns, so it fails natively."""
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

    def test_str_regex_matches_anywhere_in_the_value(self) -> None:
        series = pd.Series(["abc123", "abc"])
        fail_count, samples = apply_check(series, "str_regex", r"\d+")
        assert fail_count == 1
        assert samples == ["abc"]

    def test_str_regex_honours_caller_start_anchor(self) -> None:
        series = pd.Series(["123abc", "abc123"])
        fail_count, samples = apply_check(series, "str_regex", r"^\d+")
        assert fail_count == 1
        assert samples == ["abc123"]

    def test_str_regex_honours_caller_full_match_anchors(self) -> None:
        series = pd.Series(["123", "123abc"])
        fail_count, samples = apply_check(series, "str_regex", r"^\d+$")
        assert fail_count == 1
        assert samples == ["123abc"]

    def test_str_regex_alternation_is_not_rewritten(self) -> None:
        series = pd.Series(["xb", "c"])
        fail_count, samples = apply_check(series, "str_regex", "a|b")
        assert fail_count == 1
        assert samples == ["c"]


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


class TestNullSemanticsFollowTheBackend:
    """Checks constrain values; a null is not a value.

    Daffy does not rewrite null comparison results. On backends with three-valued logic
    (Polars, PyArrow, Pandas nullable dtypes) comparing against a null yields "unknown",
    which is not a violation. Pandas float NaN is the exception: it compares as False
    natively, so NaN does fail a comparison there. Use `nullable=False` or the `notnull`
    check to constrain nulls explicitly.
    """

    @pytest.mark.parametrize("backend", THREE_VALUED_NUMERIC)
    @pytest.mark.parametrize(
        ("check_name", "check_value"),
        [("gt", 0), ("ge", 1), ("lt", 9), ("le", 9), ("between", (0, 9))],
    )
    def test_comparison_ignores_null_on_three_valued_backends(
        self, backend: str, check_name: str, check_value: Any
    ) -> None:
        fail_count, _samples = apply_check(numeric_with_null(backend), check_name, check_value)
        assert fail_count == 0

    @pytest.mark.parametrize(("check_name", "check_value"), [("gt", 0), ("between", (0, 9))])
    def test_comparison_fails_nan_on_pandas_float(self, check_name: str, check_value: Any) -> None:
        fail_count, _samples = apply_check(numeric_with_null("pandas-float"), check_name, check_value)
        assert fail_count == 1

    @pytest.mark.parametrize("backend", NUMERIC_BACKENDS)
    def test_ne_ignores_null_everywhere(self, backend: str) -> None:
        fail_count, _samples = apply_check(numeric_with_null(backend), "ne", 9)
        assert fail_count == 0

    @pytest.mark.parametrize("backend", NUMERIC_BACKENDS)
    def test_notin_ignores_null_everywhere(self, backend: str) -> None:
        fail_count, _samples = apply_check(numeric_with_null(backend), "notin", [9])
        assert fail_count == 0

    @pytest.mark.parametrize("backend", NUMERIC_BACKENDS)
    def test_notnull_reports_null_everywhere(self, backend: str) -> None:
        fail_count, _samples = apply_check(numeric_with_null(backend), "notnull", True)
        assert fail_count == 1

    @pytest.mark.parametrize("backend", THREE_VALUED_NUMERIC)
    def test_custom_check_ignores_null_on_three_valued_backends(self, backend: str) -> None:
        fail_count, _samples = apply_check(numeric_with_null(backend), "positive", lambda s: s > 0)
        assert fail_count == 0

    @pytest.mark.parametrize("backend", STRING_BACKENDS)
    @pytest.mark.parametrize(
        ("check_name", "check_value"),
        [
            ("str_regex", r"ab\dx"),
            ("str_startswith", "ab"),
            ("str_endswith", "x"),
            ("str_contains", "b"),
        ],
    )
    def test_string_check_ignores_null(self, backend: str, check_name: str, check_value: Any) -> None:
        fail_count, _samples = apply_check(strings_with_null(backend), check_name, check_value)
        assert fail_count == 0

    @pytest.mark.parametrize("backend", STRING_BACKENDS)
    def test_string_check_does_not_crash_on_pandas_object_nulls(self, backend: str) -> None:
        """Regression: `~` on a pandas object-dtype mask holding None raised TypeError."""
        fail_count, _samples = apply_check(strings_with_null(backend), "str_regex", r"nomatch")
        assert fail_count == 2


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


class TestBuiltinCheckNamesStayInSync:
    """The names offered to callers must be exactly the names apply_check implements.

    Decoration-time validation rejects unknown names using BUILTIN_CHECK_NAMES, so a
    name that drifts out of apply_check would be accepted and then fail on first call -
    or worse, a working check would be rejected before it ever ran.
    """

    SAMPLE_VALUES: ClassVar[dict[str, Any]] = {
        "gt": 0,
        "ge": 0,
        "lt": 100,
        "le": 100,
        "between": (0, 100),
        "eq": 1,
        "ne": 9,
        "isin": [1, 2, 3],
        "notin": [9],
        "notnull": True,
        "str_regex": r"\d+",
        "str_startswith": "1",
        "str_endswith": "1",
        "str_contains": "1",
        "str_length": (1, 5),
    }

    def test_sample_values_cover_every_advertised_check(self) -> None:
        assert set(self.SAMPLE_VALUES) == BUILTIN_CHECK_NAMES

    @pytest.mark.parametrize("check_name", sorted(BUILTIN_CHECK_NAMES))
    def test_every_advertised_check_is_implemented(self, check_name: str) -> None:
        series = pd.Series(["1", "2", "3"]) if check_name.startswith("str_") else pd.Series([1, 2, 3])

        apply_check(series, check_name, self.SAMPLE_VALUES[check_name])

    def test_a_name_outside_the_set_is_rejected(self) -> None:
        assert "gtt" not in BUILTIN_CHECK_NAMES
        with pytest.raises(ValueError, match="Unknown check"):
            apply_check(pd.Series([1]), "gtt", 0)


class TestChecksRejectMismatchedDtypes:
    """A check that cannot mean what the caller intended is an error, not a guess.

    Backends disagreed here: Pandas and PyArrow raised their own errors while Polars
    coerced the bound to a string and compared lexicographically, reporting '10' as
    failing `gt: 5` in a message indistinguishable from a real violation.
    """

    @pytest.mark.parametrize("backend", STRING_BACKENDS)
    @pytest.mark.parametrize("check_name", ["gt", "ge", "lt", "le", "between"])
    def test_ordering_check_on_string_column_is_rejected(self, backend: str, check_name: str) -> None:
        series = strings_with_null(backend)
        value = (0, 9) if check_name == "between" else 5
        with pytest.raises(ValueError, match="compares order"):
            apply_check(series, check_name, value)

    @pytest.mark.parametrize("backend", NUMERIC_BACKENDS)
    @pytest.mark.parametrize(
        ("check_name", "check_value"),
        [("str_regex", r"\d+"), ("str_startswith", "1"), ("str_contains", "1"), ("str_length", (1, 5))],
    )
    def test_string_check_on_numeric_column_is_rejected(self, backend: str, check_name: str, check_value: Any) -> None:
        with pytest.raises(ValueError, match="needs a string column"):
            apply_check(numeric_with_null(backend), check_name, check_value)

    def test_all_null_column_is_not_second_guessed(self) -> None:
        """Pandas reports an all-null object column as String; that must not trip the guard."""
        fail_count, _samples = apply_check(pd.Series([None, None, None]), "gt", 0)
        assert fail_count == 3

    def test_numeric_dtype_is_trusted_even_when_empty(self) -> None:
        """An empty Float64 column still has a reliable dtype, unlike an all-null object column."""
        with pytest.raises(ValueError, match="needs a string column"):
            apply_check(pd.Series([], dtype=float), "str_regex", r"\d+")

    def test_empty_string_column_accepts_string_checks(self) -> None:
        fail_count, _samples = apply_check(pd.Series([], dtype="string"), "str_regex", r"\d+")
        assert fail_count == 0

    def test_backend_failure_is_wrapped_with_context(self) -> None:
        with pytest.raises(ValueError, match="Check 'between' could not run"):
            apply_check(pd.Series([1, 2, 3]), "between", 5)
