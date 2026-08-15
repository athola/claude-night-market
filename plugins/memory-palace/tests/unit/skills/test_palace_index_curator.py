"""Contract tests for the palace-index-curator skill.

Feature: a corrupted capture is repaired rather than re-diagnosed
  Captures whose frontmatter cannot be parsed are invisible to every
  reader, and the repair for them is a script most people will never
  guess exists. The skill that owns index health has to name it.
"""

from __future__ import annotations

from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parent.parent.parent.parent
CURATOR = PLUGIN_ROOT / "skills" / "palace-index-curator"
SKILL = CURATOR / "SKILL.md"
REPAIR_SCRIPT = PLUGIN_ROOT / "scripts" / "repair_capture_frontmatter.py"


@pytest.mark.bdd
def test_skill_names_the_repair_script() -> None:
    """Scenario: the workflow points at the repair, not just the drain."""
    assert "repair_capture_frontmatter.py" in SKILL.read_text()


@pytest.mark.bdd
def test_the_named_script_exists() -> None:
    """Scenario: the reference resolves.

    A skill naming a script that is not there is worse than silence:
    the reader spends the diagnosis time anyway, then finds nothing.
    """
    assert REPAIR_SCRIPT.exists(), f"missing {REPAIR_SCRIPT}"


@pytest.mark.bdd
def test_skill_states_the_symptom_that_sends_you_there() -> None:
    """Scenario: the pointer is findable from the symptom, not the fix.

    Nobody searches for the script by name. They arrive holding a
    capture that vanished from search results.
    """
    content = SKILL.read_text().lower()
    assert "frontmatter" in content
    assert any(word in content for word in ("unparsable", "cannot be parsed"))
