"""Tests for column validators."""

from typing import Any

import pandas as pd
import polars as pl
import pytest

from daffy.validators.columns import (
    ColumnsExistValidator,
    DtypeValidator,
    NullableValidator,
    StrictModeValidator,
)
from daffy.validators.context import ValidationContext


class TestColumnsExistValidator:
    def test_passes_when_no_missing_columns(self) -> None:
        ctx = ValidationContext(df=pd.DataFrame({"a": [1], "b": [2]}))
        validator = ColumnsExistValidator(missing_columns=[], available_columns=["a", "b"])

        assert validator.validate(ctx) == []

    def test_fails_when_columns_missing(self) -> None:
        ctx = ValidationContext(df=pd.DataFrame({"a": [1]}))
        validator = ColumnsExistValidator(missing_columns=["b", "c"], available_columns=["a"])

        errors = validator.validate(ctx)
        assert len(errors) == 1
        assert "Missing columns" in errors[0]
        assert "b" in errors[0]
        assert "c" in errors[0]

    def test_includes_available_columns(self) -> None:
        ctx = ValidationContext(df=pd.DataFrame({"x": [1], "y": [2]}))
        validator = ColumnsExistValidator(missing_columns=["z"], available_columns=["x", "y"])

        errors = validator.validate(ctx)
        assert "Got columns:" in errors[0]


class TestDtypeValidator:
    def test_passes_when_dtypes_match(self) -> None:
        df = pd.DataFrame({"a": [1, 2, 3]})
        ctx = ValidationContext(df=df)
        expected_dtype = ctx.get_dtype("a")
        validator = DtypeValidator({"a": expected_dtype})

        assert validator.validate(ctx) == []

    def test_fails_when_dtype_mismatch(self) -> None:
        df = pd.DataFrame({"a": [1, 2, 3]})
        ctx = ValidationContext(df=df)
        validator = DtypeValidator({"a": "String"})

        errors = validator.validate(ctx)
        assert len(errors) == 1
        assert "wrong dtype" in errors[0]

    def test_skips_missing_columns(self) -> None:
        ctx = ValidationContext(df=pd.DataFrame({"a": [1]}))
        validator = DtypeValidator({"nonexistent": "int64"})

        assert validator.validate(ctx) == []


class TestParameterisedDtypes:
    """Parameterised dtypes are declarable by base name; spell out parameters to constrain them."""

    @pytest.mark.parametrize(
        ("df", "expected"),
        [
            pytest.param(pd.DataFrame({"c": pd.to_datetime(["2024-01-01"])}), "datetime", id="pandas-datetime"),
            pytest.param(
                pd.DataFrame({"c": pd.to_datetime(["2024-01-01"]).tz_localize("UTC")}),
                "datetime",
                id="pandas-datetime-tz",
            ),
            pytest.param(pd.DataFrame({"c": pd.to_timedelta(["1 days"])}), "duration", id="pandas-duration"),
            pytest.param(pl.DataFrame({"c": [[1, 2]]}), "list", id="polars-list"),
            pytest.param(pl.DataFrame({"c": [{"x": 1}]}), "struct", id="polars-struct"),
            pytest.param(pl.DataFrame({"c": ["a"]}, schema={"c": pl.Enum(["a"])}), "enum", id="polars-enum"),
        ],
    )
    def test_base_name_accepted(self, df: Any, expected: str) -> None:
        ctx = ValidationContext(df=df)
        assert DtypeValidator({"c": expected}).validate(ctx) == []

    def test_full_parameterised_spelling_still_accepted(self) -> None:
        ctx = ValidationContext(df=pd.DataFrame({"c": pd.to_datetime(["2024-01-01"])}))
        assert DtypeValidator({"c": "datetime(time_unit='ns', time_zone=none)"}).validate(ctx) == []

    def test_parameters_are_enforced_when_spelled_out(self) -> None:
        ctx = ValidationContext(df=pd.DataFrame({"c": pd.to_datetime(["2024-01-01"])}))
        errors = DtypeValidator({"c": "datetime(time_unit='ms', time_zone=none)"}).validate(ctx)
        assert len(errors) == 1

    @pytest.mark.parametrize(
        ("df", "expected"),
        [
            pytest.param(pd.DataFrame({"c": pd.to_datetime(["2024-01-01"])}), "int64", id="datetime-vs-int"),
            pytest.param(pd.DataFrame({"c": pd.to_timedelta(["1 days"])}), "datetime", id="duration-vs-datetime"),
            pytest.param(pl.DataFrame({"c": [[1, 2]]}), "struct", id="list-vs-struct"),
            pytest.param(pl.DataFrame({"c": ["a"]}, schema={"c": pl.Enum(["a"])}), "string", id="enum-vs-string"),
        ],
    )
    def test_base_name_does_not_match_a_different_dtype(self, df: Any, expected: str) -> None:
        ctx = ValidationContext(df=df)
        assert len(DtypeValidator({"c": expected}).validate(ctx)) == 1


class TestNullableValidator:
    def test_passes_when_no_nulls(self) -> None:
        ctx = ValidationContext(df=pd.DataFrame({"a": [1, 2, 3]}))
        validator = NullableValidator(["a"])

        assert validator.validate(ctx) == []

    def test_fails_when_nulls_present(self) -> None:
        ctx = ValidationContext(df=pd.DataFrame({"a": [1, None, 3]}))
        validator = NullableValidator(["a"])

        errors = validator.validate(ctx)
        assert len(errors) == 1
        assert "null values" in errors[0]
        assert "nullable=False" in errors[0]

    def test_reports_null_count(self) -> None:
        ctx = ValidationContext(df=pd.DataFrame({"a": [None, None, None]}))
        validator = NullableValidator(["a"])

        errors = validator.validate(ctx)
        assert "3 null values" in errors[0]

    def test_skips_missing_columns(self) -> None:
        ctx = ValidationContext(df=pd.DataFrame({"a": [1]}))
        validator = NullableValidator(["nonexistent"])

        assert validator.validate(ctx) == []

    def test_multiple_columns(self) -> None:
        ctx = ValidationContext(df=pd.DataFrame({"a": [None], "b": [None]}))
        validator = NullableValidator(["a", "b"])

        errors = validator.validate(ctx)
        assert len(errors) == 1
        assert "Null violations" in errors[0]
        assert "a" in errors[0]
        assert "b" in errors[0]


class TestStrictModeValidator:
    def test_passes_when_only_allowed_columns(self) -> None:
        ctx = ValidationContext(df=pd.DataFrame({"a": [1], "b": [2]}))
        validator = StrictModeValidator({"a", "b"})

        assert validator.validate(ctx) == []

    def test_fails_when_extra_columns(self) -> None:
        ctx = ValidationContext(df=pd.DataFrame({"a": [1], "b": [2], "c": [3]}))
        validator = StrictModeValidator({"a", "b"})

        errors = validator.validate(ctx)
        assert len(errors) == 1
        assert "unexpected column" in errors[0].lower()
        assert "c" in errors[0]

    def test_allows_subset(self) -> None:
        ctx = ValidationContext(df=pd.DataFrame({"a": [1]}))
        validator = StrictModeValidator({"a", "b", "c"})

        assert validator.validate(ctx) == []
