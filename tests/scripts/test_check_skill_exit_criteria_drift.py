"""Tests for the SKILL.md Exit-Criteria coverage ratchet.

The guard counts SKILL.md files that lack an ``## Exit Criteria`` section
(the backlog tracked in issue #454 and required by
``.claude/rules/skill-exit-criteria.md``) and fails a commit only when
that count rises above a committed baseline. This stops new skills from
shipping without exit criteria while letting the existing backfill
proceed in batches.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from check_skill_exit_criteria_drift import evaluate_drift, has_exit_criteria


class TestHasExitCriteria:
    """Detection of the Exit-Criteria heading in SKILL.md text."""

    def test_detects_h2_heading(self) -> None:
        """A standard ``## Exit Criteria`` heading is detected."""
        text = "# Skill\n\nbody\n\n## Exit Criteria\n\n- [ ] thing\n"
        assert has_exit_criteria(text) is True

    def test_detects_deeper_heading(self) -> None:
        """A deeper ``### Exit Criteria`` heading still counts."""
        assert has_exit_criteria("### Exit Criteria\n") is True

    def test_absent_when_missing(self) -> None:
        """A skill with no exit-criteria heading is flagged."""
        assert has_exit_criteria("# Skill\n\njust a description\n") is False

    def test_prose_mention_does_not_count(self) -> None:
        """A passing mention in prose is not a heading and does not count."""
        text = "We should define exit criteria somewhere.\n"
        assert has_exit_criteria(text) is False

    def test_requires_heading_marker(self) -> None:
        """A bare line 'Exit Criteria' without '##' does not count."""
        assert has_exit_criteria("Exit Criteria\n\n- [ ] thing\n") is False


class TestEvaluateDrift:
    """The ratchet comparison for the missing-count."""

    def test_equal_to_baseline_passes(self) -> None:
        """At the baseline, the commit is allowed."""
        ok, _ = evaluate_drift(current=127, baseline=127)
        assert ok is True

    def test_below_baseline_passes(self) -> None:
        """Fewer missing files than baseline passes and nudges downward."""
        ok, message = evaluate_drift(current=120, baseline=127)
        assert ok is True
        assert "120" in message

    def test_above_baseline_fails(self) -> None:
        """A new skill without exit criteria blocks the commit."""
        ok, message = evaluate_drift(current=128, baseline=127)
        assert ok is False
        assert "128" in message and "127" in message
