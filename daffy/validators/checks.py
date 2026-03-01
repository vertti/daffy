"""Checks validator - value constraints."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from daffy.checks import validate_checks as run_checks
from daffy.config import get_checks_max_samples

if TYPE_CHECKING:
    from daffy.validators.context import ValidationContext


@dataclass
class ChecksValidator:
    checks_by_column: dict[str, dict[str, Any]]
    max_samples: int | None = None

    def validate(self, ctx: ValidationContext) -> list[str]:
        max_samples = self.max_samples if self.max_samples is not None else get_checks_max_samples()
        all_violations: list[tuple[str, str, int, list[Any]]] = []

        for col, checks in self.checks_by_column.items():
            if not ctx.has_column(col):
                continue

            violations = run_checks(ctx.get_series(col), col, checks, max_samples)
            all_violations.extend(violations)

        if not all_violations:
            return []

        if len(all_violations) == 1:
            col, check, count, samples = all_violations[0]
            return [f"Column '{col}'{ctx.param_info} failed check {check}: {count} values failed. Examples: {samples}"]

        violation_lines = [
            f"Column '{col}' failed {check}: {count} values. Examples: {samples}"
            for col, check, count, samples in all_violations
        ]
        return [f"Check violations{ctx.param_info}:\n  " + "\n  ".join(violation_lines)]
