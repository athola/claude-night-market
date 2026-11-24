"""A review answers four questions, and the first two belong before it.

ADR-0031 splits a pull request review into four questions: is the change
needed (Q1), is the approach right (Q2), is the code correct (Q3), and
does it fit what the team already understands of the system (Q4). Q1 and
Q2 are best settled before the PR opens. Zanaty et al. 2018 found that
changes drawing design feedback in review are abandoned more often.

The review records where Q1 and Q2 were settled and checks the diff
against that record. A disagreement with a settled decision is a REVISIT
routed to the record, not a re-litigation in the PR. Q3 attention is
ordered by risk, and what was read lightly is stated, because no study
shows an agreed design shrinks the space bugs hide in. Q4 still covers
every file: about three quarters of what review finds is evolvability,
and team understanding is the outcome review demonstrably delivers.

Nothing imports these documents. A deleted passage would fail
silently. Each test anchors on a clause unique to the passage it guards.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parents[3]
REPO_ROOT = PLUGIN_ROOT.parents[1]

PR_REVIEW = PLUGIN_ROOT / "skills" / "pr-review"
MODULE = PR_REVIEW / "modules" / "review-questions.md"
SKILL = PR_REVIEW / "SKILL.md"
SCOPE = PR_REVIEW / "modules" / "scope-classification.md"
PHASES_1_4 = (
    PLUGIN_ROOT / "commands" / "pr-review" / "modules" / "review-workflow-phases-1-4.md"
)
PR_TEMPLATE = PLUGIN_ROOT / "skills" / "pr-prep" / "modules" / "pr-template.md"
PR_PREP = PLUGIN_ROOT / "skills" / "pr-prep" / "SKILL.md"
ADR = REPO_ROOT / "docs" / "adr" / "0031-review-questions-answered-in-order.md"


def _text(path: Path) -> str:
    """Collapse whitespace: an 80-column reflow must not break an anchor."""
    return re.sub(r"\s+", " ", path.read_text(encoding="utf-8"))


class TestReviewQuestionsModule:
    """The module names the four questions and how each is routed."""

    @pytest.mark.parametrize(
        "question",
        [
            "Q1: Is this change needed?",
            "Q2: Is the approach right?",
            "Q3: Does the code do what it claims?",
            "Q4: Does it fit the team's understanding of the system?",
        ],
    )
    def test_names_each_question(self, question: str) -> None:
        assert question in _text(MODULE)

    def test_settled_decision_is_checked_not_reargued(self) -> None:
        text = _text(MODULE)
        assert "check the diff against the record" in text
        assert "REVISIT" in text

    def test_missing_record_matters_only_for_design_bearing_changes(self) -> None:
        text = _text(MODULE)
        assert "design-bearing" in text
        assert "A routine change with no record is not a finding" in text

    def test_light_reads_are_disclosed(self) -> None:
        assert "Read lightly" in _text(MODULE)

    def test_q4_covers_every_file(self) -> None:
        assert "Q4 applies to every changed file" in _text(MODULE)

    def test_narrowed_bug_space_is_labelled_a_hypothesis(self) -> None:
        assert "unmeasured hypothesis" in _text(MODULE)


class TestPrReviewSkill:
    """The skill runs the module at Phase 1 and reports its answers."""

    def test_lists_the_module(self) -> None:
        assert "modules/review-questions.md" in _text(SKILL)

    def test_phase_one_locates_the_decision_record(self) -> None:
        assert "Locate the decision record" in _text(SKILL)

    def test_report_has_review_questions_block(self) -> None:
        assert "### Review Questions" in _text(SKILL)

    def test_exit_criterion_records_q1_and_q2(self) -> None:
        assert "Q1 and Q2 are each recorded as settled" in _text(SKILL)


class TestCommandCopy:
    """The command's Phase 1 copy carries the same step, or it drifts."""

    def test_phase_one_locates_the_decision_record(self) -> None:
        text = _text(PHASES_1_4)
        assert "Locate the decision record" in text
        assert "review-questions.md" in text


class TestRevisitCategory:
    """REVISIT routes disagreement with a settled decision to its record."""

    def test_revisit_row_exists(self) -> None:
        assert "| **REVISIT** |" in SCOPE.read_text(encoding="utf-8")

    def test_new_facts_escalate_to_blocking(self) -> None:
        assert "new facts the decision did not have" in _text(SCOPE)


class TestAuthorSide:
    """The author links the record and says where review time should go."""

    def test_template_links_the_decision_record(self) -> None:
        assert "link where the need and the approach were agreed" in _text(PR_TEMPLATE)

    def test_template_names_where_to_look(self) -> None:
        assert "Where to look" in _text(PR_TEMPLATE)

    def test_facts_table_stays_three_rows(self) -> None:
        text = PR_TEMPLATE.read_text(encoding="utf-8")
        assert "**Decided**" not in text

    def test_pr_prep_flags_design_bearing_change_without_record(self) -> None:
        text = _text(PR_PREP)
        assert "design-bearing" in text
        assert "no decision record" in text


class TestAdr:
    """The decision and its evidence are kept where git tracks them."""

    def test_adr_is_accepted(self) -> None:
        assert "**Status**: Accepted" in ADR.read_text(encoding="utf-8")

    def test_adr_cites_the_abandonment_finding(self) -> None:
        assert "Zanaty" in _text(ADR)

    def test_adr_reads_fagan_from_the_paper(self) -> None:
        """82% is design and code inspection together, read from Table 1."""
        text = _text(ADR)
        assert "Fagan" in text
        assert "design and code inspections together found 82%" in text


GITHUB_TEMPLATES = [
    REPO_ROOT / ".github" / "PULL_REQUEST_TEMPLATE.md",
    *sorted((REPO_ROOT / ".github" / "PULL_REQUEST_TEMPLATE").glob("*.md")),
]
PREPARE_PR = PLUGIN_ROOT / "commands" / "prepare-pr.md"
PR_AGENT = PLUGIN_ROOT / "agents" / "pr-agent.md"


class TestWiring:
    """Every surface that builds a report or a description carries the change."""

    def test_command_local_report_has_both_sections(self) -> None:
        text = PHASES_1_4.read_text(encoding="utf-8")
        assert "## Review Questions" in text
        assert "## Revisit (N)" in text

    def test_skill_report_has_revisit_section(self) -> None:
        assert "### Revisit (" in SKILL.read_text(encoding="utf-8")

    def test_read_lists_come_from_what_was_read(self) -> None:
        assert "from what it reports having read" in _text(SKILL)

    def test_revisit_is_confirmed_before_posting(self) -> None:
        text = _text(MODULE)
        assert "Posting a REVISIT is outward-facing, so ask first" in text
        assert "REVISIT findings appear in the report only" in text

    @pytest.mark.parametrize(
        "path",
        [*GITHUB_TEMPLATES, PREPARE_PR, PR_AGENT],
        ids=lambda p: p.name,
    )
    def test_author_copy_names_where_to_look(self, path: Path) -> None:
        assert "Where to look" in path.read_text(encoding="utf-8")
