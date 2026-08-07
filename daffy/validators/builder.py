"""Pipeline builder - assembles validators from decorator parameters."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from daffy.patterns import compile_regex_pattern, is_regex_string, match_column_with_regex

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

from daffy.validators.checks import ChecksValidator
from daffy.validators.columns import ColumnsExistValidator, DtypeValidator, NullableValidator, StrictModeValidator
from daffy.validators.pipeline import ValidationPipeline
from daffy.validators.rows import RowValidator
from daffy.validators.shape import ShapeValidator
from daffy.validators.spec_parser import parse_column_spec
from daffy.validators.uniqueness import CompositeUniqueValidator, UniqueValidator


def _resolve_columns(specs: list[str], df_columns: list[str]) -> tuple[list[str], dict[str, list[str]]]:
    """Resolve column specs to actual columns. Returns (missing_specs, spec_to_columns)."""
    missing: list[str] = []
    resolved: dict[str, list[str]] = {}

    for spec in specs:
        if is_regex_string(spec):
            pattern = compile_regex_pattern(spec)
            matched = match_column_with_regex(pattern, df_columns)
        else:
            matched = [spec] if spec in df_columns else []

        resolved[spec] = matched
        if not matched:
            missing.append(spec)

    return missing, resolved


def _expand_columns(specs: list[str], resolved: dict[str, list[str]]) -> list[str]:
    """Expand specs to the columns they matched, without repeating a column.

    Two specs can resolve to the same column - `"r/^price/"` and `"price_eur"` both
    match `price_eur`. Emitting it twice makes validators build duplicate expressions,
    which the backends reject.
    """
    return list(dict.fromkeys(col for spec in specs for col in resolved.get(spec, [])))


def _expand_dtypes(specs: dict[str, Any], resolved: dict[str, list[str]]) -> dict[str, Any]:
    """Expand dtype specs. The most specific spec for a column wins."""
    result: dict[str, Any] = {}
    for spec, dtype in specs.items():
        for col in resolved.get(spec, []):
            if col not in result or not is_regex_string(spec):
                result[col] = dtype
    return result


def _expand_checks(specs: dict[str, dict[str, Any]], resolved: dict[str, list[str]]) -> dict[str, dict[str, Any]]:
    """Expand check specs, merging every spec that matched a column.

    `{"r/^price/": {"checks": {"gt": 0}}, "price_eur": {"checks": {"lt": 100}}}` means
    both checks apply to `price_eur`; keeping only one would silently stop validating.
    """
    result: dict[str, dict[str, Any]] = {}
    for spec, checks in specs.items():
        for col in resolved.get(spec, []):
            result[col] = {**result.get(col, {}), **checks}
    return result


def build_validation_pipeline(  # noqa: C901
    columns: Sequence[Any] | Mapping[str, Any] | None,
    strict: bool,
    strict_specs: bool,
    lazy: bool,
    composite_unique: list[list[str]] | None,
    row_validator: type | None,
    min_rows: int | None,
    max_rows: int | None,
    exact_rows: int | None,
    allow_empty: bool,
    df_columns: list[str],
) -> ValidationPipeline:
    """Build a validation pipeline from decorator parameters."""
    pipeline = ValidationPipeline(lazy=lazy)

    has_shape_constraints = min_rows is not None or max_rows is not None or exact_rows is not None or not allow_empty
    if has_shape_constraints:
        pipeline.add(
            ShapeValidator(min_rows=min_rows, max_rows=max_rows, exact_rows=exact_rows, allow_empty=allow_empty)
        )

    if columns is not None:
        spec = parse_column_spec(columns, strict_specs=strict_specs)

        missing_required, resolved_required = _resolve_columns(spec.required_columns, df_columns)
        if missing_required:
            pipeline.add(ColumnsExistValidator(missing_required, df_columns))

        _, resolved_optional = _resolve_columns(spec.optional_columns, df_columns)
        resolved_all = {**resolved_required, **resolved_optional}

        if dtypes := _expand_dtypes(spec.dtype_constraints, resolved_all):
            pipeline.add(DtypeValidator(dtypes))
        if non_nullable := _expand_columns(spec.non_nullable_columns, resolved_all):
            pipeline.add(NullableValidator(non_nullable))
        if unique := _expand_columns(spec.unique_columns, resolved_all):
            pipeline.add(UniqueValidator(unique))
        if checks := _expand_checks(spec.checks_by_column, resolved_all):
            pipeline.add(ChecksValidator(checks))

        if strict:
            all_matched = set()
            for cols in resolved_required.values():
                all_matched.update(cols)
            for cols in resolved_optional.values():
                all_matched.update(cols)
            allowed = set(spec.all_columns) | all_matched
            pipeline.add(StrictModeValidator(allowed))

    if composite_unique:
        pipeline.add(CompositeUniqueValidator(composite_unique))

    if row_validator:
        pipeline.add(RowValidator(row_validator))

    return pipeline
