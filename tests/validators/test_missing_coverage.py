import pytest
import pandas as pd
from daffy.validators.context import ValidationContext
from daffy.validators.columns import NullableValidator
from daffy.validators.uniqueness import UniqueValidator
from daffy.validators.checks import ChecksValidator

def test_nullable_validator_missing_column():
    ctx = ValidationContext(df=pd.DataFrame({"a": [1]}))
    val = NullableValidator(["missing"])
    assert val.validate(ctx) == []

def test_unique_validator_missing_column():
    ctx = ValidationContext(df=pd.DataFrame({"a": [1]}))
    val = UniqueValidator(["missing"])
    assert val.validate(ctx) == []

def test_checks_validator_missing_column():
    ctx = ValidationContext(df=pd.DataFrame({"a": [1]}))
    val = ChecksValidator({"missing": {"gt": 0}})
    assert val.validate(ctx) == []
