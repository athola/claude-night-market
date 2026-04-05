# ruff: noqa: D101,D102,D103,D205,D212,PLR2004,E501,E402,I001
"""Tests for permission_denied_logger hook — in-process coverage.

Tests PermissionDenied event handling: JSON parsing from stdin,
JSONL log file creation, and auto-retry signaling for read-only tools.
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

from permission_denied_logger import RETRY_SAFE_TOOLS, main


# ============================================================================
# RETRY_SAFE_TOOLS constant
# ============================================================================


class TestRetrySafeTools:
    """Feature: RETRY_SAFE_TOOLS contains only read-only operations."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_is_a_frozenset(self) -> None:
        """Given RETRY_SAFE_TOOLS, it should be immutable."""
        assert isinstance(RETRY_SAFE_TOOLS, frozenset)

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_contains_expected_read_only_tools(self) -> None:
        """Given RETRY_SAFE_TOOLS, it should include Read, Glob, Grep."""
        for tool in ("Read", "Glob", "Grep"):
            assert tool in RETRY_SAFE_TOOLS

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_does_not_contain_write_tools(self) -> None:
        """Given RETRY_SAFE_TOOLS, it should not include Write, Edit, Bash."""
        for tool in ("Write", "Edit", "Bash"):
            assert tool not in RETRY_SAFE_TOOLS


# ============================================================================
# main() — retry signaling
# ============================================================================


class TestMainRetrySignaling:
    """Feature: main() outputs retry signal for read-only tools."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_retry_safe_tool_emits_retry_true(self, tmp_path) -> None:
        """
        Given a PermissionDenied event for a read-only tool,
        When main() processes it,
        Then it should output {"retry": true} on stdout.
        """
        input_data = json.dumps(
            {
                "tool_name": "Read",
                "reason": "auto-mode classifier denied",
            }
        )
        captured_stdout = StringIO()
        captured_stderr = StringIO()
        with (
            patch("sys.stdin", StringIO(input_data)),
            patch("sys.stdout", captured_stdout),
            patch("sys.stderr", captured_stderr),
            patch(
                "permission_denied_logger.LOG_DIR",
                tmp_path / "logs",
            ),
        ):
            try:
                main()
                code = 0
            except SystemExit as e:
                code = e.code if e.code is not None else 0

        assert code == 0
        output = captured_stdout.getvalue().strip()
        assert json.loads(output) == {"retry": True}

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_non_retry_tool_does_not_emit_retry(self, tmp_path) -> None:
        """
        Given a PermissionDenied event for a write tool,
        When main() processes it,
        Then it should NOT output retry JSON on stdout.
        """
        input_data = json.dumps(
            {
                "tool_name": "Write",
                "reason": "auto-mode classifier denied",
            }
        )
        captured_stdout = StringIO()
        captured_stderr = StringIO()
        with (
            patch("sys.stdin", StringIO(input_data)),
            patch("sys.stdout", captured_stdout),
            patch("sys.stderr", captured_stderr),
            patch(
                "permission_denied_logger.LOG_DIR",
                tmp_path / "logs",
            ),
        ):
            try:
                main()
                code = 0
            except SystemExit as e:
                code = e.code if e.code is not None else 0

        assert code == 0
        assert captured_stdout.getvalue().strip() == ""

    @pytest.mark.bdd
    @pytest.mark.unit
    @pytest.mark.parametrize("tool_name", list(RETRY_SAFE_TOOLS))
    def test_all_safe_tools_emit_retry(self, tmp_path, tool_name) -> None:
        """
        Given each tool in RETRY_SAFE_TOOLS,
        When denied by auto-mode,
        Then main() should emit retry: true.
        """
        input_data = json.dumps(
            {
                "tool_name": tool_name,
                "reason": "denied",
            }
        )
        captured_stdout = StringIO()
        with (
            patch("sys.stdin", StringIO(input_data)),
            patch("sys.stdout", captured_stdout),
            patch("sys.stderr", StringIO()),
            patch(
                "permission_denied_logger.LOG_DIR",
                tmp_path / "logs",
            ),
        ):
            try:
                main()
            except SystemExit:
                pass

        output = captured_stdout.getvalue().strip()
        assert json.loads(output) == {"retry": True}


# ============================================================================
# main() — logging behavior
# ============================================================================


class TestMainLogging:
    """Feature: main() logs denials to stderr and JSONL file."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_logs_denial_to_stderr(self, tmp_path) -> None:
        """
        Given a PermissionDenied event,
        When main() processes it,
        Then it should log the denial to stderr.
        """
        input_data = json.dumps(
            {
                "tool_name": "Bash",
                "reason": "risky command",
            }
        )
        captured_stderr = StringIO()
        with (
            patch("sys.stdin", StringIO(input_data)),
            patch("sys.stdout", StringIO()),
            patch("sys.stderr", captured_stderr),
            patch(
                "permission_denied_logger.LOG_DIR",
                tmp_path / "logs",
            ),
        ):
            try:
                main()
            except SystemExit:
                pass

        stderr_output = captured_stderr.getvalue()
        assert "[PermissionDenied]" in stderr_output
        assert "tool=Bash" in stderr_output
        assert "reason=risky command" in stderr_output

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_writes_jsonl_log_file(self, tmp_path) -> None:
        """
        Given a PermissionDenied event,
        When main() processes it,
        Then it should append a JSONL entry to the log file.
        """
        log_dir = tmp_path / "logs"
        input_data = json.dumps(
            {
                "tool_name": "Edit",
                "reason": "classifier denied",
            }
        )
        with (
            patch("sys.stdin", StringIO(input_data)),
            patch("sys.stdout", StringIO()),
            patch("sys.stderr", StringIO()),
            patch("permission_denied_logger.LOG_DIR", log_dir),
        ):
            try:
                main()
            except SystemExit:
                pass

        log_file = log_dir / "permission_denials.jsonl"
        assert log_file.exists()
        entry = json.loads(log_file.read_text().strip())
        assert entry["tool"] == "Edit"
        assert entry["reason"] == "classifier denied"
        assert "timestamp" in entry
        assert "session" in entry

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_appends_multiple_entries(self, tmp_path) -> None:
        """
        Given two PermissionDenied events,
        When main() processes each,
        Then the log file should contain two JSONL lines.
        """
        log_dir = tmp_path / "logs"
        for tool in ("Bash", "Write"):
            input_data = json.dumps(
                {
                    "tool_name": tool,
                    "reason": "denied",
                }
            )
            with (
                patch("sys.stdin", StringIO(input_data)),
                patch("sys.stdout", StringIO()),
                patch("sys.stderr", StringIO()),
                patch("permission_denied_logger.LOG_DIR", log_dir),
            ):
                try:
                    main()
                except SystemExit:
                    pass

        log_file = log_dir / "permission_denials.jsonl"
        lines = log_file.read_text().strip().split("\n")
        assert len(lines) == 2
        assert json.loads(lines[0])["tool"] == "Bash"
        assert json.loads(lines[1])["tool"] == "Write"


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
            patch("sys.stdin", StringIO("not valid json")),
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
    def test_missing_tool_name_uses_unknown(self, tmp_path) -> None:
        """
        Given JSON without tool_name,
        When main() processes it,
        Then it should default to 'unknown'.
        """
        input_data = json.dumps({"reason": "some reason"})
        captured_stderr = StringIO()
        with (
            patch("sys.stdin", StringIO(input_data)),
            patch("sys.stdout", StringIO()),
            patch("sys.stderr", captured_stderr),
            patch(
                "permission_denied_logger.LOG_DIR",
                tmp_path / "logs",
            ),
        ):
            try:
                main()
            except SystemExit:
                pass

        assert "tool=unknown" in captured_stderr.getvalue()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_log_dir_write_failure_does_not_crash(self) -> None:
        """
        Given a non-writable log directory,
        When main() tries to write the JSONL log,
        Then it should still exit 0 (logging is non-critical).
        """
        input_data = json.dumps(
            {
                "tool_name": "Bash",
                "reason": "denied",
            }
        )
        with (
            patch("sys.stdin", StringIO(input_data)),
            patch("sys.stdout", StringIO()),
            patch("sys.stderr", StringIO()),
            patch(
                "permission_denied_logger.LOG_DIR",
                Path("/nonexistent/impossible/path"),
            ),
        ):
            try:
                main()
                code = 0
            except SystemExit as e:
                code = e.code if e.code is not None else 0

        assert code == 0
