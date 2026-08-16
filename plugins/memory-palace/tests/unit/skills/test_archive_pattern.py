"""Contract tests for the archive-pattern module.

Feature: Completed work is frozen and stays findable
  Deleting loses the record; leaving in place obscures what is live.
"""

from __future__ import annotations

from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parent.parent.parent.parent
CURATOR = PLUGIN_ROOT / "skills" / "palace-index-curator"
MODULE = CURATOR / "modules" / "archive-pattern.md"


@pytest.mark.bdd
def test_archive_module_exists() -> None:
    """Scenario: the module is present."""
    assert MODULE.exists(), f"missing {MODULE}"


@pytest.mark.bdd
def test_module_is_linked_from_the_skill() -> None:
    """Scenario: an unlinked module is never loaded."""
    assert "archive-pattern" in (CURATOR / "SKILL.md").read_text()


@pytest.mark.bdd
def test_archive_index_is_the_discoverability_layer() -> None:
    """Scenario: the index is what keeps archived work reachable."""
    content = MODULE.read_text()
    assert "ARCHIVE_INDEX" in content


@pytest.mark.bdd
def test_closing_note_precedes_archiving() -> None:
    """Scenario: an archived item explains why it stops where it does."""
    content = MODULE.read_text().lower()
    assert "closing note" in content


@pytest.mark.bdd
def test_deletion_is_rejected_as_the_alternative() -> None:
    """Scenario: the module states why deleting is the wrong move."""
    content = MODULE.read_text().lower()
    assert any(word in content for word in ("deleted", "deleting"))
