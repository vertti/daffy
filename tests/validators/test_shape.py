"""Tests for ShapeValidator."""

import pandas as pd

from daffy.validators.context import ValidationContext
from daffy.validators.shape import ShapeValidator


class TestShapeValidator:
    def test_passes_when_no_constraints(self) -> None:
        ctx = ValidationContext(df=pd.DataFrame({"a": [1, 2, 3]}))
        validator = ShapeValidator()

        assert not validator.validate(ctx)

    def test_passes_min_rows(self) -> None:
        ctx = ValidationContext(df=pd.DataFrame({"a": [1, 2, 3]}))
        validator = ShapeValidator(min_rows=2)

        assert not validator.validate(ctx)

    def test_fails_min_rows(self) -> None:
        ctx = ValidationContext(df=pd.DataFrame({"a": [1]}))
        validator = ShapeValidator(min_rows=5)

        errors = validator.validate(ctx)
        assert len(errors) == 1
        assert "has 1 rows but min_rows=5" in errors[0]

    def test_passes_max_rows(self) -> None:
        ctx = ValidationContext(df=pd.DataFrame({"a": [1, 2, 3]}))
        validator = ShapeValidator(max_rows=10)

        assert not validator.validate(ctx)

    def test_fails_max_rows(self) -> None:
        ctx = ValidationContext(df=pd.DataFrame({"a": [1, 2, 3, 4, 5]}))
        validator = ShapeValidator(max_rows=3)

        errors = validator.validate(ctx)
        assert len(errors) == 1
        assert "has 5 rows but max_rows=3" in errors[0]

    def test_passes_exact_rows(self) -> None:
        ctx = ValidationContext(df=pd.DataFrame({"a": [1, 2, 3]}))
        validator = ShapeValidator(exact_rows=3)

        assert not validator.validate(ctx)

    def test_fails_exact_rows(self) -> None:
        ctx = ValidationContext(df=pd.DataFrame({"a": [1, 2]}))
        validator = ShapeValidator(exact_rows=5)

        errors = validator.validate(ctx)
        assert len(errors) == 1
        assert "has 2 rows but exact_rows=5" in errors[0]

    def test_passes_allow_empty_true(self) -> None:
        ctx = ValidationContext(df=pd.DataFrame({"a": []}))
        validator = ShapeValidator(allow_empty=True)

        assert not validator.validate(ctx)

    def test_fails_allow_empty_false(self) -> None:
        ctx = ValidationContext(df=pd.DataFrame({"a": []}))
        validator = ShapeValidator(allow_empty=False)

        errors = validator.validate(ctx)
        assert len(errors) == 1
        assert "empty but allow_empty=False" in errors[0]

    def test_collects_multiple_errors(self) -> None:
        ctx = ValidationContext(df=pd.DataFrame({"a": [1]}))
        validator = ShapeValidator(min_rows=10, max_rows=0)

        errors = validator.validate(ctx)
        assert len(errors) == 2

    def test_includes_param_info(self) -> None:
        ctx = ValidationContext(
            df=pd.DataFrame({"a": [1]}),
            func_name="test_func",
            is_return_value=True,
        )
        validator = ShapeValidator(min_rows=10)

        errors = validator.validate(ctx)
        assert "test_func" in errors[0]
        assert "return value" in errors[0]
