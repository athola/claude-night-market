"""Tests for the check_docstring_quality pre-commit script.

Feature: Block docstrings that merely restate the function name

As a codebase maintainer
I want pre-commit to flag docstrings that add no information
So that documentation costs are matched by reader value
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from check_docstring_quality import check_file, is_restating_docstring


class TestIsRestatingDocstring:
    """Scenario: is_restating_docstring detects empty paraphrase."""

    @pytest.mark.unit
    def test_flags_exact_name_restate(self) -> None:
        """``def get_user(): \"\"\"Get user.\"\"\"`` is flagged."""
        assert is_restating_docstring("get_user", "Get user.") is True

    @pytest.mark.unit
    def test_flags_articled_restate(self) -> None:
        """``def get_user(): \"\"\"Get the user.\"\"\"`` is flagged."""
        assert is_restating_docstring("get_user", "Get the user.") is True

    @pytest.mark.unit
    def test_flags_third_person_restate(self) -> None:
        """``def parse_config(): \"\"\"Parses config.\"\"\"`` is flagged."""
        assert is_restating_docstring("parse_config", "Parses config.") is True

    @pytest.mark.unit
    def test_passes_substantive_docstring(self) -> None:
        """A docstring that adds information passes."""
        assert (
            is_restating_docstring(
                "get_user",
                "Fetch a user record from the database, returning None if not found.",
            )
            is False
        )

    @pytest.mark.unit
    def test_passes_empty_docstring(self) -> None:
        """An empty docstring is not flagged by THIS rule."""
        assert is_restating_docstring("get_user", "") is False

    @pytest.mark.unit
    def test_passes_underscored_function(self) -> None:
        """Private helpers (``_helper``) without docstrings pass."""
        assert is_restating_docstring("_helper", "") is False

    @pytest.mark.unit
    def test_passes_dunder_method(self) -> None:
        """Dunder methods are skipped (Python convention)."""
        assert is_restating_docstring("__init__", "Initialize.") is False


class TestCheckFile:
    """Scenario: check_file scans a Python source file."""

    @pytest.mark.unit
    def test_flags_restating_docstring(self, tmp_path: Path) -> None:
        """A file with restating docstring yields one hit."""
        f = tmp_path / "bad.py"
        f.write_text('def get_user():\n    """Get user."""\n    return None\n')
        hits = check_file(f)
        assert len(hits) == 1
        assert "get_user" in hits[0]

    @pytest.mark.unit
    def test_clean_file_passes(self, tmp_path: Path) -> None:
        """A file with substantive docstrings yields no hits."""
        f = tmp_path / "good.py"
        f.write_text(
            "def get_user(uid):\n"
            '    """Fetch a user record by id, returning None if absent."""\n'
            "    return None\n"
        )
        assert check_file(f) == []

    @pytest.mark.unit
    def test_no_docstring_passes(self, tmp_path: Path) -> None:
        """Functions without docstrings are not flagged by this rule."""
        f = tmp_path / "ok.py"
        f.write_text("def helper():\n    return 1\n")
        assert check_file(f) == []

    @pytest.mark.unit
    def test_ignores_dunder_methods(self, tmp_path: Path) -> None:
        """``__init__`` and other dunders are skipped."""
        f = tmp_path / "dunder.py"
        f.write_text(
            "class Foo:\n"
            '    def __init__(self):\n        """Initialize."""\n        pass\n'
        )
        assert check_file(f) == []

    @pytest.mark.unit
    def test_ignores_private_helpers(self, tmp_path: Path) -> None:
        """Single-leading-underscore helpers are not flagged."""
        f = tmp_path / "private.py"
        f.write_text('def _helper():\n    """Helper."""\n    pass\n')
        assert check_file(f) == []

    @pytest.mark.unit
    def test_handles_syntax_error(self, tmp_path: Path) -> None:
        """A file with syntax errors is skipped without crashing."""
        f = tmp_path / "broken.py"
        f.write_text("def broken(\n    return\n")
        assert check_file(f) == []
