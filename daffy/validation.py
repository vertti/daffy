"""Type definitions for DAFFY DataFrame validation."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, TypeAlias, TypedDict

from daffy.patterns import RegexColumnDef


class ColumnConstraints(TypedDict, total=False):
    """Type-safe specification for column constraints.

    All fields are optional. Use this instead of untyped dicts to catch
    typos like {"nulllable": False} at type-check time.
    """

    dtype: Any
    nullable: bool
    unique: bool
    required: bool
    checks: dict[str, Any]


# Mapping rather than dict, and str keys only: dict keys are invariant, so a
# dict[str, ...] built elsewhere - including dict[str, ColumnConstraints] - would not be
# assignable and only inline literals would type-check. Regex specs are written as
# "r/pattern/" strings; RegexColumnDef is the compiled internal form.
ColumnsDef: TypeAlias = Sequence[str | RegexColumnDef] | Mapping[str, Any] | None
