"""Configuration handling for DAFFY."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from types import MappingProxyType
from typing import Any

import tomli

# Configuration keys
_KEY_STRICT = "strict"
_KEY_LAZY = "lazy"
_KEY_ROW_VALIDATION_MAX_ERRORS = "row_validation_max_errors"
_KEY_CHECKS_MAX_SAMPLES = "checks_max_samples"
_KEY_ALLOW_EMPTY = "allow_empty"

# Default values
_DEFAULT_STRICT = False
_DEFAULT_LAZY = False
_DEFAULT_MAX_ERRORS = 5
_DEFAULT_CHECKS_MAX_SAMPLES = 5
_DEFAULT_ALLOW_EMPTY = True


def _validate_bool_config(daffy_config: dict[str, Any], key: str) -> bool | None:
    """Validate and extract a boolean config value.

    Returns None if key not present. Raises TypeError if value is not a boolean.
    """
    if key not in daffy_config:
        return None
    value = daffy_config[key]
    if not isinstance(value, bool):
        raise TypeError(f"Config '{key}' must be a boolean, got {type(value).__name__}: {value!r}")
    return value


def _validate_int_config(daffy_config: dict[str, Any], key: str, min_value: int = 1) -> int | None:
    """Validate and extract an integer config value.

    Returns None if key not present. Raises TypeError/ValueError if invalid.
    """
    if key not in daffy_config:
        return None
    value = daffy_config[key]
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"Config '{key}' must be an integer, got {type(value).__name__}: {value!r}")
    if value < min_value:
        raise ValueError(f"Config '{key}' must be >= {min_value}, got {value}")
    return value


_BOOL_KEYS = [_KEY_STRICT, _KEY_LAZY, _KEY_ALLOW_EMPTY]
_INT_KEYS = [_KEY_ROW_VALIDATION_MAX_ERRORS, _KEY_CHECKS_MAX_SAMPLES]

_DEFAULTS: dict[str, Any] = {
    _KEY_STRICT: _DEFAULT_STRICT,
    _KEY_LAZY: _DEFAULT_LAZY,
    _KEY_ROW_VALIDATION_MAX_ERRORS: _DEFAULT_MAX_ERRORS,
    _KEY_CHECKS_MAX_SAMPLES: _DEFAULT_CHECKS_MAX_SAMPLES,
    _KEY_ALLOW_EMPTY: _DEFAULT_ALLOW_EMPTY,
}


def load_config() -> dict[str, Any]:
    """Load daffy configuration from pyproject.toml."""
    config = dict(_DEFAULTS)

    config_path = find_config_file()
    if not config_path:
        return config

    try:
        with Path(config_path).open("rb") as f:
            daffy_config = tomli.load(f).get("tool", {}).get("daffy", {})

        for key in _BOOL_KEYS:
            if (value := _validate_bool_config(daffy_config, key)) is not None:
                config[key] = value

        for key in _INT_KEYS:
            if (value := _validate_int_config(daffy_config, key)) is not None:
                config[key] = value
    except (FileNotFoundError, tomli.TOMLDecodeError):
        pass

    return config


def find_config_file() -> str | None:
    """Find pyproject.toml in the current working directory."""
    path = Path.cwd() / "pyproject.toml"
    return str(path) if path.is_file() else None


@lru_cache(maxsize=1)
def get_config() -> MappingProxyType[str, Any]:
    """Get the daffy configuration, cached after first load.

    Returns an immutable view of the configuration to prevent accidental modification.
    """
    return MappingProxyType(load_config())


def clear_config_cache() -> None:
    """Clear the configuration cache. Primarily for testing."""
    get_config.cache_clear()


def _get_bool_config(param: bool | None, key: str) -> bool:
    """Return param if provided, otherwise config value."""
    if param is not None:
        return param
    return bool(get_config()[key])


def _get_int_config(param: int | None, key: str, min_value: int = 1) -> int:
    """Return param if provided, otherwise config value. Validates minimum."""
    value = param if param is not None else int(get_config()[key])
    if value < min_value:
        raise ValueError(f"{key} must be >= {min_value}, got {value}")
    return value


def get_strict(strict_param: bool | None = None) -> bool:
    """Get the strict mode setting, with explicit parameter taking precedence over configuration.

    Args:
        strict_param: Explicitly provided strict parameter value, or None to use config

    Returns:
        bool: The effective strict mode setting

    """
    return _get_bool_config(strict_param, _KEY_STRICT)


def get_lazy(lazy_param: bool | None = None) -> bool:
    """Get the lazy mode setting, with explicit parameter taking precedence over configuration.

    When lazy=True, validation collects all errors before raising instead of stopping at the first.

    Args:
        lazy_param: Explicitly provided lazy parameter value, or None to use config

    Returns:
        bool: The effective lazy mode setting

    """
    return _get_bool_config(lazy_param, _KEY_LAZY)


def get_row_validation_max_errors() -> int:
    """Get max_errors setting for row validation."""
    return _get_int_config(None, _KEY_ROW_VALIDATION_MAX_ERRORS)


def get_checks_max_samples(max_samples: int | None = None) -> int:
    """Get max_samples setting for value checks."""
    return _get_int_config(max_samples, _KEY_CHECKS_MAX_SAMPLES)


def get_allow_empty(allow_empty_param: bool | None = None) -> bool:
    """Get the allow_empty setting, with explicit parameter taking precedence over configuration.

    When allow_empty=False, empty DataFrames (0 rows) will raise an error.

    Args:
        allow_empty_param: Explicitly provided allow_empty parameter value, or None to use config

    Returns:
        bool: The effective allow_empty setting

    """
    return _get_bool_config(allow_empty_param, _KEY_ALLOW_EMPTY)
