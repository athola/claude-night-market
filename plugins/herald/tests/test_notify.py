"""Tests for the herald notification system.

Feature: Standalone notification system
    As a Claude Code plugin developer
    I want a standalone notification library
    So that I can send alerts via GitHub issues and webhooks
    independently of the egregore orchestrator.
"""

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
    """Feature: Webhook URL validation prevents SSRF attacks.

    As a plugin operator
    I want webhook URLs validated against SSRF
    So that internal services cannot be reached via webhook config.
    """

    def test_accepts_valid_https_url(self) -> None:
        """Scenario: Valid public HTTPS URL passes validation.

        Given a valid https URL pointing to a public host
        When validating the URL
        Then no error is raised.
        """
        validate_webhook_url("https://hooks.slack.com/services/T00/B00/xxx")

    def test_accepts_https_with_port(self) -> None:
        """Scenario: HTTPS URL with explicit port passes validation.

        Given an https URL with a non-standard port
        When validating the URL
        Then no error is raised.
        """
        validate_webhook_url("https://example.com:8443/webhook")

    def test_rejects_http_scheme(self) -> None:
        """Scenario: HTTP scheme is rejected.

        Given an http:// URL
        When validating the URL
        Then raises WebhookURLError mentioning https.
        """
        with pytest.raises(WebhookURLError, match="https://"):
            validate_webhook_url("http://example.com/hook")

    def test_rejects_file_scheme(self) -> None:
        """Scenario: file:// scheme is rejected.

        Given a file:// URL
        When validating the URL
        Then raises WebhookURLError mentioning https.
        """
        with pytest.raises(WebhookURLError, match="https://"):
            validate_webhook_url("file:///etc/passwd")

    def test_rejects_ftp_scheme(self) -> None:
        """Scenario: ftp:// scheme is rejected.

        Given an ftp:// URL
        When validating the URL
        Then raises WebhookURLError mentioning https.
        """
        with pytest.raises(WebhookURLError, match="https://"):
            validate_webhook_url("ftp://evil.com/payload")

    def test_rejects_empty_scheme(self) -> None:
        """Scenario: URL with no scheme is rejected.

        Given a URL with no scheme
        When validating the URL
        Then raises WebhookURLError mentioning https.
        """
        with pytest.raises(WebhookURLError, match="https://"):
            validate_webhook_url("example.com/hook")

    def test_rejects_localhost(self) -> None:
        """Scenario: localhost is rejected.

        Given https://localhost
        When validating the URL
        Then raises WebhookURLError mentioning localhost.
        """
        with pytest.raises(WebhookURLError, match="localhost"):
            validate_webhook_url("https://localhost/admin")

    def test_rejects_localhost_localdomain(self) -> None:
        """Scenario: localhost.localdomain is rejected.

        Given https://localhost.localdomain
        When validating the URL
        Then raises WebhookURLError mentioning localhost.
        """
        with pytest.raises(WebhookURLError, match="localhost"):
            validate_webhook_url("https://localhost.localdomain/admin")

    def test_rejects_127_0_0_1(self) -> None:
        """Scenario: IPv4 loopback 127.0.0.1 is rejected.

        Given https://127.0.0.1
        When validating the URL
        Then raises WebhookURLError mentioning private/reserved.
        """
        with pytest.raises(WebhookURLError, match="private/reserved"):
            validate_webhook_url("https://127.0.0.1/admin")

    def test_rejects_0_0_0_0(self) -> None:
        """Scenario: 0.0.0.0 is rejected.

        Given https://0.0.0.0
        When validating the URL
        Then raises WebhookURLError mentioning private/reserved.
        """
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
        """Scenario: Private IP ranges are rejected.

        Given an https URL pointing to a private IP
        When validating the URL
        Then raises WebhookURLError mentioning private/reserved.
        """
        with pytest.raises(WebhookURLError, match="private/reserved"):
            validate_webhook_url(f"https://{ip}/hook")

    def test_rejects_ipv6_loopback(self) -> None:
        """Scenario: IPv6 loopback ::1 is rejected.

        Given https://[::1]
        When validating the URL
        Then raises WebhookURLError mentioning private/reserved.
        """
        with pytest.raises(WebhookURLError, match="private/reserved"):
            validate_webhook_url("https://[::1]/hook")

    def test_rejects_empty_hostname(self) -> None:
        """Scenario: URL with empty hostname is rejected.

        Given https:///path (no hostname)
        When validating the URL
        Then raises WebhookURLError mentioning no hostname.
        """
        with pytest.raises(WebhookURLError, match="no hostname"):
            validate_webhook_url("https:///path")

    def test_send_webhook_rejects_invalid_url(self) -> None:
        """Scenario: send_webhook rejects non-https URL.

        Given an http URL
        When calling send_webhook
        Then returns False without making a request.
        """
        result = send_webhook(
            url="http://internal-service.local/api",
            event=AlertEvent.CRASH,
            detail="test",
        )
        assert result is False

    @patch("subprocess.run")
    def test_send_webhook_rejects_private_ip(self, mock_run: MagicMock) -> None:
        """Scenario: send_webhook rejects private IP without calling curl.

        Given a private IP webhook URL
        When calling send_webhook
        Then returns False and subprocess.run is not called.
        """
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
        """Scenario: alert() returns False when all channels fail.

        Given an invalid webhook URL and disabled GitHub method
        When calling alert()
        Then returns False.
        """
        result = alert(
            event=AlertEvent.CRASH,
            webhook_url="http://localhost/admin",
            overseer_method="none",
        )
        assert result is False


class TestBuildIssueBody:
    """Feature: Issue body formatting for GitHub alerts.

    As a notification consumer
    I want well-formatted GitHub issue bodies
    So that alerts are easy to read and triage.
    """

    def test_crash_event_contains_key_fields(self) -> None:
        """Scenario: Crash event body includes all context fields.

        Given a crash event with full context
        When building the issue body
        Then all fields appear in the output.
        """
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
        """Scenario: Completion event body includes detail.

        Given a completion event with work item and detail
        When building the issue body
        Then both appear in the output.
        """
        body = build_issue_body(
            event=AlertEvent.COMPLETION,
            work_item_id="WI-99",
            detail="All tasks finished successfully",
        )
        assert "completion" in body.lower()
        assert "WI-99" in body
        assert "All tasks finished successfully" in body

    def test_rate_limit_event(self) -> None:
        """Scenario: Rate limit event includes stage and detail.

        Given a rate_limit event with stage and detail
        When building the issue body
        Then both appear in the output.
        """
        body = build_issue_body(
            event=AlertEvent.RATE_LIMIT,
            stage="deploy",
            detail="API quota exceeded",
        )
        assert "rate_limit" in body.lower() or "rate limit" in body.lower()
        assert "deploy" in body
        assert "API quota exceeded" in body

    def test_body_with_alert_context(self) -> None:
        """Scenario: AlertContext object provides all fields.

        Given an AlertContext with all fields populated
        When building the issue body with ctx=
        Then all context fields appear in the output.
        """
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
        """Scenario: Missing detail shows placeholder text.

        Given no detail argument
        When building the issue body
        Then a placeholder message appears.
        """
        body = build_issue_body(event=AlertEvent.COMPLETION)
        assert "No additional detail provided" in body

    @pytest.mark.parametrize(
        "event",
        list(AlertEvent),
        ids=[e.value for e in AlertEvent],
    )
    def test_body_includes_event_value(self, event: AlertEvent) -> None:
        """Scenario: Every event type appears in the body.

        Given any AlertEvent enum value
        When building the issue body
        Then the event's string value appears in the output.
        """
        body = build_issue_body(event=event)
        assert event.value in body

    def test_default_source_is_herald(self) -> None:
        """Scenario: Default source label is 'herald'.

        Given no explicit source argument
        When building the issue body
        Then the heading uses 'Herald' as prefix.
        """
        body = build_issue_body(event=AlertEvent.CRASH)
        assert "Herald Alert" in body

    def test_custom_source_label(self) -> None:
        """Scenario: Custom source label overrides default.

        Given source="egregore"
        When building the issue body
        Then the heading uses 'Egregore' as prefix.
        """
        body = build_issue_body(
            event=AlertEvent.CRASH,
            source="egregore",
        )
        assert "Egregore Alert" in body


class TestCreateGithubAlert:
    """Feature: GitHub issue creation via gh CLI.

    As an alerting system
    I want to create GitHub issues for alerts
    So that human overseers are notified through their workflow.
    """

    @patch("subprocess.run")
    def test_calls_gh_issue_create(self, mock_run: MagicMock) -> None:
        """Scenario: Successful issue creation.

        Given valid title, body, and labels
        When creating a GitHub alert
        Then gh CLI is called with correct arguments and returns True.
        """
        mock_run.return_value = MagicMock(returncode=0)
        result = create_github_alert(
            title="[herald] Crash detected",
            body="Something broke",
            labels=["bug", "herald"],
        )
        assert result is True
        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert "gh" in cmd
        assert "issue" in cmd
        assert "create" in cmd
        title_idx = cmd.index("--title")
        assert cmd[title_idx + 1] == "[herald] Crash detected"
        body_idx = cmd.index("--body")
        assert cmd[body_idx + 1] == "Something broke"
        label_idx = cmd.index("--label")
        assert "bug" in cmd[label_idx + 1]

    @patch("subprocess.run")
    def test_without_labels(self, mock_run: MagicMock) -> None:
        """Scenario: Issue creation without labels omits --label flag.

        Given no labels argument
        When creating a GitHub alert
        Then --label is not in the command.
        """
        mock_run.return_value = MagicMock(returncode=0)
        result = create_github_alert(title="Test", body="Body")
        assert result is True
        cmd = mock_run.call_args[0][0]
        assert "--label" not in cmd

    @patch("subprocess.run")
    def test_returns_false_on_nonzero_exit(self, mock_run: MagicMock) -> None:
        """Scenario: gh CLI error returns False.

        Given gh CLI returns a nonzero exit code
        When creating a GitHub alert
        Then returns False.
        """
        mock_run.return_value = MagicMock(returncode=1, stderr="auth required")
        result = create_github_alert(title="Fail", body="Body")
        assert result is False

    @patch("subprocess.run", side_effect=FileNotFoundError)
    def test_returns_false_when_gh_not_found(self, mock_run: MagicMock) -> None:
        """Scenario: Missing gh CLI returns False.

        Given gh CLI is not installed
        When creating a GitHub alert
        Then returns False.
        """
        result = create_github_alert(title="Fail", body="Body")
        assert result is False

    @patch(
        "subprocess.run",
        side_effect=subprocess.TimeoutExpired(cmd="gh", timeout=30),
    )
    def test_returns_false_on_timeout(self, mock_run: MagicMock) -> None:
        """Scenario: gh CLI timeout returns False.

        Given gh CLI times out after 30 seconds
        When creating a GitHub alert
        Then returns False.
        """
        result = create_github_alert(title="Fail", body="Body")
        assert result is False


class TestSendWebhook:
    """Feature: Webhook notification delivery.

    As a plugin operator
    I want webhook notifications sent to Slack, Discord, or generic endpoints
    So that I receive alerts in my preferred communication channel.
    """

    @patch("subprocess.run")
    def test_generic_format(self, mock_run: MagicMock) -> None:
        """Scenario: Generic webhook includes event, detail, and source.

        Given generic webhook format
        When sending a webhook
        Then payload contains event, detail, and source fields.
        """
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
        assert payload["source"] == "herald"

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
        """Scenario: Chat platform formats use correct payload key.

        Given a slack or discord webhook format
        When sending a webhook
        Then the payload uses the platform-specific key.
        """
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
        """Scenario: curl error returns False.

        Given curl returns a nonzero exit code
        When sending a webhook
        Then returns False.
        """
        mock_run.return_value = MagicMock(returncode=1, stderr="connection refused")
        result = send_webhook(url="https://bad.url", event=AlertEvent.CRASH)
        assert result is False

    @patch("subprocess.run", side_effect=FileNotFoundError)
    def test_returns_false_when_curl_not_found(self, mock_run: MagicMock) -> None:
        """Scenario: Missing curl returns False.

        Given curl is not installed
        When sending a webhook
        Then returns False.
        """
        result = send_webhook(url="https://example.com", event=AlertEvent.CRASH)
        assert result is False

    @patch(
        "subprocess.run",
        side_effect=subprocess.TimeoutExpired(cmd="curl", timeout=15),
    )
    def test_returns_false_on_timeout(self, mock_run: MagicMock) -> None:
        """Scenario: curl timeout returns False.

        Given curl times out after 15 seconds
        When sending a webhook
        Then returns False.
        """
        result = send_webhook(url="https://example.com", event=AlertEvent.CRASH)
        assert result is False

    @patch("subprocess.run")
    def test_webhook_without_detail(self, mock_run: MagicMock) -> None:
        """Scenario: Webhook without detail sends event-only message.

        Given no detail argument
        When sending a slack webhook
        Then message contains only the event prefix.
        """
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

    @patch("subprocess.run")
    def test_custom_source_in_generic_payload(self, mock_run: MagicMock) -> None:
        """Scenario: Custom source appears in generic webhook payload.

        Given source="egregore"
        When sending a generic webhook
        Then payload source field is "egregore".
        """
        mock_run.return_value = MagicMock(returncode=0)
        send_webhook(
            url="https://example.com/hook",
            event=AlertEvent.CRASH,
            source="egregore",
        )
        cmd = mock_run.call_args[0][0]
        d_idx = cmd.index("-d")
        payload = json.loads(cmd[d_idx + 1])
        assert payload["source"] == "egregore"

    @patch("subprocess.run")
    def test_custom_source_in_slack_prefix(self, mock_run: MagicMock) -> None:
        """Scenario: Custom source appears in slack message prefix.

        Given source="egregore" and webhook_format="slack"
        When sending a webhook
        Then the text contains [egregore] prefix.
        """
        mock_run.return_value = MagicMock(returncode=0)
        send_webhook(
            url="https://hooks.slack.com/x",
            event=AlertEvent.CRASH,
            detail="test",
            webhook_format="slack",
            source="egregore",
        )
        cmd = mock_run.call_args[0][0]
        d_idx = cmd.index("-d")
        payload = json.loads(cmd[d_idx + 1])
        assert "[egregore]" in payload["text"]


class TestAlert:
    """Feature: Top-level alert dispatcher.

    As a plugin developer
    I want a single alert() function that routes to multiple channels
    So that I do not need to call individual notification methods.
    """

    @patch("notify.create_github_alert", return_value=True)
    def test_github_repo_owner_method_creates_issue(
        self, mock_create: MagicMock
    ) -> None:
        """Scenario: GitHub repo owner method creates an issue.

        Given overseer_method="github-repo-owner"
        When calling alert()
        Then a GitHub issue is created with herald labels.
        """
        result = alert(
            event=AlertEvent.CRASH,
            overseer_method="github-repo-owner",
            detail="System failure",
        )
        assert result is True
        mock_create.assert_called_once()
        call_kwargs = mock_create.call_args[1]
        assert "herald" in call_kwargs["title"]
        assert "crash" in call_kwargs["title"]
        assert "herald" in call_kwargs["labels"]

    @patch("notify.create_github_alert", return_value=True)
    def test_alert_includes_work_item_id_in_title(self, mock_create: MagicMock) -> None:
        """Scenario: Work item ID appears in issue title.

        Given a work_item_id="WI-55"
        When calling alert()
        Then the GitHub issue title includes WI-55.
        """
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
        """Scenario: Webhook succeeds when GitHub fails.

        Given GitHub alert creation fails
        When calling alert() with a webhook URL
        Then returns True because webhook succeeded.
        """
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
        """Scenario: All notification channels fail returns False.

        Given both GitHub and webhook fail
        When calling alert()
        Then returns False.
        """
        result = alert(
            event=AlertEvent.CRASH,
            webhook_url="https://bad.url",
        )
        assert result is False

    @patch("notify.create_github_alert", return_value=True)
    def test_alert_with_context_object(self, mock_create: MagicMock) -> None:
        """Scenario: AlertContext object provides all fields to alert().

        Given an AlertContext with all fields
        When calling alert()
        Then the issue body includes all context fields.
        """
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
        """Scenario: No webhook URL means only GitHub is attempted.

        Given no webhook_url
        When calling alert()
        Then only GitHub is tried, not webhooks.
        """
        result = alert(
            event=AlertEvent.CRASH,
            overseer_method="github-repo-owner",
        )
        assert result is False
        mock_create.assert_called_once()

    @patch("notify.send_webhook", return_value=True)
    def test_non_github_method_skips_github(self, mock_wh: MagicMock) -> None:
        """Scenario: Non-github method skips issue creation.

        Given overseer_method="webhook-only"
        When calling alert() with a webhook URL
        Then only the webhook is called.
        """
        result = alert(
            event=AlertEvent.WATCHDOG_RELAUNCH,
            overseer_method="webhook-only",
            webhook_url="https://example.com/hook",
        )
        assert result is True
        mock_wh.assert_called_once()

    @patch("notify.create_github_alert", return_value=True)
    def test_custom_source_passed_to_github(self, mock_create: MagicMock) -> None:
        """Scenario: Custom source label appears in GitHub issue.

        Given source="egregore"
        When calling alert()
        Then the issue title and labels use "egregore".
        """
        alert(
            event=AlertEvent.CRASH,
            source="egregore",
        )
        call_kwargs = mock_create.call_args[1]
        assert "[egregore]" in call_kwargs["title"]
        assert "egregore" in call_kwargs["labels"]

    @patch("notify.send_webhook", return_value=True)
    def test_custom_source_passed_to_webhook(self, mock_wh: MagicMock) -> None:
        """Scenario: Custom source label flows to webhook.

        Given source="egregore" and a webhook URL
        When calling alert()
        Then send_webhook receives source="egregore".
        """
        alert(
            event=AlertEvent.CRASH,
            overseer_method="none",
            webhook_url="https://example.com/hook",
            source="egregore",
        )
        assert mock_wh.call_args[1]["source"] == "egregore"
