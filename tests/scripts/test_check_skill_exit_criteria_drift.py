"""Tests for the SKILL.md Exit-Criteria coverage guard.

The guard counts SKILL.md files that lack an ``## Exit Criteria`` section
(required by ``.claude/rules/skill-exit-criteria.md``) and fails a commit
when that count rises above a committed baseline.

The issue #454 backfill it was built for is complete, so the baseline is
zero and the ratchet is now a hard gate: the first skill to ship without
the section fails. Two things had to be true for that to hold, and each
is asserted below. The count and the allowance have to move together, or
a cleared backlog leaves behind silent permission. And the guard has to
walk the surface the rule governs, or it judges reference documentation
by a standard written for shipped skills.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import check_skill_exit_criteria_drift as gate
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


class TestSurfaceMatchesTheRule:
    """The guard walks only what the rule governs."""

    WITH = "---\nname: demo\n---\n\n## Exit Criteria\n\n- [ ] Observable\n"
    WITHOUT = "---\nname: demo\n---\n\nBody with no criteria.\n"

    def test_excludes_reference_documentation(self, tmp_path, monkeypatch) -> None:
        """
        Scenario: A SKILL.md lives under a plugin's docs tree
        Given a real skill and a documentation example
        When skill files are enumerated
        Then only the real skill is returned

        The rule's own "does not apply" list exempts reference
        documentation under ``docs/``, but the walk was a bare rglob over
        ``plugins/``. It therefore counted an example teaching
        hub-and-spoke structure as though it were a shipped skill, and
        that single file was the whole remaining backlog. Backfilling it
        would have papered over the real defect: the guard judged a wider
        surface than the rule governs.

        Exactly one SKILL.md in this repository sits under a ``docs/``
        path, so this exclusion removes that file and nothing else.
        """
        real = tmp_path / "p" / "skills" / "s" / "SKILL.md"
        real.parent.mkdir(parents=True)
        real.write_text(self.WITH, encoding="utf-8")
        example = tmp_path / "p" / "docs" / "examples" / "e" / "SKILL.md"
        example.parent.mkdir(parents=True)
        example.write_text(self.WITHOUT, encoding="utf-8")

        monkeypatch.setattr(gate, "PLUGINS_ROOT", tmp_path)
        assert gate.iter_skill_files() == [real]

    def test_excludes_vendored_virtualenvs(self, tmp_path, monkeypatch) -> None:
        """
        Scenario: A vendored venv carries a SKILL.md
        Given a plugin tree containing a .venv
        When skill files are enumerated
        Then no path from the venv is returned
        And vendored code is never judged by this guard
        """
        vendored = tmp_path / "p" / ".venv" / "pkg" / "SKILL.md"
        vendored.parent.mkdir(parents=True)
        vendored.write_text(self.WITHOUT, encoding="utf-8")

        monkeypatch.setattr(gate, "PLUGINS_ROOT", tmp_path)
        assert gate.iter_skill_files() == []


class TestRepositoryIsClean:
    """The live repository satisfies the rule at a zero allowance."""

    def test_no_skill_lacks_exit_criteria(self) -> None:
        """
        Scenario: The shipped skills satisfy the rule today
        Given every SKILL.md this guard walks
        When each is checked for an Exit Criteria heading
        Then none is missing one
        """
        missing = [
            path
            for path in gate.iter_skill_files()
            if not has_exit_criteria(path.read_text(encoding="utf-8"))
        ]
        assert missing == [], "\n".join(str(p) for p in missing)

    def test_committed_baseline_permits_nothing(self) -> None:
        """
        Scenario: The baseline records the cleared backlog
        Given the committed baseline file
        When its allowance is read
        Then it permits nothing

        A baseline left at 127 after the count fell to 1 is 126 skills of
        permission nobody meant to grant. The guard reported the drop on
        every run for months; nothing was listening.
        """
        assert gate._load_baseline() == 0

    def test_first_uncovered_skill_fails_the_gate(self) -> None:
        """
        Scenario: A new skill ships without Exit Criteria
        Given an allowance of zero
        When one file is missing the section
        Then the guard fails
        And the message names the rule that requires it

        At a zero allowance there is no slack to absorb a regression, so
        the illegal state is unrepresentable rather than capped.
        """
        ok, message = evaluate_drift(1, 0)
        assert not ok
        assert "skill-exit-criteria" in message
