"""Every shipped SKILL.md fits the window Claude Code keeps after compaction.

After auto-compaction Claude Code re-attaches the most recent invocation
of each skill and keeps only its first 5,000 tokens
(https://code.claude.com/docs/en/skills, "Skill content after
compaction"). Text past that point is gone for the rest of the session.
superpowers hit this in v7.0.1: subagent-driven-development lost its
five-round limit to the cut and ran 18 fix rounds on one task.

No tokenizer ships here, so the bound is 20,000 bytes, the proxy
superpowers adopted for the same limit (about four bytes per token in
English prose). A skill that needs more moves the overflow into
``modules/`` and reads it at the step that uses it.
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
REATTACH_BYTES = 20_000
SKILLS = sorted(REPO_ROOT.glob("plugins/*/skills/*/SKILL.md"))


def test_skills_were_found() -> None:
    assert SKILLS, "glob matched no SKILL.md, so the size check below checks nothing"


@pytest.mark.parametrize(
    "skill", SKILLS, ids=lambda p: str(p.relative_to(REPO_ROOT / "plugins"))
)
def test_skill_fits_the_post_compaction_window(skill: Path) -> None:
    size = skill.stat().st_size
    assert size < REATTACH_BYTES, (
        f"{skill.relative_to(REPO_ROOT)} is {size} bytes. After compaction "
        f"Claude Code keeps only its first ~{REATTACH_BYTES} bytes; move "
        f"detail into modules/."
    )
