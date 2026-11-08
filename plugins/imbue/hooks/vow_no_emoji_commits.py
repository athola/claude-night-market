#!/usr/bin/env python3
"""Vow: No emojis in commits (Hard layer).

PreToolUse hook that blocks (or warns in shadow mode) when a
`git commit` command contains emoji characters in the commit message.

Shadow mode is ON by default (warn only).  Set VOW_SHADOW_MODE=0
to switch to full blocking.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# D-06: shadow_mode + git_commit_offset live in shared/vow_utils.
sys.path.insert(0, str(Path(__file__).parent))
from shared.vow_utils import (  # noqa: E402 - hook script must inject sys.path before importing sibling shared/ module
    git_commit_offset,
    shadow_mode_active,
    vow_output,
)

# The astral emoji blocks are emoji throughout. U+2300-27BF and the
# arrows and stars past it are mostly text symbols that commit messages
# use on purpose (the check mark, the command key, arrows), so only the
# characters that render as emoji by default (Emoji_Presentation=Yes),
# or a symbol followed by the emoji selector U+FE0F, count there.
_EMOJI_RE = re.compile(
    "["
    "\U0001f300-\U0001faff"
    "\U0001f000-\U0001f02f"
    "\U0001f0a0-\U0001f0ff"
    "\U0001f100-\U0001f1ff"
    "\U0001f200-\U0001f2ff"
    "\u231a\u231b\u23e9-\u23ec\u23f0\u23f3\u25fd\u25fe\u2614\u2615"
    "\u2648-\u2653\u267f\u2693\u26a1\u26aa\u26ab\u26bd\u26be\u26c4"
    "\u26c5\u26ce\u26d4\u26ea\u26f2\u26f3\u26f5\u26fa\u26fd\u2705"
    "\u270a\u270b\u2728\u274c\u274e\u2753-\u2755\u2757\u2795-\u2797"
    "\u27b0\u27bf\u2b1b\u2b1c\u2b50\u2b55"
    "]"
    "|[\u2190-\u2bff\u3030\u303d]\ufe0f",
    re.UNICODE,
)


def _has_emoji(command: str) -> bool:
    """Return True if *command* contains an emoji character."""
    return bool(_EMOJI_RE.search(command))


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
        offset = git_commit_offset(command)
        if offset is None:
            sys.exit(0)

        # An emoji in an earlier command ("echo ... && git commit") is not
        # in the commit message.
        if not _has_emoji(command[offset:]):
            sys.exit(0)

        shadow = shadow_mode_active()
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

        output = vow_output(enforce=decision == "block", reason=reason)
        print(json.dumps(output))
        print(
            f"[vow-no-emoji-commits] {decision.upper()}: emoji in commit",
            file=sys.stderr,
        )
        sys.exit(0)

    except Exception as exc:  # hook must not crash the agent under any circumstance
        print(f"[vow-no-emoji-commits] internal error: {exc}", file=sys.stderr)
        sys.exit(0)


if __name__ == "__main__":
    main()
