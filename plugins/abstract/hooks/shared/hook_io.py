"""Shared hook input reader for Claude Code PostToolUse/PreToolUse hooks.

Claude Code delivers the hook payload as a single JSON object on **stdin**
(fields: ``tool_name``, ``tool_input``, ``tool_response``, ``session_id``,
``hook_event_name``, ...). It does **not** set ``CLAUDE_TOOL_NAME`` /
``CLAUDE_TOOL_INPUT`` / ``CLAUDE_TOOL_OUTPUT`` environment variables.

Hooks that read those env vars silently no-op on every real invocation.
``read_hook_payload`` reads stdin first and falls back to the legacy env
vars only when stdin is empty, so the synthetic test harness and any older
callers keep working.
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any

_LEGACY_TOOL_INPUT = "CLAUDE_TOOL_INPUT"
_LEGACY_TOOL_NAME = "CLAUDE_TOOL_NAME"
_LEGACY_TOOL_OUTPUT = "CLAUDE_TOOL_OUTPUT"
_LEGACY_SESSION_ID = "CLAUDE_SESSION_ID"


def _coerce_tool_input(value: Any) -> dict[str, Any]:
    """Normalize ``tool_input`` to a dict regardless of source.

    Stdin delivers it already parsed; the legacy env var delivers a JSON
    string. A non-object value collapses to an empty dict rather than
    raising, matching the lenient behavior the hooks relied on.
    """
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


def _legacy_env_payload() -> dict[str, Any]:
    """Build a payload from the legacy ``CLAUDE_TOOL_*`` environment vars."""
    return {
        "tool_name": os.environ.get(_LEGACY_TOOL_NAME, ""),
        "tool_input": _coerce_tool_input(os.environ.get(_LEGACY_TOOL_INPUT, "{}")),
        "tool_response": os.environ.get(_LEGACY_TOOL_OUTPUT, ""),
        "session_id": os.environ.get(_LEGACY_SESSION_ID, ""),
    }


def read_hook_payload() -> dict[str, Any]:
    """Return the hook payload, preferring stdin JSON over legacy env vars.

    Always returns a dict with at least ``tool_name``, ``tool_input``
    (a dict), ``tool_response``, and ``session_id`` keys populated.

    Sync note: parallels ``leyline/hooks/noqa_guard._read_payload`` and
    ``sanctum/hooks/deferred_item_watcher.read_payload`` (and
    ``tool_response_text`` below mirrors their response-to-text coercion).
    Plugin isolation forbids a cross-plugin import, so the copies must change
    together.
    """
    raw = ""
    try:
        if not sys.stdin.isatty():
            raw = sys.stdin.read()
    except (OSError, ValueError):
        raw = ""

    payload: dict[str, Any] | None = None
    if raw.strip():
        try:
            candidate = json.loads(raw)
        except json.JSONDecodeError as exc:
            # A corrupted payload must not be indistinguishable from an idle
            # hook: warn before falling back to legacy env vars (which are
            # unset on real invocations, making every consumer silently
            # no-op). Mirrors noqa_guard._read_payload's stderr signal.
            sys.stderr.write(f"hook_io: ignoring malformed stdin JSON: {exc}\n")
            candidate = None
        if isinstance(candidate, dict):
            payload = candidate

    if payload is None:
        payload = _legacy_env_payload()

    payload["tool_name"] = payload.get("tool_name") or ""
    payload["tool_input"] = _coerce_tool_input(payload.get("tool_input", {}))
    payload["tool_response"] = payload.get("tool_response") or ""
    # Session id: payload value wins, else legacy env, else "unknown".
    payload["session_id"] = (
        payload.get("session_id") or os.environ.get(_LEGACY_SESSION_ID, "") or "unknown"
    )
    return payload


def tool_response_text(payload: dict[str, Any]) -> str:
    """Return ``tool_response`` as text for substring outcome checks.

    The runtime sends ``tool_response`` as a dict or a string; callers that
    scan for 'error'/'warning' need a string either way.
    """
    value = payload.get("tool_response", "")
    if isinstance(value, str):
        return value
    try:
        return json.dumps(value)
    except (TypeError, ValueError):
        return str(value)
