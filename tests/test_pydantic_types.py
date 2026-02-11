"""Tests for optional Pydantic dependency support."""

from pathlib import Path

import tomli

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
    pyproject_path = Path(__file__).resolve().parents[1] / "pyproject.toml"
    with pyproject_path.open("rb") as f:
        project = tomli.load(f)["project"]

    optional_deps = project.get("optional-dependencies", {})
    assert "pydantic" in optional_deps
    assert "pydantic>=2.4.0" in optional_deps["pydantic"]
