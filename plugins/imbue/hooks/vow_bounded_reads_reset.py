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

import json
import os
import sys
from pathlib import Path

# The symlink-safe state primitives live in shared/vow_utils, the same
# home the increment hook uses, so both compute an identical private
# counter path and share one audited CWE-59 defense.
sys.path.insert(0, str(Path(__file__).parent))
from shared.vow_utils import (  # noqa: E402 - hook script must inject sys.path before importing sibling shared/ module
    fd_owned_by_us,
    read_counter_path,
    secure_open,
    session_id_from,
)

# One definition, shared with the other read-budget hook, so the reset
# truncates exactly the file the increment writes.
_counter_path = read_counter_path
_get_session_id = session_id_from

# fcntl is POSIX-only; degrade to unlocked truncate on Windows.
try:
    import fcntl as _fcntl  # type: ignore[import-not-found]  # POSIX-only; Windows takes the except branch

    _HAS_FCNTL = True
except ImportError:  # pragma: no cover - exercised only on non-POSIX
    _fcntl = None  # type: ignore[assignment]  # intentional None sentinel; guarded by _HAS_FCNTL at call sites
    _HAS_FCNTL = False
    # One-shot operator signal so non-POSIX hosts see parity with the
    # POSIX-side flock-failure warning. Suppressed under pytest so unit
    # runs that exercise the no-fcntl path do not spam stderr.
    if "PYTEST_CURRENT_TEST" not in os.environ:
        print(
            "[vow-bounded-reads] WARN: fcntl unavailable on this platform; "
            "counter resets are not atomic with concurrent increments",
            file=sys.stderr,
        )


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
        # O_NOFOLLOW (via secure_open) refuses a symlinked counter path.
        fd = secure_open(path, os.O_RDWR | os.O_CREAT, 0o600)
        try:
            os.fchmod(fd, 0o600)
        except OSError:
            pass
        if not fd_owned_by_us(fd):
            return
        if _HAS_FCNTL and _fcntl is not None:
            try:
                _fcntl.flock(fd, _fcntl.LOCK_EX)
            except (OSError, RuntimeError, NotImplementedError) as exc:
                # Lock unavailable (NFS quirks, FUSE/Windows-shim layers
                # that surface as RuntimeError/NotImplementedError).
                # Surface so operators see when the reset path runs
                # without serialization vs concurrent increments.
                print(
                    f"[vow-bounded-reads] WARN: flock unavailable on "
                    f"reset, falling back to unlocked truncate: {exc}",
                    file=sys.stderr,
                )
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
                except (OSError, RuntimeError, NotImplementedError) as exc:
                    # Asymmetry with the acquire-side warning above
                    # would hide a lock leak on shutdown. Surface the
                    # failure so it shows up in operator triage.
                    print(
                        f"[vow-bounded-reads] WARN: flock unlock failed "
                        f"on reset: {exc}",
                        file=sys.stderr,
                    )
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
