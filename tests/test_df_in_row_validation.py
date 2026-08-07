"""Tests for df_in decorator with row validation."""

from typing import Any

import pandas as pd
import pytest
from pydantic import BaseModel, ConfigDict, Field

from daffy import df_in


class PersonValidator(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str
    age: int = Field(ge=0, le=120)


def test_df_in_with_valid_rows() -> None:
    @df_in(row_validator=PersonValidator)
    def process_people(df: Any) -> Any:
        return df

    df = pd.DataFrame(
        {
            "name": ["Alice", "Bob"],
            "age": [25, 30],
        }
    )

    result = process_people(df)
    assert result.equals(df)


def test_df_in_with_invalid_rows() -> None:
    @df_in(row_validator=PersonValidator)
    def process_people(df: Any) -> Any:
        return df

    df = pd.DataFrame(
        {
            "name": ["Alice", "Bob"],
            "age": [25, -5],
        }
    )

    with pytest.raises(AssertionError) as exc_info:
        process_people(df)

    message = str(exc_info.value)
    assert "Row validation failed" in message
    assert "Row 1:" in message
    assert "age" in message
    assert "function 'process_people' parameter 'df'" in message


def test_df_in_with_columns_and_row_validator() -> None:
    @df_in(columns=["name", "age"], row_validator=PersonValidator)
    def process_people(df: Any) -> Any:
        return df

    df = pd.DataFrame(
        {
            "name": ["Alice"],
        }
    )

    with pytest.raises(AssertionError, match="Missing columns"):
        process_people(df)

    df = pd.DataFrame(
        {
            "name": ["Alice"],
            "age": [150],
        }
    )

    with pytest.raises(AssertionError) as exc_info:
        process_people(df)

    message = str(exc_info.value)
    assert "Row validation failed" in message


def test_df_in_with_named_parameter() -> None:
    @df_in(name="people_df", row_validator=PersonValidator)
    def process(data: Any, people_df: Any, config: Any = None) -> Any:
        return people_df

    df = pd.DataFrame(
        {
            "name": ["Alice", "Bob"],
            "age": [25, -5],
        }
    )

    with pytest.raises(AssertionError) as exc_info:
        process("other", df, "config")

    message = str(exc_info.value)
    assert "people_df" in message


def test_df_in_without_row_validator() -> None:
    @df_in(columns=["name", "age"])
    def process_people(df: Any) -> Any:
        return df

    df = pd.DataFrame(
        {
            "name": ["Alice", "Bob"],
            "age": [25, -5],
        }
    )

    result = process_people(df)
    assert result.equals(df)


class TestMaxErrorsBoundary:
    """row_validation_max_errors caps how many failing rows are listed, not how many exist."""

    @staticmethod
    def _run_with_bad_rows(count: int) -> str:
        @df_in(row_validator=PersonValidator)
        def process_people(df: Any) -> Any:
            return df

        df = pd.DataFrame({"name": ["A"] * count, "age": [-5] * count})
        with pytest.raises(AssertionError) as exc_info:
            process_people(df)
        return str(exc_info.value)

    def test_lists_every_failing_row_up_to_the_limit(self) -> None:
        message = self._run_with_bad_rows(5)
        assert message.count("  Row ") == 5
        assert message.startswith("Row validation failed for 5 out of 5 rows in function")
        assert "more row" not in message
        assert "stopped after" not in message

    def test_stops_listing_past_the_limit(self) -> None:
        message = self._run_with_bad_rows(8)
        assert message.count("  Row ") == 5
        assert "at least" in message
        assert "stopped after 5 reported rows" in message

    def test_does_not_understate_how_many_rows_failed(self) -> None:
        """Counting stops at the break, so the trailer must not claim a specific remainder."""
        message = self._run_with_bad_rows(10000)
        assert "and 1 more row(s)" not in message
        assert "more rows may have errors" in message


class TestValidatorConstructorArguments:
    """RowValidator and ChecksValidator advertise these, but nothing ever passed them."""

    def test_row_validator_max_errors_overrides_config(self) -> None:
        from daffy.validators.context import ValidationContext
        from daffy.validators.rows import RowValidator

        ctx = ValidationContext(df=pd.DataFrame({"v": ["x"] * 8}))
        errors = RowValidator(PersonValidator, max_errors=2).validate(ctx)

        assert len(errors) == 1
        assert errors[0].count("  Row ") == 2, "config default is 5, so the argument must win"
        assert errors[0].startswith("Row validation failed for at least 3 out of 8 rows")

    def test_checks_validator_max_samples_overrides_config(self) -> None:
        from daffy.validators.checks import ChecksValidator
        from daffy.validators.context import ValidationContext

        ctx = ValidationContext(df=pd.DataFrame({"v": [-1] * 10}))
        errors = ChecksValidator({"v": {"gt": 0}}, max_samples=2).validate(ctx)

        assert len(errors) == 1
        assert "Examples: [-1, -1]" in errors[0], "config default is 5, so the argument must win"
