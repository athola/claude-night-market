"""Guard that the discussion write-back loop stays connected end to end.

``scripts/reconcile_discussions.py`` can only close the loop if commits
actually carry the ``Addresses-Discussion:`` trailer, and commits only
carry it if the skill that writes commit messages says to. A reconciler
nobody feeds reports "0 pending write-back" forever, which reads
exactly like success.

That failure mode is the one this whole loop exists to remove. The
board accumulated 46 findings with no comment, roughly half of them
long since fixed, because every individual step worked and no step
connected them. A gate wired to nothing repeats it one level up.

These assertions anchor on the trailer token itself, so deleting the
guidance from the skill or renaming the trailer in the script turns
them red rather than leaving a quietly disconnected pipeline.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "reconcile_discussions.py"
COMMIT_SKILL = (
    REPO_ROOT / "plugins" / "sanctum" / "skills" / "commit-messages" / "SKILL.md"
)
TRAILER = "Addresses-Discussion:"


def test_reconciler_exists_and_is_the_gate() -> None:
    assert SCRIPT.is_file(), "the reconciler the commit skill points at is missing"


def test_script_and_skill_agree_on_the_trailer_token() -> None:
    """One spelling of the trailer, in both places that must know it."""
    assert TRAILER in SCRIPT.read_text(encoding="utf-8")
    assert TRAILER in COMMIT_SKILL.read_text(encoding="utf-8")


def test_commit_skill_shows_the_trailer_in_a_code_block() -> None:
    """Guidance an agent can copy, not a sentence describing one."""
    text = COMMIT_SKILL.read_text(encoding="utf-8")
    blocks = re.findall(r"```[a-z]*\n(.*?)```", text, re.DOTALL)
    assert any(TRAILER in block for block in blocks), (
        f"{COMMIT_SKILL.name} mentions the trailer but never shows it in a "
        "fenced block, so there is nothing to copy"
    )


def test_commit_skill_warns_against_trailering_a_mention() -> None:
    """The distinction that keeps the reconciler from lying.

    A commit that opens a discussion must not trailer it. Without this
    warning the skill reads as "name the discussion, add the trailer",
    which is how `6b28aa1a` would have announced "Addressed" on the
    thirteen findings it had just posted.
    """
    text = COMMIT_SKILL.read_text(encoding="utf-8")
    section = text.split("Addresses-Discussion", 1)[1][:1600].lower()
    assert "resolves" in section or "resolution" in section
    assert "mention" in section, (
        "the skill does not distinguish a resolution trailer from a prose "
        "mention, so an agent will trailer discussions it merely cited"
    )
