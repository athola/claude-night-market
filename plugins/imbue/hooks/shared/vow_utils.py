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
import re
import tempfile
from pathlib import Path

__all__ = [
    "O_NOFOLLOW",
    "fd_owned_by_us",
    "is_git_commit",
    "secure_open",
    "secure_state_dir",
    "shadow_mode_active",
]

_GIT_COMMIT_RE = re.compile(r"git\s+commit\b")
_OFF_VALUES = ("0", "false", "no")

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
    shared tmpdir root only if the private dir cannot be created; the
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
        return os.fstat(fd).st_uid == geteuid()
    except OSError:
        return False


def shadow_mode_active() -> bool:
    """Return True when shadow (warn-only) mode is active.

    Shadow mode is the default. Set VOW_SHADOW_MODE=0 to enable blocking.
    """
    val = os.environ.get("VOW_SHADOW_MODE", "1")
    return val.strip() not in _OFF_VALUES


def is_git_commit(command: str) -> bool:
    """Return True if the Bash command is a git commit invocation."""
    return bool(_GIT_COMMIT_RE.match(command.strip()))
