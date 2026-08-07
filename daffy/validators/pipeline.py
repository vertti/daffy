"""Validation pipeline - orchestrates validators."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from daffy.validators.base import Validator
    from daffy.validators.context import ValidationContext


@dataclass
class ValidationPipeline:
    lazy: bool = False
    validators: list[Validator] = field(default_factory=list)

    def add(self, validator: Validator) -> ValidationPipeline:
        self.validators.append(validator)
        return self

    def run(self, ctx: ValidationContext) -> None:
        """In lazy mode: collect all errors, raise once. In eager mode: raise on first error."""
        all_errors: list[str] = []

        for validator in self.validators:
            errors = validator.validate(ctx)

            if errors:
                if not self.lazy:
                    raise AssertionError(errors[0])
                all_errors.extend(errors)

        if all_errors:
            raise AssertionError("\n\n".join(all_errors))

    def __len__(self) -> int:
        return len(self.validators)
