"""BDD tests for scribe doc-generator skill structure.

Feature: Doc Generator Enforces Document-Economy
  As a documentation author
  I want the doc-generator skill to require a thesis and to
  surface the reader-time budget at scope time
  So that generated docs cannot bypass document-level economy.
"""

from __future__ import annotations

from pathlib import Path

import pytest

SKILL_DIR = (
    Path(__file__).resolve().parent.parent.parent.parent / "skills" / "doc-generator"
)
SKILL_FILE = SKILL_DIR / "SKILL.md"


class TestDocGeneratorScopeRequiresThesis:
    """Feature: Generation Request template requires a thesis.

    Scope must force the author to state the single takeaway.
    """

    @pytest.fixture
    def skill_text(self) -> str:
        return SKILL_FILE.read_text()

    @pytest.mark.unit
    def test_skill_file_exists(self) -> None:
        """The doc-generator SKILL.md must exist."""
        assert SKILL_FILE.exists()

    @pytest.mark.unit
    def test_scope_template_includes_thesis_field(self, skill_text: str) -> None:
        """Generation Request must include a Thesis field."""
        assert "**Thesis**" in skill_text, (
            "Generation Request template must include a Thesis field "
            "so authors cannot skip stating the takeaway"
        )

    @pytest.mark.unit
    def test_scope_template_includes_audience_size(self, skill_text: str) -> None:
        """Generation Request must surface audience size."""
        assert "Audience size" in skill_text, (
            "Generation Request must include audience size so the "
            "reader-time budget can be estimated"
        )

    @pytest.mark.unit
    def test_scope_template_includes_read_frequency(self, skill_text: str) -> None:
        """Generation Request must surface read frequency."""
        assert "Read frequency" in skill_text, (
            "Generation Request must include read frequency so the "
            "reader-time budget reflects ongoing cost"
        )


class TestDocGeneratorDraftStepEnforcesThesisFirst:
    """Feature: Draft Content step leads with thesis-first.

    The drafting guidance must direct authors to state the
    thesis before anything else.
    """

    @pytest.fixture
    def skill_text(self) -> str:
        return SKILL_FILE.read_text()

    @pytest.mark.unit
    def test_draft_step_demands_thesis_in_lead(self, skill_text: str) -> None:
        """Draft Content step must instruct lead-with-thesis."""
        text_lower = skill_text.lower()
        assert "lead with the thesis" in text_lower or (
            "thesis" in text_lower and "first paragraph" in text_lower
        ), "Step 3: Draft Content must explicitly require leading with the thesis"

    @pytest.mark.unit
    def test_skill_references_document_economy_module(self, skill_text: str) -> None:
        """Skill must point readers at the document-economy module."""
        assert "document-economy" in skill_text, (
            "doc-generator must reference the slop-detector "
            "document-economy module so the rubric is discoverable"
        )


class TestDocGeneratorEatsItsOwnDogfood:
    """Feature: doc-generator SKILL.md follows document-economy itself.

    The skill that teaches thesis-first drafting cannot itself
    bury its own thesis.
    """

    @pytest.fixture
    def skill_text(self) -> str:
        return SKILL_FILE.read_text()

    @pytest.mark.unit
    def test_skill_states_thesis_in_lead(self, skill_text: str) -> None:
        """First section after H1 must contain a bolded thesis."""
        h1_idx = skill_text.find("# Documentation Generator")
        assert h1_idx >= 0
        lead = skill_text[h1_idx : h1_idx + 800]
        assert "**" in lead, "Lead must contain a bolded thesis sentence"
