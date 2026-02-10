"""Simple tests for optional dependencies functionality."""

from typing import Any

import pytest

from daffy.dataframe_types import HAS_MODIN, HAS_PANDAS, HAS_POLARS, HAS_PYARROW


class TestOptionalDependenciesDetection:
    """Test that daffy correctly detects available dependencies."""

    def test_library_detection_flags_exist(self) -> None:
        """Test that the detection flags exist and are boolean."""
        assert isinstance(HAS_PANDAS, bool)
        assert isinstance(HAS_POLARS, bool)
        assert isinstance(HAS_MODIN, bool)
        assert isinstance(HAS_PYARROW, bool)

    def test_at_least_one_library_available(self) -> None:
        """Test that at least one DataFrame library is available in test environment."""
        assert HAS_PANDAS or HAS_POLARS or HAS_MODIN or HAS_PYARROW, (
            "At least one DataFrame library should be available for tests"
        )

    def test_import_detection_consistency(self) -> None:
        """Test that import detection is consistent with actual imports."""
        if HAS_PANDAS:
            # If we detected pandas, we should be able to import it
            import pandas as pd

            assert pd is not None

        if HAS_POLARS:
            # If we detected polars, we should be able to import it
            import polars as pl

            assert pl is not None

        if HAS_PYARROW:
            # If we detected pyarrow, we should be able to import it
            import pyarrow as pa

            assert pa is not None

    def test_error_messages_reflect_available_libraries(self) -> None:
        """Test that error messages reflect only available libraries."""
        from daffy import df_in

        @df_in()
        def test_func(df: Any) -> Any:
            return df

        with pytest.raises(AssertionError) as excinfo:
            test_func("not_a_dataframe")

        error_msg = str(excinfo.value)

        # Check that error message mentions available libraries
        if HAS_PANDAS:
            assert "Pandas" in error_msg
        if HAS_POLARS:
            assert "Polars" in error_msg
        if HAS_MODIN:
            assert "Modin" in error_msg
        if HAS_PYARROW:
            assert "PyArrow" in error_msg

    def test_dataframe_validation_works_with_available_libraries(self) -> None:
        """Test that DataFrame validation works with whatever libraries are available."""
        from daffy import df_in, df_out

        if HAS_PANDAS:
            import pandas as pd

            @df_in(columns=["A", "B"])
            @df_out(columns=["A", "B", "C"])
            def pandas_test(df: Any) -> Any:
                df = df.copy()
                df["C"] = df["A"] + df["B"]
                return df

            pandas_df = pd.DataFrame({"A": [1, 2], "B": [3, 4]})
            result = pandas_test(pandas_df)
            assert list(result.columns) == ["A", "B", "C"]

        if HAS_POLARS:
            import polars as pl

            @df_in(columns=["A", "B"])
            @df_out(columns=["A", "B", "C"])
            def polars_test(df: Any) -> Any:
                return df.with_columns((pl.col("A") + pl.col("B")).alias("C"))

            polars_df = pl.DataFrame({"A": [1, 2], "B": [3, 4]})
            result = polars_test(polars_df)
            assert result.columns == ["A", "B", "C"]

        if HAS_PYARROW:
            import pyarrow as pa

            @df_in(columns=["A", "B"])
            @df_out(columns=["A", "B", "C"])
            def pyarrow_test(df: Any) -> Any:
                a_values = df.column("A").to_pylist()
                b_values = df.column("B").to_pylist()
                c_values = [a + b for a, b in zip(a_values, b_values, strict=False)]
                return df.append_column("C", pa.array(c_values))

            pyarrow_table = pa.table({"A": [1, 2], "B": [3, 4]})
            result = pyarrow_test(pyarrow_table)
            assert result.column_names == ["A", "B", "C"]


def test_basic_import_works() -> None:
    """Test that basic daffy import works regardless of available libraries."""
    from daffy import df_in, df_log, df_out

    # These should all be importable
    assert df_in is not None
    assert df_out is not None
    assert df_log is not None


@pytest.mark.skipif(not (HAS_PANDAS and HAS_POLARS), reason="Test requires both pandas and polars")
def test_both_libraries_work_together() -> None:
    """Test that both libraries can be used in the same environment."""
    import pandas as pd
    import polars as pl

    from daffy import df_in

    @df_in(columns=["A", "B"])
    def works_with_both(df: Any) -> Any:
        return df

    # Both should work
    pandas_df = pd.DataFrame({"A": [1, 2], "B": [3, 4]})
    polars_df = pl.DataFrame({"A": [1, 2], "B": [3, 4]})

    works_with_both(pandas_df)
    works_with_both(polars_df)


def test_describe_dataframe_with_dtypes() -> None:
    """Test describe_dataframe function with dtype information."""
    from daffy.utils import describe_dataframe

    if HAS_PANDAS:
        import pandas as pd

        pandas_df = pd.DataFrame({"A": [1, 2], "B": ["x", "y"]})
        result = describe_dataframe(pandas_df, include_dtypes=True)
        assert "columns: ['A', 'B']" in result
        assert "with dtypes" in result

    if HAS_POLARS:
        import polars as pl

        polars_df = pl.DataFrame({"A": [1, 2], "B": ["x", "y"]})
        result = describe_dataframe(polars_df, include_dtypes=True)
        assert "columns: ['A', 'B']" in result
        assert "with dtypes" in result

    if HAS_PYARROW:
        import pyarrow as pa

        pyarrow_table = pa.table({"A": [1, 2], "B": ["x", "y"]})
        result = describe_dataframe(pyarrow_table, include_dtypes=True)
        assert "columns: ['A', 'B']" in result
        assert "with dtypes" in result


def test_log_dataframe_functions() -> None:
    """Test DataFrame logging functions."""
    import logging

    from daffy.utils import log_dataframe_input, log_dataframe_output

    # Set up logging to capture messages
    logging.basicConfig(level=logging.DEBUG)

    if HAS_PANDAS:
        import pandas as pd

        pandas_df = pd.DataFrame({"A": [1, 2], "B": [3, 4]})

        # These should not raise errors
        log_dataframe_input(logging.INFO, "test_func", pandas_df, False)
        log_dataframe_output(logging.INFO, "test_func", pandas_df, True)

        # Test with non-DataFrame input
        log_dataframe_input(logging.INFO, "test_func", "not_a_df", False)
        log_dataframe_output(logging.INFO, "test_func", "not_a_df", False)

    if HAS_POLARS:
        import polars as pl

        polars_df = pl.DataFrame({"A": [1, 2], "B": [3, 4]})

        # These should not raise errors
        log_dataframe_input(logging.INFO, "test_func", polars_df, False)
        log_dataframe_output(logging.INFO, "test_func", polars_df, True)

    if HAS_PYARROW:
        import pyarrow as pa

        pyarrow_table = pa.table({"A": [1, 2], "B": [3, 4]})

        # These should not raise errors
        log_dataframe_input(logging.INFO, "test_func", pyarrow_table, False)
        log_dataframe_output(logging.INFO, "test_func", pyarrow_table, True)
