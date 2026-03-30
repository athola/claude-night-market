# ruff: noqa: D101,D102
"""Tests for leyline.fs — the public file-system walking module.

Feature: Public source-file iterator and filesystem constants

As a plugin developer
I want a stable public API for walking source trees
So that I can reuse leyline's directory-walking logic without
duplicating skip-dir and extension sets.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_SRC = Path(__file__).resolve().parents[3] / "src"
sys.path.insert(0, str(_SRC))

from leyline.fs import (
    FILE_OVERHEAD_TOKENS,
    SKIP_DIRS,
    SOURCE_EXTENSIONS,
    iter_source_files,
)


@pytest.mark.unit
class TestIterSourceFiles:
    """Scenarios for iter_source_files()."""

    @pytest.mark.bdd
    def test_yields_source_files_in_flat_directory(self, tmp_path: Path) -> None:
        """Scenario: Walking a flat directory returns matching files.
        Given a directory with .py and .bin files
        When iter_source_files is called
        Then only the .py file is yielded.
        """
        (tmp_path / "main.py").write_text("print('hello')")
        (tmp_path / "binary.bin").write_text("data")

        found = {p.name for p in iter_source_files(tmp_path)}

        assert found == {"main.py"}

    @pytest.mark.bdd
    def test_skips_default_skip_dirs(self, tmp_path: Path) -> None:
        """Scenario: Common build/cache directories are skipped.
        Given a project tree containing __pycache__, .git, node_modules
        When iter_source_files is called with defaults
        Then files inside those directories are not yielded.
        """
        src = tmp_path / "src"
        src.mkdir()
        (src / "app.py").write_text("pass")

        for skip_dir in ("__pycache__", ".git", "node_modules", ".venv"):
            d = tmp_path / skip_dir
            d.mkdir()
            (d / "ignored.py").write_text("ignored")

        found = {p.name for p in iter_source_files(tmp_path)}

        assert found == {"app.py"}

    @pytest.mark.bdd
    def test_accepts_custom_extensions(self, tmp_path: Path) -> None:
        """Scenario: Caller can supply a custom extension set.
        Given a directory with .py, .go, and .rs files
        When iter_source_files is called with extensions={'.go'}
        Then only the .go file is yielded.
        """
        (tmp_path / "main.py").write_text("pass")
        (tmp_path / "main.go").write_text("package main")
        (tmp_path / "lib.rs").write_text("fn main() {}")

        found = {
            p.name for p in iter_source_files(tmp_path, extensions=frozenset({".go"}))
        }

        assert found == {"main.go"}

    @pytest.mark.bdd
    def test_accepts_custom_skip_dirs(self, tmp_path: Path) -> None:
        """Scenario: Caller can supply a custom skip-dirs set.
        Given a directory tree where 'vendor' should be skipped
        When iter_source_files is called with skip_dirs={'vendor'}
        Then files inside 'vendor' are not yielded.
        """
        (tmp_path / "main.py").write_text("pass")
        vendor = tmp_path / "vendor"
        vendor.mkdir()
        (vendor / "dep.py").write_text("dep")

        found = {
            p.name for p in iter_source_files(tmp_path, skip_dirs=frozenset({"vendor"}))
        }

        assert found == {"main.py"}

    @pytest.mark.bdd
    def test_walks_nested_directories(self, tmp_path: Path) -> None:
        """Scenario: Recursion into nested directories works correctly.
        Given a multi-level directory tree with .py files at each level
        When iter_source_files is called
        Then all .py files are yielded regardless of depth.
        """
        a = tmp_path / "a"
        b = a / "b"
        b.mkdir(parents=True)
        (tmp_path / "root.py").write_text("root")
        (a / "mid.py").write_text("mid")
        (b / "deep.py").write_text("deep")

        found = {p.name for p in iter_source_files(tmp_path)}

        assert found == {"root.py", "mid.py", "deep.py"}

    @pytest.mark.bdd
    def test_extension_matching_is_case_insensitive(self, tmp_path: Path) -> None:
        """Scenario: Extension matching ignores case.
        Given files named app.PY and util.Py
        When iter_source_files is called
        Then both files are yielded because .PY/.Py match .py.
        """
        (tmp_path / "app.PY").write_text("pass")
        (tmp_path / "util.Py").write_text("pass")

        found = {p.name for p in iter_source_files(tmp_path)}

        assert {"app.PY", "util.Py"}.issubset(found)


@pytest.mark.unit
class TestModuleConstants:
    """Scenarios for module-level constants."""

    def test_file_overhead_tokens_is_positive_int(self) -> None:
        """FILE_OVERHEAD_TOKENS must be a positive integer."""
        assert isinstance(FILE_OVERHEAD_TOKENS, int)
        assert FILE_OVERHEAD_TOKENS > 0

    def test_skip_dirs_contains_common_build_artifacts(self) -> None:
        """SKIP_DIRS must include the most common build/cache directories."""
        for expected in (
            "__pycache__",
            ".git",
            "node_modules",
            ".venv",
            "dist",
            "build",
        ):
            assert expected in SKIP_DIRS, f"{expected!r} missing from SKIP_DIRS"

    def test_source_extensions_contains_common_types(self) -> None:
        """SOURCE_EXTENSIONS must cover common code and config file types."""
        for expected in (".py", ".js", ".ts", ".md", ".json", ".yaml", ".toml"):
            assert expected in SOURCE_EXTENSIONS, (
                f"{expected!r} missing from SOURCE_EXTENSIONS"
            )
