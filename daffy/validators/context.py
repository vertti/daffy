"""Validation context - shared state for all validators."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import narwhals as nw


@dataclass(frozen=True)
class ValidationContext:
    """Single narwhals conversion per validation, shared by all validators."""

    df: Any
    func_name: str = ""
    param_name: str | None = None
    is_return_value: bool = False

    nw_df: Any = field(init=False, repr=False)
    columns: tuple[str, ...] = field(init=False)
    column_set: frozenset[str] = field(init=False)
    row_count: int = field(init=False)
    schema: dict[str, Any] = field(init=False)

    def __post_init__(self) -> None:
        nw_df = nw.from_native(self.df, eager_only=True)
        object.__setattr__(self, "nw_df", nw_df)
        object.__setattr__(self, "columns", tuple(nw_df.columns))
        object.__setattr__(self, "column_set", frozenset(nw_df.columns))
        object.__setattr__(self, "row_count", nw_df.shape[0])
        object.__setattr__(self, "schema", dict(nw_df.schema))

    @property
    def param_info(self) -> str:
        if self.func_name:
            if self.is_return_value:
                return f" in function '{self.func_name}' return value"
            if self.param_name:
                return f" in function '{self.func_name}' parameter '{self.param_name}'"
        return ""

    def has_column(self, col: str) -> bool:
        return col in self.column_set

    def get_series(self, col: str) -> Any:
        return self.nw_df[col]

    def get_dtype(self, col: str) -> Any:
        return self.schema.get(col)
