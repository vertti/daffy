"""Pipeline builder - assembles validators from decorator parameters."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from daffy.patterns import compile_regex_pattern, is_regex_string, match_column_with_regex

if TYPE_CHECKING:
    from collections.abc import Sequence

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


def _expand_specs(specs: dict[str, Any] | list[str], resolved: dict[str, list[str]]) -> dict[str, Any] | list[str]:
    """Expand column specs to actual column names using resolution map."""
    if isinstance(specs, dict):
        result: dict[str, Any] = {}
        for spec, value in specs.items():
            for col in resolved.get(spec, []):
                result[col] = value
        return result

    result_list: list[str] = []
    for spec in specs:
        result_list.extend(resolved.get(spec, []))
    return result_list


def build_validation_pipeline(  # noqa: C901
    columns: Sequence[Any] | dict[Any, Any] | None,
    strict: bool,
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

    if columns:
        spec = parse_column_spec(columns)

        missing_required, resolved_required = _resolve_columns(spec.required_columns, df_columns)
        if missing_required:
            pipeline.add(ColumnsExistValidator(missing_required, df_columns))

        _, resolved_optional = _resolve_columns(spec.optional_columns, df_columns)
        _, resolved_all = _resolve_columns(spec.all_columns, df_columns)

        validators = [
            (spec.dtype_constraints, DtypeValidator),
            (spec.non_nullable_columns, NullableValidator),
            (spec.unique_columns, UniqueValidator),
            (spec.checks_by_column, ChecksValidator),
        ]
        for source, validator_cls in validators:
            if source and (expanded := _expand_specs(source, resolved_all)):
                pipeline.add(validator_cls(expanded))  # type: ignore[arg-type]

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
