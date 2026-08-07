"""Configuration handling for DAFFY."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from types import MappingProxyType
from typing import Any, NamedTuple

import tomli

# Configuration keys
_KEY_STRICT = "strict"
_KEY_LAZY = "lazy"
_KEY_STRICT_SPECS = "strict_specs"
_KEY_ROW_VALIDATION_MAX_ERRORS = "row_validation_max_errors"
_KEY_CHECKS_MAX_SAMPLES = "checks_max_samples"
_KEY_ALLOW_EMPTY = "allow_empty"

# Default values
_DEFAULT_STRICT = False
_DEFAULT_LAZY = False
_DEFAULT_STRICT_SPECS = False
_DEFAULT_MAX_ERRORS = 5
_DEFAULT_CHECKS_MAX_SAMPLES = 5
_DEFAULT_ALLOW_EMPTY = True


_DEFAULTS: dict[str, Any] = {
    _KEY_STRICT: _DEFAULT_STRICT,
    _KEY_LAZY: _DEFAULT_LAZY,
    _KEY_STRICT_SPECS: _DEFAULT_STRICT_SPECS,
    _KEY_ROW_VALIDATION_MAX_ERRORS: _DEFAULT_MAX_ERRORS,
    _KEY_CHECKS_MAX_SAMPLES: _DEFAULT_CHECKS_MAX_SAMPLES,
    _KEY_ALLOW_EMPTY: _DEFAULT_ALLOW_EMPTY,
}


def load_config(cwd: Path | None = None) -> dict[str, Any]:
    """Load daffy configuration from pyproject.toml."""
    config = dict(_DEFAULTS)

    config_path = find_config_file(cwd)
    if not config_path:
        return config

    try:
        with Path(config_path).open("rb") as f:
            daffy_config = tomli.load(f).get("tool", {}).get("daffy", {})

        for key, default_value in _DEFAULTS.items():
            if key in daffy_config:
                val = daffy_config[key]
                if isinstance(default_value, bool):
                    if not isinstance(val, bool):
                        raise TypeError(f"Config '{key}' must be a boolean, got {type(val).__name__}: {val!r}")
                else:  # isinstance(default_value, int)
                    if not isinstance(val, int) or isinstance(val, bool):
                        raise TypeError(f"Config '{key}' must be an integer, got {type(val).__name__}: {val!r}")
                    if val < 1:
                        raise ValueError(f"Config '{key}' must be >= 1, got {val}")
                config[key] = val
    except (FileNotFoundError, tomli.TOMLDecodeError):
        pass

    return config


def find_config_file(cwd: Path | None = None) -> str | None:
    """Find pyproject.toml in the current working directory or any parent directory."""
    current_dir = cwd.resolve() if cwd is not None else Path.cwd().resolve()
    for parent in [current_dir, *current_dir.parents]:
        path = parent / "pyproject.toml"
        if path.is_file():
            return str(path)
    return None


@lru_cache(maxsize=128)
def _get_config_for_cwd(cwd: str) -> MappingProxyType[str, Any]:
    """Load and cache configuration for a specific current working directory."""
    return MappingProxyType(load_config(Path(cwd)))


def get_config() -> MappingProxyType[str, Any]:
    """Get the daffy configuration, cached by current working directory.

    Keyed on the unresolved working directory: resolving symlinks costs a syscall on
    every validated call, and `find_config_file` resolves the path anyway on a cache
    miss. Two aliases of the same directory get two cache entries with equal contents.

    Returns an immutable view of the configuration to prevent accidental modification.
    """
    return _get_config_for_cwd(str(Path.cwd()))


def clear_config_cache() -> None:
    """Clear the configuration cache. Primarily for testing."""
    _get_config_for_cwd.cache_clear()


class DecoratorSettings(NamedTuple):
    """Settings resolved for one validation run."""

    strict: bool
    strict_specs: bool
    lazy: bool
    allow_empty: bool


def resolve_decorator_settings(strict: bool | None, lazy: bool | None, allow_empty: bool | None) -> DecoratorSettings:
    """Resolve the decorator settings with a single configuration lookup.

    Reading the config resolves the current working directory, so doing it once per
    validation instead of once per setting keeps that cost off the hot path.
    """
    config = get_config()
    return DecoratorSettings(
        strict=strict if strict is not None else bool(config[_KEY_STRICT]),
        strict_specs=bool(config[_KEY_STRICT_SPECS]),
        lazy=lazy if lazy is not None else bool(config[_KEY_LAZY]),
        allow_empty=allow_empty if allow_empty is not None else bool(config[_KEY_ALLOW_EMPTY]),
    )


def _get_int_config(param: int | None, key: str, min_value: int = 1) -> int:
    """Return param if provided, otherwise config value. Validates minimum."""
    value = param if param is not None else int(get_config()[key])
    if value < min_value:
        raise ValueError(f"{key} must be >= {min_value}, got {value}")
    return value


def get_row_validation_max_errors() -> int:
    """Get max_errors setting for row validation."""
    return _get_int_config(None, _KEY_ROW_VALIDATION_MAX_ERRORS)


def get_checks_max_samples(max_samples: int | None = None) -> int:
    """Get max_samples setting for value checks."""
    return _get_int_config(max_samples, _KEY_CHECKS_MAX_SAMPLES)
