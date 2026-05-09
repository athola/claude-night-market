"""Tests for update_versions.py script."""

import importlib.util
import sys
import tempfile
from pathlib import Path

# Load the script as a module
script_path = Path(__file__).parent.parent / "scripts" / "update_versions.py"
spec = importlib.util.spec_from_file_location("update_versions", script_path)
assert spec is not None
assert spec.loader is not None
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


def test_update_plugin_json_version():
    """plugin.json / marketplace.json carries the same shape as package.json."""
    content = '{\n  "name": "x",\n  "version": "1.0.0",\n  "x": 1\n}\n'
    updated = update_versions.update_plugin_json_version(content, "9.8.7")
    assert '"version": "9.8.7"' in updated
    assert '"version": "1.0.0"' not in updated


def test_update_init_py_version():
    """__version__ = "X" in a Python module is line-anchored."""
    content = (
        '"""Module docstring."""\n'
        '__version__ = "1.2.3"\n'
        'OTHER = "1.2.3"\n'  # only __version__ should change
    )
    updated = update_versions.update_init_py_version(content, "9.0.0")
    assert '__version__ = "9.0.0"' in updated
    # Ensure we did not touch the unrelated string
    assert 'OTHER = "1.2.3"' in updated


def test_update_openpackage_version_unquoted():
    """openpackage.yml accepts unquoted YAML versions."""
    content = "name: foo\nversion: 1.0.0\nrest: bar\n"
    updated = update_versions.update_openpackage_version(content, "2.0.0")
    assert "version: 2.0.0" in updated
    assert "version: 1.0.0" not in updated


def test_update_openpackage_version_quoted():
    """openpackage.yml also accepts double-quoted values."""
    content = 'name: foo\nversion: "1.0.0"\n'
    updated = update_versions.update_openpackage_version(content, "2.0.0")
    assert "version: 2.0.0" in updated


def test_update_version_file_dispatches_by_filename():
    """update_version_file routes to the right per-format updater."""
    cases = [
        ("Cargo.toml", 'name = "x"\nversion = "1.0.0"\n', '"2.0.0"'),
        ("package.json", '{"name":"x","version":"1.0.0"}', '"2.0.0"'),
        ("plugin.json", '{"version":"1.0.0"}', '"2.0.0"'),
        ("metadata.json", '{"version":"1.0.0"}', '"2.0.0"'),
        ("marketplace.json", '{"version":"1.0.0"}', '"2.0.0"'),
        ("__init__.py", '__version__ = "1.0.0"\n', '"2.0.0"'),
        ("openpackage.yml", "version: 1.0.0\n", "2.0.0"),
    ]
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        for name, content, expected_token in cases:
            p = root / name
            p.write_text(content)
            assert update_versions.update_version_file(p, "2.0.0", dry_run=False), name
            assert expected_token in p.read_text(), name


def test_update_version_file_no_change_returns_false():
    """An unmatched filename leaves the file untouched and reports False."""
    with tempfile.TemporaryDirectory() as tmpdir:
        p = Path(tmpdir) / "random.cfg"
        original = "version = '1.0.0'\n"
        p.write_text(original)
        assert update_versions.update_version_file(p, "2.0.0", dry_run=False) is False
        assert p.read_text() == original


def test_update_version_file_handles_read_error(capsys):
    """Errors reading a file are caught and surfaced on stderr."""
    bogus = Path("/nonexistent/sanctum/bogus_pyproject.toml")
    bogus_named = Path("/tmp/sanctum-pyproject.toml")  # noqa: S108 - test fixture path, not user input
    # Use a path that won't exist as the path object's .name
    # but read_text will fail.
    result = update_versions.update_version_file(bogus, "2.0.0", dry_run=True)
    assert result is False
    err = capsys.readouterr().err
    assert "ERROR updating" in err
    # Sanity: ensure we didn't crash on the named-tmp path either
    if bogus_named.exists():
        bogus_named.unlink()


def test_main_invalid_version_returns_1(monkeypatch, capsys):
    """main() rejects a non-semver argument with stderr message and exit 1."""
    monkeypatch.setattr(sys, "argv", ["update_versions.py", "not-a-version"])
    rc = update_versions.main()
    assert rc == 1
    err = capsys.readouterr().err
    assert "Invalid version format" in err


def test_main_missing_root_returns_1(monkeypatch, capsys):
    """main() rejects a non-existent --root with stderr message and exit 1."""
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "update_versions.py",
            "1.2.3",
            "--root",
            "/path/that/should/not/exist/sanctum-test",
        ],
    )
    rc = update_versions.main()
    assert rc == 1
    err = capsys.readouterr().err
    assert "does not exist" in err


def test_main_dry_run_reports_files_without_modifying(monkeypatch, capsys):
    """main --dry-run lists files and emits the dry-run banner."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        target = root / "pyproject.toml"
        target.write_text('version = "1.0.0"\n')

        monkeypatch.setattr(
            sys,
            "argv",
            [
                "update_versions.py",
                "2.0.0",
                "--root",
                str(root),
                "--dry-run",
            ],
        )
        rc = update_versions.main()
        assert rc == 0
        out = capsys.readouterr().out
        assert "DRY RUN" in out
        assert "Would update" in out
        # File must remain unchanged on dry run
        assert 'version = "1.0.0"' in target.read_text()


def test_main_apply_updates_real_file(monkeypatch, capsys):
    """main() without --dry-run writes new versions to disk."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        target = root / "pyproject.toml"
        target.write_text('version = "1.0.0"\n')

        monkeypatch.setattr(
            sys,
            "argv",
            ["update_versions.py", "2.0.0", "--root", str(root)],
        )
        rc = update_versions.main()
        assert rc == 0
        out = capsys.readouterr().out
        assert "Updated" in out
        assert 'version = "2.0.0"' in target.read_text()


def test_main_no_files_found_returns_0(monkeypatch, capsys):
    """An empty repo prints "No version files" and exits 0."""
    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.setattr(
            sys,
            "argv",
            ["update_versions.py", "2.0.0", "--root", tmpdir],
        )
        rc = update_versions.main()
        assert rc == 0
        out = capsys.readouterr().out
        assert "No version files found" in out


def test_main_include_cache_emits_warning(monkeypatch, capsys):
    """--include-cache adds a cache-directory warning."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "pyproject.toml").write_text('version = "1.0.0"\n')
        monkeypatch.setattr(
            sys,
            "argv",
            [
                "update_versions.py",
                "2.0.0",
                "--root",
                str(root),
                "--include-cache",
                "--dry-run",
            ],
        )
        rc = update_versions.main()
        assert rc == 0
        out = capsys.readouterr().out
        assert "Searching cache directories" in out


def test_init_py_skipped_when_no_dunder_version():
    """find_version_files skips __init__.py without __version__."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        # __init__.py without __version__ should be excluded
        empty_init = root / "pkg" / "__init__.py"
        empty_init.parent.mkdir()
        empty_init.write_text('"""empty package."""\n')
        # __init__.py with __version__ should be included
        keeper = root / "pkg2" / "__init__.py"
        keeper.parent.mkdir()
        keeper.write_text('__version__ = "1.0.0"\n')

        files = update_versions.find_version_files(root)
        assert empty_init not in files
        assert keeper in files


if __name__ == "__main__":
    # Run tests
    test_find_version_files()
    test_find_version_files_include_cache()
    test_update_pyproject_version()
    test_update_cargo_version()
    test_update_package_json_version()
    test_update_version_file_pyproject()
    test_nested_hooks_directory()
    print("All tests passed.")
