"""Tests for the egregore notification system."""

from __future__ import annotations

import json
import subprocess
from unittest.mock import MagicMock, patch

import pytest
from notify import (
    AlertContext,
    AlertEvent,
    WebhookURLError,
    alert,
    build_issue_body,
    create_github_alert,
    send_webhook,
    validate_webhook_url,
)


class TestValidateWebhookUrl:
    """Tests for validate_webhook_url."""

    def test_accepts_valid_https_url(self) -> None:
        """Given a valid https URL, when validating, then no error is raised."""
        validate_webhook_url("https://hooks.slack.com/services/T00/B00/xxx")

    def test_accepts_https_with_port(self) -> None:
        """Given an https URL with a port, when validating, then no error is raised."""
        validate_webhook_url("https://example.com:8443/webhook")

    def test_rejects_http_scheme(self) -> None:
        """Given an http:// URL, when validating, then raises WebhookURLError."""
        with pytest.raises(WebhookURLError, match="https://"):
            validate_webhook_url("http://example.com/hook")

    def test_rejects_file_scheme(self) -> None:
        """Given a file:// URL, when validating, then raises WebhookURLError."""
        with pytest.raises(WebhookURLError, match="https://"):
            validate_webhook_url("file:///etc/passwd")

    def test_rejects_ftp_scheme(self) -> None:
        """Given an ftp:// URL, when validating, then raises WebhookURLError."""
        with pytest.raises(WebhookURLError, match="https://"):
            validate_webhook_url("ftp://evil.com/payload")

    def test_rejects_empty_scheme(self) -> None:
        """Given a URL with no scheme, when validating, then raises WebhookURLError."""
        with pytest.raises(WebhookURLError, match="https://"):
            validate_webhook_url("example.com/hook")

    def test_rejects_localhost(self) -> None:
        """Given https://localhost, when validating, then raises WebhookURLError."""
        with pytest.raises(WebhookURLError, match="localhost"):
            validate_webhook_url("https://localhost/admin")

    def test_rejects_localhost_localdomain(self) -> None:
        """Given localhost.localdomain, when validating, then raises WebhookURLError."""
        with pytest.raises(WebhookURLError, match="localhost"):
            validate_webhook_url("https://localhost.localdomain/admin")

    def test_rejects_127_0_0_1(self) -> None:
        """Given 127.0.0.1, when validating, then raises WebhookURLError."""
        with pytest.raises(WebhookURLError, match="private/reserved"):
            validate_webhook_url("https://127.0.0.1/admin")

    def test_rejects_0_0_0_0(self) -> None:
        """Given 0.0.0.0, when validating, then raises WebhookURLError."""
        with pytest.raises(WebhookURLError, match="private/reserved"):
            validate_webhook_url("https://0.0.0.0/admin")

    @pytest.mark.parametrize(
        "ip",
        [
            "10.0.0.1",
            "10.255.255.255",
            "172.16.0.1",
            "172.31.255.255",
            "192.168.0.1",
            "192.168.1.100",
        ],
        ids=[
            "10.0.0.1",
            "10.255.255.255",
            "172.16.0.1",
            "172.31.255.255",
            "192.168.0.1",
            "192.168.1.100",
        ],
    )
    def test_rejects_private_ip_ranges(self, ip: str) -> None:
        """Given a private IP address, when validating, then raises WebhookURLError."""
        with pytest.raises(WebhookURLError, match="private/reserved"):
            validate_webhook_url(f"https://{ip}/hook")

    def test_rejects_ipv6_loopback(self) -> None:
        """Given IPv6 loopback ::1, when validating, then raises WebhookURLError."""
        with pytest.raises(WebhookURLError, match="private/reserved"):
            validate_webhook_url("https://[::1]/hook")

    def test_rejects_empty_hostname(self) -> None:
        """Given https URL with no hostname, then raises."""
        with pytest.raises(WebhookURLError, match="no hostname"):
            validate_webhook_url("https:///path")

    def test_send_webhook_rejects_invalid_url(self) -> None:
        """Given http URL, send_webhook returns False."""
        result = send_webhook(
            url="http://internal-service.local/api",
            event=AlertEvent.CRASH,
            detail="test",
        )
        assert result is False

    @patch("subprocess.run")
    def test_send_webhook_rejects_private_ip(self, mock_run: MagicMock) -> None:
        """Given private IP URL, returns False and skips curl."""
        result = send_webhook(
            url="https://192.168.1.1/hook",
            event=AlertEvent.CRASH,
        )
        assert result is False
        mock_run.assert_not_called()

    @patch("notify.send_webhook", return_value=False)
    @patch("notify.create_github_alert", return_value=False)
    def test_alert_with_invalid_webhook_returns_false(
        self, mock_gh: MagicMock, mock_wh: MagicMock
    ) -> None:
        """Given an invalid webhook URL in alert(), then overall returns False."""
        result = alert(
            event=AlertEvent.CRASH,
            webhook_url="http://localhost/admin",
            overseer_method="none",
        )
        assert result is False


class TestBuildIssueBody:
    """Tests for build_issue_body."""

    def test_crash_event_contains_key_fields(self) -> None:
        """Given a crash event with full context, when building body, then all fields appear."""
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
        """Given a completion event, when building body, then includes detail."""
        body = build_issue_body(
            event=AlertEvent.COMPLETION,
            work_item_id="WI-99",
            detail="All tasks finished successfully",
        )
        assert "completion" in body.lower()
        assert "WI-99" in body
        assert "All tasks finished successfully" in body

    def test_rate_limit_event(self) -> None:
        """Given a rate-limit event, when building body, then includes stage and detail."""
        body = build_issue_body(
            event=AlertEvent.RATE_LIMIT,
            stage="deploy",
            detail="API quota exceeded",
        )
        assert "rate_limit" in body.lower() or "rate limit" in body.lower()
        assert "deploy" in body
        assert "API quota exceeded" in body

    def test_body_with_alert_context(self) -> None:
        """Given an AlertContext, when building body, then uses context fields."""
        ctx = AlertContext(
            work_item_id="WI-10",
            work_item_ref="fix/auth",
            stage="test",
            step="unit",
            detail="Timeout in auth module",
        )
        body = build_issue_body(event=AlertEvent.CRASH, ctx=ctx)
        assert "WI-10" in body
        assert "fix/auth" in body
        assert "test" in body
        assert "unit" in body
        assert "Timeout in auth module" in body

    def test_body_without_detail_shows_placeholder(self) -> None:
        """Given no detail, when building body, then shows placeholder text."""
        body = build_issue_body(event=AlertEvent.COMPLETION)
        assert "No additional detail provided" in body

    @pytest.mark.parametrize(
        "event",
        list(AlertEvent),
        ids=[e.value for e in AlertEvent],
    )
    def test_body_includes_event_value(self, event: AlertEvent) -> None:
        """Given any event type, when building body, then event value appears."""
        body = build_issue_body(event=event)
        assert event.value in body


class TestCreateGithubAlert:
    """Tests for create_github_alert."""

    @patch("subprocess.run")
    def test_calls_gh_issue_create(self, mock_run: MagicMock) -> None:
        """Given valid args, when creating alert, then invokes gh CLI correctly."""
        mock_run.return_value = MagicMock(returncode=0)
        result = create_github_alert(
            title="[egregore] Crash detected",
            body="Something broke",
            labels=["bug", "egregore"],
        )
        assert result is True
        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert "gh" in cmd
        assert "issue" in cmd
        assert "create" in cmd
        title_idx = cmd.index("--title")
        assert cmd[title_idx + 1] == "[egregore] Crash detected"
        body_idx = cmd.index("--body")
        assert cmd[body_idx + 1] == "Something broke"
        label_idx = cmd.index("--label")
        assert "bug" in cmd[label_idx + 1]

    @patch("subprocess.run")
    def test_without_labels(self, mock_run: MagicMock) -> None:
        """Given no labels, when creating alert, then omits --label flag."""
        mock_run.return_value = MagicMock(returncode=0)
        result = create_github_alert(title="Test", body="Body")
        assert result is True
        cmd = mock_run.call_args[0][0]
        assert "--label" not in cmd

    @patch("subprocess.run")
    def test_returns_false_on_nonzero_exit(self, mock_run: MagicMock) -> None:
        """Given gh CLI returns error, when creating alert, then returns False."""
        mock_run.return_value = MagicMock(returncode=1, stderr="auth required")
        result = create_github_alert(title="Fail", body="Body")
        assert result is False

    @patch("subprocess.run", side_effect=FileNotFoundError)
    def test_returns_false_when_gh_not_found(self, mock_run: MagicMock) -> None:
        """Given gh CLI is missing, when creating alert, then returns False."""
        result = create_github_alert(title="Fail", body="Body")
        assert result is False

    @patch(
        "subprocess.run",
        side_effect=subprocess.TimeoutExpired(cmd="gh", timeout=30),
    )
    def test_returns_false_on_timeout(self, mock_run: MagicMock) -> None:
        """Given gh CLI times out, when creating alert, then returns False."""
        result = create_github_alert(title="Fail", body="Body")
        assert result is False


class TestSendWebhook:
    """Tests for send_webhook."""

    @patch("subprocess.run")
    def test_generic_format(self, mock_run: MagicMock) -> None:
        """Given generic format, when sending webhook, then payload has event/detail/source."""
        mock_run.return_value = MagicMock(returncode=0)
        result = send_webhook(
            url="https://example.com/hook",
            event=AlertEvent.CRASH,
            detail="Server down",
            webhook_format="generic",
        )
        assert result is True
        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert "curl" in cmd
        d_idx = cmd.index("-d")
        payload = json.loads(cmd[d_idx + 1])
        assert payload["event"] == "crash"
        assert payload["detail"] == "Server down"
        assert payload["source"] == "egregore"

    @pytest.mark.parametrize(
        ("fmt", "key"),
        [
            ("slack", "text"),
            ("discord", "content"),
        ],
        ids=["slack-format", "discord-format"],
    )
    @patch("subprocess.run")
    def test_chat_formats(self, mock_run: MagicMock, fmt: str, key: str) -> None:
        """Given slack/discord format, when sending webhook, then uses correct payload key."""
        mock_run.return_value = MagicMock(returncode=0)
        result = send_webhook(
            url="https://hooks.example.com",
            event=AlertEvent.PIPELINE_FAILURE,
            detail="Build broken",
            webhook_format=fmt,
        )
        assert result is True
        cmd = mock_run.call_args[0][0]
        d_idx = cmd.index("-d")
        payload = json.loads(cmd[d_idx + 1])
        assert key in payload
        assert "pipeline_failure" in payload[key]
        assert "Build broken" in payload[key]

    @patch("subprocess.run")
    def test_returns_false_on_nonzero_exit(self, mock_run: MagicMock) -> None:
        """Given curl returns error, when sending webhook, then returns False."""
        mock_run.return_value = MagicMock(returncode=1, stderr="connection refused")
        result = send_webhook(url="https://bad.url", event=AlertEvent.CRASH)
        assert result is False

    @patch("subprocess.run", side_effect=FileNotFoundError)
    def test_returns_false_when_curl_not_found(self, mock_run: MagicMock) -> None:
        """Given curl is missing, when sending webhook, then returns False."""
        result = send_webhook(url="https://example.com", event=AlertEvent.CRASH)
        assert result is False

    @patch(
        "subprocess.run",
        side_effect=subprocess.TimeoutExpired(cmd="curl", timeout=15),
    )
    def test_returns_false_on_timeout(self, mock_run: MagicMock) -> None:
        """Given curl times out, when sending webhook, then returns False."""
        result = send_webhook(url="https://example.com", event=AlertEvent.CRASH)
        assert result is False

    @patch("subprocess.run")
    def test_webhook_without_detail(self, mock_run: MagicMock) -> None:
        """Given no detail, when sending slack webhook, then message has event only."""
        mock_run.return_value = MagicMock(returncode=0)
        send_webhook(
            url="https://hooks.slack.com/x",
            event=AlertEvent.WATCHDOG_RELAUNCH,
            webhook_format="slack",
        )
        cmd = mock_run.call_args[0][0]
        d_idx = cmd.index("-d")
        payload = json.loads(cmd[d_idx + 1])
        assert "watchdog_relaunch" in payload["text"]


class TestAlert:
    """Tests for the top-level alert dispatcher."""

    @patch("notify.create_github_alert", return_value=True)
    def test_github_repo_owner_method_creates_issue(
        self, mock_create: MagicMock
    ) -> None:
        """Given github-repo-owner method, when alerting, then creates GitHub issue."""
        result = alert(
            event=AlertEvent.CRASH,
            overseer_method="github-repo-owner",
            detail="System failure",
        )
        assert result is True
        mock_create.assert_called_once()
        call_kwargs = mock_create.call_args[1]
        assert "egregore" in call_kwargs["title"]
        assert "crash" in call_kwargs["title"]
        assert "egregore" in call_kwargs["labels"]

    @patch("notify.create_github_alert", return_value=True)
    def test_alert_includes_work_item_id_in_title(self, mock_create: MagicMock) -> None:
        """Given a work_item_id, when alerting, then title includes it."""
        alert(
            event=AlertEvent.PIPELINE_FAILURE,
            work_item_id="WI-55",
        )
        title = mock_create.call_args[1]["title"]
        assert "WI-55" in title

    @patch("notify.send_webhook", return_value=True)
    @patch("notify.create_github_alert", return_value=False)
    def test_webhook_fallback_when_github_fails(
        self, mock_gh: MagicMock, mock_wh: MagicMock
    ) -> None:
        """Given GitHub alert fails but webhook succeeds, then returns True."""
        result = alert(
            event=AlertEvent.RATE_LIMIT,
            webhook_url="https://hooks.slack.com/x",
            webhook_format="slack",
            detail="Rate limited",
        )
        assert result is True
        mock_wh.assert_called_once()
        assert mock_wh.call_args[1]["url"] == "https://hooks.slack.com/x"
        assert mock_wh.call_args[1]["webhook_format"] == "slack"

    @patch("notify.send_webhook", return_value=False)
    @patch("notify.create_github_alert", return_value=False)
    def test_returns_false_when_all_methods_fail(
        self, mock_gh: MagicMock, mock_wh: MagicMock
    ) -> None:
        """Given both GitHub and webhook fail, then returns False."""
        result = alert(
            event=AlertEvent.CRASH,
            webhook_url="https://bad.url",
        )
        assert result is False

    @patch("notify.create_github_alert", return_value=True)
    def test_alert_with_context_object(self, mock_create: MagicMock) -> None:
        """Given an AlertContext, when alerting, then uses context fields."""
        ctx = AlertContext(
            work_item_id="WI-77",
            work_item_ref="main",
            stage="deploy",
            step="rollout",
            detail="Rollout complete",
        )
        result = alert(event=AlertEvent.COMPLETION, ctx=ctx)
        assert result is True
        body = mock_create.call_args[1]["body"]
        assert "WI-77" in body
        assert "deploy" in body
        assert "Rollout complete" in body

    @patch("notify.create_github_alert", return_value=False)
    def test_no_webhook_url_skips_webhook(self, mock_create: MagicMock) -> None:
        """Given no webhook_url, when alerting, then only tries GitHub."""
        result = alert(
            event=AlertEvent.CRASH,
            overseer_method="github-repo-owner",
        )
        assert result is False
        mock_create.assert_called_once()

    @patch("notify.send_webhook", return_value=True)
    def test_non_github_method_skips_github(self, mock_wh: MagicMock) -> None:
        """Given non-github overseer method, when alerting, then skips GitHub issue."""
        result = alert(
            event=AlertEvent.WATCHDOG_RELAUNCH,
            overseer_method="webhook-only",
            webhook_url="https://example.com/hook",
        )
        assert result is True
        mock_wh.assert_called_once()
