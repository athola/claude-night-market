"""Tests for phantom.cli - command-line interface.

Feature: CLI Entry Point
    As a developer
    I want a CLI to run computer use tasks or check my environment
    So that I can use phantom without writing Python code
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from phantom.cli import build_parser, check_environment, main
from phantom.loop import LoopConfig


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


class TestModelDefault:
    """Feature: one default model, not two.

    The CLI declared its own ``--model`` default and ``LoopConfig``
    declared another. Nothing tied them together, so they drifted: the
    CLI kept a Sonnet generation the library had already moved off, and
    which one a run got depended on whether it came through ``main()``
    or constructed a config directly.

    Asserting the two agree, rather than asserting a literal, is what
    keeps the next model release from reopening the gap.
    """

    def test_cli_default_matches_loop_config_default(self):
        """
        Scenario: The CLI and the library disagree about the default
        Given LoopConfig declares a default model
        When the CLI's --model default is read
        Then the two are the same string
        """
        default = build_parser().get_default("model")
        assert default == LoopConfig.model

    def test_cli_help_text_states_the_real_default(self):
        """
        Scenario: Help text repeats the default as prose
        Given --model's help mentions a default
        When the help string is read
        Then it names the value argparse would actually apply
        """
        action = next(a for a in build_parser()._actions if a.dest == "model")
        assert action.default in action.help
