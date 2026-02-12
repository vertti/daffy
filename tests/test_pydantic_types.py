"""Tests for optional Pydantic dependency support."""

from importlib.metadata import PackageNotFoundError, metadata

from daffy.pydantic_types import (
    HAS_PYDANTIC,
    BaseModel,
    ValidationError,
    require_pydantic,
)


def test_pydantic_availability() -> None:
    assert HAS_PYDANTIC is True


def test_require_pydantic() -> None:
    require_pydantic()


def test_pydantic_imports_available() -> None:
    assert BaseModel is not None
    assert ValidationError is not None


def test_pydantic_extra_declared_in_pyproject() -> None:
    try:
        meta = metadata("daffy")
    except PackageNotFoundError as exc:  # pragma: no cover
        raise AssertionError("Package metadata for 'daffy' not found") from exc

    provides_extra = meta.get_all("Provides-Extra") or []
    assert "pydantic" in provides_extra
