"""Test pensive:performance-review SKILL.md passes meta-evaluation.

Issue #469: the meta-evaluation in
``plugins/sanctum/scripts/update_plugins_modules/meta_evaluation.py``
flags performance-review for two missing patterns:

- ``verification|validate|check.*work|test.*correctness``
- ``test|spec``

This test pins the fix so a later edit cannot quietly remove the
content that satisfies these regexes.
"""

from __future__ import annotations

import re
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[2]
SKILL_FILE = PLUGIN_ROOT / "skills" / "performance-review" / "SKILL.md"


def test_skill_has_verification_content() -> None:
    """Scenario: performance-review SKILL.md contains verification guidance.

    Given the meta-evaluation verification regex
    When applied to the SKILL.md content
    Then it matches at least once.
    """
    text = SKILL_FILE.read_text(encoding="utf-8")
    pattern = re.compile(
        r"verification|validate|check.*work|test.*correctness", re.IGNORECASE
    )
    assert pattern.search(text), "SKILL.md must include verification language"


def test_skill_has_test_or_spec_content() -> None:
    """Scenario: performance-review SKILL.md contains test/spec guidance.

    Given the meta-evaluation test regex
    When applied to the SKILL.md content
    Then it matches at least once.
    """
    text = SKILL_FILE.read_text(encoding="utf-8")
    pattern = re.compile(r"test|spec", re.IGNORECASE)
    assert pattern.search(text), "SKILL.md must include test or spec language"


def test_verification_section_heading_present() -> None:
    """A '## Verification' heading is the chosen visible home for the content."""
    text = SKILL_FILE.read_text(encoding="utf-8")
    assert "## Verification" in text


def test_testing_section_heading_present() -> None:
    """A '## Testing' heading is the chosen visible home for the test pointer."""
    text = SKILL_FILE.read_text(encoding="utf-8")
    assert "## Testing" in text


def test_test_file_referenced() -> None:
    """The Testing section points at the existing test file location."""
    text = SKILL_FILE.read_text(encoding="utf-8")
    assert "test_performance_review.py" in text
