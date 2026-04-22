"""Tests for vow_no_emoji_commits hook.

Feature: Block emoji characters in git commit messages.

As a Night Market vow enforcement system
I want to detect and block emoji in commits
So that commit messages remain plain-text and professional.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.fixture
def hook_module():
    """Import vow_no_emoji_commits via importlib (hook is a standalone script)."""
    hooks_path = Path(__file__).resolve().parents[3] / "hooks"
    module_path = hooks_path / "vow_no_emoji_commits.py"
    spec = importlib.util.spec_from_file_location("vow_no_emoji_commits", module_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["vow_no_emoji_commits"] = mod
    spec.loader.exec_module(mod)
    return mod


def _make_input(tool_name="Bash", command="git commit -m 'clean message'"):
    return json.dumps({"tool_name": tool_name, "tool_input": {"command": command}})


class TestIsGitCommit:
    """Feature: Identify git commit commands.

    As the hook
    I want to skip non-commit Bash commands
    So that I only inspect commit operations.
    """

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "command,expected",
        [
            ("git commit -m 'msg'", True),
            ("git   commit --amend", True),
            ("git status", False),
            ("git push origin main", False),
            ("echo 'git commit'", False),
        ],
        ids=["plain-commit", "amend", "status", "push", "echo-with-commit"],
    )
    def test_is_git_commit_detection(self, hook_module, command, expected):
        """
        Scenario: Correctly identify git commit invocations
        Given a Bash command string
        When _is_git_commit is called
        Then it returns True only for git commit commands
        """
        assert hook_module._is_git_commit(command) == expected


class TestHasEmoji:
    """Feature: Detect emoji characters in commit command strings.

    As the hook
    I want to detect emoji Unicode characters in commits
    So that I can enforce the no-emoji vow.
    """

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "command",
        [
            "git commit -m 'fix: \U0001f41b bug'",  # bug emoji
            "git commit -m '\U0001f680 launch'",  # rocket
            "git commit -m 'feat ✨ sparkles'",  # sparkles (U+2728)
            "git commit -m '\U0001f916 bot commit'",  # robot
            "git commit -m 'done ✅'",  # white check mark
        ],
        ids=["bug-emoji", "rocket", "sparkles", "robot", "check-mark"],
    )
    def test_emoji_detected(self, hook_module, command):
        """
        Scenario: Detect emoji characters in commit messages
        Given a commit command containing emoji
        When _has_emoji is called
        Then it returns True
        """
        assert hook_module._has_emoji(command) is True

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "command",
        [
            "git commit -m 'fix: correct off-by-one error'",
            "git commit -m 'feat: add user authentication'",
            "git commit -m 'chore: update dependencies'",
            "git commit -m 'docs: update README'",
        ],
        ids=["bugfix", "feature", "chore", "docs"],
    )
    def test_clean_message_not_flagged(self, hook_module, command):
        """
        Scenario: Allow clean commit messages without emoji
        Given a commit command without emoji
        When _has_emoji is called
        Then it returns False
        """
        assert hook_module._has_emoji(command) is False


class TestShadowMode:
    """Feature: Shadow mode controls warn vs block decision.

    As a deployment operator
    I want shadow mode on by default
    So that the hook warns before enforcing fully.
    """

    @pytest.mark.unit
    def test_shadow_mode_on_by_default(self, hook_module):
        """
        Scenario: Shadow mode active when VOW_SHADOW_MODE=1
        Given VOW_SHADOW_MODE=1
        When _shadow_mode is called
        Then it returns True
        """
        with patch.dict("os.environ", {"VOW_SHADOW_MODE": "1"}):
            assert hook_module._shadow_mode() is True

    @pytest.mark.unit
    def test_shadow_mode_disabled_by_zero(self, hook_module):
        """
        Scenario: Shadow mode disabled when VOW_SHADOW_MODE=0
        Given VOW_SHADOW_MODE=0
        When _shadow_mode is called
        Then it returns False
        """
        with patch.dict("os.environ", {"VOW_SHADOW_MODE": "0"}):
            assert hook_module._shadow_mode() is False


class TestMainHook:
    """Feature: Hook main() integrates detection and decision output.

    As the Claude Code hook runner
    I want the hook to emit correct JSON decisions
    So that violations are handled appropriately.
    """

    @pytest.mark.unit
    def test_warn_in_shadow_mode_on_violation(self, hook_module, capsys):
        """
        Scenario: Warn when shadow mode on and emoji found
        Given a git commit containing an emoji
        And VOW_SHADOW_MODE=1
        When main() runs
        Then output JSON has decision=warn
        """
        stdin_data = _make_input(command="git commit -m 'fix \U0001f41b bug'")
        with patch.dict("os.environ", {"VOW_SHADOW_MODE": "1"}):
            with patch("sys.stdin", StringIO(stdin_data)):
                with pytest.raises(SystemExit) as exc:
                    hook_module.main()
        assert exc.value.code == 0
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        hook_out = output["hookSpecificOutput"]
        assert hook_out["permissionDecision"] == "warn"
        assert "Vow violation" in hook_out["permissionDecisionReason"]

    @pytest.mark.unit
    def test_block_when_shadow_mode_off_and_violation(self, hook_module, capsys):
        """
        Scenario: Block when shadow mode off and emoji found
        Given a git commit containing an emoji
        And VOW_SHADOW_MODE=0
        When main() runs
        Then output JSON has decision=block
        """
        stdin_data = _make_input(command="git commit -m 'launch \U0001f680'")
        with patch.dict("os.environ", {"VOW_SHADOW_MODE": "0"}):
            with patch("sys.stdin", StringIO(stdin_data)):
                with pytest.raises(SystemExit) as exc:
                    hook_module.main()
        assert exc.value.code == 0
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert output["hookSpecificOutput"]["permissionDecision"] == "block"

    @pytest.mark.unit
    def test_no_output_on_clean_commit(self, hook_module, capsys):
        """
        Scenario: Allow clean commit without emitting decision JSON
        Given a git commit with no emoji
        When main() runs
        Then no JSON is printed to stdout
        """
        stdin_data = _make_input(command="git commit -m 'fix: clean message'")
        with patch.dict("os.environ", {"VOW_SHADOW_MODE": "1"}):
            with patch("sys.stdin", StringIO(stdin_data)):
                with pytest.raises(SystemExit) as exc:
                    hook_module.main()
        assert exc.value.code == 0
        captured = capsys.readouterr()
        assert captured.out.strip() == ""

    @pytest.mark.unit
    def test_non_bash_tool_ignored(self, hook_module, capsys):
        """
        Scenario: Non-Bash tool calls pass through silently
        Given a Write tool call
        When main() runs
        Then no output is produced
        """
        stdin_data = json.dumps(
            {
                "tool_name": "Write",
                "tool_input": {"file_path": "/tmp/x.py", "content": ""},
            }
        )
        with patch("sys.stdin", StringIO(stdin_data)):
            with pytest.raises(SystemExit) as exc:
                hook_module.main()
        assert exc.value.code == 0
        captured = capsys.readouterr()
        assert captured.out.strip() == ""

    @pytest.mark.unit
    def test_non_commit_bash_ignored(self, hook_module, capsys):
        """
        Scenario: Non-commit Bash commands pass through silently
        Given a Bash call running git status
        When main() runs
        Then no output is produced
        """
        stdin_data = _make_input(command="git status")
        with patch("sys.stdin", StringIO(stdin_data)):
            with pytest.raises(SystemExit) as exc:
                hook_module.main()
        assert exc.value.code == 0
        captured = capsys.readouterr()
        assert captured.out.strip() == ""

    @pytest.mark.unit
    def test_malformed_stdin_exits_cleanly(self, hook_module, capsys):
        """
        Scenario: Malformed stdin does not crash the hook
        Given non-JSON input on stdin
        When main() runs
        Then it exits 0 without output (fail-safe)
        """
        with patch("sys.stdin", StringIO("not valid json")):
            with pytest.raises(SystemExit) as exc:
                hook_module.main()
        assert exc.value.code == 0
        captured = capsys.readouterr()
        assert captured.out.strip() == ""
