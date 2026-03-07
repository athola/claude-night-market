"""Tests for the egregore notification system."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from notify import AlertEvent, build_issue_body, create_github_alert, send_webhook


class TestBuildIssueBody:
    """Tests for build_issue_body."""

    def test_crash_event_contains_key_fields(self) -> None:
        body = build_issue_body(
            event=AlertEvent.CRASH,
            work_item_id="WI-42",
            work_item_ref="feature/login",
            stage="build",
            step="compile",
            detail="Segfault in module X",
        )
        assert "crash" in body.lower()
        assert "WI-42" in body
        assert "feature/login" in body
        assert "build" in body
        assert "compile" in body
        assert "Segfault in module X" in body

    def test_completion_event(self) -> None:
        body = build_issue_body(
            event=AlertEvent.COMPLETION,
            work_item_id="WI-99",
            detail="All tasks finished successfully",
        )
        assert "completion" in body.lower()
        assert "WI-99" in body
        assert "All tasks finished successfully" in body

    def test_rate_limit_event(self) -> None:
        body = build_issue_body(
            event=AlertEvent.RATE_LIMIT,
            stage="deploy",
            detail="API quota exceeded",
        )
        assert "rate_limit" in body.lower() or "rate limit" in body.lower()
        assert "deploy" in body
        assert "API quota exceeded" in body


class TestCreateGithubAlert:
    """Tests for create_github_alert."""

    @patch("subprocess.run")
    def test_calls_gh_issue_create(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(returncode=0)
        create_github_alert(
            title="[egregore] Crash detected",
            body="Something broke",
            labels=["bug", "egregore"],
        )
        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert "gh" in cmd
        assert "issue" in cmd
        assert "create" in cmd
        # Title should be passed
        title_idx = cmd.index("--title")
        assert cmd[title_idx + 1] == "[egregore] Crash detected"
        # Body should be passed
        body_idx = cmd.index("--body")
        assert cmd[body_idx + 1] == "Something broke"
        # Labels should be passed
        label_idx = cmd.index("--label")
        assert "bug" in cmd[label_idx + 1]


class TestSendWebhook:
    """Tests for send_webhook."""

    @patch("subprocess.run")
    def test_generic_format(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(returncode=0)
        send_webhook(
            url="https://example.com/hook",
            event=AlertEvent.CRASH,
            detail="Server down",
            webhook_format="generic",
        )
        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert "curl" in cmd
        # Find the JSON payload in the command
        # The payload should be passed via -d flag
        d_idx = cmd.index("-d")
        payload = json.loads(cmd[d_idx + 1])
        assert payload["event"] == "crash"
        assert payload["detail"] == "Server down"
        assert payload["source"] == "egregore"
