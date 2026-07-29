"""Tests for column validators."""

import pandas as pd

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

        assert not validator.validate(ctx)

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

        assert not validator.validate(ctx)

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

        assert not validator.validate(ctx)


class TestNullableValidator:
    def test_passes_when_no_nulls(self) -> None:
        ctx = ValidationContext(df=pd.DataFrame({"a": [1, 2, 3]}))
        validator = NullableValidator(["a"])

        assert not validator.validate(ctx)

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

        assert not validator.validate(ctx)

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

        assert not validator.validate(ctx)

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

        assert not validator.validate(ctx)
