"""Tests for narwhals compatibility utilities."""

from typing import Any

import pandas as pd
import polars as pl
import pytest

from daffy.narwhals_compat import is_supported_dataframe


class TestIsSupportedDataframe:
    @pytest.mark.parametrize("df", [pd.DataFrame({"A": [1, 2, 3]}), pl.DataFrame({"A": [1, 2, 3]})])
    def test_dataframes_supported(self, df: Any) -> None:
        assert is_supported_dataframe(df) is True

    def test_pyarrow_table_supported(self) -> None:
        pa = pytest.importorskip("pyarrow")
        pyarrow_table = pa.table({"A": [1, 2, 3]})
        assert is_supported_dataframe(pyarrow_table) is True

    @pytest.mark.parametrize("obj", [[1, 2, 3], {"A": [1, 2, 3]}, "not a dataframe", None, 42])
    def test_non_dataframes_not_supported(self, obj: Any) -> None:
        assert is_supported_dataframe(obj) is False
