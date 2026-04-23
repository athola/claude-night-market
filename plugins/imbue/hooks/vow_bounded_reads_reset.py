#!/usr/bin/env python3
"""Vow: Reset bounded-reads counter when implementation starts.

PreToolUse hook triggered on Write/Edit/MultiEdit.  Truncates the
per-session read counter file back to zero.

Intentionally minimal: reads only the session ID from stdin, then
writes ``{"count": 0}`` to the counter file.  No JSON parsing of
tool output, no pattern checks, no budget logic.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path


# Duplicated from vow_bounded_reads.py — a shared import would pay the
# same startup cost this script is designed to avoid.
def _counter_path(session_id: str) -> Path:
    """Return the path to the session-scoped counter file."""
    safe_id = (
        session_id.replace("/", "_").replace("\\", "_") if session_id else "default"
    )
    return Path(f"/tmp/vow_read_counter_{safe_id[:200]}.json")  # noqa: S108 - cross-process session counter requires a shared tmpfs path


# Duplicated from vow_bounded_reads.py — a shared import would pay the
# same startup cost this script is designed to avoid.
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
        session_id = _get_session_id(data)
        counter_file = _counter_path(session_id)

        try:
            fd = os.open(
                str(counter_file),
                os.O_WRONLY | os.O_CREAT | os.O_TRUNC,
                0o600,
            )
            try:
                os.fchmod(fd, 0o600)
            except OSError:
                pass
            try:
                with os.fdopen(fd, "w") as fh:
                    fh.write('{"count": 0}')
            except Exception:
                try:
                    os.close(fd)
                except OSError:
                    pass
                raise
        except Exception as exc:  # noqa: S110 - write failures are non-fatal
            print(
                f"[vow-bounded-reads] WARN: counter write failed: {exc}",
                file=sys.stderr,
            )

        sys.exit(0)

    except Exception:  # hook must not crash the agent under any circumstance
        sys.exit(0)


if __name__ == "__main__":
    main()
