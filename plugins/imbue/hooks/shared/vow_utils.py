"""Shared helpers for imbue vow hooks.

Previously each vow hook (`vow_no_emoji_commits`,
`vow_no_ai_attribution`, `vow_bounded_reads`) defined its own
copy of `_shadow_mode()` and two of them duplicated
`_is_git_commit()`. Consolidating here per finding D-06.
"""

from __future__ import annotations

import os
import re

__all__ = ["is_git_commit", "shadow_mode_active"]

_GIT_COMMIT_RE = re.compile(r"git\s+commit\b")
_OFF_VALUES = ("0", "false", "no")


def shadow_mode_active() -> bool:
    """Return True when shadow (warn-only) mode is active.

    Shadow mode is the default. Set VOW_SHADOW_MODE=0 to enable blocking.
    """
    val = os.environ.get("VOW_SHADOW_MODE", "1")
    return val.strip() not in _OFF_VALUES


def is_git_commit(command: str) -> bool:
    """Return True if the Bash command is a git commit invocation."""
    return bool(_GIT_COMMIT_RE.match(command.strip()))
