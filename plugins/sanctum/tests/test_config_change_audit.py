# ruff: noqa: D101,D102,D103,E402,PLR2004,S603,S607
"""Tests for config_change_audit hook - audit logging for configuration changes.

Tests the ConfigChange hook that logs configuration changes to stderr
for security audit trail purposes. This hook is observe-only and never blocks.

Mock verification: every patch() has a corresponding assertion that the
patched object was consumed (stdin.read called, stderr written to, etc.).
"""

from __future__ import annotations

import json
import re
import sys
from datetime import UTC, datetime
from io import StringIO
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Add hooks directory to path for import
HOOKS_DIR = Path(__file__).parent.parent / "hooks"
sys.path.insert(0, str(HOOKS_DIR))

from config_change_audit import main


def _make_stdin_mock(data: str) -> Mock:
    """Build a Mock(spec=StringIO) whose .read() returns *data* once."""
    mock = Mock(spec=StringIO)
    mock.read.return_value = data
    return mock


class TestValidInput:
    """Tests for successful audit log output."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_logs_config_change_to_stderr(self) -> None:
        """Given valid ConfigChange JSON input, logs audit line to stderr."""
        input_data = json.dumps(
            {
                "session_id": "abc-123",
                "source": "user_settings",
                "file_path": "/home/user/.claude/settings.json",
                "permission_mode": "default",
            }
        )

        mock_stdin = _make_stdin_mock(input_data)
        with patch("sys.stdin", mock_stdin):
            captured_stderr = StringIO()
            with patch("sys.stderr", captured_stderr):
                with pytest.raises(SystemExit) as exc_info:
                    main()

        # Verify stdin was consumed
        mock_stdin.read.assert_called_once()

        assert exc_info.value.code == 0
        output = captured_stderr.getvalue()
        assert "[CONFIG_CHANGE_AUDIT]" in output
        assert "session=abc-123" in output
        assert "source=user_settings" in output
        assert "file=/home/user/.claude/settings.json" in output
        assert "permission_mode=default" in output

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_includes_utc_timestamp(self) -> None:
        """Given valid input, audit line includes ISO 8601 UTC timestamp."""
        input_data = json.dumps(
            {
                "session_id": "sess-1",
                "source": "project_settings",
                "file_path": "/project/.claude/settings.json",
                "permission_mode": "acceptEdits",
            }
        )

        mock_stdin = _make_stdin_mock(input_data)
        with patch("sys.stdin", mock_stdin):
            captured_stderr = StringIO()
            with patch("sys.stderr", captured_stderr):
                with pytest.raises(SystemExit):
                    main()

        mock_stdin.read.assert_called_once()

        output = captured_stderr.getvalue()
        # Verify ISO 8601 UTC pattern: YYYY-MM-DDTHH:MM:SSZ
        iso_pattern = r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z"
        assert re.search(iso_pattern, output), (
            f"Expected ISO 8601 UTC timestamp in output, got: {output}"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_timestamp_is_utc_not_local(self) -> None:
        """Given valid input and a fixed UTC time, the logged timestamp matches."""
        input_data = json.dumps(
            {
                "session_id": "tz-test",
                "source": "user_settings",
                "file_path": "/path",
                "permission_mode": "default",
            }
        )
        fixed_dt = datetime(2026, 3, 8, 12, 30, 45, tzinfo=UTC)

        mock_stdin = _make_stdin_mock(input_data)
        with patch("sys.stdin", mock_stdin):
            captured_stderr = StringIO()
            with (
                patch("sys.stderr", captured_stderr),
                patch("config_change_audit.datetime") as mock_datetime,
            ):
                mock_datetime.now.return_value = fixed_dt
                mock_datetime.side_effect = lambda *a, **kw: datetime(*a, **kw)
                with pytest.raises(SystemExit):
                    main()

        mock_stdin.read.assert_called_once()
        mock_datetime.now.assert_called_once_with(UTC)
        assert "2026-03-08T12:30:45Z" in captured_stderr.getvalue()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_handles_all_supported_sources(self) -> None:
        """Given each supported source type, logs it correctly."""
        sources = [
            "user_settings",
            "project_settings",
            "local_settings",
            "policy_settings",
            "skills",
        ]

        for source in sources:
            input_data = json.dumps(
                {
                    "session_id": "test",
                    "source": source,
                    "file_path": "/path",
                    "permission_mode": "default",
                }
            )

            mock_stdin = _make_stdin_mock(input_data)
            with patch("sys.stdin", mock_stdin):
                captured_stderr = StringIO()
                with patch("sys.stderr", captured_stderr):
                    with pytest.raises(SystemExit) as exc_info:
                        main()

            mock_stdin.read.assert_called_once()
            assert exc_info.value.code == 0
            stderr_output = captured_stderr.getvalue()
            assert f"source={source}" in stderr_output, (
                f"source={source} not found in: {stderr_output}"
            )


class TestMissingFields:
    """Tests for input with missing optional fields."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_defaults_missing_fields_to_unknown(self) -> None:
        """Given input missing all fields, uses 'unknown' defaults."""
        mock_stdin = _make_stdin_mock(json.dumps({}))

        with patch("sys.stdin", mock_stdin):
            captured_stderr = StringIO()
            with patch("sys.stderr", captured_stderr):
                with pytest.raises(SystemExit) as exc_info:
                    main()

        mock_stdin.read.assert_called_once()
        assert exc_info.value.code == 0
        output = captured_stderr.getvalue()
        assert "session=unknown" in output
        assert "source=unknown" in output
        assert "file=unknown" in output
        assert "permission_mode=unknown" in output

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_partial_input_fills_missing_with_unknown(self) -> None:
        """Given input with only session_id, other fields default to 'unknown'."""
        mock_stdin = _make_stdin_mock(json.dumps({"session_id": "partial-sess"}))

        with patch("sys.stdin", mock_stdin):
            captured_stderr = StringIO()
            with patch("sys.stderr", captured_stderr):
                with pytest.raises(SystemExit) as exc_info:
                    main()

        mock_stdin.read.assert_called_once()
        assert exc_info.value.code == 0
        output = captured_stderr.getvalue()
        assert "session=partial-sess" in output
        assert "source=unknown" in output
        assert "file=unknown" in output
        assert "permission_mode=unknown" in output


class TestErrorHandling:
    """Tests for malformed or unexpected input."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_invalid_json_exits_cleanly(self) -> None:
        """Given invalid JSON input, exits with code 0 (never blocks)."""
        mock_stdin = _make_stdin_mock("not valid json {")

        with patch("sys.stdin", mock_stdin):
            captured_stderr = StringIO()
            with patch("sys.stderr", captured_stderr):
                with pytest.raises(SystemExit) as exc_info:
                    main()

        mock_stdin.read.assert_called_once()
        assert exc_info.value.code == 0
        assert "parse failed" in captured_stderr.getvalue()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_empty_stdin_exits_cleanly(self) -> None:
        """Given empty stdin, exits with code 0 (never blocks)."""
        mock_stdin = _make_stdin_mock("")

        with patch("sys.stdin", mock_stdin):
            captured_stderr = StringIO()
            with patch("sys.stderr", captured_stderr):
                with pytest.raises(SystemExit) as exc_info:
                    main()

        mock_stdin.read.assert_called_once()
        assert exc_info.value.code == 0

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_never_exits_nonzero(self) -> None:
        """Given any input (valid or not), always exits with code 0.

        This is critical: the hook is observe-only and must never block
        configuration changes.
        """
        inputs = [
            "null",
            "[]",
            '{"unexpected_field": true}',
            "42",
        ]

        for raw in inputs:
            mock_stdin = _make_stdin_mock(raw)
            with patch("sys.stdin", mock_stdin):
                captured_stderr = StringIO()
                with patch("sys.stderr", captured_stderr):
                    with pytest.raises(SystemExit) as exc_info:
                        main()

            mock_stdin.read.assert_called_once()
            assert exc_info.value.code == 0, f"Non-zero exit for input: {raw}"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_non_dict_json_logs_debug_and_exits_0(self) -> None:
        """Given JSON that is not an object (e.g. array), logs debug and exits 0."""
        mock_stdin = _make_stdin_mock("[]")

        with patch("sys.stdin", mock_stdin):
            captured_stderr = StringIO()
            with patch("sys.stderr", captured_stderr):
                with pytest.raises(SystemExit) as exc_info:
                    main()

        mock_stdin.read.assert_called_once()
        assert exc_info.value.code == 0
        assert "not a JSON object" in captured_stderr.getvalue()
