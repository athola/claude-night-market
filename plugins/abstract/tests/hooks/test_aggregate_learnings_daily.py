"""Tests for aggregate_learnings_daily.py hook (UserPromptSubmit).

Tests follow Given-When-Then pattern for:
1. Daily cadence gating (>24h since last run)
2. Timestamp file management
3. Chaining to aggregate_skill_logs.py
4. Silent/fast execution (no user-visible output)
5. Error handling and graceful failure
"""

from __future__ import annotations

import io
import json
import time
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def hook_module(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Import the hook module with paths redirected to tmp_path."""
    import sys  # noqa: PLC0415

    hook_path = Path(__file__).resolve().parent.parent.parent / "hooks"
    if str(hook_path) not in sys.path:
        sys.path.insert(0, str(hook_path))

    # Redirect CLAUDE_HOME to tmp_path so timestamp files go there
    monkeypatch.setenv("CLAUDE_HOME", str(tmp_path))

    # Force reimport to pick up env changes
    if "aggregate_learnings_daily" in sys.modules:
        del sys.modules["aggregate_learnings_daily"]

    import aggregate_learnings_daily  # noqa: PLC0415

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
        Then: It contains the expected structure
        """
        # The hook should output empty/pass-through for UserPromptSubmit
        output = hook_module.format_hook_output()
        parsed = json.loads(output)
        assert "decision" in parsed or "hookSpecificOutput" in parsed

    def test_hook_always_allows_prompt(self, hook_module) -> None:
        """Given: Hook runs (regardless of aggregation state)
        When: Output is checked
        Then: It never blocks the user prompt
        """
        output = hook_module.format_hook_output()
        parsed = json.loads(output)
        # UserPromptSubmit hooks should not block
        if "decision" in parsed:
            assert parsed["decision"] == "ALLOW"


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
    """Test that daily hook chains to auto_promote after aggregation."""

    def test_chains_to_auto_promote_after_successful_aggregation(
        self, hook_module, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Given: Aggregation completed successfully
        When: run_daily_pipeline() is called
        Then: auto_promote is also triggered
        """
        monkeypatch.setattr(
            hook_module, "run_aggregation", MagicMock(return_value=True)
        )
        mock_promote = MagicMock()
        monkeypatch.setattr(hook_module, "run_auto_promote", mock_promote)
        monkeypatch.setattr(
            hook_module, "should_aggregate", MagicMock(return_value=True)
        )
        monkeypatch.setattr(
            hook_module, "has_logs_to_aggregate", MagicMock(return_value=True)
        )

        hook_module.run_daily_pipeline()
        mock_promote.assert_called_once()

    def test_skips_auto_promote_when_aggregation_fails(
        self, hook_module, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Given: Aggregation failed
        When: run_daily_pipeline() is called
        Then: auto_promote is NOT triggered
        """
        monkeypatch.setattr(
            hook_module, "run_aggregation", MagicMock(return_value=False)
        )
        mock_promote = MagicMock()
        monkeypatch.setattr(hook_module, "run_auto_promote", mock_promote)
        monkeypatch.setattr(
            hook_module, "should_aggregate", MagicMock(return_value=True)
        )
        monkeypatch.setattr(
            hook_module, "has_logs_to_aggregate", MagicMock(return_value=True)
        )

        hook_module.run_daily_pipeline()
        mock_promote.assert_not_called()

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
        """Given: auto_promote raises an exception
        When: run_auto_promote() is called
        Then: Exception is silently caught (hook must not crash)
        """
        monkeypatch.setattr(
            hook_module,
            "run_auto_promote",
            hook_module.run_auto_promote,  # Use actual function
        )
        # Mock the import to raise
        import builtins  # noqa: PLC0415

        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "auto_promote_learnings":
                raise ImportError("module not found")
            return original_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", mock_import)

        # Should not raise
        hook_module.run_auto_promote()


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
        Then: Reads stdin, runs pipeline, prints ALLOW JSON
        """
        monkeypatch.setattr("sys.stdin", io.StringIO('{"user_prompt": "test"}'))
        monkeypatch.setattr(hook_module, "run_daily_pipeline", MagicMock())

        hook_module.main()

        captured = capsys.readouterr()
        parsed = json.loads(captured.out.strip())
        assert parsed["decision"] == "ALLOW"

    def test_main_outputs_allow_even_on_pipeline_error(
        self, hook_module, monkeypatch: pytest.MonkeyPatch, capsys
    ) -> None:
        """Given: The daily pipeline raises an exception
        When: main() runs
        Then: Still prints ALLOW (never blocks the user)
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
        assert parsed["decision"] == "ALLOW"

    def test_main_handles_stdin_read_error(
        self, hook_module, monkeypatch: pytest.MonkeyPatch, capsys
    ) -> None:
        """Given: stdin.read() raises an error
        When: main() runs
        Then: Still runs pipeline and outputs ALLOW
        """
        mock_stdin = MagicMock()
        mock_stdin.read.side_effect = OSError("stdin broken")
        monkeypatch.setattr("sys.stdin", mock_stdin)
        monkeypatch.setattr(hook_module, "run_daily_pipeline", MagicMock())

        hook_module.main()

        captured = capsys.readouterr()
        parsed = json.loads(captured.out.strip())
        assert parsed["decision"] == "ALLOW"


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
