# ruff: noqa: D101,D102,D103,E402,PLR2004,S603,S607
"""Tests for config_change_audit hook - audit logging for configuration changes.

Tests the ConfigChange hook that logs configuration changes to stderr
for security audit trail purposes. This hook is observe-only and never blocks.
"""

from __future__ import annotations

import json
import sys
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest

# Add hooks directory to path for import
HOOKS_DIR = Path(__file__).parent.parent / "hooks"
sys.path.insert(0, str(HOOKS_DIR))

from config_change_audit import main


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

        with patch("sys.stdin", StringIO(input_data)):
            captured_stderr = StringIO()
            with patch("sys.stderr", captured_stderr):
                with pytest.raises(SystemExit) as exc_info:
                    main()

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

        with patch("sys.stdin", StringIO(input_data)):
            captured_stderr = StringIO()
            with patch("sys.stderr", captured_stderr):
                with pytest.raises(SystemExit):
                    main()

        output = captured_stderr.getvalue()
        # Timestamp should match ISO 8601 pattern ending in Z
        assert "T" in output
        assert "Z" in output

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

            with patch("sys.stdin", StringIO(input_data)):
                captured_stderr = StringIO()
                with patch("sys.stderr", captured_stderr):
                    with pytest.raises(SystemExit) as exc_info:
                        main()

            assert exc_info.value.code == 0
            assert f"source={source}" in captured_stderr.getvalue()


class TestMissingFields:
    """Tests for input with missing optional fields."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_defaults_missing_fields_to_unknown(self) -> None:
        """Given input missing all fields, uses 'unknown' defaults."""
        input_data = json.dumps({})

        with patch("sys.stdin", StringIO(input_data)):
            captured_stderr = StringIO()
            with patch("sys.stderr", captured_stderr):
                with pytest.raises(SystemExit) as exc_info:
                    main()

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
        input_data = json.dumps({"session_id": "partial-sess"})

        with patch("sys.stdin", StringIO(input_data)):
            captured_stderr = StringIO()
            with patch("sys.stderr", captured_stderr):
                with pytest.raises(SystemExit) as exc_info:
                    main()

        assert exc_info.value.code == 0
        output = captured_stderr.getvalue()
        assert "session=partial-sess" in output
        assert "source=unknown" in output


class TestErrorHandling:
    """Tests for malformed or unexpected input."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_invalid_json_exits_cleanly(self) -> None:
        """Given invalid JSON input, exits with code 0 (never blocks)."""
        with patch("sys.stdin", StringIO("not valid json {")):
            captured_stderr = StringIO()
            with patch("sys.stderr", captured_stderr):
                with pytest.raises(SystemExit) as exc_info:
                    main()

        assert exc_info.value.code == 0
        assert "parse failed" in captured_stderr.getvalue()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_empty_stdin_exits_cleanly(self) -> None:
        """Given empty stdin, exits with code 0 (never blocks)."""
        with patch("sys.stdin", StringIO("")):
            captured_stderr = StringIO()
            with patch("sys.stderr", captured_stderr):
                with pytest.raises(SystemExit) as exc_info:
                    main()

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
            with patch("sys.stdin", StringIO(raw)):
                captured_stderr = StringIO()
                with patch("sys.stderr", captured_stderr):
                    with pytest.raises(SystemExit) as exc_info:
                        main()

            assert exc_info.value.code == 0, f"Non-zero exit for input: {raw}"
