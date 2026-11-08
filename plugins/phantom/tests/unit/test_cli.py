"""Tests for phantom.cli - command-line interface.

Feature: CLI Entry Point
    As a developer
    I want a CLI to run computer use tasks or check my environment
    So that I can use phantom without writing Python code
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from phantom.cli import _ask_before_acting, build_parser, check_environment, main
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
            pytest.raises(SystemExit) as exc,
        ):
            main()
        assert exc.value.code == 1


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


class TestRunTask:
    """Feature: a task on the command line runs the agent loop."""

    def test_missing_api_key_names_the_variable(self, capsys, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.setattr("sys.argv", ["phantom", "do something"])
        with pytest.raises(SystemExit):
            main()
        assert "ANTHROPIC_API_KEY" in capsys.readouterr().out

    def test_blank_task_exits_before_calling_the_api(self, capsys, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        monkeypatch.setattr("sys.argv", ["phantom", ""])

        def no_client(api_key):
            raise AssertionError("API client built for a blank task")

        monkeypatch.setattr("phantom.loop.anthropic.Anthropic", no_client)
        with pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code == 1
        assert "No task provided" in capsys.readouterr().out

    def test_flags_reach_the_api_request_and_the_reply_is_printed(
        self, capsys, monkeypatch
    ):
        """
        Scenario: A task runs to completion
        Given a scripted Anthropic client that answers with text only
        When main() runs with --model, --max-tokens and --system-prompt
        Then the request carries those values and the reply is printed
        """
        client = MagicMock()
        client.beta.messages.create.return_value = SimpleNamespace(
            content=[
                SimpleNamespace(
                    type="text", text="Done it", model_dump=lambda: {"type": "text"}
                )
            ],
            usage=SimpleNamespace(input_tokens=1, output_tokens=1),
        )
        monkeypatch.setattr("phantom.loop.anthropic.Anthropic", lambda api_key: client)
        monkeypatch.setattr("phantom.display._check_command", lambda name: True)
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        monkeypatch.setattr(
            "sys.argv",
            [
                "phantom",
                "--model",
                "claude-opus-4-6",
                "--max-tokens",
                "512",
                "--system-prompt",
                "Be careful",
                "open",
                "firefox",
            ],
        )
        main()
        kwargs = client.beta.messages.create.call_args.kwargs
        assert kwargs["model"] == "claude-opus-4-6"
        assert kwargs["max_tokens"] == 512
        assert kwargs["system"] == "Be careful"
        assert kwargs["messages"][0]["content"] == "open firefox"
        out = capsys.readouterr().out
        assert "Stop reason: completed" in out
        assert "Done it" in out


class TestSafetyControlsReachTheCli:
    """The library's budget and confirmation gate had no CLI switch."""

    def test_budget_usd_is_parsed(self) -> None:
        args = build_parser().parse_args(["--budget-usd", "0.50", "open", "it"])
        assert args.budget_usd == 0.5

    def test_confirm_is_off_unless_asked_for(self) -> None:
        assert build_parser().parse_args(["go"]).confirm is False
        assert build_parser().parse_args(["--confirm", "go"]).confirm is True

    def test_a_thinking_budget_at_or_over_max_tokens_is_refused(
        self, monkeypatch, capsys
    ) -> None:
        """The API rejects budget_tokens >= max_tokens; say so before calling it."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        loop = MagicMock()
        monkeypatch.setattr("phantom.cli.run_loop", loop)
        with pytest.raises(SystemExit) as exc:
            main(["--thinking-budget", "8000", "--max-tokens", "4096", "go"])
        assert exc.value.code == 2
        assert "--thinking-budget must be smaller than --max-tokens" in (
            capsys.readouterr().err
        )
        loop.assert_not_called()

    @staticmethod
    def _run_with_loop(monkeypatch, argv: list[str]) -> MagicMock:
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        loop = MagicMock(
            return_value=SimpleNamespace(
                iterations=1, actions_taken=0, stopped_reason="completed", final_text=""
            )
        )
        monkeypatch.setattr("phantom.cli.run_loop", loop)
        main(argv)
        return loop

    def test_budget_usd_reaches_the_loop(self, monkeypatch) -> None:
        loop = self._run_with_loop(monkeypatch, ["--budget-usd", "0.50", "go"])
        assert loop.call_args.kwargs["setup"].loop_config.budget_usd == 0.5

    def test_confirm_installs_the_confirmation_gate(self, monkeypatch) -> None:
        loop = self._run_with_loop(monkeypatch, ["--confirm", "go"])
        assert loop.call_args.kwargs["hooks"].confirm_callback is _ask_before_acting

    def test_no_confirmation_gate_without_confirm(self, monkeypatch) -> None:
        loop = self._run_with_loop(monkeypatch, ["go"])
        assert loop.call_args.kwargs["hooks"].confirm_callback is None
