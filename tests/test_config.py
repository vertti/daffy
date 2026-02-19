"""Tests for the daffy configuration system."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from daffy.config import clear_config_cache, get_checks_max_samples, get_config, get_strict, get_strict_specs


def test_get_config_default() -> None:
    """Test that get_config returns default values when no config file is found."""
    with patch("daffy.config.find_config_file", return_value=None):
        config = get_config()
        assert config["strict"] is False


def test_get_strict_default() -> None:
    """Test that get_strict returns default value when no explicit value is provided."""
    with patch("daffy.config.get_config", return_value={"strict": False}):
        assert get_strict() is False

    with patch("daffy.config.get_config", return_value={"strict": True}):
        assert get_strict() is True


def test_get_strict_override() -> None:
    """Test that get_strict respects explicitly provided value."""
    with patch("daffy.config.get_config", return_value={"strict": False}):
        assert get_strict(True) is True

    with patch("daffy.config.get_config", return_value={"strict": True}):
        assert get_strict(False) is False


def test_get_strict_specs_default() -> None:
    with patch("daffy.config.get_config", return_value={"strict_specs": False}):
        assert get_strict_specs() is False

    with patch("daffy.config.get_config", return_value={"strict_specs": True}):
        assert get_strict_specs() is True


def test_get_strict_specs_override() -> None:
    with patch("daffy.config.get_config", return_value={"strict_specs": False}):
        assert get_strict_specs(True) is True

    with patch("daffy.config.get_config", return_value={"strict_specs": True}):
        assert get_strict_specs(False) is False


def test_config_from_pyproject() -> None:
    """Test loading configuration from pyproject.toml."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a mock pyproject.toml file
        with open(os.path.join(tmpdir, "pyproject.toml"), "w") as f:
            f.write("""
[tool.daffy]
strict = true
            """)

        # Test loading from this file
        with patch("daffy.config.Path.cwd", return_value=Path(tmpdir)):
            from daffy.config import load_config

            clear_config_cache()

            config = load_config()
            assert config["strict"] is True


def test_strict_specs_from_pyproject() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "pyproject.toml"), "w") as f:
            f.write("""
[tool.daffy]
strict_specs = true
            """)

        with patch("daffy.config.Path.cwd", return_value=Path(tmpdir)):
            from daffy.config import load_config

            clear_config_cache()
            config = load_config()
            assert config["strict_specs"] is True


def test_config_strict_specs_string_raises_error() -> None:
    """Test that non-boolean strict_specs config raises TypeError."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "pyproject.toml"), "w") as f:
            f.write("""
[tool.daffy]
strict_specs = "true"
            """)

        with patch("daffy.config.Path.cwd", return_value=Path(tmpdir)):
            from daffy.config import load_config

            clear_config_cache()

            with pytest.raises(TypeError) as exc_info:
                load_config()
            assert "strict_specs" in str(exc_info.value)
            assert "boolean" in str(exc_info.value)


def test_load_config_returns_default_when_file_not_found() -> None:
    with patch("daffy.config.find_config_file", return_value="/nonexistent/pyproject.toml"):
        config = get_config()
        assert config["strict"] is False


def test_load_config_returns_default_when_toml_malformed() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "pyproject.toml"), "w") as f:
            f.write("invalid toml [[[")

        with patch("daffy.config.Path.cwd", return_value=Path(tmpdir)):
            clear_config_cache()

            config = get_config()
            assert config["strict"] is False


def test_find_config_file_returns_none_when_no_pyproject_exists() -> None:
    with tempfile.TemporaryDirectory() as tmpdir, patch("daffy.config.Path.cwd", return_value=Path(tmpdir)):
        from daffy.config import find_config_file

        result = find_config_file()
        assert result is None


def test_find_config_file_searches_parent_directories() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir) / "project"
        nested_dir = project_dir / "src" / "module"
        nested_dir.mkdir(parents=True)
        pyproject_path = project_dir / "pyproject.toml"
        pyproject_path.write_text("[tool.daffy]\nstrict = true\n", encoding="utf-8")

        with patch("daffy.config.Path.cwd", return_value=nested_dir):
            from daffy.config import find_config_file

            result = find_config_file()
            assert result == str(pyproject_path.resolve())


def test_find_config_file_prefers_nearest_parent() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir) / "project"
        package_dir = project_dir / "pkg"
        nested_dir = package_dir / "tests"
        nested_dir.mkdir(parents=True)

        root_pyproject = project_dir / "pyproject.toml"
        package_pyproject = package_dir / "pyproject.toml"
        root_pyproject.write_text("[tool.daffy]\nstrict = false\n", encoding="utf-8")
        package_pyproject.write_text("[tool.daffy]\nstrict = true\n", encoding="utf-8")

        with patch("daffy.config.Path.cwd", return_value=nested_dir):
            from daffy.config import find_config_file

            result = find_config_file()
            assert result == str(package_pyproject.resolve())


def test_load_config_without_strict_setting() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "pyproject.toml"), "w") as f:
            f.write("""
[tool.daffy]
other_setting = "value"
            """)

        with patch("daffy.config.Path.cwd", return_value=Path(tmpdir)):
            clear_config_cache()

            config = get_config()
            assert config["strict"] is False


def test_load_config_daffy_section_without_strict() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "pyproject.toml"), "w") as f:
            f.write("""
[tool.daffy]
some_other_setting = "value"
            """)

        with patch("daffy.config.Path.cwd", return_value=Path(tmpdir)):
            clear_config_cache()

            config = get_config()
            assert config["strict"] is False


def test_get_checks_max_samples_default() -> None:
    with patch("daffy.config.get_config", return_value={"checks_max_samples": 5}):
        assert get_checks_max_samples() == 5


def test_get_checks_max_samples_override() -> None:
    with patch("daffy.config.get_config", return_value={"checks_max_samples": 5}):
        assert get_checks_max_samples(10) == 10


def test_checks_max_samples_from_pyproject() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "pyproject.toml"), "w") as f:
            f.write("""
[tool.daffy]
checks_max_samples = 10
            """)

        with patch("daffy.config.Path.cwd", return_value=Path(tmpdir)):
            from daffy.config import load_config

            clear_config_cache()

            config = load_config()
            assert config["checks_max_samples"] == 10


def test_config_strict_string_raises_error() -> None:
    """Test that non-boolean strict config raises TypeError."""
    import pytest

    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "pyproject.toml"), "w") as f:
            f.write("""
[tool.daffy]
strict = "false"
            """)

        with patch("daffy.config.Path.cwd", return_value=Path(tmpdir)):
            from daffy.config import load_config

            clear_config_cache()

            with pytest.raises(TypeError) as exc_info:
                load_config()
            assert "strict" in str(exc_info.value)
            assert "boolean" in str(exc_info.value)


def test_config_max_samples_string_raises_error() -> None:
    """Test that non-integer max_samples config raises TypeError."""
    import pytest

    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "pyproject.toml"), "w") as f:
            f.write("""
[tool.daffy]
checks_max_samples = "five"
            """)

        with patch("daffy.config.Path.cwd", return_value=Path(tmpdir)):
            from daffy.config import load_config

            clear_config_cache()

            with pytest.raises(TypeError) as exc_info:
                load_config()
            assert "checks_max_samples" in str(exc_info.value)
            assert "integer" in str(exc_info.value)


def test_config_max_samples_zero_raises_error() -> None:
    """Test that max_samples < 1 raises ValueError."""
    import pytest

    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "pyproject.toml"), "w") as f:
            f.write("""
[tool.daffy]
checks_max_samples = 0
            """)

        with patch("daffy.config.Path.cwd", return_value=Path(tmpdir)):
            from daffy.config import load_config

            clear_config_cache()

            with pytest.raises(ValueError) as exc_info:
                load_config()
            assert "checks_max_samples" in str(exc_info.value)
            assert ">= 1" in str(exc_info.value)


def test_config_max_samples_one_passes() -> None:
    """Test that max_samples = 1 is valid (boundary value)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "pyproject.toml"), "w") as f:
            f.write("""
[tool.daffy]
checks_max_samples = 1
            """)

        with patch("daffy.config.Path.cwd", return_value=Path(tmpdir)):
            from daffy.config import load_config

            clear_config_cache()

            config = load_config()
            assert config["checks_max_samples"] == 1


def test_config_row_validation_max_errors_one_passes() -> None:
    """Test that row_validation_max_errors = 1 is valid (boundary value)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "pyproject.toml"), "w") as f:
            f.write("""
[tool.daffy]
row_validation_max_errors = 1
            """)

        with patch("daffy.config.Path.cwd", return_value=Path(tmpdir)):
            from daffy.config import load_config

            clear_config_cache()

            config = load_config()
            assert config["row_validation_max_errors"] == 1


def test_config_row_validation_max_errors_zero_raises_error() -> None:
    """Test that row_validation_max_errors < 1 raises ValueError."""
    import pytest

    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "pyproject.toml"), "w") as f:
            f.write("""
[tool.daffy]
row_validation_max_errors = 0
            """)

        with patch("daffy.config.Path.cwd", return_value=Path(tmpdir)):
            from daffy.config import load_config

            clear_config_cache()

            with pytest.raises(ValueError) as exc_info:
                load_config()
            assert "row_validation_max_errors" in str(exc_info.value)
            assert ">= 1" in str(exc_info.value)


def test_get_config_cache_isolated_by_cwd() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir) / "project"
        nested_dir = project_dir / "src"
        external_dir = Path(tmpdir) / "external"
        nested_dir.mkdir(parents=True)
        external_dir.mkdir(parents=True)

        (project_dir / "pyproject.toml").write_text("[tool.daffy]\nstrict = true\n", encoding="utf-8")

        clear_config_cache()
        with patch("daffy.config.Path.cwd", return_value=nested_dir):
            nested_config = get_config()
            assert nested_config["strict"] is True

        with patch("daffy.config.Path.cwd", return_value=external_dir):
            external_config = get_config()
            assert external_config["strict"] is False


def test_get_config_uses_cache_for_same_cwd() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        pyproject_path = Path(tmpdir) / "pyproject.toml"
        pyproject_path.write_text("[tool.daffy]\nstrict = true\n", encoding="utf-8")

        from daffy.config import load_config

        clear_config_cache()
        with (
            patch("daffy.config.Path.cwd", return_value=Path(tmpdir)),
            patch("daffy.config.load_config", wraps=load_config) as mocked_load_config,
        ):
            first = get_config()
            second = get_config()

            assert first["strict"] is True
            assert second["strict"] is True
            assert mocked_load_config.call_count == 1
