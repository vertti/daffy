"""Base validator protocol."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from daffy.validators.context import ValidationContext


@runtime_checkable
class Validator(Protocol):
    """Interface for all validators.

    Design principles:
    - Validators are stateless after construction
    - validate() is pure: same context → same errors
    - Return empty list for success, list of error strings for failure
    """

    def validate(self, ctx: ValidationContext) -> list[str]:
        """Validate the DataFrame in context. Return list of error messages."""
        ...
