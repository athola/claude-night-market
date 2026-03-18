#!/usr/bin/env python3
"""Egregore notification system.

Provides GitHub issue alerts and webhook support for the egregore
autonomous agent orchestrator. Sends notifications on crashes,
rate limits, pipeline failures, completions, and watchdog relaunches.
"""

from __future__ import annotations

import enum
import ipaddress
import json
import logging
import socket
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class WebhookURLError(ValueError):
    """Raised when a webhook URL fails validation."""


def validate_webhook_url(url: str) -> None:
    """Validate that a webhook URL is safe to request.

    Only ``https://`` URLs pointing to public IP addresses are
    allowed.  This prevents SSRF attacks where an attacker who
    controls webhook configuration could reach internal services.

    Args:
        url: The webhook URL to validate.

    Raises:
        WebhookURLError: If the URL uses a forbidden scheme, points
            to localhost, or resolves to a private/reserved IP range.

    """
    parsed = urlparse(url)

    # Scheme must be https
    if parsed.scheme != "https":
        raise WebhookURLError(
            f"Webhook URL must use https:// scheme, got {parsed.scheme!r}"
        )

    hostname = parsed.hostname or ""

    # Reject empty hostname
    if not hostname:
        raise WebhookURLError("Webhook URL has no hostname")

    # Reject localhost variants
    localhost_names = {"localhost", "localhost.localdomain"}
    if hostname.lower() in localhost_names:
        raise WebhookURLError(f"Webhook URL must not target localhost ({hostname!r})")

    # Check if hostname is an IP address and reject private/reserved ranges
    try:
        addr = ipaddress.ip_address(hostname)
    except ValueError:
        # DNS name -- resolve and validate all addresses
        try:
            results = socket.getaddrinfo(hostname, None)
        except socket.gaierror:
            # Cannot resolve -- allow through; the actual HTTP
            # request will fail with a clear network error.
            return
        for _family, _type, _proto, _canon, sockaddr in results:
            resolved = ipaddress.ip_address(sockaddr[0])
            if resolved.is_private or resolved.is_reserved or resolved.is_loopback:
                raise WebhookURLError(
                    f"Webhook URL hostname {hostname!r} resolves to "
                    f"private/reserved IP ({sockaddr[0]})"
                ) from None
        return

    if addr.is_private or addr.is_reserved or addr.is_loopback:
        raise WebhookURLError(
            f"Webhook URL must not target private/reserved IP ({hostname})"
        )


class AlertEvent(enum.Enum):
    """Types of alert events the notification system can emit."""

    CRASH = "crash"
    RATE_LIMIT = "rate_limit"
    PIPELINE_FAILURE = "pipeline_failure"
    COMPLETION = "completion"
    WATCHDOG_RELAUNCH = "watchdog_relaunch"


@dataclass
class AlertContext:
    """Shared context for alert notifications."""

    work_item_id: str = ""
    work_item_ref: str = ""
    stage: str = ""
    step: str = ""
    detail: str = ""


def build_issue_body(
    event: AlertEvent,
    ctx: AlertContext | None = None,
    work_item_id: str = "",
    work_item_ref: str = "",
    stage: str = "",
    step: str = "",
    detail: str = "",
) -> str:
    """Build a markdown body for a GitHub issue alert.

    Args:
        event: The alert event type.
        ctx: AlertContext with shared parameters. When provided,
            individual keyword arguments are ignored.
        work_item_id: Identifier for the work item (e.g. "WI-42").
        work_item_ref: Reference for the work item (e.g. branch name).
        stage: Pipeline stage where the event occurred.
        step: Pipeline step where the event occurred.
        detail: Human-readable description of what happened.

    Returns:
        Markdown-formatted issue body string.

    """
    if ctx is not None:
        work_item_id = ctx.work_item_id
        work_item_ref = ctx.work_item_ref
        stage = ctx.stage
        step = ctx.step
        detail = ctx.detail
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines: list[str] = [
        f"## Egregore Alert: {event.value}",
        "",
        f"**Event:** `{event.value}`",
        f"**Timestamp:** {timestamp}",
    ]

    if work_item_id:
        lines.append(f"**Work Item ID:** {work_item_id}")
    if work_item_ref:
        lines.append(f"**Work Item Ref:** {work_item_ref}")
    if stage:
        lines.append(f"**Stage:** {stage}")
    if step:
        lines.append(f"**Step:** {step}")

    lines.append("")

    if detail:
        lines.extend(["### Detail", "", detail])
    else:
        lines.extend(["### Detail", "", "_No additional detail provided._"])

    return "\n".join(lines)


def create_github_alert(
    title: str,
    body: str,
    labels: list[str] | None = None,
) -> bool:
    """Create a GitHub issue alert via the gh CLI.

    Args:
        title: Issue title.
        body: Markdown issue body.
        labels: Optional list of labels to apply.

    Returns:
        True if the issue was created successfully, False otherwise.

    """
    cmd: list[str] = [
        "gh",
        "issue",
        "create",
        "--title",
        title,
        "--body",
        body,
    ]

    if labels:
        cmd.extend(["--label", ",".join(labels)])

    try:
        result = subprocess.run(  # noqa: S603
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        if result.returncode != 0:
            logger.error(
                "gh issue create failed (rc=%d): %s",
                result.returncode,
                result.stderr.strip(),
            )
            return False
        logger.info("GitHub issue created: %s", result.stdout.strip())
        return True
    except FileNotFoundError:
        logger.error("gh CLI not found. Install GitHub CLI to use alerts.")
        return False
    except subprocess.TimeoutExpired:
        logger.error("gh issue create timed out after 30s.")
        return False


def send_webhook(
    url: str,
    event: AlertEvent,
    detail: str = "",
    webhook_format: str = "generic",
) -> bool:
    """Send a webhook notification via curl.

    Args:
        url: Webhook URL to POST to.
        event: The alert event type.
        detail: Human-readable description of what happened.
        webhook_format: One of "slack", "discord", or "generic".

    Returns:
        True if the webhook was sent successfully, False otherwise.

    """
    try:
        validate_webhook_url(url)
    except WebhookURLError as exc:
        logger.error("Webhook URL rejected: %s", exc)
        return False

    prefix = f"[egregore] {event.value}"
    if webhook_format == "slack":
        message = f"{prefix}: {detail}" if detail else prefix
        payload = {"text": message}
    elif webhook_format == "discord":
        message = f"{prefix}: {detail}" if detail else prefix
        payload = {"content": message}
    else:
        payload = {
            "event": event.value,
            "detail": detail,
            "source": "egregore",
        }

    payload_json = json.dumps(payload)

    cmd: list[str] = [
        "curl",
        "-s",
        "-S",
        "-X",
        "POST",
        "-H",
        "Content-Type: application/json",
        "-d",
        payload_json,
        url,
    ]

    try:
        result = subprocess.run(  # noqa: S603
            cmd,
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        if result.returncode != 0:
            logger.error(
                "Webhook POST failed (rc=%d): %s",
                result.returncode,
                result.stderr.strip(),
            )
            return False
        logger.info("Webhook sent to %s", url)
        return True
    except FileNotFoundError:
        logger.error("curl not found. Cannot send webhook.")
        return False
    except subprocess.TimeoutExpired:
        logger.error("Webhook POST timed out after 15s.")
        return False


def alert(
    event: AlertEvent,
    overseer_method: str = "github-repo-owner",
    webhook_url: str | None = None,
    webhook_format: str = "generic",
    ctx: AlertContext | None = None,
    work_item_id: str = "",
    work_item_ref: str = "",
    stage: str = "",
    step: str = "",
    detail: str = "",
) -> bool:
    """Send egregore alerts via GitHub issues and/or webhooks.

    Dispatches to create_github_alert and/or send_webhook depending
    on the configured overseer method and webhook URL.

    Args:
        event: The alert event type.
        overseer_method: How to notify. "github-repo-owner" creates
            a GitHub issue.
        webhook_url: Webhook URL for additional notification.
        webhook_format: Webhook payload format ("slack", "discord",
            or "generic").
        ctx: AlertContext with shared parameters. When provided,
            individual keyword arguments are ignored.
        work_item_id: Identifier for the work item.
        work_item_ref: Reference for the work item.
        stage: Pipeline stage where the event occurred.
        step: Pipeline step where the event occurred.
        detail: Human-readable description of what happened.

    Returns:
        True if at least one notification was sent successfully.

    """
    if ctx is not None:
        work_item_id = ctx.work_item_id
        work_item_ref = ctx.work_item_ref
        stage = ctx.stage
        step = ctx.step
        detail = ctx.detail

    success = False

    body = build_issue_body(
        event=event,
        work_item_id=work_item_id,
        work_item_ref=work_item_ref,
        stage=stage,
        step=step,
        detail=detail,
    )

    if overseer_method == "github-repo-owner":
        title = f"[egregore] {event.value}"
        if work_item_id:
            title = f"[egregore] {event.value} - {work_item_id}"
        labels = ["egregore", event.value]
        if create_github_alert(title=title, body=body, labels=labels):
            success = True

    if webhook_url:
        if send_webhook(
            url=webhook_url,
            event=event,
            detail=detail,
            webhook_format=webhook_format,
        ):
            success = True

    return success
