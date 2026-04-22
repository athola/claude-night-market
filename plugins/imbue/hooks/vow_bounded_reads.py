#!/usr/bin/env python3
"""Vow: Bounded discovery reads (warn-only vow).

PreToolUse hook that tracks consecutive Read/Grep/Glob calls in a
session-scoped counter file.  When the counter exceeds the budget
(default 15) a warning is emitted.  When a Write/Edit/MultiEdit tool
fires the counter is reset (implementation phase started).

Unlike the sibling ``vow_no_ai_attribution`` and ``vow_no_emoji_commits``
hooks, this one is **always warn-only** and does not consult
``VOW_SHADOW_MODE``: bounded-reads is advisory signal, not a hard
enforcement vow.  The other two vows can be promoted to blocking via
``VOW_SHADOW_MODE=0``; this one cannot, by design.

Session ID is taken from the stdin JSON ``session_id`` field, with
``CLAUDE_SESSION_ID`` env var as a fallback, and a fixed filename as
the last resort.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_READ_TOOLS = frozenset({"Read", "Grep", "Glob"})
_WRITE_TOOLS = frozenset({"Write", "Edit", "MultiEdit"})
_BUDGET = 15


def _counter_path(session_id: str) -> Path:
    """Return the path to the session-scoped counter file."""
    safe_id = (
        session_id.replace("/", "_").replace("\\", "_") if session_id else "default"
    )
    return Path(f"/tmp/vow_read_counter_{safe_id}.json")  # noqa: S108 - cross-process session counter requires a shared tmpfs path


def _read_counter(path: Path) -> int:
    """Read the current counter value from *path*, returning 0 on any error."""
    try:
        data = json.loads(path.read_text())
        return int(data.get("count", 0))
    except Exception:  # hook must not crash on corrupt/missing counter file
        return 0


def _write_counter(path: Path, count: int) -> None:
    """Write *count* to the counter file at *path* with 0o600 perms.

    Uses ``os.open`` + ``O_CREAT | O_WRONLY | O_TRUNC`` with mode 0o600 so
    the counter is never world-readable on shared systems (the filename
    embeds the session id). ``os.chmod`` is called after open to tighten
    permissions even when the file pre-existed with looser modes.
    """
    try:
        fd = os.open(
            str(path),
            os.O_WRONLY | os.O_CREAT | os.O_TRUNC,
            0o600,
        )
        try:
            os.fchmod(fd, 0o600)
        except OSError:
            pass
        with os.fdopen(fd, "w") as fh:
            fh.write(json.dumps({"count": count}))
    except Exception:  # noqa: S110 - write failures are non-fatal; hook must not crash the agent
        pass


def _is_read_tool(tool_name: str) -> bool:
    """Return True if *tool_name* is a discovery read tool."""
    return tool_name in _READ_TOOLS


def _is_write_tool(tool_name: str) -> bool:
    """Return True if *tool_name* signals the start of implementation."""
    return tool_name in _WRITE_TOOLS


def _get_session_id(data: dict) -> str:
    """Extract session ID from stdin data, env var, or fall back to 'default'."""
    sid = data.get("session_id", "")
    if sid:
        return str(sid)
    sid = os.environ.get("CLAUDE_SESSION_ID", "")
    if sid:
        return sid
    return "default"


def main() -> None:
    """Entry point for the PreToolUse hook."""
    try:
        raw = sys.stdin.read()
        data = json.loads(raw)
    except (json.JSONDecodeError, OSError):
        sys.exit(0)

    try:
        tool_name = data.get("tool_name", "")
        session_id = _get_session_id(data)
        counter_file = _counter_path(session_id)

        if _is_write_tool(tool_name):
            _write_counter(counter_file, 0)
            sys.exit(0)

        if not _is_read_tool(tool_name):
            sys.exit(0)

        current = _read_counter(counter_file)
        new_count = current + 1
        _write_counter(counter_file, new_count)

        if new_count > _BUDGET:
            reason = (
                f"Bounded discovery vow: {new_count} reads in this discovery phase. "
                f"Budget is {_BUDGET} for open exploration. "
                "Consider starting implementation."
            )
            output = {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "warn",
                    "permissionDecisionReason": reason,
                }
            }
            print(json.dumps(output))
            print(
                f"[vow-bounded-reads] WARN: {new_count} reads (budget {_BUDGET})",
                file=sys.stderr,
            )

        sys.exit(0)

    except Exception:  # hook must not crash the agent under any circumstance
        sys.exit(0)


if __name__ == "__main__":
    main()
