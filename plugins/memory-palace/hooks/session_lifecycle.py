#!/usr/bin/env python3
"""Session lifecycle hook for memory-palace.

Records a summary of the current Claude Code session to persistent storage
when the session ends (Stop event).  Designed to stay well under the 2-second
timeout budget: it reads a small JSON payload, constructs a SessionRecord, and
writes one JSON file plus a lightweight index update.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Path setup: add the plugin src/ directory so we can import memory_palace.
# Hooks run as standalone scripts; the package is not installed in sys.path.
# ---------------------------------------------------------------------------
PLUGIN_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PLUGIN_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

_HAS_SESSION_HISTORY = False
try:
    from memory_palace.session_history import SessionHistoryManager, SessionRecord

    _HAS_SESSION_HISTORY = True
except (ImportError, ModuleNotFoundError) as _import_err:
    logging.getLogger(__name__).debug(
        "session_lifecycle: memory_palace.session_history not available: %s",
        _import_err,
    )

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _derive_session_id(payload: dict) -> str:
    """Generate a stable, filesystem-safe session ID.

    Combines available environment variables with payload data so that the
    same invocation context always produces the same ID.  The result is a
    date-prefixed hex digest safe to use as a filename.
    """
    seed_parts = [
        os.environ.get("CLAUDE_SESSION_ID", ""),
        os.environ.get("TERM_SESSION_ID", ""),
        os.environ.get("TMUX", ""),
        os.getcwd(),
        str(payload.get("session_id", "")),
    ]
    seed = "|".join(part for part in seed_parts if part)
    if not seed:
        seed = datetime.now(timezone.utc).isoformat()
    digest = hashlib.sha256(seed.encode()).hexdigest()[:12]
    date_prefix = datetime.now(timezone.utc).strftime("%Y%m%d")
    return f"{date_prefix}-{digest}"


def _safe_float(value: object, default: float = 0.0) -> float:
    """Convert value to float, returning default on failure."""
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default


def _build_record(payload: dict) -> SessionRecord:
    """Construct a SessionRecord from a Stop hook payload.

    The Stop event payload may contain:
    - session_id (str, optional)
    - stop_reason (str): "end_turn", "max_tokens", "stop_sequence"
    - stats (dict, optional): tool_uses, duration_ms, context_tokens_used, etc.
    - tools_used (list[str], optional)
    - files_modified (list[str], optional)
    - transcript_summary (str, optional)

    Fields absent from the payload receive sensible defaults.
    """
    stats: dict = payload.get("stats") or {}

    session_id: str = str(payload.get("session_id") or _derive_session_id(payload))
    started_at: str = str(
        payload.get("started_at") or datetime.now(timezone.utc).isoformat()
    )
    ended_at: str = datetime.now(timezone.utc).isoformat()

    duration_ms = _safe_float(stats.get("duration_ms", 0))
    duration_seconds = duration_ms / 1000.0

    # Derive outcome from stop_reason
    stop_reason: str = str(payload.get("stop_reason", "") or "")
    if stop_reason == "max_tokens":
        outcome = "interrupted"
    elif stop_reason in ("end_turn", "stop_sequence"):
        outcome = "completed"
    else:
        outcome = stop_reason or "completed"

    # Context usage as a fraction 0.0–1.0
    context_tokens = _safe_float(stats.get("context_tokens_used", 0))
    context_limit = _safe_float(stats.get("context_window_size", 0))
    context_peak = (
        min(context_tokens / context_limit, 1.0) if context_limit > 0 else 0.0
    )

    tools_used: list[str] = list(payload.get("tools_used") or [])
    files_modified: list[str] = list(payload.get("files_modified") or [])
    summary: str = str(payload.get("transcript_summary") or "")

    return SessionRecord(
        session_id=session_id,
        started_at=started_at,
        ended_at=ended_at,
        duration_seconds=duration_seconds,
        summary=summary,
        topics=[],
        skills_used=[],
        tools_used=tools_used,
        files_modified=files_modified,
        key_decisions=[],
        outcome=outcome,
        context_usage_peak=context_peak,
        continuation_count=0,
        parent_session_id=None,
        tags=[],
        metadata={
            "stop_reason": stop_reason,
            "tool_use_count": int(_safe_float(stats.get("tool_uses", 0))),
        },
    )


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Record session summary on Stop event."""
    if not _HAS_SESSION_HISTORY:
        sys.exit(0)

    try:
        payload: dict = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        logger.warning("session_lifecycle: Failed to parse Stop payload: %s", exc)
        sys.exit(0)

    # Only process Stop events (empty hook_event_name means Claude Code
    # invoked the hook directly for the Stop event without setting the field)
    hook_event = str(
        payload.get("hook_event_name") or payload.get("hookEventName") or ""
    )
    if hook_event and hook_event != "Stop":
        sys.exit(0)

    try:
        record = _build_record(payload)
        mgr = SessionHistoryManager(data_dir=PLUGIN_ROOT / "data")
        mgr.record_session(record)
    except Exception as exc:  # noqa: BLE001
        # Non-critical: never block the session from ending
        logger.warning("session_lifecycle: Failed to record session: %s", exc)

    sys.exit(0)


if __name__ == "__main__":
    main()
