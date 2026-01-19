# ruff: noqa: D101,D102,D103,PLR2004,S603,S607
"""Tests for stop_combined hook - notification filtering by stop reason."""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add hooks directory to path for import
HOOKS_DIR = Path(__file__).parent.parent / "hooks"
sys.path.insert(0, str(HOOKS_DIR))

from stop_combined import main, spawn_notification_background, workflow_verification


class TestStopReasonFiltering:
    """Tests for notification filtering based on stop reason."""

    def test_notifies_on_end_turn(self) -> None:
        """Should spawn notification when stop reason is 'end_turn'."""
        # Simulate stdin with end_turn reason
        stdin_data = json.dumps({"reason": "end_turn", "final_message": "Done!"})

        with patch("sys.stdin", io.StringIO(stdin_data)):
            with patch("stop_combined.spawn_notification_background") as mock_notify:
                with pytest.raises(SystemExit) as exc_info:
                    main()

        assert exc_info.value.code == 0
        mock_notify.assert_called_once()

    def test_no_notification_on_tool_use(self) -> None:
        """Should NOT notify when stop reason is 'tool_use' (intermediate)."""
        stdin_data = json.dumps({"reason": "tool_use", "final_message": ""})

        with patch("sys.stdin", io.StringIO(stdin_data)):
            with patch("stop_combined.spawn_notification_background") as mock_notify:
                with pytest.raises(SystemExit):
                    main()

        mock_notify.assert_not_called()

    def test_no_notification_on_max_tokens(self) -> None:
        """Should NOT notify when stop reason is 'max_tokens'."""
        stdin_data = json.dumps({"reason": "max_tokens", "final_message": ""})

        with patch("sys.stdin", io.StringIO(stdin_data)):
            with patch("stop_combined.spawn_notification_background") as mock_notify:
                with pytest.raises(SystemExit):
                    main()

        mock_notify.assert_not_called()

    def test_no_notification_on_stop_sequence(self) -> None:
        """Should NOT notify when stop reason is 'stop_sequence'."""
        stdin_data = json.dumps({"reason": "stop_sequence", "final_message": ""})

        with patch("sys.stdin", io.StringIO(stdin_data)):
            with patch("stop_combined.spawn_notification_background") as mock_notify:
                with pytest.raises(SystemExit):
                    main()

        mock_notify.assert_not_called()

    def test_no_notification_on_empty_reason(self) -> None:
        """Should NOT notify when stop reason is missing/empty."""
        stdin_data = json.dumps({"final_message": "Done!"})

        with patch("sys.stdin", io.StringIO(stdin_data)):
            with patch("stop_combined.spawn_notification_background") as mock_notify:
                with pytest.raises(SystemExit):
                    main()

        mock_notify.assert_not_called()

    def test_no_notification_on_invalid_json(self) -> None:
        """Should NOT notify when stdin is invalid JSON."""
        with patch("sys.stdin", io.StringIO("not valid json")):
            with patch("stop_combined.spawn_notification_background") as mock_notify:
                with pytest.raises(SystemExit):
                    main()

        mock_notify.assert_not_called()

    def test_no_notification_on_empty_stdin(self) -> None:
        """Should NOT notify when stdin is empty."""
        with patch("sys.stdin", io.StringIO("")):
            with patch("stop_combined.spawn_notification_background") as mock_notify:
                with pytest.raises(SystemExit):
                    main()

        mock_notify.assert_not_called()


class TestWorkflowVerification:
    """Tests for workflow verification output."""

    def test_returns_reminder_in_reason(self) -> None:
        """Should return workflow reminder in reason field."""
        result = workflow_verification()

        assert "reason" in result
        assert "PROOF-OF-WORK" in result["reason"]
        assert "Documentation Updates" in result["reason"]

    def test_outputs_valid_json(self) -> None:
        """Main should output valid JSON with workflow reminder."""
        stdin_data = json.dumps({"reason": "end_turn"})

        with patch("sys.stdin", io.StringIO(stdin_data)):
            with patch("stop_combined.spawn_notification_background"):
                with patch("builtins.print") as mock_print:
                    with pytest.raises(SystemExit):
                        main()

        # Verify output is valid JSON
        call_args = mock_print.call_args[0][0]
        output = json.loads(call_args)
        assert "reason" in output


class TestSpawnNotificationBackground:
    """Tests for background notification spawning."""

    def test_skips_when_disabled(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should not spawn when CLAUDE_NO_NOTIFICATIONS=1."""
        monkeypatch.setenv("CLAUDE_NO_NOTIFICATIONS", "1")

        with patch("stop_combined.subprocess.Popen") as mock_popen:
            spawn_notification_background()

        mock_popen.assert_not_called()

    def test_spawns_when_enabled(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should spawn notification subprocess when enabled."""
        monkeypatch.delenv("CLAUDE_NO_NOTIFICATIONS", raising=False)

        with patch("stop_combined.subprocess.Popen") as mock_popen:
            with patch("stop_combined.os.path.exists", return_value=True):
                spawn_notification_background()

        mock_popen.assert_called_once()
        call_args = mock_popen.call_args[0][0]
        assert "--background" in call_args

    def test_fails_silently_on_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should not raise on subprocess errors (notifications are non-critical)."""
        monkeypatch.delenv("CLAUDE_NO_NOTIFICATIONS", raising=False)

        with patch("stop_combined.subprocess.Popen") as mock_popen:
            mock_popen.side_effect = OSError("spawn failed")
            with patch("stop_combined.os.path.exists", return_value=True):
                # Should not raise
                spawn_notification_background()
