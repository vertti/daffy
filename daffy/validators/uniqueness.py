"""Uniqueness validators - single column and composite."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from daffy.validators.context import ValidationContext


@dataclass
class UniqueValidator:
    unique_columns: list[str]

    def validate(self, ctx: ValidationContext) -> list[str]:
        errors = []

        for col in self.unique_columns:
            if ctx.has_column(col):
                dup_count = ctx.row_count - ctx.get_series(col).n_unique()
                if dup_count > 0:
                    errors.append(
                        f"Column '{col}'{ctx.param_info} contains {dup_count} duplicate values but unique=True"
                    )

        return errors


@dataclass
class CompositeUniqueValidator:
    column_combinations: list[list[str]]

    def validate(self, ctx: ValidationContext) -> list[str]:
        errors = []

        for combo in self.column_combinations:
            col_desc = " + ".join(f"'{c}'" for c in combo)
            missing = [c for c in combo if not ctx.has_column(c)]
            if missing:
                errors.append(
                    f"composite_unique references missing columns {missing} in combination [{col_desc}]{ctx.param_info}"
                )
                continue

            unique_count = ctx.nw_df.select(combo).unique().shape[0]
            dup_count = ctx.row_count - unique_count

            if dup_count > 0:
                errors.append(
                    f"Columns {col_desc}{ctx.param_info} contain {dup_count} "
                    f"duplicate combinations but composite_unique is set"
                )

        return errors
