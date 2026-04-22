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

Additionally provides config_alert() which gates dispatch
on AlertsConfig flags so the orchestrator can call a single
function without checking config itself.
"""

from __future__ import annotations

import enum
import importlib.util
import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from config import AlertsConfig, OverseerConfig

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
    AlertEvent: Any = _herald_mod.AlertEvent  # type: ignore[no-redef]  # conditional re-export from herald
    AlertContext: Any = _herald_mod.AlertContext  # type: ignore[no-redef]  # conditional re-export from herald
    WebhookURLError: Any = _herald_mod.WebhookURLError  # type: ignore[no-redef]  # conditional re-export from herald
    validate_webhook_url: Any = _herald_mod.validate_webhook_url  # type: ignore[no-redef]  # conditional re-export from herald
    create_github_alert: Any = _herald_mod.create_github_alert  # type: ignore[no-redef]  # conditional re-export from herald
    _herald_build_issue_body = _herald_mod.build_issue_body
    _herald_send_webhook = _herald_mod.send_webhook

# --- Stub fallbacks (when herald is absent) -------------------------

else:

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
        _ = url

    def create_github_alert(  # type: ignore[misc]  # conditional stub when herald absent
        title: str,
        body: str,
        labels: list[str] | None = None,
    ) -> bool:
        _ = title, body, labels
        """Stub that warns and returns False when herald is absent."""
        logger.warning("Cannot create alert: herald plugin not installed")
        return False

    def _herald_build_issue_body(
        event: Any,
        ctx: Any,
        source: str = "herald",
    ) -> str:
        return ""

    def _herald_send_webhook(**kwargs: Any) -> bool:
        return False


# --- AlertEvent-to-AlertsConfig mapping ------------------------------

#: Maps each AlertEvent to the corresponding AlertsConfig flag name.
_EVENT_TO_CONFIG_FLAG: dict[str, str] = {
    "crash": "on_crash",
    "rate_limit": "on_rate_limit",
    "pipeline_failure": "on_pipeline_failure",
    "completion": "on_completion",
    "watchdog_relaunch": "on_watchdog_relaunch",
}


def _is_event_enabled(alerts_cfg: AlertsConfig, event: Any) -> bool:
    """Check whether *event* is enabled in the AlertsConfig.

    Unknown event values are allowed through (fail-open) so
    that new event types added to herald do not require an
    immediate config update in egregore.
    """
    flag = _EVENT_TO_CONFIG_FLAG.get(event.value)
    if flag is None:
        return True
    return bool(getattr(alerts_cfg, flag, True))


# --- Egregore wrappers (source defaults to "egregore") --------------


def _build_ctx(  # noqa: PLR0913 - mirrors AlertContext fields
    ctx: Any | None,
    work_item_id: str,
    work_item_ref: str,
    stage: str,
    step: str,
    detail: str,
) -> Any:
    """Build an AlertContext from either an existing ctx or kwargs.

    If *ctx* is provided its fields take precedence; individual
    kwargs are used as fallbacks.  Returns a fully-populated
    AlertContext suitable for passing to herald.
    """
    if ctx is not None:
        return ctx
    return AlertContext(
        work_item_id=work_item_id,
        work_item_ref=work_item_ref,
        stage=stage,
        step=step,
        detail=detail,
    )


def build_issue_body(  # noqa: PLR0913 - backward-compat wrapper
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
    compatibility. Constructs an AlertContext from kwargs when
    *ctx* is not provided, then delegates to herald.
    Returns empty string when herald is absent.
    """
    if ctx is None:
        ctx = AlertContext(
            work_item_id=work_item_id,
            work_item_ref=work_item_ref,
            stage=stage,
            step=step,
            detail=detail,
        )
    return str(
        _herald_build_issue_body(
            event=event,
            ctx=ctx,
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


def alert(  # noqa: PLR0913 - backward-compat wrapper
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

    Composes ``build_issue_body``, ``create_github_alert``, and
    ``send_webhook`` (which delegate to herald when available).
    Returns False when herald is absent.
    """
    resolved_ctx = _build_ctx(
        ctx,
        work_item_id,
        work_item_ref,
        stage,
        step,
        detail,
    )

    success = False

    body = build_issue_body(event=event, ctx=resolved_ctx, source=source)

    if overseer_method == "github-repo-owner":
        title = f"[{source}] {event.value}"
        if resolved_ctx.work_item_id:
            title = f"[{source}] {event.value} - {resolved_ctx.work_item_id}"
        labels = [source, event.value]
        if create_github_alert(title=title, body=body, labels=labels):
            success = True

    if webhook_url:
        if send_webhook(
            url=webhook_url,
            event=event,
            detail=resolved_ctx.detail,
            webhook_format=webhook_format,
            source=source,
        ):
            success = True

    return success


def config_alert(  # noqa: PLR0913 - config-aware entry point
    event: Any,
    alerts_cfg: AlertsConfig,
    overseer_cfg: OverseerConfig,
    ctx: Any | None = None,
    work_item_id: str = "",
    work_item_ref: str = "",
    stage: str = "",
    step: str = "",
    detail: str = "",
    source: str = "egregore",
) -> bool:
    """Config-aware alert dispatch.

    Checks ``alerts_cfg`` to decide whether *event* should fire,
    then uses ``overseer_cfg`` to route the notification through
    herald.  This is the recommended entry point for the
    orchestrator and watchdog.

    Returns True if at least one notification was delivered,
    False if the event was suppressed or delivery failed.
    """
    if not _is_event_enabled(alerts_cfg, event):
        logger.debug(
            "Alert suppressed by config: %s (flag %s is off)",
            event.value,
            _EVENT_TO_CONFIG_FLAG.get(event.value, "?"),
        )
        return False

    return alert(
        event=event,
        overseer_method=overseer_cfg.method,
        webhook_url=overseer_cfg.webhook_url,
        webhook_format=overseer_cfg.webhook_format,
        ctx=ctx,
        work_item_id=work_item_id,
        work_item_ref=work_item_ref,
        stage=stage,
        step=step,
        detail=detail,
        source=source,
    )


__all__ = [
    "AlertContext",
    "AlertEvent",
    "WebhookURLError",
    "alert",
    "build_issue_body",
    "config_alert",
    "create_github_alert",
    "send_webhook",
    "validate_webhook_url",
]
