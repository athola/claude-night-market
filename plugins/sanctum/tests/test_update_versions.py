"""Tests for update_versions.py script."""

import importlib.util
import sys
import tempfile
from pathlib import Path

# Load the script as a module
script_path = Path(__file__).parent.parent / "scripts" / "update_versions.py"
spec = importlib.util.spec_from_file_location("update_versions", script_path)
update_versions = importlib.util.module_from_spec(spec)
sys.modules["update_versions"] = update_versions
spec.loader.exec_module(update_versions)


def test_find_version_files():
    """Test that version files are found correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)

        # Create test structure
        (root / "pyproject.toml").write_text('version = "1.0.0"')
        (root / "plugin1").mkdir()
        (root / "plugin1" / "pyproject.toml").write_text('version = "1.0.0"')
        (root / "plugin1" / "hooks").mkdir()
        (root / "plugin1" / "hooks" / "pyproject.toml").write_text('version = "1.0.0"')

        # Create excluded directories
        (root / ".venv").mkdir()
        (root / ".venv" / "pyproject.toml").write_text('version = "9.9.9"')
        (root / ".uv-cache").mkdir()
        (root / ".uv-cache" / "pyproject.toml").write_text('version = "9.9.9"')
        (root / "node_modules").mkdir()
        (root / "node_modules" / "package.json").write_text('{"version": "9.9.9"}')
        (root / "target").mkdir()
        (root / "target" / "Cargo.toml").write_text('version = "9.9.9"')

        # Default behavior: exclude cache directories
        files = update_versions.find_version_files(root, include_cache=False)

        # Should find 3 files (root, plugin1, plugin1/hooks)
        assert len(files) == 3

        # Should not include cache directories
        assert all(".venv" not in str(f) for f in files)
        assert all(".uv-cache" not in str(f) for f in files)
        assert all("node_modules" not in str(f) for f in files)
        assert all("target" not in str(f) for f in files)


def test_find_version_files_include_cache():
    """Test that --include-cache flag works."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)

        # Create test structure
        (root / "pyproject.toml").write_text('version = "1.0.0"')
        (root / ".venv").mkdir()
        (root / ".venv" / "pyproject.toml").write_text('version = "9.9.9"')

        # With include_cache=True, should find both
        files = update_versions.find_version_files(root, include_cache=True)
        assert len(files) == 2
        assert any(".venv" in str(f) for f in files)


def test_update_pyproject_version():
    """Test pyproject.toml version updating."""
    content = """[project]
name = "test"
version = "1.0.0"
description = "test"
"""

    updated = update_versions.update_pyproject_version(content, "2.0.0")

    assert 'version = "2.0.0"' in updated
    assert 'version = "1.0.0"' not in updated


def test_update_cargo_version():
    """Test Cargo.toml version updating."""
    content = """[package]
name = "test"
version = "1.0.0"
edition = "2021"
"""

    updated = update_versions.update_cargo_version(content, "2.0.0")

    assert 'version = "2.0.0"' in updated
    assert 'version = "1.0.0"' not in updated


def test_update_package_json_version():
    """Test package.json version updating."""
    content = """{
  "name": "test",
  "version": "1.0.0",
  "description": "test"
}
"""

    updated = update_versions.update_package_json_version(content, "2.0.0")

    assert '"version": "2.0.0"' in updated
    assert '"version": "1.0.0"' not in updated


def test_update_version_file_pyproject():
    """Test updating a pyproject.toml file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "pyproject.toml"
        file_path.write_text('version = "1.0.0"')

        # Dry run should not modify file
        result = update_versions.update_version_file(file_path, "2.0.0", dry_run=True)
        assert result is True
        assert 'version = "1.0.0"' in file_path.read_text()

        # Real run should modify file
        result = update_versions.update_version_file(file_path, "2.0.0", dry_run=False)
        assert result is True
        assert 'version = "2.0.0"' in file_path.read_text()


def test_nested_hooks_directory():
    """Test that nested hooks directories are found (memory-palace case)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)

        # Create memory-palace structure
        mp = root / "plugins" / "memory-palace"
        mp.mkdir(parents=True)
        (mp / "pyproject.toml").write_text('version = "1.2.3"')

        hooks = mp / "hooks"
        hooks.mkdir()
        (hooks / "pyproject.toml").write_text('version = "1.0.1"')

        files = update_versions.find_version_files(root, include_cache=False)

        # Should find both files
        assert len(files) == 2
        assert any("memory-palace/pyproject.toml" in str(f) for f in files)
        assert any("memory-palace/hooks/pyproject.toml" in str(f) for f in files)


if __name__ == "__main__":
    # Run tests
    test_find_version_files()
    test_find_version_files_include_cache()
    test_update_pyproject_version()
    test_update_cargo_version()
    test_update_package_json_version()
    test_update_version_file_pyproject()
    test_nested_hooks_directory()
    print("✅ All tests passed!")
