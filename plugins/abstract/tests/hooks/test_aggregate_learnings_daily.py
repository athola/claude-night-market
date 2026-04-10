"""Tests for aggregate_learnings_daily.py hook (UserPromptSubmit).

Tests follow Given-When-Then pattern for:
1. Daily cadence gating (>24h since last run)
2. Timestamp file management
3. Chaining to aggregate_skill_logs.py
4. Silent/fast execution (no user-visible output)
5. Error handling and graceful failure
"""

from __future__ import annotations

import importlib
import io
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock

import pytest

_hook_path = str(Path(__file__).resolve().parent.parent.parent / "hooks")
if _hook_path not in sys.path:
    sys.path.insert(0, _hook_path)

_scripts_path = str(Path(__file__).resolve().parent.parent.parent / "scripts")
if _scripts_path not in sys.path:
    sys.path.insert(0, _scripts_path)

import aggregate_learnings_daily  # noqa: E402 - import after sys.path setup
from aggregate_skill_logs import (  # noqa: E402 - import after sys.path setup
    AggregationResult,
    SkillLogSummary,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def hook_module(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Import the hook module with paths redirected to tmp_path."""
    # Redirect CLAUDE_HOME to tmp_path so timestamp files go there
    monkeypatch.setenv("CLAUDE_HOME", str(tmp_path))

    # Force reimport to pick up env changes
    importlib.reload(aggregate_learnings_daily)

    # Patch the home directory functions
    monkeypatch.setattr(
        aggregate_learnings_daily,
        "get_timestamp_path",
        lambda: tmp_path / "logs" / ".last_aggregation",
    )
    monkeypatch.setattr(
        aggregate_learnings_daily,
        "get_log_directory",
        lambda: tmp_path / "logs",
    )

    return aggregate_learnings_daily


@pytest.fixture()
def timestamp_path(tmp_path: Path) -> Path:
    """Return the timestamp file path under tmp_path."""
    ts_path = tmp_path / "logs" / ".last_aggregation"
    ts_path.parent.mkdir(parents=True, exist_ok=True)
    return ts_path


# ---------------------------------------------------------------------------
# Cadence gating tests
# ---------------------------------------------------------------------------


class TestCadenceGating:
    """Test that aggregation only runs once per 24h window."""

    def test_should_run_when_no_timestamp_file_exists(
        self, hook_module, timestamp_path: Path
    ) -> None:
        """Given: No timestamp file exists
        When: should_aggregate() is called
        Then: Returns True (first run ever)
        """
        assert not timestamp_path.exists()
        assert hook_module.should_aggregate() is True

    def test_should_not_run_when_recently_aggregated(
        self, hook_module, timestamp_path: Path
    ) -> None:
        """Given: Timestamp file written <24h ago
        When: should_aggregate() is called
        Then: Returns False (too soon)
        """
        timestamp_path.parent.mkdir(parents=True, exist_ok=True)
        timestamp_path.write_text(str(time.time()))

        assert hook_module.should_aggregate() is False

    def test_should_run_when_timestamp_is_stale(
        self, hook_module, timestamp_path: Path
    ) -> None:
        """Given: Timestamp file written >24h ago
        When: should_aggregate() is called
        Then: Returns True (overdue)
        """
        stale_time = time.time() - (25 * 3600)  # 25 hours ago
        timestamp_path.parent.mkdir(parents=True, exist_ok=True)
        timestamp_path.write_text(str(stale_time))

        assert hook_module.should_aggregate() is True

    def test_should_run_when_timestamp_file_is_corrupt(
        self, hook_module, timestamp_path: Path
    ) -> None:
        """Given: Timestamp file contains invalid data
        When: should_aggregate() is called
        Then: Returns True (treat as never run)
        """
        timestamp_path.parent.mkdir(parents=True, exist_ok=True)
        timestamp_path.write_text("not-a-timestamp")

        assert hook_module.should_aggregate() is True


# ---------------------------------------------------------------------------
# Timestamp management tests
# ---------------------------------------------------------------------------


class TestTimestampManagement:
    """Test timestamp file creation and updates."""

    def test_update_timestamp_creates_file(
        self, hook_module, timestamp_path: Path
    ) -> None:
        """Given: No timestamp file
        When: update_timestamp() is called
        Then: File is created with current time
        """
        hook_module.update_timestamp()

        assert timestamp_path.exists()
        ts = float(timestamp_path.read_text().strip())
        assert abs(ts - time.time()) < 5  # Within 5 seconds

    def test_update_timestamp_creates_parent_dirs(
        self, hook_module, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Given: Parent directory doesn't exist
        When: update_timestamp() is called
        Then: Directories are created
        """
        deep_path = tmp_path / "deep" / "nested" / ".last_aggregation"
        monkeypatch.setattr(hook_module, "get_timestamp_path", lambda: deep_path)

        hook_module.update_timestamp()
        assert deep_path.exists()


# ---------------------------------------------------------------------------
# Log directory check tests
# ---------------------------------------------------------------------------


class TestLogDirectoryCheck:
    """Test that hook checks for log files before running aggregation."""

    def test_should_not_aggregate_when_no_log_directory(
        self, hook_module, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Given: Log directory doesn't exist
        When: has_logs_to_aggregate() is called
        Then: Returns False
        """
        nonexistent = tmp_path / "nonexistent"
        monkeypatch.setattr(hook_module, "get_log_directory", lambda: nonexistent)
        assert hook_module.has_logs_to_aggregate() is False

    def test_should_not_aggregate_when_log_directory_empty(
        self, hook_module, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Given: Log directory exists but has no JSONL files
        When: has_logs_to_aggregate() is called
        Then: Returns False
        """
        log_dir = tmp_path / "logs"
        log_dir.mkdir(parents=True)
        monkeypatch.setattr(hook_module, "get_log_directory", lambda: log_dir)
        assert hook_module.has_logs_to_aggregate() is False

    def test_should_aggregate_when_log_files_exist(
        self, hook_module, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Given: Log directory contains JSONL files
        When: has_logs_to_aggregate() is called
        Then: Returns True
        """
        log_dir = tmp_path / "logs"
        plugin_dir = log_dir / "abstract" / "some-skill"
        plugin_dir.mkdir(parents=True)
        (plugin_dir / "2026-02-23.jsonl").write_text('{"test": true}\n')
        monkeypatch.setattr(hook_module, "get_log_directory", lambda: log_dir)
        assert hook_module.has_logs_to_aggregate() is True


# ---------------------------------------------------------------------------
# Hook output format tests
# ---------------------------------------------------------------------------


class TestHookOutputFormat:
    """Test that hook produces valid UserPromptSubmit JSON."""

    def test_hook_output_is_valid_json(self, hook_module) -> None:
        """Given: Hook produces output
        When: Output is parsed as JSON
        Then: It uses the hookSpecificOutput schema
        """
        output = hook_module.format_hook_output()
        parsed = json.loads(output)
        hook_output = parsed.get("hookSpecificOutput", {})
        assert hook_output.get("hookEventName") == "UserPromptSubmit"

    def test_hook_always_allows_prompt(self, hook_module) -> None:
        """Given: Hook runs (regardless of aggregation state)
        When: Output is checked
        Then: It never blocks the user prompt
        """
        output = hook_module.format_hook_output()
        parsed = json.loads(output)
        # UserPromptSubmit hooks use hookSpecificOutput, not decision
        assert "hookSpecificOutput" in parsed
        # Should not contain blocking decision keys
        assert "decision" not in parsed


# ---------------------------------------------------------------------------
# Aggregation execution tests
# ---------------------------------------------------------------------------


class TestAggregationExecution:
    """Test the actual aggregation trigger logic."""

    def test_run_aggregation_calls_aggregate_script(
        self, hook_module, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Given: Aggregation is due
        When: run_aggregation() is called
        Then: It invokes aggregate_skill_logs.aggregate_logs and generates LEARNINGS.md
        """
        mock_aggregate = MagicMock()
        mock_result = MagicMock()
        mock_result.skills_analyzed = 5
        mock_result.total_executions = 100
        mock_aggregate.return_value = mock_result

        mock_generate = MagicMock(return_value="# Learnings\n")
        monkeypatch.setattr(hook_module, "_run_aggregate", mock_aggregate)
        monkeypatch.setattr(hook_module, "_write_learnings", mock_generate)

        result = hook_module.run_aggregation()
        assert result is True
        mock_aggregate.assert_called_once()

    def test_run_aggregation_returns_false_on_error(
        self, hook_module, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Given: aggregate_skill_logs raises an error
        When: run_aggregation() is called
        Then: Returns False without crashing
        """
        monkeypatch.setattr(
            hook_module,
            "_run_aggregate",
            MagicMock(side_effect=Exception("test error")),
        )
        result = hook_module.run_aggregation()
        assert result is False


# ---------------------------------------------------------------------------
# Auto-promote chaining tests
# ---------------------------------------------------------------------------


class TestAutoPromoteChaining:
    """Test that network-heavy operations are NOT in the daily pipeline.

    Auto-promote and post-learnings moved to the Stop hook
    (post_learnings_stop.py) to avoid exceeding the 2-second
    UserPromptSubmit timeout.
    """

    def test_does_not_call_auto_promote(
        self, hook_module, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Given: Aggregation completed successfully
        When: run_daily_pipeline() is called
        Then: auto_promote is NOT triggered (moved to Stop hook)
        """
        monkeypatch.setattr(
            hook_module, "run_aggregation", MagicMock(return_value=True)
        )
        mock_promote = MagicMock()
        monkeypatch.setattr(hook_module, "run_auto_promote", mock_promote)
        monkeypatch.setattr(hook_module, "run_post_learnings", MagicMock())
        monkeypatch.setattr(
            hook_module, "should_aggregate", MagicMock(return_value=True)
        )
        monkeypatch.setattr(
            hook_module, "has_logs_to_aggregate", MagicMock(return_value=True)
        )

        hook_module.run_daily_pipeline()
        mock_promote.assert_not_called()

    def test_does_not_call_post_learnings(
        self, hook_module, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Given: Aggregation completed successfully
        When: run_daily_pipeline() is called
        Then: post_learnings is NOT triggered (moved to Stop hook)
        """
        monkeypatch.setattr(
            hook_module, "run_aggregation", MagicMock(return_value=True)
        )
        monkeypatch.setattr(hook_module, "run_auto_promote", MagicMock())
        mock_post = MagicMock()
        monkeypatch.setattr(hook_module, "run_post_learnings", mock_post)
        monkeypatch.setattr(
            hook_module, "should_aggregate", MagicMock(return_value=True)
        )
        monkeypatch.setattr(
            hook_module, "has_logs_to_aggregate", MagicMock(return_value=True)
        )

        hook_module.run_daily_pipeline()
        mock_post.assert_not_called()

    def test_skips_everything_when_not_due(
        self, hook_module, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Given: Aggregation is not due (<24h since last run)
        When: run_daily_pipeline() is called
        Then: Neither aggregation nor promotion runs
        """
        mock_agg = MagicMock()
        mock_promote = MagicMock()
        monkeypatch.setattr(hook_module, "run_aggregation", mock_agg)
        monkeypatch.setattr(hook_module, "run_auto_promote", mock_promote)
        monkeypatch.setattr(
            hook_module, "should_aggregate", MagicMock(return_value=False)
        )

        hook_module.run_daily_pipeline()
        mock_agg.assert_not_called()
        mock_promote.assert_not_called()

    def test_skips_when_no_logs_to_aggregate(
        self, hook_module, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Given: Aggregation is due but no log files exist
        When: run_daily_pipeline() is called
        Then: Neither aggregation nor promotion runs
        """
        mock_agg = MagicMock()
        mock_promote = MagicMock()
        monkeypatch.setattr(hook_module, "run_aggregation", mock_agg)
        monkeypatch.setattr(hook_module, "run_auto_promote", mock_promote)
        monkeypatch.setattr(
            hook_module, "should_aggregate", MagicMock(return_value=True)
        )
        monkeypatch.setattr(
            hook_module, "has_logs_to_aggregate", MagicMock(return_value=False)
        )

        hook_module.run_daily_pipeline()
        mock_agg.assert_not_called()
        mock_promote.assert_not_called()

    def test_updates_timestamp_only_on_success(
        self, hook_module, timestamp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Given: Aggregation succeeds
        When: run_daily_pipeline() completes
        Then: Timestamp is updated
        """
        monkeypatch.setattr(
            hook_module, "should_aggregate", MagicMock(return_value=True)
        )
        monkeypatch.setattr(
            hook_module, "has_logs_to_aggregate", MagicMock(return_value=True)
        )
        monkeypatch.setattr(
            hook_module, "run_aggregation", MagicMock(return_value=True)
        )
        monkeypatch.setattr(hook_module, "run_auto_promote", MagicMock())
        monkeypatch.setattr(hook_module, "run_post_learnings", MagicMock())

        hook_module.run_daily_pipeline()
        assert timestamp_path.exists()

    def test_does_not_update_timestamp_on_failure(
        self, hook_module, timestamp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Given: Aggregation fails
        When: run_daily_pipeline() completes
        Then: Timestamp is NOT updated
        """
        monkeypatch.setattr(
            hook_module, "should_aggregate", MagicMock(return_value=True)
        )
        monkeypatch.setattr(
            hook_module, "has_logs_to_aggregate", MagicMock(return_value=True)
        )
        monkeypatch.setattr(
            hook_module, "run_aggregation", MagicMock(return_value=False)
        )

        hook_module.run_daily_pipeline()
        assert not timestamp_path.exists()


# ---------------------------------------------------------------------------
# Auto-promote error isolation tests
# ---------------------------------------------------------------------------


class TestAutoPromoteErrorIsolation:
    """Test that auto-promote errors don't affect the hook."""

    def test_auto_promote_exception_is_swallowed(
        self, hook_module, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Given: _promote raises an exception
        When: run_auto_promote() is called
        Then: Exception is silently caught (hook must not crash)
        """
        # Ensure the scripts-available flag is set so run_auto_promote
        # actually calls _promote rather than returning early.
        monkeypatch.setattr(hook_module, "_HAS_SCRIPTS", True)

        def boom():
            raise RuntimeError("boom")

        monkeypatch.setattr(hook_module, "_promote", boom)

        # Should not raise
        hook_module.run_auto_promote()

    def test_post_learnings_exception_is_swallowed(
        self, hook_module, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Given: _post_learnings raises an exception
        When: run_post_learnings() is called
        Then: Exception is silently caught (hook must not crash)
        """
        monkeypatch.setattr(hook_module, "_HAS_SCRIPTS", True)

        def boom():
            raise RuntimeError("post boom")

        monkeypatch.setattr(hook_module, "_post_learnings", boom)

        # Should not raise
        hook_module.run_post_learnings()


# ---------------------------------------------------------------------------
# Main entry point tests
# ---------------------------------------------------------------------------


class TestMainEntryPoint:
    """Test the main() hook entry point."""

    def test_main_reads_stdin_and_outputs_json(
        self, hook_module, monkeypatch: pytest.MonkeyPatch, capsys
    ) -> None:
        """Given: Hook is invoked as UserPromptSubmit handler
        When: main() runs
        Then: Reads stdin, runs pipeline, prints hookSpecificOutput JSON
        """
        monkeypatch.setattr("sys.stdin", io.StringIO('{"user_prompt": "test"}'))
        monkeypatch.setattr(hook_module, "run_daily_pipeline", MagicMock())

        hook_module.main()

        captured = capsys.readouterr()
        parsed = json.loads(captured.out.strip())
        assert "hookSpecificOutput" in parsed

    def test_main_outputs_valid_json_even_on_pipeline_error(
        self, hook_module, monkeypatch: pytest.MonkeyPatch, capsys
    ) -> None:
        """Given: The daily pipeline raises an exception
        When: main() runs
        Then: Still prints valid JSON (never blocks the user)
        """
        monkeypatch.setattr("sys.stdin", io.StringIO(""))
        monkeypatch.setattr(
            hook_module,
            "run_daily_pipeline",
            MagicMock(side_effect=RuntimeError("pipeline crash")),
        )

        hook_module.main()

        captured = capsys.readouterr()
        parsed = json.loads(captured.out.strip())
        assert "hookSpecificOutput" in parsed

    def test_main_handles_stdin_read_error(
        self, hook_module, monkeypatch: pytest.MonkeyPatch, capsys
    ) -> None:
        """Given: stdin.read() raises an error
        When: main() runs
        Then: Still runs pipeline and outputs valid JSON
        """
        mock_stdin = MagicMock()
        mock_stdin.read.side_effect = OSError("stdin broken")
        monkeypatch.setattr("sys.stdin", mock_stdin)
        monkeypatch.setattr(hook_module, "run_daily_pipeline", MagicMock())

        hook_module.main()

        captured = capsys.readouterr()
        parsed = json.loads(captured.out.strip())
        assert "hookSpecificOutput" in parsed


# ---------------------------------------------------------------------------
# Timestamp overwrite tests
# ---------------------------------------------------------------------------


class TestTimestampOverwrite:
    """Test that update_timestamp overwrites old values correctly."""

    def test_overwrites_existing_timestamp(
        self, hook_module, timestamp_path: Path
    ) -> None:
        """Given: A stale timestamp exists
        When: update_timestamp() is called
        Then: Old value is replaced with current time
        """
        old_time = time.time() - (48 * 3600)
        timestamp_path.parent.mkdir(parents=True, exist_ok=True)
        timestamp_path.write_text(str(old_time))

        hook_module.update_timestamp()

        new_ts = float(timestamp_path.read_text().strip())
        assert new_ts > old_time
        assert abs(new_ts - time.time()) < 5


# ---------------------------------------------------------------------------
# _write_learnings integration test
# ---------------------------------------------------------------------------


class TestWriteLearningsIntegration:
    """Integration test for _write_learnings with real file I/O."""

    def test_write_learnings_preserves_pinned_section(
        self,
        hook_module,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Given: An existing LEARNINGS.md with a Pinned Learnings section
        When: _write_learnings() is called with a real AggregationResult
        Then: The output file contains both new content AND the
              preserved pinned learnings
        """
        learnings_file = tmp_path / "skills" / "LEARNINGS.md"
        learnings_file.parent.mkdir(parents=True, exist_ok=True)

        # Seed LEARNINGS.md with a pinned section
        learnings_file.write_text(
            "# Skill Performance Learnings\n"
            "\n"
            "## Pinned Learnings\n"
            "\n"
            "- Always retry on transient 503 errors\n"
            "- Prefer batch reads over single-file reads\n"
            "\n"
            "## High-Impact Issues\n"
            "\n"
            "old content that will be regenerated\n"
        )

        # Point get_learnings_path at the temp file
        monkeypatch.setattr(hook_module, "get_learnings_path", lambda: learnings_file)

        # Build a minimal but real AggregationResult
        metrics = SkillLogSummary(
            skill="abstract:test-skill",
            plugin="abstract",
            skill_name="test-skill",
            total_executions=10,
            success_count=8,
            failure_count=2,
            partial_count=0,
            avg_duration_ms=1500.0,
            max_duration_ms=3000,
            success_rate=80.0,
            avg_rating=4.2,
            common_friction=["slow response"],
            improvement_suggestions=["cache results"],
            recent_errors=["timeout"],
        )

        result = AggregationResult(
            timestamp=datetime(2026, 3, 1, 12, 0, 0, tzinfo=timezone.utc),
            skills_analyzed=1,
            total_executions=10,
            high_impact_issues=[],
            slow_skills=[],
            low_rated_skills=[],
            metrics_by_skill={"abstract:test-skill": metrics},
        )

        # Call the real _write_learnings (no mock)
        hook_module._write_learnings(result)

        # Verify the file was written
        assert learnings_file.exists()
        content = learnings_file.read_text()

        # Pinned learnings must survive regeneration
        assert "## Pinned Learnings" in content
        assert "Always retry on transient 503 errors" in content
        assert "Prefer batch reads over single-file reads" in content

        # New aggregated content must be present
        assert "# Skill Performance Learnings" in content
        assert "Skills Analyzed" in content
        assert "abstract:test-skill" in content

        # Old non-pinned content must NOT survive
        assert "old content that will be regenerated" not in content

    def test_write_learnings_creates_file_when_none_exists(
        self,
        hook_module,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Given: No existing LEARNINGS.md file
        When: _write_learnings() is called
        Then: A new file is created with the aggregated content
        """
        learnings_file = tmp_path / "new_dir" / "LEARNINGS.md"

        monkeypatch.setattr(hook_module, "get_learnings_path", lambda: learnings_file)

        metrics = SkillLogSummary(
            skill="leyline:fmt",
            plugin="leyline",
            skill_name="fmt",
            total_executions=5,
            success_count=5,
            failure_count=0,
            partial_count=0,
            avg_duration_ms=200.0,
            max_duration_ms=500,
            success_rate=100.0,
            avg_rating=None,
            common_friction=[],
            improvement_suggestions=[],
            recent_errors=[],
        )

        result = AggregationResult(
            timestamp=datetime(2026, 3, 1, 12, 0, 0, tzinfo=timezone.utc),
            skills_analyzed=1,
            total_executions=5,
            high_impact_issues=[],
            slow_skills=[],
            low_rated_skills=[],
            metrics_by_skill={"leyline:fmt": metrics},
        )

        hook_module._write_learnings(result)

        assert learnings_file.exists()
        content = learnings_file.read_text()
        assert "# Skill Performance Learnings" in content
        assert "leyline:fmt" in content
        # No pinned section when there was no pre-existing file
        assert "## Pinned Learnings" not in content
