"""Every shipped SKILL.md carries an Exit Criteria section.

`.claude/rules/skill-exit-criteria.md` requires one: a skill without exit
criteria gives the model no observable point at which to stop. The rule
alone let most skills ship without the section until a backfill closed the
gap, so this sweep is what keeps it closed.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
EXIT_CRITERIA = re.compile(r"^## Exit Criteria\s*$", re.MULTILINE)
EXIT_CRITERIA_BODY = re.compile(
    r"^## Exit Criteria[ \t]*\n(.*?)(?=^## |\Z)", re.MULTILINE | re.DOTALL
)
CHECKBOX = re.compile(r"^- \[ \] ", re.MULTILINE)


def test_every_skill_file_has_an_exit_criteria_section() -> None:
    """List every skill missing the section, so the fix needs no search."""
    missing = [
        skill.relative_to(REPO_ROOT).as_posix()
        for skill in sorted(REPO_ROOT.glob("plugins/*/skills/*/SKILL.md"))
        if not EXIT_CRITERIA.search(skill.read_text(encoding="utf-8"))
    ]
    assert missing == [], "\n".join(missing)


def test_every_exit_criteria_section_has_a_checkbox_item() -> None:
    """The rule's format is `- [ ]` items, which a plain bullet list is not.

    A section without a single checkbox reads as prose to a reviewer
    ticking criteria off, so each offending skill is named.
    """
    without_checkbox = []
    for skill in sorted(REPO_ROOT.glob("plugins/*/skills/*/SKILL.md")):
        section = EXIT_CRITERIA_BODY.search(skill.read_text(encoding="utf-8"))
        if section and not CHECKBOX.search(section.group(1)):
            without_checkbox.append(skill.relative_to(REPO_ROOT).as_posix())
    assert without_checkbox == [], "\n".join(without_checkbox)
