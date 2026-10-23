"""No shipped skill pins the session model from its frontmatter.

Since Claude Code 2.1.259 a skill's ``model:`` field is honored in
interactive sessions, and it applies "for the rest of the current turn"
(code.claude.com/docs/en/skills, frontmatter reference). A skill written as
``model: sonnet`` to hint at a cheap tier therefore drops an Opus or Fable
session to Sonnet partway through a mission, and ``model: opus`` drops a
Fable session to Opus. With ``context: fork`` the field sets the forked
subagent's model instead, which is the one place a pin is a routing choice
rather than a downgrade of the operator's session.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
MODEL_KEY = re.compile(r"^model:\s*(\S+)", re.MULTILINE)
FORK_KEY = re.compile(r"^context:\s*fork\s*$", re.MULTILINE)


def _model_pins() -> list[str]:
    pins = []
    for skill in sorted(REPO_ROOT.glob("plugins/*/skills/*/SKILL.md")):
        block = FRONTMATTER.match(skill.read_text(encoding="utf-8"))
        if block is None:
            continue
        model = MODEL_KEY.search(block.group(1))
        if model is None or model.group(1) == "inherit":
            continue
        if FORK_KEY.search(block.group(1)):
            continue
        pins.append(f"{skill.relative_to(REPO_ROOT).as_posix()}: {model.group(1)}")
    return pins


def test_no_inline_skill_overrides_the_session_model() -> None:
    """List every pin, so the fix needs no search."""
    pins = _model_pins()
    assert pins == [], "\n".join(pins)
