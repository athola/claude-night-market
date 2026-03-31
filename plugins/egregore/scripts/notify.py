#!/usr/bin/env python3
"""Egregore notification compatibility shim.

This module re-exports the notification API from the herald plugin.
The egregore plugin depends on herald for notification functionality.

All public names are preserved for backward compatibility:

- AlertEvent, AlertContext
- WebhookURLError
- validate_webhook_url, build_issue_body
- create_github_alert, send_webhook, alert
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

# Load herald's notify module from its known file path using
# importlib.util.spec_from_file_location (safe, no exec).
_herald_notify_path = (
    Path(__file__).resolve().parent.parent.parent / "herald" / "scripts" / "notify.py"
)

_spec = importlib.util.spec_from_file_location(
    "_herald_notify", str(_herald_notify_path)
)
if _spec is None or _spec.loader is None:
    raise ImportError(
        f"Cannot load herald notification module from {_herald_notify_path}. "
        "Ensure the herald plugin is installed alongside egregore."
    )

_herald_mod = importlib.util.module_from_spec(_spec)
# Register under a private name so it does not collide with this
# module's own "notify" entry in sys.modules.
sys.modules["_herald_notify"] = _herald_mod
_spec.loader.exec_module(_herald_mod)

# Re-export types and utilities directly from herald.
# These are dynamically loaded so use Any for type annotations.
AlertEvent: Any = _herald_mod.AlertEvent
AlertContext: Any = _herald_mod.AlertContext
WebhookURLError: Any = _herald_mod.WebhookURLError
validate_webhook_url: Any = _herald_mod.validate_webhook_url
create_github_alert: Any = _herald_mod.create_github_alert

# Re-export build_issue_body and send_webhook with egregore defaults.
_herald_build_issue_body = _herald_mod.build_issue_body
_herald_send_webhook = _herald_mod.send_webhook


def build_issue_body(  # noqa: PLR0913 - matches herald's signature
    event: Any,
    ctx: Any | None = None,
    work_item_id: str = "",
    work_item_ref: str = "",
    stage: str = "",
    step: str = "",
    detail: str = "",
    source: str = "egregore",
) -> str:
    """Build a markdown body for a GitHub issue alert.

    Thin wrapper that defaults source to "egregore" for backward
    compatibility. Delegates to herald's build_issue_body().
    """
    return str(
        _herald_build_issue_body(
            event=event,
            ctx=ctx,
            work_item_id=work_item_id,
            work_item_ref=work_item_ref,
            stage=stage,
            step=step,
            detail=detail,
            source=source,
        )
    )


def send_webhook(
    url: str,
    event: Any,
    detail: str = "",
    webhook_format: str = "generic",
    source: str = "egregore",
) -> bool:
    """Send a webhook notification via curl.

    Thin wrapper that defaults source to "egregore" for backward
    compatibility. Delegates to herald's send_webhook().
    """
    return bool(
        _herald_send_webhook(
            url=url,
            event=event,
            detail=detail,
            webhook_format=webhook_format,
            source=source,
        )
    )


def alert(  # noqa: PLR0913 - matches herald's signature
    event: Any,
    overseer_method: str = "github-repo-owner",
    webhook_url: str | None = None,
    webhook_format: str = "generic",
    ctx: Any | None = None,
    work_item_id: str = "",
    work_item_ref: str = "",
    stage: str = "",
    step: str = "",
    detail: str = "",
    source: str = "egregore",
) -> bool:
    """Send egregore alerts via GitHub issues and/or webhooks.

    This wrapper reproduces the dispatch logic so that
    ``@patch("notify.create_github_alert")`` and
    ``@patch("notify.send_webhook")`` work correctly in tests.
    The source parameter defaults to "egregore" for backward
    compatibility.
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
        source=source,
    )

    if overseer_method == "github-repo-owner":
        title = f"[{source}] {event.value}"
        if work_item_id:
            title = f"[{source}] {event.value} - {work_item_id}"
        labels = [source, event.value]
        if create_github_alert(title=title, body=body, labels=labels):
            success = True

    if webhook_url:
        if send_webhook(
            url=webhook_url,
            event=event,
            detail=detail,
            webhook_format=webhook_format,
            source=source,
        ):
            success = True

    return success


__all__ = [
    "AlertContext",
    "AlertEvent",
    "WebhookURLError",
    "alert",
    "build_issue_body",
    "create_github_alert",
    "send_webhook",
    "validate_webhook_url",
]
