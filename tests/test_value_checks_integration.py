"""Integration tests for value checks with df_in/df_out decorators."""

from typing import Any

import pandas as pd
import pytest

from daffy import df_in, df_out
from tests.utils import DataFrameFactory, to_list


class TestDfInWithChecks:
    def test_gt_check_passes(self) -> None:
        @df_in(columns={"price": {"checks": {"gt": 0}}})
        def process(df: pd.DataFrame) -> pd.DataFrame:
            return df

        df = pd.DataFrame({"price": [1, 2, 3]})
        result = process(df)
        assert to_list(result["price"]) == [1, 2, 3]

    def test_gt_check_fails(self) -> None:
        @df_in(columns={"price": {"checks": {"gt": 0}}})
        def process(df: pd.DataFrame) -> pd.DataFrame:
            return df

        df = pd.DataFrame({"price": [0, 1, 2]})
        with pytest.raises(AssertionError, match="gt"):
            process(df)

    def test_multiple_checks_pass(self) -> None:
        @df_in(columns={"score": {"checks": {"gt": 0, "lt": 100}}})
        def process(df: pd.DataFrame) -> pd.DataFrame:
            return df

        df = pd.DataFrame({"score": [50, 60, 70]})
        result = process(df)
        assert to_list(result["score"]) == [50, 60, 70]

    def test_multiple_checks_fail(self) -> None:
        @df_in(columns={"score": {"checks": {"gt": 0, "lt": 100}}})
        def process(df: pd.DataFrame) -> pd.DataFrame:
            return df

        df = pd.DataFrame({"score": [50, 150, 70]})
        with pytest.raises(AssertionError, match="lt"):
            process(df)

    def test_isin_check_passes(self) -> None:
        @df_in(columns={"status": {"checks": {"isin": ["active", "pending", "closed"]}}})
        def process(df: pd.DataFrame) -> pd.DataFrame:
            return df

        df = pd.DataFrame({"status": ["active", "pending", "closed"]})
        result = process(df)
        assert to_list(result["status"]) == ["active", "pending", "closed"]

    def test_isin_check_fails(self) -> None:
        @df_in(columns={"status": {"checks": {"isin": ["active", "pending", "closed"]}}})
        def process(df: pd.DataFrame) -> pd.DataFrame:
            return df

        df = pd.DataFrame({"status": ["active", "deleted", "closed"]})
        with pytest.raises(AssertionError, match="isin"):
            process(df)

    def test_between_check(self) -> None:
        @df_in(columns={"age": {"checks": {"between": (0, 120)}}})
        def process(df: pd.DataFrame) -> pd.DataFrame:
            return df

        df = pd.DataFrame({"age": [25, 50, 75]})
        result = process(df)
        assert to_list(result["age"]) == [25, 50, 75]

    def test_checks_with_dtype(self) -> None:
        @df_in(columns={"price": {"dtype": "float64", "checks": {"gt": 0}}})
        def process(df: pd.DataFrame) -> pd.DataFrame:
            return df

        df = pd.DataFrame({"price": [1.0, 2.0, 3.0]})
        result = process(df)
        assert to_list(result["price"]) == [1.0, 2.0, 3.0]

    def test_checks_with_nullable(self) -> None:
        @df_in(columns={"price": {"nullable": False, "checks": {"gt": 0}}})
        def process(df: pd.DataFrame) -> pd.DataFrame:
            return df

        df = pd.DataFrame({"price": [1.0, 2.0, 3.0]})
        result = process(df)
        assert to_list(result["price"]) == [1.0, 2.0, 3.0]


class TestDfOutWithChecks:
    def test_check_passes(self) -> None:
        @df_out(columns={"result": {"checks": {"ge": 0}}})
        def process(df: pd.DataFrame) -> pd.DataFrame:
            return df

        df = pd.DataFrame({"result": [0, 1, 2]})
        result = process(df)
        assert to_list(result["result"]) == [0, 1, 2]

    def test_check_fails(self) -> None:
        @df_out(columns={"result": {"checks": {"ge": 0}}})
        def process(df: pd.DataFrame) -> pd.DataFrame:
            return df

        df = pd.DataFrame({"result": [-1, 0, 1]})
        with pytest.raises(AssertionError, match="ge"):
            process(df)


class TestChecksWithAllBackends:
    def test_gt_check_passes(self, make_df: DataFrameFactory) -> None:
        @df_in(columns={"price": {"checks": {"gt": 0}}})
        def process(df: Any) -> Any:
            return df

        df = make_df({"price": [1, 2, 3]})
        result = process(df)
        assert to_list(result["price"]) == [1, 2, 3]

    def test_gt_check_fails(self, make_df: DataFrameFactory) -> None:
        @df_in(columns={"price": {"checks": {"gt": 0}}})
        def process(df: Any) -> Any:
            return df

        df = make_df({"price": [0, 1, 2]})
        with pytest.raises(AssertionError, match="gt"):
            process(df)

    def test_between_check(self, make_df: DataFrameFactory) -> None:
        @df_in(columns={"score": {"checks": {"between": (0, 100)}}})
        def process(df: Any) -> Any:
            return df

        df = make_df({"score": [0, 50, 100]})
        result = process(df)
        assert to_list(result["score"]) == [0, 50, 100]

    def test_isin_check(self, make_df: DataFrameFactory) -> None:
        @df_in(columns={"status": {"checks": {"isin": ["a", "b", "c"]}}})
        def process(df: Any) -> Any:
            return df

        df = make_df({"status": ["a", "b", "c"]})
        result = process(df)
        assert to_list(result["status"]) == ["a", "b", "c"]

    def test_notnull_check_passes(self, make_df: DataFrameFactory) -> None:
        @df_in(columns={"value": {"checks": {"notnull": True}}})
        def process(df: Any) -> Any:
            return df

        df = make_df({"value": [1, 2, 3]})
        result = process(df)
        assert to_list(result["value"]) == [1, 2, 3]

    def test_notnull_check_fails(self, make_df: DataFrameFactory) -> None:
        @df_in(columns={"value": {"checks": {"notnull": True}}})
        def process(df: Any) -> Any:
            return df

        df = make_df({"value": [1, None, 3]})
        with pytest.raises(AssertionError, match="notnull"):
            process(df)

    def test_eq_check(self, make_df: DataFrameFactory) -> None:
        @df_in(columns={"flag": {"checks": {"eq": "yes"}}})
        def process(df: Any) -> Any:
            return df

        df = make_df({"flag": ["yes", "yes", "yes"]})
        result = process(df)
        assert to_list(result["flag"]) == ["yes", "yes", "yes"]

    def test_ne_check(self, make_df: DataFrameFactory) -> None:
        @df_in(columns={"flag": {"checks": {"ne": "deleted"}}})
        def process(df: Any) -> Any:
            return df

        df = make_df({"flag": ["active", "pending", "closed"]})
        result = process(df)
        assert to_list(result["flag"]) == ["active", "pending", "closed"]

    def test_str_regex_check(self, make_df: DataFrameFactory) -> None:
        @df_in(columns={"code": {"checks": {"str_regex": r"^[A-Z]{2}\d{3}$"}}})
        def process(df: Any) -> Any:
            return df

        df = make_df({"code": ["AB123", "CD456", "EF789"]})
        result = process(df)
        assert to_list(result["code"]) == ["AB123", "CD456", "EF789"]


class TestChecksWithRegexPatterns:
    def test_regex_pattern_check_passes(self, make_df: DataFrameFactory) -> None:
        @df_in(columns={"r/price_\\d+/": {"checks": {"gt": 0}}})
        def process(df: Any) -> Any:
            return df

        df = make_df({"price_1": [1, 2, 3], "price_2": [4, 5, 6]})
        result = process(df)
        assert to_list(result["price_1"]) == [1, 2, 3]

    def test_regex_pattern_check_fails(self, make_df: DataFrameFactory) -> None:
        @df_in(columns={"r/score_\\d+/": {"checks": {"gt": 0}}})
        def process(df: Any) -> Any:
            return df

        df = make_df({"score_1": [1, 2, 3], "score_2": [0, 5, 6]})
        with pytest.raises(AssertionError, match="gt"):
            process(df)

    def test_regex_pattern_multiple_columns_checked(self, make_df: DataFrameFactory) -> None:
        @df_in(columns={"r/val_\\d+/": {"checks": {"between": (0, 100)}}})
        def process(df: Any) -> Any:
            return df

        df = make_df({"val_1": [50, 60, 70], "val_2": [80, 90, 100]})
        result = process(df)
        assert to_list(result["val_1"]) == [50, 60, 70]


class TestChecksWithOptionalColumns:
    def test_checks_skipped_for_missing_optional_column(self, make_df: DataFrameFactory) -> None:
        @df_in(
            columns={
                "required_col": {"checks": {"gt": 0}},
                "optional_col": {"required": False, "checks": {"gt": 0}},
            }
        )
        def process(df: Any) -> Any:
            return df

        df = make_df({"required_col": [1, 2, 3]})
        result = process(df)
        assert to_list(result["required_col"]) == [1, 2, 3]

    def test_checks_run_for_present_optional_column(self, make_df: DataFrameFactory) -> None:
        @df_in(
            columns={
                "required_col": {"checks": {"gt": 0}},
                "optional_col": {"required": False, "checks": {"gt": 0}},
            }
        )
        def process(df: Any) -> Any:
            return df

        df = make_df({"required_col": [1, 2, 3], "optional_col": [0, 1, 2]})
        with pytest.raises(AssertionError, match="gt"):
            process(df)

    def test_optional_column_with_passing_checks(self, make_df: DataFrameFactory) -> None:
        @df_in(
            columns={
                "required_col": {},
                "optional_col": {"required": False, "checks": {"gt": 0}},
            }
        )
        def process(df: Any) -> Any:
            return df

        df = make_df({"required_col": [1, 2, 3], "optional_col": [1, 2, 3]})
        result = process(df)
        assert to_list(result["optional_col"]) == [1, 2, 3]


class TestErrorMessages:
    def test_error_includes_column_name(self) -> None:
        @df_in(columns={"price": {"checks": {"gt": 0}}})
        def process(df: pd.DataFrame) -> pd.DataFrame:
            return df

        df = pd.DataFrame({"price": [0]})
        with pytest.raises(AssertionError, match="price"):
            process(df)

    def test_error_includes_check_name(self) -> None:
        @df_in(columns={"value": {"checks": {"lt": 100}}})
        def process(df: pd.DataFrame) -> pd.DataFrame:
            return df

        df = pd.DataFrame({"value": [150]})
        with pytest.raises(AssertionError, match="lt"):
            process(df)

    def test_error_includes_sample_values(self) -> None:
        @df_in(columns={"x": {"checks": {"gt": 0}}})
        def process(df: pd.DataFrame) -> pd.DataFrame:
            return df

        df = pd.DataFrame({"x": [-5, 1, 2]})
        with pytest.raises(AssertionError, match="-5"):
            process(df)

    def test_multiple_column_check_violations(self) -> None:
        @df_in(
            columns={
                "a": {"checks": {"gt": 0}},
                "b": {"checks": {"gt": 0}},
            }
        )
        def process(df: pd.DataFrame) -> pd.DataFrame:
            return df

        df = pd.DataFrame({"a": [-1], "b": [-2]})
        with pytest.raises(AssertionError, match="Check violations"):
            process(df)


class TestCheckNamesValidatedAtDecoration:
    """A misspelled built-in check fails when the decorator is applied, not on first call."""

    @pytest.mark.parametrize("decorator", [df_in, df_out])
    def test_unknown_check_name_rejected(self, decorator: Any) -> None:
        with pytest.raises(ValueError, match="Unknown check 'gtt' for column 'price'"):
            decorator(columns={"price": {"checks": {"gtt": 0}}})

    def test_error_lists_the_valid_names(self) -> None:
        with pytest.raises(ValueError, match="str_startswith"):
            df_in(columns={"price": {"checks": {"startswith": "x"}}})

    def test_rejected_before_the_function_is_ever_called(self) -> None:
        with pytest.raises(ValueError, match="Unknown check"):

            @df_in(columns={"price": {"checks": {"greater_than": 0}}})
            def process(df: pd.DataFrame) -> pd.DataFrame:  # pragma: no cover
                return df

    def test_shorthand_positional_spec_is_checked_too(self) -> None:
        with pytest.raises(ValueError, match="Unknown check 'gtt'"):
            df_in({"price": {"checks": {"gtt": 0}}})

    def test_custom_callable_may_use_any_name(self) -> None:
        @df_in(columns={"price": {"checks": {"no_outliers": lambda s: s > 0}}})
        def process(df: pd.DataFrame) -> pd.DataFrame:
            return df

        df = pd.DataFrame({"price": [1, 2, 3]})
        assert to_list(process(df)["price"]) == [1, 2, 3]

    @pytest.mark.parametrize("columns", [["price"], {"price": "int64"}, {"price": {"dtype": "int64"}}, None])
    def test_specs_without_checks_are_untouched(self, columns: Any) -> None:
        df_in(columns=columns)

    def test_non_dict_checks_left_to_runtime(self) -> None:
        """Malformed `checks` is a spec-shape problem, handled by strict_specs, not here."""
        df_in(columns={"price": {"checks": "nonsense"}})


class TestOverlappingSpecs:
    """Two specs can name the same column - a regex and an explicit name, or two regexes."""

    def test_checks_from_both_specs_apply(self) -> None:
        @df_in(columns={"r/^col/": {"checks": {"gt": 0}}, "col1": {"checks": {"lt": 100}}})
        def process(df: pd.DataFrame) -> pd.DataFrame:
            return df

        with pytest.raises(AssertionError, match="gt"):
            process(pd.DataFrame({"col1": [-5]}))
        with pytest.raises(AssertionError, match="lt"):
            process(pd.DataFrame({"col1": [500]}))
        assert to_list(process(pd.DataFrame({"col1": [5]}))["col1"]) == [5]

    def test_check_merging_does_not_depend_on_spec_order(self) -> None:
        @df_in(columns={"col1": {"checks": {"lt": 100}}, "r/^col/": {"checks": {"gt": 0}}})
        def process(df: pd.DataFrame) -> pd.DataFrame:
            return df

        with pytest.raises(AssertionError, match="gt"):
            process(pd.DataFrame({"col1": [-5]}))

    @pytest.mark.parametrize(("constraint", "value"), [("nullable", False), ("unique", True)])
    def test_overlapping_column_constraints_do_not_duplicate(self, constraint: str, value: bool) -> None:
        """A column matched by two specs must not produce a duplicate backend expression."""

        @df_in(columns={"r/^col/": {constraint: value}, "col1": {constraint: value}})
        def process(df: pd.DataFrame) -> pd.DataFrame:
            return df

        assert to_list(process(pd.DataFrame({"col1": [1, 2]}))["col1"]) == [1, 2]

    def test_explicit_dtype_wins_over_regex_dtype(self) -> None:
        @df_in(columns={"r/^col/": "int64", "col1": "float64"})
        def process(df: pd.DataFrame) -> pd.DataFrame:
            return df

        assert to_list(process(pd.DataFrame({"col1": [1.5]}))["col1"]) == [1.5]


class TestStrictWithoutColumnConstraints:
    def test_empty_spec_with_strict_rejects_every_column(self) -> None:
        @df_in([], strict=True)
        def process(df: pd.DataFrame) -> pd.DataFrame:
            return df

        with pytest.raises(AssertionError, match="unexpected column"):
            process(pd.DataFrame({"a": [1]}))

    def test_empty_spec_with_strict_accepts_an_empty_frame(self) -> None:
        @df_in([], strict=True)
        def process(df: pd.DataFrame) -> pd.DataFrame:
            return df

        assert process(pd.DataFrame()) is not None

    def test_optional_regex_columns_are_allowed_under_strict(self) -> None:
        @df_in({"a": {"required": True}, "r/^price_/": {"required": False}}, strict=True)
        def process(df: pd.DataFrame) -> pd.DataFrame:
            return df

        assert process(pd.DataFrame({"a": [1], "price_eur": [1.0]})) is not None
