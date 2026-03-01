"""Column validators - existence, dtype, nullable, strict mode."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import narwhals as nw

if TYPE_CHECKING:
    from daffy.validators.context import ValidationContext


@dataclass
class ColumnsExistValidator:
    missing_columns: list[str]
    available_columns: list[str]

    def validate(self, ctx: ValidationContext) -> list[str]:
        if self.missing_columns:
            return [f"Missing columns: {self.missing_columns}{ctx.param_info}. Got columns: {self.available_columns}"]
        return []


_DTYPE_ALIASES = {
    "object": "string",
    "str": "string",
    "int": "int64",
    "float": "float64",
    "bool": "boolean",
}


def _normalize_dtype(dtype: str) -> str:
    dtype_lower = str(dtype).lower()
    return _DTYPE_ALIASES.get(dtype_lower, dtype_lower)


@dataclass
class DtypeValidator:
    expected: dict[str, Any]

    def validate(self, ctx: ValidationContext) -> list[str]:
        errors = []
        for col, expected_dtype in self.expected.items():
            if ctx.has_column(col):
                actual = ctx.get_dtype(col)
                if _normalize_dtype(actual) != _normalize_dtype(expected_dtype):
                    actual_str = str(actual).lower()
                    msg = f"Column {col}{ctx.param_info} has wrong dtype. Was {actual_str}, expected {expected_dtype}"
                    errors.append(msg)
        return errors


@dataclass
class NullableValidator:
    non_nullable_columns: list[str]

    def validate(self, ctx: ValidationContext) -> list[str]:
        cols_to_check = [col for col in self.non_nullable_columns if ctx.has_column(col)]
        if not cols_to_check:
            return []

        exprs = [nw.col(col).is_null().sum().alias(col) for col in cols_to_check]
        results = ctx.nw_df.select(*exprs).to_dict(as_series=False)

        violations: list[tuple[str, int]] = []
        for col in cols_to_check:
            null_count = int(results[col][0])
            if null_count > 0:
                violations.append((col, null_count))

        if not violations:
            return []

        if len(violations) == 1:
            col, count = violations[0]
            return [f"Column '{col}'{ctx.param_info} contains {count} null values but nullable=False"]

        violation_desc = ", ".join(f"Column '{col}' contains {count} null values" for col, count in violations)
        return [f"Null violations: {violation_desc}{ctx.param_info}"]


@dataclass
class StrictModeValidator:
    allowed_columns: set[str]

    def validate(self, ctx: ValidationContext) -> list[str]:
        extra = ctx.column_set - self.allowed_columns

        if extra:
            return [f"DataFrame{ctx.param_info} contained unexpected column(s): {', '.join(sorted(extra))}"]

        return []
