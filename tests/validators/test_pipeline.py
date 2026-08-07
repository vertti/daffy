"""Tests for ValidationPipeline."""

from dataclasses import dataclass

import pandas as pd
import pytest

from daffy.validators.context import ValidationContext
from daffy.validators.pipeline import ValidationPipeline


@dataclass
class AlwaysPassValidator:
    def validate(self, ctx: ValidationContext) -> list[str]:  # noqa: ARG002
        return []


@dataclass
class AlwaysFailValidator:
    message: str = "Validation failed"

    def validate(self, ctx: ValidationContext) -> list[str]:  # noqa: ARG002
        return [self.message]


@dataclass
class MultiErrorValidator:
    def validate(self, ctx: ValidationContext) -> list[str]:  # noqa: ARG002
        return ["Error 1", "Error 2"]


class TestValidationPipeline:
    def test_empty_pipeline_passes(self) -> None:
        ctx = ValidationContext(df=pd.DataFrame({"a": [1]}))
        pipeline = ValidationPipeline()

        pipeline.run(ctx)

    def test_passing_validators(self) -> None:
        ctx = ValidationContext(df=pd.DataFrame({"a": [1]}))
        pipeline = ValidationPipeline()
        pipeline.add(AlwaysPassValidator())
        pipeline.add(AlwaysPassValidator())

        pipeline.run(ctx)

    def test_eager_mode_fails_on_first_error(self) -> None:
        ctx = ValidationContext(df=pd.DataFrame({"a": [1]}))
        pipeline = ValidationPipeline(lazy=False)
        pipeline.add(AlwaysFailValidator(message="First error"))
        pipeline.add(AlwaysFailValidator(message="Second error"))

        with pytest.raises(AssertionError, match="First error"):
            pipeline.run(ctx)

    def test_lazy_mode_collects_all_errors(self) -> None:
        ctx = ValidationContext(df=pd.DataFrame({"a": [1]}))
        pipeline = ValidationPipeline(lazy=True)
        pipeline.add(AlwaysFailValidator(message="First error"))
        pipeline.add(AlwaysFailValidator(message="Second error"))

        with pytest.raises(AssertionError) as exc_info:
            pipeline.run(ctx)

        error = str(exc_info.value)
        assert "First error" in error
        assert "Second error" in error

    def test_lazy_mode_separates_errors(self) -> None:
        ctx = ValidationContext(df=pd.DataFrame({"a": [1]}))
        pipeline = ValidationPipeline(lazy=True)
        pipeline.add(AlwaysFailValidator(message="Error A"))
        pipeline.add(AlwaysFailValidator(message="Error B"))

        with pytest.raises(AssertionError) as exc_info:
            pipeline.run(ctx)

        assert "\n\n" in str(exc_info.value)

    def test_add_returns_self_for_chaining(self) -> None:
        pipeline = ValidationPipeline()
        result = pipeline.add(AlwaysPassValidator())
        assert result is pipeline

    def test_len_returns_validator_count(self) -> None:
        pipeline = ValidationPipeline()
        assert len(pipeline) == 0

        pipeline.add(AlwaysPassValidator())
        assert len(pipeline) == 1

        pipeline.add(AlwaysPassValidator())
        assert len(pipeline) == 2
