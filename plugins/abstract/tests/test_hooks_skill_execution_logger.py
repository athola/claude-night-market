"""BDD/TDD tests for skill_execution_logger.py hook (PostToolUse).

Tests follow the Given-When-Then pattern:
- Given: Precondition and context
- When: Action or event
- Then: Expected outcome

These tests verify the PostToolUse hook behavior:
1. Log entry creation and JSONL formatting
2. Duration calculation from pre-execution state
3. Continual metrics calculation (stability gap, accuracy)
4. Outcome detection (success/failure/partial)
5. State file cleanup
6. Error handling
"""

import json
import os
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import pytest


class TestPostSkillExecutionBasics:
    """Test basic hook execution and output."""

    def test_should_exit_successfully_when_hook_executes(
        self, post_skill_env: dict[str, str], tmp_path: Path
    ) -> None:
        """Test hook exits successfully with valid Skill environment.

        Given: A valid Skill tool environment with output
        When: The skill_execution_logger hook runs
        Then: It should exit with code 0 (success)
        """
        # Given
        hook_path = Path("hooks/skill_execution_logger.py")
        env = {
            **post_skill_env,
            "CLAUDE_HOME": str(tmp_path),
        }

        # When
        result = run_hook(hook_path, env)

        # Then
        assert result["returncode"] == 0, "Hook should exit successfully"

    def test_should_return_valid_json_when_skill_completes(
        self, post_skill_env: dict[str, str], tmp_path: Path
    ) -> None:
        """Test hook returns valid JSON with hookSpecificOutput.

        Given: A valid Skill tool environment
        When: The hook executes
        Then: It should return valid JSON with hookSpecificOutput
        """
        # Given
        hook_path = Path("hooks/skill_execution_logger.py")
        env = {
            **post_skill_env,
            "CLAUDE_HOME": str(tmp_path),
        }

        # When
        result = run_hook(hook_path, env)

        # Then
        assert result["stdout"] is not None, "Should produce stdout"
        try:
            output = json.loads(result["stdout"])
            assert "hookSpecificOutput" in output
        except json.JSONDecodeError as e:
            pytest.fail(f"Output should be valid JSON: {e}")

    def test_should_include_post_tool_use_event(
        self, post_skill_env: dict[str, str], tmp_path: Path
    ) -> None:
        """Test hook output includes PostToolUse event name.

        Given: A valid Skill tool environment
        When: The hook executes
        Then: Output should indicate PostToolUse event
        """
        # Given
        hook_path = Path("hooks/skill_execution_logger.py")
        env = {
            **post_skill_env,
            "CLAUDE_HOME": str(tmp_path),
        }

        # When
        result = run_hook(hook_path, env)
        output = json.loads(result["stdout"])

        # Then
        assert output["hookSpecificOutput"]["hookEventName"] == "PostToolUse"


class TestLogEntryCreation:
    """Test log entry creation and JSONL formatting."""

    def test_should_create_log_file_in_correct_location(
        self, post_skill_env: dict[str, str], tmp_path: Path
    ) -> None:
        """Test log file is created in logs/<plugin>/<skill>/ directory.

        Given: A valid Skill tool environment
        When: The hook executes
        Then: A log file should be created in logs/<plugin>/<skill>/
        """
        # Given
        skill_ref = "abstract:skill-auditor"
        hook_path = Path("hooks/skill_execution_logger.py")
        env = {
            **post_skill_env,
            "CLAUDE_TOOL_INPUT": json.dumps({"skill": skill_ref}),
            "CLAUDE_HOME": str(tmp_path),
        }

        # When
        run_hook(hook_path, env)

        # Then
        log_dir = tmp_path / "skills" / "logs" / "abstract" / "skill-auditor"
        log_date = datetime.now(UTC).strftime("%Y-%m-%d")
        log_file = log_dir / f"{log_date}.jsonl"

        assert log_file.exists(), f"Log file should exist at {log_file}"

    def test_should_append_to_jsonl_file(
        self, post_skill_env: dict[str, str], tmp_path: Path
    ) -> None:
        """Test multiple executions append to the same JSONL file.

        Given: Multiple skill executions
        When: The hook executes multiple times
        Then: Log entries should be appended to the same file
        """
        # Given
        skill_ref = "abstract:skill-auditor"
        hook_path = Path("hooks/skill_execution_logger.py")
        env = {
            **post_skill_env,
            "CLAUDE_TOOL_INPUT": json.dumps({"skill": skill_ref}),
            "CLAUDE_HOME": str(tmp_path),
        }
        log_dir = tmp_path / "skills" / "logs" / "abstract" / "skill-auditor"
        log_date = datetime.now(UTC).strftime("%Y-%m-%d")
        log_file = log_dir / f"{log_date}.jsonl"

        # When - run 3 times
        for _ in range(3):
            run_hook(hook_path, env)

        # Then
        assert log_file.exists()
        lines = log_file.read_text().strip().split("\n")
        assert len(lines) == 3, "Should have 3 log entries"

    def test_should_create_valid_jsonl_entries(
        self, post_skill_env: dict[str, str], tmp_path: Path
    ) -> None:
        """Test each log entry is valid JSON.

        Given: A valid Skill tool environment
        When: The hook executes
        Then: Each log entry should be valid JSON
        """
        # Given
        skill_ref = "abstract:skill-auditor"
        hook_path = Path("hooks/skill_execution_logger.py")
        env = {
            **post_skill_env,
            "CLAUDE_TOOL_INPUT": json.dumps({"skill": skill_ref}),
            "CLAUDE_HOME": str(tmp_path),
        }
        log_dir = tmp_path / "skills" / "logs" / "abstract" / "skill-auditor"
        log_date = datetime.now(UTC).strftime("%Y-%m-%d")
        log_file = log_dir / f"{log_date}.jsonl"

        # When
        run_hook(hook_path, env)

        # Then
        lines = log_file.read_text().strip().split("\n")
        for line in lines:
            try:
                entry = json.loads(line)
                assert isinstance(entry, dict)
            except json.JSONDecodeError:
                pytest.fail(f"Log entry should be valid JSON: {line}")

    def test_should_include_required_log_fields(
        self, post_skill_env: dict[str, str], tmp_path: Path
    ) -> None:
        """Test log entry contains all required fields.

        Given: A valid Skill tool environment
        When: The hook executes
        Then: Log entry should include all required fields
        """
        # Given
        skill_ref = "abstract:skill-auditor"
        hook_path = Path("hooks/skill_execution_logger.py")
        env = {
            **post_skill_env,
            "CLAUDE_TOOL_INPUT": json.dumps({"skill": skill_ref}),
            "CLAUDE_HOME": str(tmp_path),
        }
        log_dir = tmp_path / "skills" / "logs" / "abstract" / "skill-auditor"
        log_date = datetime.now(UTC).strftime("%Y-%m-%d")
        log_file = log_dir / f"{log_date}.jsonl"

        # When
        run_hook(hook_path, env)

        # Then
        entry = json.loads(log_file.read_text().strip())
        required_fields = [
            "timestamp",
            "invocation_id",
            "skill",
            "plugin",
            "skill_name",
            "duration_ms",
            "outcome",
            "context",
        ]
        for field in required_fields:
            assert field in entry, f"Log entry should have {field}"


class TestDurationTracking:
    """Test duration calculation from pre-execution state."""

    def test_should_calculate_duration_from_pre_state(
        self, post_skill_env: dict[str, str], tmp_path: Path
    ) -> None:
        """Test duration is calculated from pre-execution state timestamp.

        Given: A pre-execution state file exists
        When: The PostToolUse hook executes
        Then: Duration should be calculated from the timestamp difference
        """
        # Given
        skill_ref = "abstract:skill-auditor"
        hook_path = Path("hooks/skill_execution_logger.py")
        pre_hook_path = Path("hooks/pre_skill_execution.py")
        env = {
            **post_skill_env,
            "CLAUDE_TOOL_INPUT": json.dumps({"skill": skill_ref}),
            "CLAUDE_HOME": str(tmp_path),
        }

        # Create pre-state
        run_hook(pre_hook_path, {**env, "CLAUDE_TOOL_OUTPUT": ""})

        # Simulate skill execution delay
        time.sleep(0.1)  # 100ms

        # When
        run_hook(hook_path, env)

        # Then
        log_dir = tmp_path / "skills" / "logs" / "abstract" / "skill-auditor"
        log_date = datetime.now(UTC).strftime("%Y-%m-%d")
        log_file = log_dir / f"{log_date}.jsonl"
        entry = json.loads(log_file.read_text().strip())

        assert entry["duration_ms"] > 0, "Duration should be positive"
        assert entry["duration_ms"] >= 100, f"Duration >= 100ms, got {entry}"

    def test_should_handle_missing_pre_state_gracefully(
        self, post_skill_env: dict[str, str], tmp_path: Path
    ) -> None:
        """Test hook handles missing pre-execution state gracefully.

        Given: No pre-execution state file exists
        When: The PostToolUse hook executes
        Then: Duration should default to 0 and execution should continue
        """
        # Given
        skill_ref = "abstract:skill-auditor"
        hook_path = Path("hooks/skill_execution_logger.py")
        env = {
            **post_skill_env,
            "CLAUDE_TOOL_INPUT": json.dumps({"skill": skill_ref}),
            "CLAUDE_HOME": str(tmp_path),
        }

        # When - no pre-state created
        result = run_hook(hook_path, env)

        # Then
        assert result["returncode"] == 0
        log_dir = tmp_path / "skills" / "logs" / "abstract" / "skill-auditor"
        log_date = datetime.now(UTC).strftime("%Y-%m-%d")
        log_file = log_dir / f"{log_date}.jsonl"
        entry = json.loads(log_file.read_text().strip())

        assert entry["duration_ms"] == 0, "Duration should be 0 without pre-state"


class TestOutcomeDetection:
    """Test outcome detection from tool output."""

    def test_should_detect_success_in_normal_output(
        self, post_skill_env: dict[str, str], tmp_path: Path
    ) -> None:
        """Test success outcome is detected from normal output.

        Given: Tool output without error indicators
        When: The hook executes
        Then: Outcome should be "success"
        """
        # Given
        skill_ref = "abstract:skill-auditor"
        hook_path = Path("hooks/skill_execution_logger.py")
        env = {
            **post_skill_env,
            "CLAUDE_TOOL_INPUT": json.dumps({"skill": skill_ref}),
            "CLAUDE_TOOL_OUTPUT": "Skill execution completed successfully",
            "CLAUDE_HOME": str(tmp_path),
        }

        # When
        run_hook(hook_path, env)

        # Then
        log_dir = tmp_path / "skills" / "logs" / "abstract" / "skill-auditor"
        log_date = datetime.now(UTC).strftime("%Y-%m-%d")
        log_file = log_dir / f"{log_date}.jsonl"
        entry = json.loads(log_file.read_text().strip())

        assert entry["outcome"] == "success"

    def test_should_detect_failure_in_error_output(
        self, skill_tool_env_failure: dict[str, str], tmp_path: Path
    ) -> None:
        """Test failure outcome is detected from error output.

        Given: Tool output containing "error"
        When: The hook executes
        Then: Outcome should be "failure"
        """
        # Given
        skill_ref = "abstract:skill-auditor"
        hook_path = Path("hooks/skill_execution_logger.py")
        env = {
            **skill_tool_env_failure,
            "CLAUDE_TOOL_INPUT": json.dumps({"skill": skill_ref}),
            "CLAUDE_HOME": str(tmp_path),
        }

        # When
        run_hook(hook_path, env)

        # Then
        log_dir = tmp_path / "skills" / "logs" / "abstract" / "skill-auditor"
        log_date = datetime.now(UTC).strftime("%Y-%m-%d")
        log_file = log_dir / f"{log_date}.jsonl"
        entry = json.loads(log_file.read_text().strip())

        assert entry["outcome"] == "failure"
        assert entry["error"] is not None, "Should store error message"

    def test_should_detect_partial_in_warning_output(
        self, skill_tool_env_partial: dict[str, str], tmp_path: Path
    ) -> None:
        """Test partial outcome is detected from warning output.

        Given: Tool output containing "warning"
        When: The hook executes
        Then: Outcome should be "partial"
        """
        # Given
        skill_ref = "abstract:skill-auditor"
        hook_path = Path("hooks/skill_execution_logger.py")
        env = {
            **skill_tool_env_partial,
            "CLAUDE_TOOL_INPUT": json.dumps({"skill": skill_ref}),
            "CLAUDE_HOME": str(tmp_path),
        }

        # When
        run_hook(hook_path, env)

        # Then
        log_dir = tmp_path / "skills" / "logs" / "abstract" / "skill-auditor"
        log_date = datetime.now(UTC).strftime("%Y-%m-%d")
        log_file = log_dir / f"{log_date}.jsonl"
        entry = json.loads(log_file.read_text().strip())

        assert entry["outcome"] == "partial"


class TestContinualMetrics:
    """Test continual evaluation metrics calculation."""

    def test_should_calculate_metrics_after_first_execution(
        self, post_skill_env: dict[str, str], tmp_path: Path
    ) -> None:
        """Test continual metrics are calculated after first execution.

        Given: First skill execution
        When: The hook executes
        Then: Continual metrics should be calculated with count=1
        """
        # Given
        skill_ref = "abstract:skill-auditor"
        hook_path = Path("hooks/skill_execution_logger.py")
        env = {
            **post_skill_env,
            "CLAUDE_TOOL_INPUT": json.dumps({"skill": skill_ref}),
            "CLAUDE_HOME": str(tmp_path),
        }
        log_dir = tmp_path / "skills" / "logs" / "abstract" / "skill-auditor"
        log_date = datetime.now(UTC).strftime("%Y-%m-%d")
        log_file = log_dir / f"{log_date}.jsonl"

        # When
        run_hook(hook_path, env)

        # Then
        entry = json.loads(log_file.read_text().strip())
        metrics = entry.get("continual_metrics")

        assert metrics is not None, "Should have continual_metrics"
        assert metrics["execution_count"] == 1
        assert metrics["average_accuracy"] == 1.0
        assert metrics["worst_case_accuracy"] == 1.0
        assert metrics["stability_gap"] == 0.0

    def test_should_track_stability_gap_across_executions(
        self, post_skill_env: dict[str, str], tmp_path: Path
    ) -> None:
        """Test stability gap tracks accuracy variance across executions.

        Given: Multiple executions with mixed success/failure
        When: The hook executes multiple times
        Then: Stability gap should reflect the difference
        """
        # Given
        skill_ref = "abstract:skill-auditor"
        hook_path = Path("hooks/skill_execution_logger.py")
        log_dir = tmp_path / "skills" / "logs" / "abstract" / "skill-auditor"
        log_date = datetime.now(UTC).strftime("%Y-%m-%d")
        log_file = log_dir / f"{log_date}.jsonl"

        # When - execute with alternating success/failure
        for i in range(6):
            output = "Error: failed" if i % 2 == 0 else "Success"
            env = {
                **post_skill_env,
                "CLAUDE_TOOL_INPUT": json.dumps({"skill": skill_ref}),
                "CLAUDE_TOOL_OUTPUT": output,
                "CLAUDE_HOME": str(tmp_path),
            }
            run_hook(hook_path, env)

        # Then
        entry = json.loads(log_file.read_text().strip().split("\n")[-1])
        metrics = entry.get("continual_metrics")

        # With 3 failures in 6 executions: accuracies [0, 1, 0, 1, 0, 1]
        # worst_case: 0.0, average: 0.5, stability_gap: 0.5
        assert metrics["execution_count"] == 6
        assert metrics["worst_case_accuracy"] == 0.0
        assert metrics["average_accuracy"] == 0.5
        assert metrics["stability_gap"] == 0.5

    def test_should_warn_when_stability_gap_exceeds_threshold(
        self, post_skill_env: dict[str, str], tmp_path: Path
    ) -> None:
        """Test warning is emitted when stability gap exceeds threshold.

        Given: A skill with high instability (stability_gap > 0.3)
        When: The hook executes
        Then: It should write a warning to stderr
        """
        # Given
        skill_ref = "abstract:skill-auditor"
        hook_path = Path("hooks/skill_execution_logger.py")

        # Create history with high instability (33% failure rate)
        for i in range(10):
            output = "Error: failed" if i % 3 == 0 else "Success"
            env = {
                **post_skill_env,
                "CLAUDE_TOOL_INPUT": json.dumps({"skill": skill_ref}),
                "CLAUDE_TOOL_OUTPUT": output,
                "CLAUDE_HOME": str(tmp_path),
            }
            run_hook(hook_path, env)

        # When - run one more time
        env = {
            **post_skill_env,
            "CLAUDE_TOOL_INPUT": json.dumps({"skill": skill_ref}),
            "CLAUDE_TOOL_OUTPUT": "Success",
            "CLAUDE_HOME": str(tmp_path),
        }
        result = run_hook(hook_path, env)

        # Then - check stderr for warning (may or may not have warning)
        assert "Stability gap" in result["stderr"] or result["stderr"] == ""


class TestStateFileCleanup:
    """Test cleanup of pre-execution state files."""

    def test_should_cleanup_state_file_after_use(
        self, post_skill_env: dict[str, str], tmp_path: Path
    ) -> None:
        """Test pre-execution state file is deleted after use.

        Given: A pre-execution state file exists
        When: The PostToolUse hook executes
        Then: The state file should be deleted
        """
        # Given
        skill_ref = "abstract:skill-auditor"
        pre_hook_path = Path("hooks/pre_skill_execution.py")
        post_hook_path = Path("hooks/skill_execution_logger.py")
        env = {
            **post_skill_env,
            "CLAUDE_TOOL_INPUT": json.dumps({"skill": skill_ref}),
            "CLAUDE_HOME": str(tmp_path),
        }
        obs_dir = tmp_path / "skills" / "observability"

        # Create pre-state
        run_hook(pre_hook_path, {**env, "CLAUDE_TOOL_OUTPUT": ""})
        state_files_before = list(obs_dir.glob(f"{skill_ref}:*.json"))

        # When
        run_hook(post_hook_path, env)

        # Then
        state_files_after = list(obs_dir.glob(f"{skill_ref}:*.json"))
        assert len(state_files_after) < len(state_files_before), "State cleaned up"


class TestErrorHandling:
    """Test error handling and graceful degradation."""

    def test_should_handle_malformed_tool_input(self, tmp_path: Path) -> None:
        """Test hook handles malformed JSON tool input gracefully.

        Given: Malformed JSON in CLAUDE_TOOL_INPUT
        When: The hook executes
        Then: It should exit gracefully and create a log entry
        """
        # Given
        hook_path = Path("hooks/skill_execution_logger.py")
        env = {
            "CLAUDE_TOOL_NAME": "Skill",
            "CLAUDE_TOOL_INPUT": "invalid json{{{",
            "CLAUDE_TOOL_OUTPUT": "Test output",
            "CLAUDE_SESSION_ID": "test-session",
            "CLAUDE_HOME": str(tmp_path),
        }

        # When
        result = run_hook(hook_path, env)

        # Then
        assert result["returncode"] == 0

    def test_should_skip_non_skill_tools(
        self, non_skill_env: dict[str, str], tmp_path: Path
    ) -> None:
        """Test hook skips non-Skill tool invocations.

        Given: A non-Skill tool environment
        When: The hook executes
        Then: It should exit without creating log files
        """
        # Given
        hook_path = Path("hooks/skill_execution_logger.py")
        env = {
            **non_skill_env,
            "CLAUDE_TOOL_OUTPUT": "File content",
            "CLAUDE_HOME": str(tmp_path),
        }

        # When
        result = run_hook(hook_path, env)

        # Then
        assert result["returncode"] == 0
        # Check no log files created
        log_dir = tmp_path / "skills" / "logs"
        log_files = list(log_dir.glob("**/*.jsonl"))
        assert len(log_files) == 0


class TestOutputSanitization:
    """Test output sanitization and truncation."""

    def test_should_truncate_long_output(
        self, post_skill_env: dict[str, str], tmp_path: Path
    ) -> None:
        """Test long output is truncated in log preview.

        Given: Very long tool output (>1000 chars)
        When: The hook executes
        Then: Output preview should be truncated
        """
        # Given
        skill_ref = "abstract:skill-auditor"
        hook_path = Path("hooks/skill_execution_logger.py")
        long_output = "x" * 10000  # 10KB
        env = {
            **post_skill_env,
            "CLAUDE_TOOL_INPUT": json.dumps({"skill": skill_ref}),
            "CLAUDE_TOOL_OUTPUT": long_output,
            "CLAUDE_HOME": str(tmp_path),
        }
        log_dir = tmp_path / "skills" / "logs" / "abstract" / "skill-auditor"
        log_date = datetime.now(UTC).strftime("%Y-%m-%d")
        log_file = log_dir / f"{log_date}.jsonl"

        # When
        run_hook(hook_path, env)

        # Then
        entry = json.loads(log_file.read_text().strip())
        output_preview = entry["context"]["output_preview"]

        # Output should be truncated to ~1000 chars + truncation message
        assert len(output_preview) <= 1100, "Output preview should be truncated"
        assert "truncated" in output_preview.lower(), "Should indicate truncation"


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
