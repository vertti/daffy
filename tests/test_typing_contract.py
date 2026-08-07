"""Typing contracts that the pyrefly gate enforces.

These assertions are mostly static: the value is that `pyrefly check .` fails if the
decorators stop preserving signatures, or if ColumnsDef goes back to a key type that
only accepts inline dict literals.
"""

from typing import Any

import pandas as pd

from daffy import df_in, df_log, df_out
from daffy.validation import ColumnConstraints

# Specs built once and shared, rather than inlined at each decorator. dict keys are
# invariant, so a narrower ColumnsDef key type rejects every one of these.
DTYPE_SPEC: dict[str, str] = {"price": "float64"}
RICH_SPEC: dict[str, ColumnConstraints] = {"price": {"nullable": False, "checks": {"gt": 0}}}
COLUMN_LIST: list[str] = ["price"]


@df_in(DTYPE_SPEC)
def with_dtype_spec(df: Any) -> Any:
    return df


@df_in(RICH_SPEC)
def with_rich_spec(df: Any) -> Any:
    return df


@df_out(DTYPE_SPEC)
def returning_dtype_spec() -> pd.DataFrame:
    return pd.DataFrame({"price": [1.0]})


@df_in(COLUMN_LIST)
def with_column_list(df: Any) -> Any:
    return df


@df_in(["price"])
def keeps_its_signature(df: Any, rate: float, *, label: str = "x") -> str:
    return f"{label}{rate}"


@df_log()
def logged(df: Any, count: int) -> int:
    return count


def test_shared_specs_work_at_runtime_too() -> None:
    df = pd.DataFrame({"price": [1.0]})

    assert with_dtype_spec(df) is df
    assert with_rich_spec(df) is df
    assert with_column_list(df) is df
    assert returning_dtype_spec() is not None


def test_decorated_functions_keep_their_signature() -> None:
    from inspect import signature

    assert list(signature(keeps_its_signature).parameters) == ["df", "rate", "label"]
    assert list(signature(logged).parameters) == ["df", "count"]

    df = pd.DataFrame({"price": [1.0]})
    assert keeps_its_signature(df, 1.5, label="n") == "n1.5"
    assert logged(df, 3) == 3
