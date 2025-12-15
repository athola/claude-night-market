"""Unit tests for CLI module.

Tests the command-line interface entry point.
"""

from __future__ import annotations

import pytest

from parseltongue.cli import main


class TestCLI:
    """Tests for CLI entry point."""

    @pytest.mark.unit
    def test_main_with_no_args(self, capsys) -> None:
        """Given no arguments, CLI should print welcome message and return 0."""
        # When: main is called with no arguments
        result = main([])

        # Then: Returns success exit code
        assert result == 0

        # Then: Prints welcome message
        captured = capsys.readouterr()
        assert "Parseltongue" in captured.out

    @pytest.mark.unit
    def test_main_with_args(self, capsys) -> None:
        """Given arguments, CLI should print them and return 0."""
        # When: main is called with arguments
        result = main(["--help", "test"])

        # Then: Returns success exit code
        assert result == 0

        # Then: Prints args received
        captured = capsys.readouterr()
        assert "Args received" in captured.out
        assert "--help" in captured.out

    @pytest.mark.unit
    def test_main_with_none_uses_sys_argv(self, monkeypatch, capsys) -> None:
        """Given None for argv, CLI should use sys.argv[1:]."""
        # Given: sys.argv is mocked
        monkeypatch.setattr("sys.argv", ["parseltongue", "test-arg"])

        # When: main is called with None
        result = main(None)

        # Then: Returns success exit code
        assert result == 0

        # Then: Uses sys.argv
        captured = capsys.readouterr()
        assert "test-arg" in captured.out
