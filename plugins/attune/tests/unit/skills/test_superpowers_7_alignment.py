"""attune's brainstorm, plan and execute phases track superpowers v7.0.2.

attune delegates to the matching superpowers skill when it is installed
and runs its own version when it is not. These tests pin the behaviors
ported from upstream (RELEASE-NOTES.md v6.0.0 to v7.0.2) and the claims
attune makes about what the superpowers skills do.
"""

from __future__ import annotations

from pathlib import Path

ATTUNE = Path(__file__).resolve().parents[3]


def _prose(relative: str) -> str:
    """Return a file with whitespace collapsed, so line wrapping cannot hide a clause."""
    return " ".join((ATTUNE / relative).read_text(encoding="utf-8").split())


PLANNING = "skills/project-planning/SKILL.md"
BLUEPRINT = "commands/blueprint.md"
BRAINSTORMING = "skills/project-brainstorming/SKILL.md"
SPEC_REVIEW = "skills/project-brainstorming/modules/spec-review-loop.md"
EXECUTION = "skills/project-execution/SKILL.md"
EXECUTE = "commands/execute.md"


class TestPlanShape:
    """writing-plans v6.0.0 to v6.4.2: a plan records decisions, not code."""

    def test_quality_checks_require_global_constraints(self) -> None:
        """Rules copied once reach implementers that see only their own task."""
        assert "Global Constraints" in _prose(PLANNING)

    def test_quality_checks_require_review_focus(self) -> None:
        """Upstream evals shipped one crash on an input the spec implied but never named."""
        assert "Review Focus" in _prose(PLANNING)

    def test_quality_checks_reject_a_code_transcript(self) -> None:
        """Full-code plans took four times as long and tempted models to build while planning."""
        assert "records decisions, not code" in _prose(PLANNING)

    def test_blueprint_task_template_names_its_interfaces(self) -> None:
        """A task's neighbors' contracts are visible without reading their tasks."""
        assert "**Interfaces**: Consumes" in _prose(BLUEPRINT)

    def test_blueprint_no_longer_claims_checkpoint_execution(self) -> None:
        """executing-plans stopped pausing every few tasks in v5.1.0 and v6.4.1."""
        assert "checkpoint-based execution flow" not in _prose(BLUEPRINT)


class TestBuilderCheck:
    """brainstorming v7.0.0: a builder check replaced the spec reviewer."""

    def test_reviewer_reads_as_the_builder(self) -> None:
        """A checklist catches placeholders; a builder's questions catch gaps the checklist cannot name."""
        assert "still need to ask" in _prose(SPEC_REVIEW)

    def test_questions_are_sorted_into_three_piles(self) -> None:
        """Only questions that change what gets built reach the human, in one round."""
        text = _prose(SPEC_REVIEW)
        assert "Answered already" in text
        assert "Minor" in text
        assert "Theirs" in text

    def test_builder_questions_do_not_depend_on_the_verdict(self) -> None:
        """An approved brief can still leave a builder with questions."""
        assert "whatever the verdict" in _prose(SPEC_REVIEW)

    def test_theirs_pile_reaches_the_human_once(self) -> None:
        """Three review rounds must not become three rounds of questions."""
        assert "once, after the loop ends" in _prose(SPEC_REVIEW)

    def test_phase_6_5_describes_the_builder_questions(self) -> None:
        """The SKILL.md procedure is what a session follows; it must match the module."""
        assert "builder questions" in _prose(BRAINSTORMING)


class TestIntentFirstQuestions:
    """brainstorming v6.4.1 and v7.0.2: ask why first, offer options."""

    def test_unstated_why_is_asked_first(self) -> None:
        """The motivating upstream session took scope approval as permission to build."""
        assert "ask why first" in _prose(BRAINSTORMING)

    def test_nameable_choice_comes_with_a_recommendation(self) -> None:
        """A bare 'which one?' made the person do the analysis the agent had already done."""
        assert "options with a recommendation" in _prose(BRAINSTORMING)


class TestExecutionClaims:
    """executing-plans v6.4.1: Native execution with one whole-branch review."""

    def test_execution_skill_names_both_modes(self) -> None:
        """Since v6.4.1 subagent-driven development is one of two modes, not the only one."""
        text = _prose(EXECUTION)
        assert "Native" in text
        assert "subagent-driven-development" in text

    def test_execute_command_no_longer_claims_checkpoints(self) -> None:
        """Without superpowers attune runs its own phase checks; the old line credited them to superpowers."""
        assert "checkpoint-based approach" not in _prose(EXECUTE)
