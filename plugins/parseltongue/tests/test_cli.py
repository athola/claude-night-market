"""Unit tests for CLI module.

Tests the command-line interface entry point.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from parseltongue.cli import main


class TestCLI:
    """Tests for CLI entry point."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_main_with_no_args(self, capsys) -> None:
        """Given no arguments, CLI should print usage and return 0."""
        result = main([])

        assert result == 0

        captured = capsys.readouterr()
        assert "Parseltongue" in captured.out
        assert "Usage" in captured.out

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_main_with_nonexistent_path(self, capsys) -> None:
        """Given a nonexistent path, CLI should return 1."""
        result = main(["check-compat", "/nonexistent/path.py"])

        assert result == 1

        captured = capsys.readouterr()
        assert "does not exist" in captured.err

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_main_analyze_async(self, capsys) -> None:
        """Given a valid file, analyze-async returns results."""
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
            f.write("async def hello(): await something()\n")
            f.flush()
            result = main(["analyze-async", f.name])

        assert result == 0
        captured = capsys.readouterr()
        assert "async_functions" in captured.out

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_main_check_compat(self, capsys) -> None:
        """Given a valid file, check-compat returns results."""
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
            f.write("x: int = 5\n")
            f.flush()
            result = main(["check-compat", f.name])

        assert result == 0
        captured = capsys.readouterr()
        assert "minimum_version" in captured.out

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_main_detect_patterns(self, capsys) -> None:
        """Given a valid file, detect-patterns returns results."""
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
            f.write("class Foo:\n    pass\n")
            f.flush()
            result = main(["detect-patterns", f.name])

        assert result == 0
        captured = capsys.readouterr()
        assert "patterns" in captured.out

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_main_test_guide(self, capsys) -> None:
        """Given a valid file, test-guide returns results."""
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
            f.write("def hello(): pass\n")
            f.flush()
            result = main(["test-guide", f.name])

        assert result == 0
        captured = capsys.readouterr()
        assert "recommendations" in captured.out

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_main_transform(self, capsys) -> None:
        """Given a valid file, transform returns results."""
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
            f.write("x = dict()\n")
            f.flush()
            result = main(["transform", f.name])

        assert result == 0
        captured = capsys.readouterr()
        assert "transformed_code" in captured.out

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_main_directory_input(self, capsys) -> None:
        """Given a directory, CLI reads all .py files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir) / "sample.py"
            p.write_text("async def foo(): await bar()\n")
            result = main(["analyze-async", tmpdir])

        assert result == 0
        captured = capsys.readouterr()
        assert "async_functions" in captured.out

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_main_empty_directory(self, capsys) -> None:
        """Given an empty directory, CLI returns 1."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = main(["analyze-async", tmpdir])

        assert result == 1

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_main_with_none_uses_sys_argv(self, monkeypatch, capsys) -> None:
        """Given None for argv, CLI should use sys.argv[1:]."""
        monkeypatch.setattr("sys.argv", ["parseltongue"])

        result = main(None)

        assert result == 0

        captured = capsys.readouterr()
        assert "Parseltongue" in captured.out
