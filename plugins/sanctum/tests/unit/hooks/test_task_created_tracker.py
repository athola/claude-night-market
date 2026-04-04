# ruff: noqa: D101,D102,D103,D205,D212,PLR2004,E501,E402,I001
"""Tests for task_created_tracker hook — in-process coverage.

Tests TaskCreated event handling: JSON parsing from stdin,
ledger file creation, description truncation, and error resilience.
All tests call hook functions directly for branch coverage.
"""

from __future__ import annotations

import json
import sys
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest

# Add hooks directory to path for import
HOOKS_DIR = Path(__file__).resolve().parents[3] / "hooks"
sys.path.insert(0, str(HOOKS_DIR))

from task_created_tracker import main


# ============================================================================
# main() — task tracking
# ============================================================================


class TestMainTaskTracking:
    """Feature: main() records created tasks to a session ledger."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_writes_task_to_ledger(self, tmp_path) -> None:
        """
        Given a TaskCreated event with task_id and description,
        When main() processes it,
        Then it should write a JSONL entry to the session ledger.
        """
        state_dir = tmp_path / "state"
        input_data = json.dumps(
            {
                "task_id": "task-42",
                "description": "Implement feature X",
            }
        )
        with (
            patch("sys.stdin", StringIO(input_data)),
            patch("sys.stdout", StringIO()),
            patch("sys.stderr", StringIO()),
            patch("task_created_tracker.STATE_DIR", state_dir),
            patch.dict(
                "os.environ",
                {"CLAUDE_SESSION_ID": "sess-abc"},
            ),
        ):
            try:
                main()
            except SystemExit:
                pass

        ledger = state_dir / "tasks_sess-abc.jsonl"
        assert ledger.exists()
        entry = json.loads(ledger.read_text().strip())
        assert entry["event"] == "created"
        assert entry["task_id"] == "task-42"
        assert entry["description"] == "Implement feature X"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_appends_multiple_tasks(self, tmp_path) -> None:
        """
        Given two TaskCreated events,
        When main() processes each,
        Then the ledger should contain two JSONL lines.
        """
        state_dir = tmp_path / "state"
        for task_id in ("task-1", "task-2"):
            input_data = json.dumps(
                {
                    "task_id": task_id,
                    "description": f"Task {task_id}",
                }
            )
            with (
                patch("sys.stdin", StringIO(input_data)),
                patch("sys.stdout", StringIO()),
                patch("sys.stderr", StringIO()),
                patch("task_created_tracker.STATE_DIR", state_dir),
                patch.dict(
                    "os.environ",
                    {"CLAUDE_SESSION_ID": "sess-xyz"},
                ),
            ):
                try:
                    main()
                except SystemExit:
                    pass

        ledger = state_dir / "tasks_sess-xyz.jsonl"
        lines = ledger.read_text().strip().split("\n")
        assert len(lines) == 2
        assert json.loads(lines[0])["task_id"] == "task-1"
        assert json.loads(lines[1])["task_id"] == "task-2"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_logs_task_to_stderr(self, tmp_path) -> None:
        """
        Given a TaskCreated event,
        When main() processes it,
        Then it should log the task info to stderr.
        """
        input_data = json.dumps(
            {
                "task_id": "task-99",
                "description": "Build the widget",
            }
        )
        captured_stderr = StringIO()
        with (
            patch("sys.stdin", StringIO(input_data)),
            patch("sys.stdout", StringIO()),
            patch("sys.stderr", captured_stderr),
            patch(
                "task_created_tracker.STATE_DIR",
                tmp_path / "state",
            ),
        ):
            try:
                main()
            except SystemExit:
                pass

        stderr_output = captured_stderr.getvalue()
        assert "[TaskCreated]" in stderr_output
        assert "task-99" in stderr_output
        assert "Build the widget" in stderr_output


# ============================================================================
# main() — description truncation
# ============================================================================


class TestMainDescriptionTruncation:
    """Feature: main() truncates long descriptions to prevent bloat."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_truncates_description_at_200_chars_in_ledger(self, tmp_path) -> None:
        """
        Given a TaskCreated event with a 300-char description,
        When main() writes to the ledger,
        Then the stored description should be at most 200 chars.
        """
        state_dir = tmp_path / "state"
        long_desc = "A" * 300
        input_data = json.dumps(
            {
                "task_id": "task-long",
                "description": long_desc,
            }
        )
        with (
            patch("sys.stdin", StringIO(input_data)),
            patch("sys.stdout", StringIO()),
            patch("sys.stderr", StringIO()),
            patch("task_created_tracker.STATE_DIR", state_dir),
            patch.dict(
                "os.environ",
                {"CLAUDE_SESSION_ID": "sess-trunc"},
            ),
        ):
            try:
                main()
            except SystemExit:
                pass

        ledger = state_dir / "tasks_sess-trunc.jsonl"
        entry = json.loads(ledger.read_text().strip())
        assert len(entry["description"]) == 200

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_truncates_description_at_80_chars_in_stderr(self, tmp_path) -> None:
        """
        Given a TaskCreated event with a 150-char description,
        When main() logs to stderr,
        Then the stderr message should truncate at 80 chars.
        """
        long_desc = "B" * 150
        input_data = json.dumps(
            {
                "task_id": "task-stderr",
                "description": long_desc,
            }
        )
        captured_stderr = StringIO()
        with (
            patch("sys.stdin", StringIO(input_data)),
            patch("sys.stdout", StringIO()),
            patch("sys.stderr", captured_stderr),
            patch(
                "task_created_tracker.STATE_DIR",
                tmp_path / "state",
            ),
        ):
            try:
                main()
            except SystemExit:
                pass

        stderr_output = captured_stderr.getvalue()
        # The full 150-char description should NOT appear in stderr
        assert long_desc not in stderr_output
        # But the first 80 chars should
        assert long_desc[:80] in stderr_output


# ============================================================================
# main() — empty/missing task_id
# ============================================================================


class TestMainEmptyTaskId:
    """Feature: main() skips tasks with no task_id."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_empty_task_id_exits_0_no_ledger(self, tmp_path) -> None:
        """
        Given a TaskCreated event with empty task_id,
        When main() processes it,
        Then it should exit 0 without creating a ledger.
        """
        state_dir = tmp_path / "state"
        input_data = json.dumps(
            {
                "task_id": "",
                "description": "orphan task",
            }
        )
        with (
            patch("sys.stdin", StringIO(input_data)),
            patch("sys.stdout", StringIO()),
            patch("sys.stderr", StringIO()),
            patch("task_created_tracker.STATE_DIR", state_dir),
        ):
            try:
                main()
                code = 0
            except SystemExit as e:
                code = e.code if e.code is not None else 0

        assert code == 0
        # No ledger file should be created
        assert not state_dir.exists() or not list(state_dir.iterdir())

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_missing_task_id_key_exits_0(self, tmp_path) -> None:
        """
        Given a TaskCreated event without task_id key,
        When main() processes it,
        Then it should exit 0 without creating a ledger.
        """
        state_dir = tmp_path / "state"
        input_data = json.dumps({"description": "no id"})
        with (
            patch("sys.stdin", StringIO(input_data)),
            patch("sys.stdout", StringIO()),
            patch("sys.stderr", StringIO()),
            patch("task_created_tracker.STATE_DIR", state_dir),
        ):
            try:
                main()
                code = 0
            except SystemExit as e:
                code = e.code if e.code is not None else 0

        assert code == 0


# ============================================================================
# main() — error handling
# ============================================================================


class TestMainErrorHandling:
    """Feature: main() handles malformed input gracefully."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_invalid_json_exits_0(self) -> None:
        """Given invalid JSON on stdin, main() exits with code 0."""
        with (
            patch("sys.stdin", StringIO("not json")),
            patch("sys.stdout", StringIO()),
            patch("sys.stderr", StringIO()),
        ):
            try:
                main()
                code = 0
            except SystemExit as e:
                code = e.code if e.code is not None else 0

        assert code == 0

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_empty_stdin_exits_0(self) -> None:
        """Given empty stdin, main() exits with code 0."""
        with (
            patch("sys.stdin", StringIO("")),
            patch("sys.stdout", StringIO()),
            patch("sys.stderr", StringIO()),
        ):
            try:
                main()
                code = 0
            except SystemExit as e:
                code = e.code if e.code is not None else 0

        assert code == 0

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_state_dir_write_failure_does_not_crash(self) -> None:
        """
        Given a non-writable state directory,
        When main() tries to write the ledger,
        Then it should still exit 0 (tracking is non-critical).
        """
        input_data = json.dumps(
            {
                "task_id": "task-fail",
                "description": "should not crash",
            }
        )
        with (
            patch("sys.stdin", StringIO(input_data)),
            patch("sys.stdout", StringIO()),
            patch("sys.stderr", StringIO()),
            patch(
                "task_created_tracker.STATE_DIR",
                Path("/nonexistent/impossible/path"),
            ),
        ):
            try:
                main()
                code = 0
            except SystemExit as e:
                code = e.code if e.code is not None else 0

        assert code == 0
