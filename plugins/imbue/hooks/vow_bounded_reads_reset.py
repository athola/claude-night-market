#!/usr/bin/env python3
"""Vow: Reset bounded-reads counter when implementation starts.

PostToolUse hook on a successful Write/Edit/MultiEdit.  Truncates the
per-session read counter to zero and deletes the remembered-calls file,
so an edited file can be read again without a repeat warning.

Intentionally minimal: reads only the session ID from stdin, writes
``{"count": 0}`` to the counter file and unlinks the remembered-calls
file.  No JSON parsing of tool output, no pattern checks, no budget
logic.

Concurrency: acquires the same ``fcntl.flock(LOCK_EX)`` as the
companion increment script so a Read in flight cannot clobber the
reset.  See issue #418.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# The symlink-safe state primitives are in shared/vow_utils, the same
# home the increment hook uses, so both compute an identical private
# counter path and share one audited CWE-59 defense.
sys.path.insert(0, str(Path(__file__).parent))
from shared.vow_utils import (  # noqa: E402 - hook script must inject sys.path before importing sibling shared/ module
    fd_owned_by_us,
    lock_fd,
    read_counter_path,
    secure_open,
    session_id_from,
    unlock_fd,
)

# One definition, shared with the other read-budget hook, so the reset
# truncates exactly the file the increment writes.
_counter_path = read_counter_path
_get_session_id = session_id_from


def _atomic_reset(path: Path) -> None:
    """Atomically zero the counter file at *path*.

    Acquires the same exclusive POSIX file lock as the increment hook
    so a Read in flight cannot clobber the reset.  Falls back to
    unlocked truncate on systems without ``fcntl``.

    I/O errors are logged to stderr. Any other exception propagates to
    main(), which reports it as an internal error and exits 0.
    """
    fd = -1
    try:
        # O_RDWR (not O_TRUNC) so the lock is acquired BEFORE any
        # destructive operation; truncation happens after the lock.
        # O_NOFOLLOW (via secure_open) refuses a symlinked counter path.
        fd = secure_open(path, os.O_RDWR | os.O_CREAT, 0o600)
        try:
            os.fchmod(fd, 0o600)
        except OSError:
            pass
        if not fd_owned_by_us(fd):
            return
        lock_fd(fd, " on reset")
        try:
            os.lseek(fd, 0, os.SEEK_SET)
            os.ftruncate(fd, 0)
            # The remembered calls and the spent escape share this file, so
            # one write forgets them too: an edited file is worth reading
            # again.
            os.write(fd, b'{"count": 0}')
        except OSError as exc:
            print(
                f"[vow-bounded-reads] WARN: counter reset failed: {exc}",
                file=sys.stderr,
            )
    # Opening or chmod-ing the counter is the I/O left to fail here. The
    # write's own OSError is handled above. Anything else is a bug and
    # reaches main(), whose catch-all keeps the hook from crashing.
    except OSError as exc:
        print(
            f"[vow-bounded-reads] WARN: counter reset failed: {exc}",
            file=sys.stderr,
        )
    finally:
        if fd >= 0:
            unlock_fd(fd, " on reset")
            try:
                os.close(fd)
            except OSError:
                pass


def main() -> None:
    """Entry point for the PostToolUse hook."""
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
