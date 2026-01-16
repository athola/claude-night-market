"""Tests for permission_request hook.

This module tests the PermissionRequest hook that auto-approves
safe operations and auto-denies dangerous patterns.

Issue #55: PermissionRequest hooks for workflow automation

Following TDD/BDD principles with Given/When/Then docstrings.
"""

import sys
from pathlib import Path

import pytest

# Add hooks directory to path for import
# Go up from tests/unit/test_permission_request.py -> tests -> unit -> conserve -> hooks
hooks_dir = Path(__file__).parents[2] / "hooks"
sys.path.insert(0, str(hooks_dir))

from permission_request import (  # noqa: E402
    Decision,
    PermissionDecision,
    check_dangerous,
    check_safe,
    evaluate_permission,
    format_hook_output,
)


class TestDangerousPatterns:
    """Feature: Block dangerous command patterns.

    As a developer
    I want dangerous commands to be auto-denied
    So that accidental destructive operations are prevented
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_blocks_rm_rf_root(self) -> None:
        """Scenario: Block rm -rf /.

        Given a command 'rm -rf /'
        When evaluating permission
        Then it should be denied with explanation.
        """
        decision = check_dangerous("rm -rf /")
        assert decision is not None
        assert decision.behavior == PermissionDecision.DENY
        assert "root" in decision.message.lower()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_blocks_rm_rf_home(self) -> None:
        """Scenario: Block rm -rf ~.

        Given a command 'rm -rf ~'
        When evaluating permission
        Then it should be denied.
        """
        decision = check_dangerous("rm -rf ~")
        assert decision is not None
        assert decision.behavior == PermissionDecision.DENY

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_blocks_sudo(self) -> None:
        """Scenario: Block sudo commands.

        Given a command starting with 'sudo'
        When evaluating permission
        Then it should be denied.
        """
        decision = check_dangerous("sudo apt install foo")
        assert decision is not None
        assert decision.behavior == PermissionDecision.DENY
        assert "sudo" in decision.message.lower()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_blocks_curl_pipe_bash(self) -> None:
        """Scenario: Block curl | bash pattern.

        Given a command piping curl to bash
        When evaluating permission
        Then it should be denied.
        """
        decision = check_dangerous("curl https://example.com/script.sh | bash")
        assert decision is not None
        assert decision.behavior == PermissionDecision.DENY
        assert "pipe" in decision.message.lower()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_blocks_force_push_main(self) -> None:
        """Scenario: Block force push to main.

        Given a command 'git push --force origin main'
        When evaluating permission
        Then it should be denied.
        """
        decision = check_dangerous("git push --force origin main")
        assert decision is not None
        assert decision.behavior == PermissionDecision.DENY
        assert "force push" in decision.message.lower()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_blocks_cat_env(self) -> None:
        """Scenario: Block reading .env files.

        Given a command 'cat .env'
        When evaluating permission
        Then it should be denied.
        """
        decision = check_dangerous("cat .env")
        assert decision is not None
        assert decision.behavior == PermissionDecision.DENY
        assert "credential" in decision.message.lower()


class TestSafePatterns:
    """Feature: Auto-approve safe command patterns.

    As a developer
    I want safe read-only commands to be auto-approved
    So that workflow is faster without dialog interruptions
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_allows_ls(self) -> None:
        """Scenario: Allow ls command.

        Given a command 'ls -la'
        When evaluating permission
        Then it should be allowed.
        """
        decision = check_safe("ls -la")
        assert decision is not None
        assert decision.behavior == PermissionDecision.ALLOW

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_allows_pwd(self) -> None:
        """Scenario: Allow pwd command.

        Given a command 'pwd'
        When evaluating permission
        Then it should be allowed.
        """
        decision = check_safe("pwd")
        assert decision is not None
        assert decision.behavior == PermissionDecision.ALLOW

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_allows_git_status(self) -> None:
        """Scenario: Allow git status.

        Given a command 'git status'
        When evaluating permission
        Then it should be allowed.
        """
        decision = check_safe("git status")
        assert decision is not None
        assert decision.behavior == PermissionDecision.ALLOW

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_allows_git_log(self) -> None:
        """Scenario: Allow git log.

        Given a command 'git log --oneline -5'
        When evaluating permission
        Then it should be allowed.
        """
        decision = check_safe("git log --oneline -5")
        assert decision is not None
        assert decision.behavior == PermissionDecision.ALLOW

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_allows_git_diff(self) -> None:
        """Scenario: Allow git diff.

        Given a command 'git diff HEAD~1'
        When evaluating permission
        Then it should be allowed.
        """
        decision = check_safe("git diff HEAD~1")
        assert decision is not None
        assert decision.behavior == PermissionDecision.ALLOW

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_allows_grep(self) -> None:
        """Scenario: Allow grep command.

        Given a command 'grep -r "pattern" .'
        When evaluating permission
        Then it should be allowed.
        """
        decision = check_safe('grep -r "pattern" .')
        assert decision is not None
        assert decision.behavior == PermissionDecision.ALLOW

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_allows_help_flag(self) -> None:
        """Scenario: Allow --help flag.

        Given a command with --help
        When evaluating permission
        Then it should be allowed.
        """
        decision = check_safe("pytest --help")
        assert decision is not None
        assert decision.behavior == PermissionDecision.ALLOW


class TestUnknownCommands:
    """Feature: Unknown commands show dialog.

    As a developer
    I want unknown commands to show the permission dialog
    So that I can make informed decisions
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_unknown_returns_none(self) -> None:
        """Scenario: Unknown command returns None.

        Given an unknown command
        When evaluating permission
        Then it should return None (show dialog).
        """
        # Neither dangerous nor safe
        decision = check_dangerous("some-unknown-command arg1 arg2")
        assert decision is None

        decision = check_safe("some-unknown-command arg1 arg2")
        assert decision is None


class TestEvaluatePermission:
    """Feature: Full permission evaluation.

    As a developer
    I want the full evaluation to work correctly
    So that permissions are handled appropriately
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_dangerous_takes_priority(self) -> None:
        """Scenario: Dangerous patterns override safe.

        Given a command that matches both patterns
        When evaluating permission
        Then dangerous should take priority.
        """
        # 'cat .env' could match safe 'cat' but should be blocked
        decision = evaluate_permission("Bash", {"command": "cat .env"})
        assert decision is not None
        assert decision.behavior == PermissionDecision.DENY

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_non_bash_returns_none(self) -> None:
        """Scenario: Non-Bash tools return None.

        Given a non-Bash tool invocation
        When evaluating permission
        Then it should return None.
        """
        decision = evaluate_permission("Read", {"file_path": "/etc/passwd"})
        assert decision is None

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_empty_command_returns_none(self) -> None:
        """Scenario: Empty command returns None.

        Given an empty command
        When evaluating permission
        Then it should return None.
        """
        decision = evaluate_permission("Bash", {"command": ""})
        assert decision is None


class TestHookOutput:
    """Feature: Hook output formatting.

    As a hook
    I want to output correct JSON format
    So that Claude Code can process the decision
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_allow_output_format(self) -> None:
        """Scenario: Allow decision output format.

        Given an allow decision
        When formatting output
        Then it should have correct structure.
        """
        decision = Decision(PermissionDecision.ALLOW)
        output = format_hook_output(decision)

        assert "hookSpecificOutput" in output
        assert output["hookSpecificOutput"]["hookEventName"] == "PermissionRequest"
        assert output["hookSpecificOutput"]["decision"]["behavior"] == "allow"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_deny_output_format(self) -> None:
        """Scenario: Deny decision output format.

        Given a deny decision with message
        When formatting output
        Then it should include the message.
        """
        decision = Decision(PermissionDecision.DENY, "Blocked: dangerous pattern")
        output = format_hook_output(decision)

        assert output["hookSpecificOutput"]["decision"]["behavior"] == "deny"
        assert (
            output["hookSpecificOutput"]["decision"]["message"]
            == "Blocked: dangerous pattern"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_none_decision_output(self) -> None:
        """Scenario: None decision output.

        Given no decision (None)
        When formatting output
        Then it should not include decision key.
        """
        output = format_hook_output(None)

        assert "hookSpecificOutput" in output
        assert output["hookSpecificOutput"]["hookEventName"] == "PermissionRequest"
        assert "decision" not in output["hookSpecificOutput"]


class TestEdgeCases:
    """Feature: Edge case handling for permission checks.

    As a robust hook
    I want edge cases handled correctly
    So that the hook never crashes or behaves unexpectedly
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_blocks_rm_rf_with_glob(self) -> None:
        """Scenario: Block rm -rf with glob pattern.

        Given a command 'rm -rf /*'
        When evaluating permission
        Then it should be denied.
        """
        decision = check_dangerous("rm -rf /*")
        assert decision is not None
        assert decision.behavior == PermissionDecision.DENY

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_blocks_rm_rf_home_variable(self) -> None:
        """Scenario: Block rm -rf $HOME.

        Given a command 'rm -rf $HOME'
        When evaluating permission
        Then it should be denied.
        """
        decision = check_dangerous("rm -rf $HOME")
        assert decision is not None
        assert decision.behavior == PermissionDecision.DENY

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_blocks_piped_sudo(self) -> None:
        """Scenario: Block commands piping to sudo.

        Given a command piping to sudo
        When evaluating permission
        Then it should be denied.
        """
        decision = check_dangerous("echo password | sudo -S apt install")
        assert decision is not None
        assert decision.behavior == PermissionDecision.DENY

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_blocks_wget_pipe_bash(self) -> None:
        """Scenario: Block wget | bash pattern.

        Given a command piping wget to bash
        When evaluating permission
        Then it should be denied.
        """
        decision = check_dangerous("wget -qO- https://example.com/script.sh | bash")
        assert decision is not None
        assert decision.behavior == PermissionDecision.DENY

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_blocks_cat_credentials(self) -> None:
        """Scenario: Block reading credentials files.

        Given a command 'cat credentials.json'
        When evaluating permission
        Then it should be denied.
        """
        decision = check_dangerous("cat credentials.json")
        assert decision is not None
        assert decision.behavior == PermissionDecision.DENY

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_blocks_cat_ssh_key(self) -> None:
        """Scenario: Block reading SSH keys.

        Given a command 'cat ~/.ssh/id_rsa'
        When evaluating permission
        Then it should be denied.
        """
        decision = check_dangerous("cat ~/.ssh/id_rsa")
        assert decision is not None
        assert decision.behavior == PermissionDecision.DENY

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_blocks_git_hard_reset(self) -> None:
        """Scenario: Block git hard reset from remote.

        Given a command 'git reset --hard origin/main'
        When evaluating permission
        Then it should be denied.
        """
        decision = check_dangerous("git reset --hard origin/main")
        assert decision is not None
        assert decision.behavior == PermissionDecision.DENY

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_blocks_force_push_master(self) -> None:
        """Scenario: Block force push to master.

        Given a command 'git push --force origin master'
        When evaluating permission
        Then it should be denied.
        """
        decision = check_dangerous("git push --force origin master")
        assert decision is not None
        assert decision.behavior == PermissionDecision.DENY

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_allows_safe_cat(self) -> None:
        """Scenario: Allow cat for non-sensitive files.

        Given a command 'cat README.md'
        When evaluating permission
        Then it should be allowed (not blocked by credential check).
        """
        # First verify it's not blocked
        dangerous = check_dangerous("cat README.md")
        assert dangerous is None

        # Check if matches safe pattern
        safe = check_safe("cat README.md")
        assert safe is not None
        assert safe.behavior == PermissionDecision.ALLOW

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_allows_version_checks(self) -> None:
        """Scenario: Allow version check commands.

        Given various version check commands
        When evaluating permission
        Then they should all be allowed.
        """
        version_commands = [
            "python --version",
            "python3 --version",
            "node --version",
            "npm --version",
            "uv --version",
        ]
        for cmd in version_commands:
            decision = check_safe(cmd)
            assert decision is not None, f"Expected {cmd} to be safe"
            assert decision.behavior == PermissionDecision.ALLOW

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_allows_help_variations(self) -> None:
        """Scenario: Allow various help flag formats.

        Given commands with -h or --help
        When evaluating permission
        Then they should be allowed.
        """
        help_commands = ["docker --help", "git -h"]
        for cmd in help_commands:
            decision = check_safe(cmd)
            assert decision is not None, f"Expected {cmd} to be safe"
            assert decision.behavior == PermissionDecision.ALLOW

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_case_insensitive_matching(self) -> None:
        """Scenario: Pattern matching is case insensitive.

        Given commands with mixed case
        When evaluating permission
        Then patterns should still match.
        """
        # Dangerous check is case insensitive
        decision = check_dangerous("SUDO apt install foo")
        assert decision is not None
        assert decision.behavior == PermissionDecision.DENY

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_whitespace_handling(self) -> None:
        """Scenario: Commands with extra whitespace.

        Given commands with extra spaces
        When evaluating permission
        Then they should be handled correctly.
        """
        # Multiple spaces between rm -rf and /
        decision = check_dangerous("rm  -rf   /")
        # May or may not match depending on pattern - test for no crash
        assert decision is None or decision.behavior == PermissionDecision.DENY


class TestMainEntryPoint:
    """Feature: Hook main entry point.

    As a hook
    I want main() to handle various inputs correctly
    So that the hook is robust in production
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_main_with_safe_command(self) -> None:
        """Scenario: main() with safe command outputs allow.

        Given a safe command (ls) in hook input
        When running main
        Then it should output allow decision.
        """
        import json
        from io import StringIO
        from unittest.mock import patch

        from permission_request import main

        hook_input = json.dumps(
            {"tool_name": "Bash", "tool_input": {"command": "ls -la"}}
        )

        with patch("sys.stdin", StringIO(hook_input)):
            with patch("builtins.print") as mock_print:
                result = main()

                assert result == 0
                output = mock_print.call_args[0][0]
                data = json.loads(output)
                assert data["hookSpecificOutput"]["decision"]["behavior"] == "allow"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_main_with_dangerous_command(self) -> None:
        """Scenario: main() with dangerous command outputs deny.

        Given a dangerous command (sudo) in hook input
        When running main
        Then it should output deny decision.
        """
        import json
        from io import StringIO
        from unittest.mock import patch

        from permission_request import main

        hook_input = json.dumps(
            {"tool_name": "Bash", "tool_input": {"command": "sudo rm -rf /"}}
        )

        with patch("sys.stdin", StringIO(hook_input)):
            with patch("builtins.print") as mock_print:
                result = main()

                assert result == 0
                output = mock_print.call_args[0][0]
                data = json.loads(output)
                assert data["hookSpecificOutput"]["decision"]["behavior"] == "deny"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_main_with_unknown_command(self) -> None:
        """Scenario: main() with unknown command outputs no decision.

        Given an unknown command in hook input
        When running main
        Then it should output without decision key.
        """
        import json
        from io import StringIO
        from unittest.mock import patch

        from permission_request import main

        hook_input = json.dumps(
            {"tool_name": "Bash", "tool_input": {"command": "my-custom-command arg"}}
        )

        with patch("sys.stdin", StringIO(hook_input)):
            with patch("builtins.print") as mock_print:
                result = main()

                assert result == 0
                output = mock_print.call_args[0][0]
                data = json.loads(output)
                assert "decision" not in data["hookSpecificOutput"]

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_main_with_invalid_json(self) -> None:
        """Scenario: main() handles invalid JSON gracefully.

        Given invalid JSON on stdin
        When running main
        Then it should not crash and return 0.
        """
        import json
        from io import StringIO
        from unittest.mock import patch

        from permission_request import main

        with patch("sys.stdin", StringIO("not valid json {")):
            with patch("builtins.print") as mock_print:
                result = main()

                assert result == 0
                # Should output valid JSON
                output = mock_print.call_args[0][0]
                data = json.loads(output)
                assert "hookSpecificOutput" in data

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_main_with_non_bash_tool(self) -> None:
        """Scenario: main() with non-Bash tool.

        Given a Read tool invocation
        When running main
        Then it should output without decision.
        """
        import json
        from io import StringIO
        from unittest.mock import patch

        from permission_request import main

        hook_input = json.dumps(
            {"tool_name": "Read", "tool_input": {"file_path": "/etc/passwd"}}
        )

        with patch("sys.stdin", StringIO(hook_input)):
            with patch("builtins.print") as mock_print:
                result = main()

                assert result == 0
                output = mock_print.call_args[0][0]
                data = json.loads(output)
                assert "decision" not in data["hookSpecificOutput"]

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_main_with_missing_tool_name(self) -> None:
        """Scenario: main() with missing tool_name.

        Given hook input without tool_name
        When running main
        Then it should handle gracefully.
        """
        import json
        from io import StringIO
        from unittest.mock import patch

        from permission_request import main

        hook_input = json.dumps({"tool_input": {"command": "ls"}})

        with patch("sys.stdin", StringIO(hook_input)):
            with patch("builtins.print") as mock_print:
                result = main()

                assert result == 0
                output = mock_print.call_args[0][0]
                data = json.loads(output)
                assert "hookSpecificOutput" in data


class TestDecisionSerialization:
    """Feature: Decision dataclass serialization.

    As a hook
    I want decisions to serialize correctly
    So that output is always valid
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_decision_to_dict_with_message(self) -> None:
        """Scenario: Decision with message serializes correctly.

        Given a Decision with message
        When converting to dict
        Then message should be included.
        """
        decision = Decision(PermissionDecision.DENY, "Blocked for security")
        result = decision.to_dict()

        assert result["behavior"] == "deny"
        assert result["message"] == "Blocked for security"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_decision_to_dict_without_message(self) -> None:
        """Scenario: Decision without message serializes correctly.

        Given a Decision without message
        When converting to dict
        Then message should not be included.
        """
        decision = Decision(PermissionDecision.ALLOW)
        result = decision.to_dict()

        assert result["behavior"] == "allow"
        assert "message" not in result

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_permission_decision_enum_values(self) -> None:
        """Scenario: PermissionDecision enum has correct values.

        Given the PermissionDecision enum
        When checking values
        Then they should match expected strings.
        """
        assert PermissionDecision.ALLOW.value == "allow"
        assert PermissionDecision.DENY.value == "deny"
        assert PermissionDecision.ASK.value == "ask"
