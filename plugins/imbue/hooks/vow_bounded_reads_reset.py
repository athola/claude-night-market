#!/usr/bin/env python3
"""Vow: Reset bounded-reads counter when implementation starts.

PreToolUse hook triggered on Write/Edit/MultiEdit.  Truncates the
per-session read counter file back to zero.

Intentionally minimal: reads only the session ID from stdin, then
writes ``{"count": 0}`` to the counter file.  No JSON parsing of
tool output, no pattern checks, no budget logic.

Concurrency: acquires the same ``fcntl.flock(LOCK_EX)`` as the
companion increment script so a Read in flight cannot clobber the
reset.  See issue #418.
"""

from __future__ import annotations

import json  # noqa: F401 - kept for forward compatibility with payload parsing
import os
import sys
from pathlib import Path

# fcntl is POSIX-only; degrade to unlocked truncate on Windows.
try:
    import fcntl as _fcntl  # type: ignore[import-not-found]  # POSIX-only; Windows takes the except branch

    _HAS_FCNTL = True
except ImportError:  # pragma: no cover - exercised only on non-POSIX
    _fcntl = None  # type: ignore[assignment]  # intentional None sentinel; guarded by _HAS_FCNTL at call sites
    _HAS_FCNTL = False


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


def _atomic_reset(path: Path) -> None:
    """Atomically zero the counter file at *path*.

    Acquires the same exclusive POSIX file lock as the increment hook
    so a Read in flight cannot clobber the reset.  Falls back to
    unlocked truncate on systems without ``fcntl``.

    Never raises -- write errors are logged to stderr only so the
    hook cannot crash the agent.
    """
    fd = -1
    try:
        # O_RDWR (not O_TRUNC) so the lock is acquired BEFORE any
        # destructive operation; truncation happens after the lock.
        fd = os.open(str(path), os.O_RDWR | os.O_CREAT, 0o600)
        try:
            os.fchmod(fd, 0o600)
        except OSError:
            pass
        if _HAS_FCNTL and _fcntl is not None:
            try:
                _fcntl.flock(fd, _fcntl.LOCK_EX)
            except OSError:
                pass
        try:
            os.lseek(fd, 0, os.SEEK_SET)
            os.ftruncate(fd, 0)
            os.write(fd, b'{"count": 0}')
        except OSError as exc:
            print(
                f"[vow-bounded-reads] WARN: counter reset failed: {exc}",
                file=sys.stderr,
            )
    except Exception as exc:  # noqa: BLE001 - hook must not crash agent
        print(
            f"[vow-bounded-reads] WARN: counter reset failed: {exc}",
            file=sys.stderr,
        )
    finally:
        if fd >= 0:
            if _HAS_FCNTL and _fcntl is not None:
                try:
                    _fcntl.flock(fd, _fcntl.LOCK_UN)
                except OSError:
                    pass
            try:
                os.close(fd)
            except OSError:
                pass


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
        _atomic_reset(counter_file)
        sys.exit(0)

    except Exception as exc:  # hook must not crash the agent under any circumstance
        print(f"[vow-bounded-reads-reset] internal error: {exc}", file=sys.stderr)
        sys.exit(0)


if __name__ == "__main__":
    main()
