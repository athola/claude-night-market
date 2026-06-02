#!/usr/bin/env python3
"""Vow: Bounded discovery reads (Hard vow, shadow mode by default).

PreToolUse hook triggered on Read/Grep/Glob.  Tracks consecutive
discovery reads in a session-scoped counter file.  When the counter
exceeds the budget (default 15) a warning is emitted in shadow mode
or the tool call is blocked when VOW_SHADOW_MODE=0.

Counter resets are handled by the companion script
``vow_bounded_reads_reset.py`` which fires on Write/Edit/MultiEdit.

Session ID is taken from the stdin JSON ``session_id`` field, with
``CLAUDE_SESSION_ID`` env var as a fallback, and a fixed filename as
the last resort.

Concurrency: read-modify-write on the counter file is serialised with
``fcntl.flock(LOCK_EX)`` so parallel Read calls (Claude Code 2.1.72+
dispatches them concurrently) cannot lose increments.  On platforms
without ``fcntl`` (Windows) the hook degrades gracefully to unlocked
RMW; the resulting small race window is acceptable because the vow
remains an advisory signal there.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# D-06: shadow_mode helper lives in shared/vow_utils, which is also the
# home of the symlink-safe state primitives (CWE-59 defense).
sys.path.insert(0, str(Path(__file__).parent))
from shared.vow_utils import (  # noqa: E402 - hook script must inject sys.path before importing sibling shared/ module
    fd_owned_by_us,
    secure_open,
    secure_state_dir,
    shadow_mode_active,
)

# fcntl is POSIX-only.  On Windows we fall back to unlocked RMW; the
# small race window is acceptable for an advisory vow on non-POSIX
# hosts.  See issue #418.
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
            "counter increments are not atomic under concurrent reads",
            file=sys.stderr,
        )

_READ_TOOLS = frozenset({"Read", "Grep", "Glob"})
_BUDGET = 15


def _counter_path(session_id: str) -> Path:
    """Return the path to the session-scoped counter file.

    Lives in a private per-user dir (mode 0o700) so another user cannot
    plant a symlink at this predictable name; opens add ``O_NOFOLLOW``
    as defense in depth. The reset companion computes the same path.
    """
    safe_id = (
        session_id.replace("/", "_").replace("\\", "_") if session_id else "default"
    )
    return (
        secure_state_dir("imbue-vow-state") / f"vow_read_counter_{safe_id[:200]}.json"
    )


def _read_counter(path: Path) -> int:
    """Read the current counter value from *path*, returning 0 on any error."""
    try:
        fd = secure_open(path, os.O_RDONLY)
    except OSError:  # missing, or ELOOP on a planted symlink
        return 0
    try:
        if not fd_owned_by_us(fd):
            return 0
        data = json.loads(os.read(fd, 4096).decode("utf-8") or "{}")
        return int(data.get("count", 0))
    except Exception as exc:  # hook must not crash on corrupt counter file
        print(f"[vow-bounded-reads] WARN: counter read failed: {exc}", file=sys.stderr)
        return 0
    finally:
        os.close(fd)


def _write_counter(path: Path, count: int) -> None:
    """Write *count* to the counter file at *path* with 0o600 perms.

    Uses ``os.open`` + ``O_CREAT | O_WRONLY | O_TRUNC`` with mode 0o600 so
    the counter is never world-readable on shared systems (the filename
    embeds the session id). ``os.chmod`` is called after open to tighten
    permissions even when the file pre-existed with looser modes.
    """
    try:
        fd = secure_open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        try:
            os.fchmod(fd, 0o600)
        except OSError:
            pass
        try:
            if not fd_owned_by_us(fd):
                return
            os.write(fd, json.dumps({"count": count}).encode("utf-8"))
        finally:
            os.close(fd)
    except Exception as exc:  # noqa: S110 - write failures are non-fatal; hook must not crash the agent
        print(f"[vow-bounded-reads] WARN: counter write failed: {exc}", file=sys.stderr)


def _atomic_increment(path: Path) -> int:  # noqa: PLR0912 - lock fallbacks plus the owner-check guard sit at the branch limit
    """Atomically read-modify-write the counter at *path*.

    Returns the new (post-increment) count.  Uses an exclusive POSIX
    file lock around the RMW so concurrent hook invocations cannot
    lose increments.  On systems without ``fcntl`` (Windows) the lock
    is skipped and the hook degrades to unlocked RMW.

    Returns 0 on any failure -- the hook must never crash the agent.
    """
    fd = -1
    try:
        # O_RDWR|O_CREAT (no O_TRUNC) so we can read the current value
        # before overwriting it.  O_NOFOLLOW (via secure_open) refuses a
        # symlinked counter path.  Mode 0o600 mirrors _write_counter.
        fd = secure_open(path, os.O_RDWR | os.O_CREAT, 0o600)
        try:
            os.fchmod(fd, 0o600)
        except OSError:
            pass
        if not fd_owned_by_us(fd):
            return 0
        if _HAS_FCNTL and _fcntl is not None:
            try:
                _fcntl.flock(fd, _fcntl.LOCK_EX)
            except (OSError, RuntimeError, NotImplementedError) as exc:
                # Lock unavailable (NFS quirks, exhausted fd table, OS
                # limits, FUSE/Windows-shim layers that surface the
                # condition as RuntimeError or NotImplementedError).
                # Emit a warning so operators have a signal that the
                # concurrency guarantee is absent on this invocation,
                # then fall through to unlocked RMW.
                print(
                    f"[vow-bounded-reads] WARN: flock unavailable, "
                    f"falling back to unlocked RMW: {exc}",
                    file=sys.stderr,
                )
        try:
            os.lseek(fd, 0, os.SEEK_SET)
            raw = os.read(fd, 4096)
        except OSError:
            raw = b""
        try:
            current = int(json.loads(raw or b"{}").get("count", 0))
        except (json.JSONDecodeError, ValueError, TypeError, AttributeError):
            current = 0
        new_count = current + 1
        try:
            os.lseek(fd, 0, os.SEEK_SET)
            os.ftruncate(fd, 0)
            os.write(fd, json.dumps({"count": new_count}).encode("utf-8"))
        except OSError as exc:
            print(
                f"[vow-bounded-reads] WARN: counter write failed: {exc}",
                file=sys.stderr,
            )
            return 0
        return new_count
    except Exception as exc:  # noqa: BLE001 - hook must not crash agent
        print(
            f"[vow-bounded-reads] WARN: counter increment failed: {exc}",
            file=sys.stderr,
        )
        return 0
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
                        f"[vow-bounded-reads] WARN: flock unlock failed: {exc}",
                        file=sys.stderr,
                    )
            try:
                os.close(fd)
            except OSError:
                pass


def _is_read_tool(tool_name: str) -> bool:
    """Return True if *tool_name* is a discovery read tool."""
    return tool_name in _READ_TOOLS


def _shadow_mode() -> bool:
    """Return True when shadow (warn-only) mode is active."""
    return shadow_mode_active()


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

        if not _is_read_tool(tool_name):
            sys.exit(0)

        new_count = _atomic_increment(counter_file)

        if new_count > _BUDGET:
            shadow = _shadow_mode()
            decision = "warn" if shadow else "block"
            reason = (
                f"Bounded discovery vow: {new_count} reads in this discovery phase. "
                f"Budget is {_BUDGET} for open exploration. "
                "Consider starting implementation."
                + (
                    " Shadow mode active — will block once VOW_SHADOW_MODE=0."
                    if shadow
                    else ""
                )
            )
            # Issue #517: Claude Code rejects the legacy hookSpecificOutput
            # wrapper. Shadow mode injects advisory text via additionalContext
            # (no permission change); block mode uses the {decision, reason}
            # root keys to halt the tool call.
            if shadow:
                output: dict[str, str] = {"additionalContext": reason}
            else:
                output = {"decision": "block", "reason": reason}
            print(json.dumps(output))
            print(
                f"[vow-bounded-reads] {decision.upper()}: "
                f"{new_count} reads (budget {_BUDGET})",
                file=sys.stderr,
            )

        sys.exit(0)

    except Exception as exc:  # hook must not crash the agent under any circumstance
        print(f"[vow-bounded-reads] internal error: {exc}", file=sys.stderr)
        sys.exit(0)


if __name__ == "__main__":
    main()
