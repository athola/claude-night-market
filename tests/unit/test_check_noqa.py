"""Tests for the check_noqa pre-commit script.

Feature: Block inline lint suppressions at commit time

As a codebase maintainer
I want pre-commit to reject inline lint suppression comments
So that suppressions use project config files instead
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from check_noqa import check_file, main


class TestCheckFile:
    """Scenario: check_file detects suppression directives."""

    @pytest.mark.unit
    def test_detects_noqa(self, tmp_path: Path) -> None:
        """Given a file with # noqa, When checked, Then it reports the hit."""
        f = tmp_path / "bad.py"
        f.write_text("x = 1  # noqa: E501\n")
        hits = check_file(f)
        assert len(hits) == 1
        assert "# noqa" in hits[0]

    @pytest.mark.unit
    def test_detects_type_ignore(self, tmp_path: Path) -> None:
        """Given a file with # type: ignore, When checked, Then flagged."""
        f = tmp_path / "bad.py"
        f.write_text("x: int = 'y'  # type: ignore\n")
        hits = check_file(f)
        assert len(hits) == 1
        assert "type: ignore" in hits[0]

    @pytest.mark.unit
    def test_clean_file_passes(self, tmp_path: Path) -> None:
        """Given a clean file, When checked, Then no hits."""
        f = tmp_path / "good.py"
        f.write_text("x = 1\ny = 2\n")
        assert check_file(f) == []

    @pytest.mark.unit
    def test_ignores_patterns_in_string_literals(self, tmp_path: Path) -> None:
        """Given a file with # noqa inside a string, When checked, Then no hits."""
        f = tmp_path / "guard.py"
        f.write_text(
            'PATTERNS = [(re.compile(r"#\\s*noqa\\b"), "# noqa")]\n'
            'label = "# type: ignore"\n'
        )
        assert check_file(f) == []

    @pytest.mark.unit
    def test_detects_actual_comment_not_string(self, tmp_path: Path) -> None:
        """Given a real noqa comment next to a string, When checked, Then flagged."""
        f = tmp_path / "mixed.py"
        f.write_text('x = "hello"  # noqa: E501\n')
        hits = check_file(f)
        assert len(hits) == 1

    @pytest.mark.unit
    def test_ignores_patterns_in_docstrings(self, tmp_path: Path) -> None:
        """Given a file with # noqa inside a docstring, When checked, Then no hits."""
        f = tmp_path / "guard.py"
        f.write_text(
            '"""Module that references ``# noqa`` and ``# type: ignore``."""\nx = 1\n'
        )
        assert check_file(f) == []

    @pytest.mark.unit
    def test_ignores_multiline_docstring(self, tmp_path: Path) -> None:
        """Given # noqa inside a multi-line docstring, When checked, Then no hits."""
        f = tmp_path / "multiline.py"
        f.write_text(
            '"""Hook that detects:\n'
            "- Python: # noqa, # type: ignore\n"
            "- Rust: #[allow(...)]\n"
            '"""\n'
            "x = 1\n"
        )
        assert check_file(f) == []

    @pytest.mark.unit
    def test_missing_file_passes(self, tmp_path: Path) -> None:
        """Given a nonexistent file, When checked, Then no hits."""
        f = tmp_path / "missing.py"
        assert check_file(f) == []


class TestMain:
    """Scenario: main returns correct exit codes."""

    @pytest.mark.unit
    def test_returns_1_on_suppression(self, tmp_path: Path) -> None:
        """Given files with suppressions, When main runs, Then exits 1."""
        f = tmp_path / "bad.py"
        f.write_text("x = 1  # noqa\n")
        assert main([str(f)]) == 1

    @pytest.mark.unit
    def test_returns_0_on_clean(self, tmp_path: Path) -> None:
        """Given clean files, When main runs, Then exits 0."""
        f = tmp_path / "good.py"
        f.write_text("x = 1\n")
        assert main([str(f)]) == 0

    @pytest.mark.unit
    def test_returns_0_on_empty(self) -> None:
        """Given no files, When main runs, Then exits 0."""
        assert main([]) == 0
