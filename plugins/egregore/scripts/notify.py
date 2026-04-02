#!/usr/bin/env python3
"""Egregore notification compatibility shim.

Re-exports the notification API from the herald plugin when
available. When herald is not installed, provides stub
implementations that log warnings and return safe defaults,
following ADR-0001 (Plugin Dependency Isolation).

All public names are preserved for backward compatibility:

- AlertEvent, AlertContext
- WebhookURLError
- validate_webhook_url, build_issue_body
- create_github_alert, send_webhook, alert
"""

from __future__ import annotations

import importlib.util
import logging
import sys
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_HERALD_AVAILABLE = False

# Load herald's notify module from its known file path using
# importlib.util.spec_from_file_location (safe, no exec).
_herald_notify_path = (
    Path(__file__).resolve().parent.parent.parent / "herald" / "scripts" / "notify.py"
)

try:
    _spec = importlib.util.spec_from_file_location(
        "_herald_notify", str(_herald_notify_path)
    )
    if _spec is None or _spec.loader is None:
        raise ImportError("spec_from_file_location returned None")

    _herald_mod = importlib.util.module_from_spec(_spec)
    sys.modules["_herald_notify"] = _herald_mod
    _spec.loader.exec_module(_herald_mod)
    _HERALD_AVAILABLE = True
except (ImportError, OSError) as _exc:
    logger.warning(
        "Herald plugin not available (%s). Egregore notifications will be disabled.",
        _exc,
    )
    _herald_mod = None  # type: ignore[assignment]  # None is valid sentinel for absent module


# --- Herald-backed exports (when available) -------------------------

if _HERALD_AVAILABLE and _herald_mod is not None:
    AlertEvent: Any = _herald_mod.AlertEvent
    AlertContext: Any = _herald_mod.AlertContext
    WebhookURLError: Any = _herald_mod.WebhookURLError
    validate_webhook_url: Any = _herald_mod.validate_webhook_url
    create_github_alert: Any = _herald_mod.create_github_alert
    _herald_build_issue_body = _herald_mod.build_issue_body
    _herald_send_webhook = _herald_mod.send_webhook

# --- Stub fallbacks (when herald is absent) -------------------------

else:
    import enum
    from dataclasses import dataclass

    class AlertEvent(enum.Enum):  # type: ignore[no-redef]  # conditional stub when herald absent
        """Stub alert events when herald is absent."""

        CRASH = "crash"
        RATE_LIMIT = "rate_limit"
        PIPELINE_FAILURE = "pipeline_failure"
        COMPLETION = "completion"
        WATCHDOG_RELAUNCH = "watchdog_relaunch"

    @dataclass
    class AlertContext:  # type: ignore[no-redef]  # conditional stub when herald absent
        """Stub alert context when herald is absent."""

        work_item_id: str = ""
        work_item_ref: str = ""
        stage: str = ""
        step: str = ""
        detail: str = ""

    class WebhookURLError(ValueError):  # type: ignore[no-redef]  # conditional stub when herald absent
        """Stub error when herald is absent."""

    def validate_webhook_url(url: str) -> None:  # type: ignore[misc]  # conditional stub when herald absent
        """No-op when herald is absent."""

    def create_github_alert(  # type: ignore[misc]  # conditional stub when herald absent
        title: str,
        body: str,
        labels: list[str] | None = None,
    ) -> bool:
        logger.warning("Cannot create alert: herald plugin not installed")
        return False

    def _herald_build_issue_body(**kwargs: Any) -> str:
        return ""

    def _herald_send_webhook(**kwargs: Any) -> bool:
        return False


# --- Egregore wrappers (source defaults to "egregore") --------------


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
    Returns empty string when herald is absent.
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
    compatibility. Returns False when herald is absent.
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

    Returns False when herald is absent.
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
