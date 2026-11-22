"""Shared helpers for imbue vow hooks.

Previously each vow hook (`vow_no_emoji_commits`,
`vow_no_ai_attribution`, `vow_bounded_reads`) defined its own
copy of `_shadow_mode()` and two of them duplicated
`_is_git_commit()`. Consolidating here per finding D-06.

Also the single home for the symlink-safe state-file primitives
(`secure_state_dir`, `secure_open`, `fd_owned_by_us`) shared by the
hooks that keep per-session state on disk (guard_scope_ramp,
vow_bounded_reads, vow_bounded_reads_reset). Keeping the CWE-59 defense
in one audited place rather than triplicating it.
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path
from typing import Any

# fcntl is POSIX-only. Without it lock_fd and unlock_fd do nothing and the
# read-budget counter degrades to an unlocked read-modify-write, an
# acceptable race for an advisory vow on non-POSIX hosts (issue #418).
try:
    import fcntl as _fcntl

    _HAS_FCNTL = True
except ImportError:  # pragma: no cover - exercised only on non-POSIX
    _HAS_FCNTL = False

# Tests load this file on its own as well as through `shared`, so the
# copy is imported through the hooks directory rather than relatively.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from shared._vendored_leyline_shell_command import (
    git_commit_end,
    git_commit_message_offset,
    git_commit_offset,
    git_commit_spans,
    is_git_commit,
)

__all__ = [
    "OFF_VALUES",
    "O_NOFOLLOW",
    "fd_owned_by_us",
    "git_commit_end",
    "git_commit_message_offset",
    "git_commit_offset",
    "git_commit_spans",
    "is_git_commit",
    "lock_fd",
    "read_counter_path",
    "secure_open",
    "secure_state_dir",
    "session_id_from",
    "shadow_mode_active",
    "unlock_fd",
    "vow_output",
]

OFF_VALUES = ("0", "false", "no")

# O_NOFOLLOW makes open() fail (ELOOP) when the final path component is a
# symlink, so an attacker who plants a symlink at a predictable state
# path cannot redirect a hook's truncating write onto their target
# (CWE-59). Absent on non-POSIX platforms, where it degrades to 0.
O_NOFOLLOW = getattr(os, "O_NOFOLLOW", 0)


def secure_state_dir(name: str) -> Path:
    """Return a private, per-user directory for hook state files.

    Defaults to ``<tmpdir>/<name>-<uid>`` created mode 0o700 so no other
    user can plant files or symlinks inside it. ``IMBUE_STATE_DIR``
    overrides the base (used by tests for isolation). Falls back to the
    shared tmpdir root only if the private dir cannot be created. The
    per-file ``O_NOFOLLOW`` guard still applies there.
    """
    override = os.environ.get("IMBUE_STATE_DIR")
    if override:
        base = Path(override)
    else:
        uid = getattr(os, "geteuid", lambda: 0)()
        base = Path(tempfile.gettempdir()) / f"{name}-{uid}"
    try:
        base.mkdir(mode=0o700, exist_ok=True)
    except OSError:
        return Path(tempfile.gettempdir())
    return base


def secure_open(path: object, flags: int, mode: int = 0o600) -> int:
    """Open *path* with ``O_NOFOLLOW`` so a symlinked path is refused.

    Returns the file descriptor (caller closes it). Raises ``OSError``
    (``ELOOP``) when the final component is a symlink, which the caller
    treats as a refusal rather than following the link.
    """
    return os.open(str(path), flags | O_NOFOLLOW, mode)


def fd_owned_by_us(fd: int) -> bool:
    """Return True if the fd is owned by the current user (else distrust it).

    On non-POSIX hosts with no uid model this is always True.
    """
    geteuid = getattr(os, "geteuid", None)
    if geteuid is None:
        return True
    try:
        return bool(os.fstat(fd).st_uid == geteuid())
    except OSError:
        return False


def shadow_mode_active() -> bool:
    """Return True when shadow (warn-only) mode is active.

    Shadow mode is the default. Set VOW_SHADOW_MODE=0 to enable blocking.
    """
    val = os.environ.get("VOW_SHADOW_MODE", "1")
    return val.strip() not in OFF_VALUES


def vow_output(enforce: bool, reason: str) -> dict[str, Any]:
    """Return the PreToolUse output for a vow that fired.

    Claude Code honors permissionDecision values allow, deny, ask and
    defer and ignores any other, so enforcement must say "deny". A vow
    in shadow mode adds the reason as context and leaves the permission
    decision to the user's settings.
    """
    hook: dict[str, Any] = {"hookEventName": "PreToolUse"}
    if enforce:
        hook["permissionDecision"] = "deny"
        hook["permissionDecisionReason"] = reason
    else:
        hook["additionalContext"] = reason
    return {"hookSpecificOutput": hook}


def read_counter_path(session_id: str) -> Path:
    """Return the session-scoped read-budget counter file.

    vow_bounded_reads increments it and vow_bounded_reads_reset zeroes it.
    One definition, so the reset cannot drift to a different file. It is
    in a private per-user dir (mode 0o700) so another user cannot plant a
    symlink at this predictable name.
    """
    safe_id = (
        session_id.replace("/", "_").replace("\\", "_") if session_id else "default"
    )
    return (
        secure_state_dir("imbue-vow-state") / f"vow_read_counter_{safe_id[:200]}.json"
    )


def session_id_from(data: dict) -> str:
    """Extract the session id from hook stdin, the environment, or the pid.

    Issue #580: the last-resort fallback must not be a fixed constant. A
    shared ``default`` filename made every session without a session_id
    write to the same counter, so a stale count over budget bled into
    every later session. The parent pid (the Claude Code process) is
    stable within a session and distinct across concurrent ones.
    """
    sid = data.get("session_id", "")
    if sid:
        # A subagent carries its parent's session_id; without its agent_id
        # it spent the parent's read budget.
        agent = data.get("agent_id")
        return f"{sid}:{agent}" if agent else str(sid)
    sid = os.environ.get("CLAUDE_SESSION_ID", "")
    if sid:
        return sid
    return f"pid-{os.getppid()}"


def lock_fd(fd: int, where: str = "") -> None:
    """Take an exclusive flock on *fd*, or warn on stderr and go on unlocked.

    *where* names the caller in the warning (" on reset"). A lock can be
    unavailable on NFS, with an exhausted fd table, or on FUSE and Windows
    shim layers that raise RuntimeError or NotImplementedError. The warning
    tells operators the concurrency guarantee is absent for this call.
    """
    if not _HAS_FCNTL:
        if "PYTEST_CURRENT_TEST" not in os.environ:
            print(
                "[vow-bounded-reads] WARN: fcntl unavailable on this platform; "
                "counter updates are not atomic under concurrent calls",
                file=sys.stderr,
            )
        return
    try:
        _fcntl.flock(fd, _fcntl.LOCK_EX)
    except (OSError, RuntimeError, NotImplementedError) as exc:
        print(
            f"[vow-bounded-reads] WARN: flock unavailable{where}, "
            f"falling back to unlocked access: {exc}",
            file=sys.stderr,
        )


def unlock_fd(fd: int, where: str = "") -> None:
    """Release the flock on *fd*, warning on stderr when that fails.

    A silent unlock failure would hide a lock leak that the acquire-side
    warning would have shown.
    """
    if not _HAS_FCNTL:
        return
    try:
        _fcntl.flock(fd, _fcntl.LOCK_UN)
    except (OSError, RuntimeError, NotImplementedError) as exc:
        print(
            f"[vow-bounded-reads] WARN: flock unlock failed{where}: {exc}",
            file=sys.stderr,
        )
