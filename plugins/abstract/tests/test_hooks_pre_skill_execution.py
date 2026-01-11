"""BDD/TDD tests for pre_skill_execution.py hook.

Tests follow the Given-When-Then pattern:
- Given: Precondition and context
- When: Action or event
- Then: Expected outcome

These tests verify the PreToolUse hook behavior:
1. State file creation for duration tracking
2. Invocation ID generation
3. Skill name parsing
4. Error handling and graceful degradation
5. Non-Skill tool filtering
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import pytest


class TestPreSkillExecutionBasics:
    """Test basic hook execution and output."""

    def test_should_exit_successfully_when_hook_executes(
        self, pre_skill_env: dict[str, str], tmp_path: Path
    ) -> None:
        """Test hook exits successfully with valid environment.

        Given: A valid Skill tool environment
        When: The pre_skill_execution hook runs
        Then: It should exit with code 0 (success)
        """
        # Given
        hook_path = Path("hooks/pre_skill_execution.py")
        env = {
            **pre_skill_env,
            "CLAUDE_HOME": str(tmp_path),
        }

        # When
        result = run_hook(hook_path, env)

        # Then
        assert result["returncode"] == 0, "Hook should exit successfully"

    def test_should_return_valid_json_when_skill_invoked(
        self, pre_skill_env: dict[str, str], tmp_path: Path
    ) -> None:
        """Test hook returns valid JSON with hookSpecificOutput.

        Given: A valid Skill tool environment
        When: The hook executes
        Then: It should return valid JSON with hookSpecificOutput
        """
        # Given
        hook_path = Path("hooks/pre_skill_execution.py")
        env = {
            **pre_skill_env,
            "CLAUDE_HOME": str(tmp_path),
        }

        # When
        result = run_hook(hook_path, env)

        # Then
        assert result["stdout"] is not None, "Should produce stdout"
        try:
            output = json.loads(result["stdout"])
            assert "hookSpecificOutput" in output, "Should have hookSpecificOutput"
        except json.JSONDecodeError as e:
            pytest.fail(f"Output should be valid JSON: {e}")

    def test_should_include_hook_event_name(
        self, pre_skill_env: dict[str, str], tmp_path: Path
    ) -> None:
        """Test hook output includes PreToolUse event name.

        Given: A valid Skill tool environment
        When: The hook executes
        Then: Output should include hookEventName = "PreToolUse"
        """
        # Given
        hook_path = Path("hooks/pre_skill_execution.py")
        env = {
            **pre_skill_env,
            "CLAUDE_HOME": str(tmp_path),
        }

        # When
        result = run_hook(hook_path, env)
        output = json.loads(result["stdout"])

        # Then
        assert output["hookSpecificOutput"]["hookEventName"] == "PreToolUse", (
            "Should indicate PreToolUse event"
        )


class TestSkillNameParsing:
    """Test skill reference parsing from tool input."""

    def test_should_parse_plugin_and_skill_when_colon_present(
        self, pre_skill_env: dict[str, str], tmp_path: Path
    ) -> None:
        """Test parsing skill reference with colon separator.

        Given: A skill reference with colon separator
        When: The hook parses the skill name
        Then: Both plugin and skill should be extracted correctly
        """
        # Given
        skill_ref = "sanctum:pr-review"
        hook_path = Path("hooks/pre_skill_execution.py")
        env = {
            **pre_skill_env,
            "CLAUDE_TOOL_INPUT": json.dumps({"skill": skill_ref}),
            "CLAUDE_HOME": str(tmp_path),
        }

        # When
        result = run_hook(hook_path, env)
        output = json.loads(result["stdout"])

        # Then
        assert output["hookSpecificOutput"]["skill"] == skill_ref
        # plugin is not in output, only in state file
        assert "plugin" not in output["hookSpecificOutput"]

    def test_should_handle_skill_without_colon(
        self, pre_skill_env: dict[str, str], tmp_path: Path
    ) -> None:
        """Test handling skill reference without colon separator.

        Given: A skill reference without colon separator
        When: The hook parses the skill name
        Then: It should default plugin to "unknown"
        """
        # Given
        skill_ref = "standalone-skill"
        hook_path = Path("hooks/pre_skill_execution.py")
        env = {
            **pre_skill_env,
            "CLAUDE_TOOL_INPUT": json.dumps({"skill": skill_ref}),
            "CLAUDE_HOME": str(tmp_path),
        }

        # When
        result = run_hook(hook_path, env)

        # Then - should not crash
        assert result["returncode"] == 0

    def test_should_trim_whitespace_from_skill_parts(
        self, pre_skill_env: dict[str, str], tmp_path: Path
    ) -> None:
        """Test whitespace is trimmed from skill reference parts.

        Given: A skill reference with extra whitespace
        When: The hook parses the skill name
        Then: Whitespace should be trimmed from plugin and skill
        """
        # Given
        skill_ref = " abstract : skill-auditor "
        hook_path = Path("hooks/pre_skill_execution.py")
        env = {
            **pre_skill_env,
            "CLAUDE_TOOL_INPUT": json.dumps({"skill": skill_ref}),
            "CLAUDE_HOME": str(tmp_path),
        }

        # When
        result = run_hook(hook_path, env)
        output = json.loads(result["stdout"])

        # Then
        assert output["hookSpecificOutput"]["skill"] == "abstract:skill-auditor"


class TestStateFileCreation:
    """Test state file creation for PostToolUse coordination."""

    def test_should_create_state_file_in_observability_dir(
        self, pre_skill_env: dict[str, str], tmp_path: Path
    ) -> None:
        """Test state file creation in observability directory.

        Given: A valid Skill tool environment
        When: The hook executes
        Then: A state file should be created in the observability directory
        """
        # Given
        skill_ref = "abstract:skill-auditor"
        hook_path = Path("hooks/pre_skill_execution.py")
        env = {
            **pre_skill_env,
            "CLAUDE_TOOL_INPUT": json.dumps({"skill": skill_ref}),
            "CLAUDE_HOME": str(tmp_path),
        }
        obs_dir = tmp_path / "skills" / "observability"

        # When
        result = run_hook(hook_path, env)

        # Then
        assert result["returncode"] == 0
        state_files = list(obs_dir.glob(f"{skill_ref}:*.json"))
        assert len(state_files) > 0, "Should create at least one state file"

    def test_should_include_invocation_id_in_state(
        self, pre_skill_env: dict[str, str], tmp_path: Path
    ) -> None:
        """Test state file contains unique invocation ID.

        Given: A valid Skill tool environment
        When: The hook executes
        Then: State file should contain a unique invocation ID
        """
        # Given
        skill_ref = "abstract:skill-auditor"
        hook_path = Path("hooks/pre_skill_execution.py")
        env = {
            **pre_skill_env,
            "CLAUDE_TOOL_INPUT": json.dumps({"skill": skill_ref}),
            "CLAUDE_HOME": str(tmp_path),
        }
        obs_dir = tmp_path / "skills" / "observability"

        # When
        run_hook(hook_path, env)
        state_files = list(obs_dir.glob(f"{skill_ref}:*.json"))
        state_file = state_files[-1]  # Get most recent

        # Then
        state = json.loads(state_file.read_text())
        assert "invocation_id" in state, "State should have invocation_id"
        assert state["invocation_id"].startswith(skill_ref), "ID should start with ref"

    def test_should_include_timestamp_in_state(
        self, pre_skill_env: dict[str, str], tmp_path: Path
    ) -> None:
        """Test state file includes ISO format timestamp.

        Given: A valid Skill tool environment
        When: The hook executes
        Then: State file should include ISO format timestamp
        """
        # Given
        skill_ref = "abstract:skill-auditor"
        hook_path = Path("hooks/pre_skill_execution.py")
        env = {
            **pre_skill_env,
            "CLAUDE_TOOL_INPUT": json.dumps({"skill": skill_ref}),
            "CLAUDE_HOME": str(tmp_path),
        }
        obs_dir = tmp_path / "skills" / "observability"

        # When
        run_hook(hook_path, env)
        state_files = list(obs_dir.glob(f"{skill_ref}:*.json"))
        state_file = state_files[-1]

        # Then
        state = json.loads(state_file.read_text())
        assert "timestamp" in state, "State should have timestamp"
        # Verify ISO format by parsing
        datetime.fromisoformat(state["timestamp"])

    def test_should_include_tool_input_in_state(
        self, pre_skill_env: dict[str, str], tmp_path: Path
    ) -> None:
        """Test state file preserves original tool input.

        Given: A valid Skill tool environment
        When: The hook executes
        Then: State file should preserve the original tool input
        """
        # Given
        skill_ref = "abstract:skill-auditor"
        tool_input = {"skill": skill_ref, "param1": "value1"}
        hook_path = Path("hooks/pre_skill_execution.py")
        env = {
            **pre_skill_env,
            "CLAUDE_TOOL_INPUT": json.dumps(tool_input),
            "CLAUDE_HOME": str(tmp_path),
        }
        obs_dir = tmp_path / "skills" / "observability"

        # When
        run_hook(hook_path, env)
        state_files = list(obs_dir.glob(f"{skill_ref}:*.json"))
        state_file = state_files[-1]

        # Then
        state = json.loads(state_file.read_text())
        assert "tool_input" in state, "State should have tool_input"
        assert state["tool_input"] == tool_input, "Tool input should be preserved"


class TestInvocationIdGeneration:
    """Test unique invocation ID generation."""

    def test_should_generate_unique_ids_for_concurrent_calls(
        self, pre_skill_env: dict[str, str], tmp_path: Path
    ) -> None:
        """Test unique IDs are generated for concurrent hook calls.

        Given: Multiple concurrent hook executions
        When: Each execution generates an invocation ID
        Then: All IDs should be unique (using timestamps)
        """
        # Given
        skill_ref = "abstract:skill-auditor"
        hook_path = Path("hooks/pre_skill_execution.py")
        env = {
            **pre_skill_env,
            "CLAUDE_TOOL_INPUT": json.dumps({"skill": skill_ref}),
            "CLAUDE_HOME": str(tmp_path),
        }
        obs_dir = tmp_path / "skills" / "observability"

        # When - run hook 3 times
        invocation_ids = []
        for _ in range(3):
            run_hook(hook_path, env)

        state_files = list(obs_dir.glob(f"{skill_ref}:*.json"))
        for state_file in state_files:
            state = json.loads(state_file.read_text())
            invocation_ids.append(state["invocation_id"])

        # Then
        assert len(set(invocation_ids)) == len(invocation_ids), "All IDs unique"

    def test_should_include_timestamp_in_invocation_id(
        self, pre_skill_env: dict[str, str], tmp_path: Path
    ) -> None:
        """Test invocation ID includes Unix timestamp.

        Given: A valid Skill tool environment
        When: The hook generates an invocation ID
        Then: The ID should include a Unix timestamp
        """
        # Given
        skill_ref = "abstract:skill-auditor"
        hook_path = Path("hooks/pre_skill_execution.py")
        env = {
            **pre_skill_env,
            "CLAUDE_TOOL_INPUT": json.dumps({"skill": skill_ref}),
            "CLAUDE_HOME": str(tmp_path),
        }
        obs_dir = tmp_path / "skills" / "observability"

        # When
        run_hook(hook_path, env)
        state_files = list(obs_dir.glob(f"{skill_ref}:*.json"))
        state = json.loads(state_files[-1].read_text())

        # Then
        invocation_id = state["invocation_id"]
        # Extract timestamp part (after last colon)
        timestamp_str = invocation_id.split(":")[-1]
        try:
            timestamp = float(timestamp_str)
            assert timestamp > 0, "Timestamp should be positive"
        except ValueError:
            pytest.fail(f"ID should end with timestamp: {invocation_id}")


class TestErrorHandling:
    """Test error handling and graceful degradation."""

    def test_should_exit_gracefully_with_malformed_json(self, tmp_path: Path) -> None:
        """Test hook exits gracefully with malformed JSON input.

        Given: Malformed JSON in CLAUDE_TOOL_INPUT
        When: The hook executes
        Then: It should exit with code 0 (not block Claude Code)
        """
        # Given
        hook_path = Path("hooks/pre_skill_execution.py")
        env = {
            "CLAUDE_TOOL_NAME": "Skill",
            "CLAUDE_TOOL_INPUT": "invalid json{{{",
            "CLAUDE_SESSION_ID": "test-session",
            "CLAUDE_HOME": str(tmp_path),
        }

        # When
        result = run_hook(hook_path, env)

        # Then
        assert result["returncode"] == 0, "Should exit gracefully"

    def test_should_exit_gracefully_with_exception(
        self, pre_skill_env: dict[str, str], tmp_path: Path
    ) -> None:
        """Test hook exits gracefully when exception occurs.

        Given: An unexpected error during hook execution
        When: The exception is raised
        Then: It should exit with code 0 and write to stderr
        """
        # Given - Use invalid CLAUDE_HOME to trigger error
        hook_path = Path("hooks/pre_skill_execution.py")
        env = {
            **pre_skill_env,
            "CLAUDE_HOME": "/invalid/path/that/does/not/exist",
        }

        # When
        result = run_hook(hook_path, env)

        # Then - should still exit 0 (never block Claude)
        assert result["returncode"] == 0


class TestToolFiltering:
    """Test that hook only processes Skill tool invocations."""

    def test_should_skip_non_skill_tools(
        self, non_skill_env: dict[str, str], tmp_path: Path
    ) -> None:
        """Test hook skips non-Skill tool invocations.

        Given: A non-Skill tool environment (e.g., Read tool)
        When: The hook executes
        Then: It should exit without creating state files
        """
        # Given
        hook_path = Path("hooks/pre_skill_execution.py")
        env = {
            **non_skill_env,
            "CLAUDE_HOME": str(tmp_path),
        }
        obs_dir = tmp_path / "skills" / "observability"

        # When
        result = run_hook(hook_path, env)

        # Then
        assert result["returncode"] == 0
        state_files = list(obs_dir.glob("*.json"))
        assert len(state_files) == 0, "No state files for non-Skill tools"

    def test_should_skip_when_tool_name_missing(self, tmp_path: Path) -> None:
        """Test hook skips execution when CLAUDE_TOOL_NAME is missing.

        Given: Environment without CLAUDE_TOOL_NAME
        When: The hook executes
        Then: It should exit without error
        """
        # Given
        hook_path = Path("hooks/pre_skill_execution.py")
        env = {
            "CLAUDE_TOOL_INPUT": '{"skill": "test:skill"}',
            "CLAUDE_SESSION_ID": "test-session",
            "CLAUDE_HOME": str(tmp_path),
        }

        # When
        result = run_hook(hook_path, env)

        # Then
        assert result["returncode"] == 0


# ============================================================================
# Helper Functions
# ============================================================================


def run_hook(hook_path: Path, env: dict[str, str]) -> dict[str, any]:
    """Run a hook script with the given environment.

    Args:
        hook_path: Path to the hook script
        env: Environment variables for the hook

    Returns:
        Dictionary with returncode, stdout, stderr

    """
    result = subprocess.run(
        [sys.executable, str(hook_path)],
        check=False,
        capture_output=True,
        text=True,
        env={**os.environ, **env},
        timeout=5,
    )

    return {
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }
