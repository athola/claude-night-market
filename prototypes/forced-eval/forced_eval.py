#!/usr/bin/env python3
"""Forced-eval skill-activation hook (PROTOTYPE).

A UserPromptSubmit hook prototype that forces the model to evaluate
available skills before acting. This targets the activation-reliability
problem documented in the tome research (Scott Spence; umputun): the
skill activation layer does near-keyword matching, so relevant skills
sometimes fail to fire. Forcing an explicit evaluation pass lifts
activation materially in the cited sources.

NOT WIRED. This is a prototype. It is not registered in any plugin.json
and is not installed globally. The core logic is unit-tested; measuring
the live activation lift requires the sandboxed-eval methodology in
README.md.

The output contract mirrors plugins/egregore/hooks/user_prompt_hook.py:
print {"hookSpecificOutput": {"hookEventName": "UserPromptSubmit",
"additionalContext": ...}} to stdout.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path


def _frontmatter(text: str) -> str:
    """Return the YAML frontmatter block of a skill file."""
    if not text.startswith("---"):
        return text[:512]
    parts = text.split("---", 2)
    return parts[1] if len(parts) >= 3 else text[:512]


def discover_skill_names(root: Path) -> list[str]:
    """Return skill names from <root>/skills/**/SKILL.md frontmatter."""
    names: list[str] = []
    skills_dir = root / "skills"
    if not skills_dir.is_dir():
        return names
    for skill_md in skills_dir.rglob("SKILL.md"):
        text = skill_md.read_text(errors="replace")
        match = re.search(r"^name:\s*(.+?)\s*$", _frontmatter(text), re.MULTILINE)
        if match:
            names.append(match.group(1).strip())
    return names


def build_eval_reminder(skill_names: list[str]) -> str:
    """Build the forced-eval additionalContext string.

    An empty list returns an empty string so the hook injects nothing
    when there are no skills to evaluate (no noisy context).
    """
    if not skill_names:
        return ""
    listing = ", ".join(skill_names)
    return (
        "Before responding, evaluate whether any installed skill "
        "matches this task and invoke it with the Skill tool if it "
        f"does. Skills to consider: {listing}."
    )


def format_response(context: str) -> dict:
    """Wrap context in the UserPromptSubmit hook output contract."""
    return {
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": context,
        }
    }


def main() -> None:
    """UserPromptSubmit hook entrypoint. Consumes the stdin event."""
    try:
        json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        pass

    # Demo default: this prototype's own dir. README shows how to point
    # FORCED_EVAL_ROOT at a real plugin tree.
    root = Path(__file__).resolve().parent
    forced_root = os.environ.get("FORCED_EVAL_ROOT")
    if forced_root:
        root = Path(forced_root)

    reminder = build_eval_reminder(discover_skill_names(root))
    if reminder:
        print(json.dumps(format_response(reminder)))
    sys.exit(0)


if __name__ == "__main__":
    main()
