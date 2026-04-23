#!/usr/bin/env python3
"""Vow: No emojis in commits (Hard layer).

PreToolUse hook that blocks (or warns in shadow mode) when a
`git commit` command contains emoji characters in the commit message.

Shadow mode is ON by default (warn only).  Set VOW_SHADOW_MODE=0
to switch to full blocking.
"""

from __future__ import annotations

import json
import os
import re
import sys

_EMOJI_RE = re.compile(
    "["
    "\U0001f300-\U0001faff"
    "\U00002600-\U000027bf"
    "\U00002300-\U000023ff"
    "\U0001f000-\U0001f02f"
    "\U0001f0a0-\U0001f0ff"
    "\U0001f100-\U0001f1ff"
    "\U0001f200-\U0001f2ff"
    "\U00003030-\U0000303f"
    "]",
    re.UNICODE,
)


def _is_git_commit(command: str) -> bool:
    """Return True if the Bash command is a git commit invocation."""
    stripped = command.strip()
    return bool(re.match(r"git\s+commit\b", stripped))


def _has_emoji(command: str) -> bool:
    """Return True if *command* contains an emoji character."""
    return bool(_EMOJI_RE.search(command))


def _shadow_mode() -> bool:
    """Return True when shadow (warn-only) mode is active.

    Shadow mode is the default.  Set VOW_SHADOW_MODE=0 to enable blocking.
    """
    val = os.environ.get("VOW_SHADOW_MODE", "1")
    return val.strip() not in ("0", "false", "no")


def main() -> None:
    """Entry point for the PreToolUse hook."""
    try:
        raw = sys.stdin.read()
        data = json.loads(raw)
    except (json.JSONDecodeError, OSError):
        sys.exit(0)

    try:
        tool_name = data.get("tool_name", "")
        if tool_name != "Bash":
            sys.exit(0)

        command = data.get("tool_input", {}).get("command", "")
        if not _is_git_commit(command):
            sys.exit(0)

        if not _has_emoji(command):
            sys.exit(0)

        shadow = _shadow_mode()
        decision = "warn" if shadow else "block"
        reason = (
            "Vow violation: emoji character detected in commit message. "
            "Night Market vow prohibits emoji in commit messages (Hard vow). "
            + (
                "Shadow mode active -- this will block once VOW_SHADOW_MODE=0."
                if shadow
                else ""
            )
        )

        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": decision,
                "permissionDecisionReason": reason,
            }
        }
        print(json.dumps(output))
        print(
            f"[vow-no-emoji-commits] {decision.upper()}: emoji in commit",
            file=sys.stderr,
        )
        sys.exit(0)

    except Exception:  # hook must not crash the agent under any circumstance
        sys.exit(0)


if __name__ == "__main__":
    main()
