"""Tests for DataFrame shape validation (min_rows, max_rows, exact_rows)."""

from typing import Any

import pytest

from daffy import df_in, df_out
from tests.utils import DataFrameFactory


class TestRowConstraints:
    @pytest.mark.parametrize("decorator", [df_out, df_in])
    @pytest.mark.parametrize(
        ("constraint", "value", "rows", "should_pass"),
        [
            ("min_rows", 3, [1, 2], False),
            ("min_rows", 3, [1, 2, 3], True),
            ("min_rows", 2, [1, 2, 3, 4], True),
            ("min_rows", 1, [], False),
            ("min_rows", 0, [], True),
            ("max_rows", 2, [1, 2, 3, 4], False),
            ("max_rows", 3, [1, 2, 3], True),
            ("max_rows", 10, [1, 2], True),
            ("max_rows", 5, [], True),
            ("exact_rows", 5, [1, 2, 3], False),
            ("exact_rows", 2, [1, 2, 3, 4], False),
            ("exact_rows", 3, [1, 2, 3], True),
            ("exact_rows", 0, [], True),
        ],
    )
    def test_row_constraints(
        self, make_df: DataFrameFactory, decorator: Any, constraint: str, value: int, rows: list[int], should_pass: bool
    ) -> None:
        kwargs = {constraint: value}

        if decorator == df_out:

            @decorator(**kwargs)
            def f() -> Any:
                return make_df({"a": rows})

            if should_pass:
                assert len(f()) == len(rows)
            else:
                with pytest.raises(AssertionError, match=rf"has {len(rows)} rows but {constraint}={value}"):
                    f()
        else:

            @decorator(**kwargs)
            def g(df: Any) -> Any:
                return df

            if should_pass:
                assert len(g(make_df({"a": rows}))) == len(rows)
            else:
                with pytest.raises(AssertionError, match=rf"has {len(rows)} rows but {constraint}={value}"):
                    g(make_df({"a": rows}))

    def test_error_includes_context(self, make_df: DataFrameFactory) -> None:
        @df_out(min_rows=5)
        def my_transform() -> Any:
            return make_df({"a": [1]})

        @df_in(min_rows=5)
        def process(df: Any) -> Any:
            return df

        with pytest.raises(AssertionError, match=r"function 'my_transform'.*return value"):
            my_transform()
        with pytest.raises(AssertionError, match=r"function 'process'.*parameter 'df'"):
            process(make_df({"a": [1]}))

    def test_combined_min_max(self, make_df: DataFrameFactory) -> None:
        @df_out(min_rows=2, max_rows=5)
        def f() -> Any:
            return make_df({"a": [1, 2, 3]})

        assert len(f()) == 3


class TestAllowEmpty:
    def test_config_rejects_empty(self, make_df: DataFrameFactory, monkeypatch: pytest.MonkeyPatch) -> None:
        from daffy import decorators

        monkeypatch.setattr(decorators, "get_allow_empty", lambda x: False if x is None else x)

        @df_out()
        def f() -> Any:
            return make_df({"a": []})

        with pytest.raises(AssertionError, match=r"allow_empty=False"):
            f()

    def test_decorator_overrides_config(self, make_df: DataFrameFactory, monkeypatch: pytest.MonkeyPatch) -> None:
        from daffy import decorators

        monkeypatch.setattr(decorators, "get_allow_empty", lambda x: False if x is None else x)

        @df_out(allow_empty=True)
        def f() -> Any:
            return make_df({"a": []})

        assert len(f()) == 0


class TestLazyMode:
    def test_collects_shape_and_column_errors(self, make_df: DataFrameFactory) -> None:
        @df_out(columns=["a", "b"], min_rows=5, lazy=True)
        def f() -> Any:
            return make_df({"a": [1, 2]})

        with pytest.raises(AssertionError) as exc_info:
            f()

        assert "min_rows=5" in str(exc_info.value)
        assert "Missing columns" in str(exc_info.value)

    @pytest.mark.parametrize("decorator", [df_out, df_in])
    def test_shape_only_errors_collected(self, make_df: DataFrameFactory, decorator: Any) -> None:
        if decorator == df_out:

            @decorator(min_rows=5, lazy=True)
            def f() -> Any:
                return make_df({"a": [1, 2]})

            with pytest.raises(AssertionError, match=r"min_rows=5"):
                f()
        else:

            @decorator(min_rows=5, lazy=True)
            def g(df: Any) -> Any:
                return df

            with pytest.raises(AssertionError, match=r"min_rows=5"):
                g(make_df({"a": [1, 2]}))


class TestInvalidConstraints:
    @pytest.mark.parametrize("decorator", [df_out, df_in])
    @pytest.mark.parametrize(
        ("kwargs", "error_match"),
        [
            ({"min_rows": -1}, r"min_rows must be >= 0"),
            ({"max_rows": -5}, r"max_rows must be >= 0"),
            ({"exact_rows": -1}, r"exact_rows must be >= 0"),
            ({"min_rows": 10, "max_rows": 5}, r"min_rows.*cannot be greater than max_rows"),
        ],
    )
    def test_rejects_invalid(self, decorator: Any, kwargs: dict[str, Any], error_match: str) -> None:
        with pytest.raises(ValueError, match=error_match):
            if decorator == df_out:

                @decorator(**kwargs)
                def f() -> Any:
                    pass

            else:

                @decorator(**kwargs)
                def g(df: Any) -> Any:
                    pass

    def test_accepts_min_rows_equal_to_max_rows(self, make_df: DataFrameFactory) -> None:
        """An exact-size range is a legal bound, not a contradiction."""

        @df_in(min_rows=2, max_rows=2)
        def process(df: Any) -> Any:
            return df

        process(make_df({"a": [1, 2]}))

        with pytest.raises(AssertionError, match="max_rows=2"):
            process(make_df({"a": [1, 2, 3]}))
