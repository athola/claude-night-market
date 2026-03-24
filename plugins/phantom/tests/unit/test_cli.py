"""Tests for phantom.cli - command-line interface.

Feature: CLI Entry Point
    As a developer
    I want a CLI to run computer use tasks or check my environment
    So that I can use phantom without writing Python code
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from phantom.cli import check_environment, main


class TestCheckEnvironment:
    """Feature: Environment diagnostics via CLI."""

    @patch("phantom.cli.check_display_environment")
    def test_prints_tool_availability(self, mock_check, capsys):
        """
        Scenario: Environment check
        Given all tools available
        When check_environment runs
        Then it prints tool status
        """
        mock_check.return_value = {
            "display": ":1",
            "wayland_display": "",
            "has_display": True,
            "tools": {"xdotool": True, "scrot": True, "xclip": True},
            "all_tools_available": True,
        }
        check_environment()
        out = capsys.readouterr().out
        assert "DISPLAY" in out
        assert "OK" in out
        assert "All required tools" in out

    @patch("phantom.cli.check_display_environment")
    def test_shows_missing_tools(self, mock_check, capsys):
        """
        Scenario: Missing tools
        Given xdotool is missing
        When check_environment runs
        Then it shows MISSING and install instructions
        """
        mock_check.return_value = {
            "display": "",
            "wayland_display": "",
            "has_display": False,
            "tools": {"xdotool": False, "scrot": False, "xclip": False},
            "all_tools_available": False,
        }
        check_environment()
        out = capsys.readouterr().out
        assert "MISSING" in out
        assert "sudo apt install" in out


class TestMain:
    """Feature: CLI argument parsing."""

    def test_no_args_shows_help(self):
        """
        Scenario: No arguments
        Given no CLI arguments
        When main() runs
        Then it exits with code 1
        """
        with patch("sys.argv", ["phantom"]):
            with pytest.raises(SystemExit) as exc:
                main()
            assert exc.value.code == 1

    def test_check_flag_calls_check(self):
        """
        Scenario: --check flag
        Given --check argument
        When main() runs
        Then it calls check_environment and returns
        """
        with (
            patch("sys.argv", ["phantom", "--check"]),
            patch("phantom.cli.check_environment") as mock,
        ):
            main()
            mock.assert_called_once()

    def test_missing_api_key_exits(self):
        """
        Scenario: No API key
        Given ANTHROPIC_API_KEY is not set
        When main() runs with a task
        Then it exits with error
        """
        with (
            patch("sys.argv", ["phantom", "do something"]),
            patch.dict("os.environ", {}, clear=True),
            pytest.raises(SystemExit),
        ):
            main()
