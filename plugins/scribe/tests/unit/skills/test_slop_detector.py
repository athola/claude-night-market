"""BDD tests for scribe slop-detector skill structure.

Feature: Slop Detector Skill Document-Economy Integration
  As a documentation maintainer
  I want the slop-detector skill to enforce both sentence-level
  and document-level economy
  So that long-but-clean docs no longer pass review.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

SKILL_DIR = (
    Path(__file__).resolve().parent.parent.parent.parent / "skills" / "slop-detector"
)
SKILL_FILE = SKILL_DIR / "SKILL.md"
MODULES_DIR = SKILL_DIR / "modules"
DOC_ECONOMY_MODULE = MODULES_DIR / "document-economy.md"


def _parse_frontmatter(content: str) -> dict:
    """Extract YAML frontmatter from a SKILL.md file."""
    if not content.startswith("---"):
        return {}
    end = content.index("---", 3)
    return yaml.safe_load(content[3:end])


class TestDocumentEconomyModuleExists:
    """Feature: document-economy module is wired into slop-detector.

    Scenario: SKILL.md frontmatter references the module
    Scenario: module file exists on disk
    Scenario: module declares its thesis in the lead
    """

    @pytest.mark.unit
    def test_skill_file_exists(self) -> None:
        """The slop-detector SKILL.md must exist."""
        assert SKILL_FILE.exists(), f"Expected SKILL.md at {SKILL_FILE}"

    @pytest.mark.unit
    def test_frontmatter_lists_document_economy_module(self) -> None:
        """Frontmatter `modules:` must include document-economy."""
        fm = _parse_frontmatter(SKILL_FILE.read_text())
        modules = fm.get("modules", [])
        assert "document-economy" in modules, (
            "document-economy must be listed in slop-detector "
            "SKILL.md frontmatter modules"
        )

    @pytest.mark.unit
    def test_module_file_exists(self) -> None:
        """The document-economy module file must exist."""
        assert DOC_ECONOMY_MODULE.exists(), f"Expected module at {DOC_ECONOMY_MODULE}"


class TestDocumentEconomyModuleStructure:
    """Feature: module follows its own thesis-first rule.

    The module must demonstrate the discipline it teaches.
    """

    @pytest.fixture
    def module_text(self) -> str:
        """Read the document-economy module."""
        return DOC_ECONOMY_MODULE.read_text()

    @pytest.mark.unit
    def test_module_states_thesis_in_lead(self, module_text: str) -> None:
        """First 600 chars must contain a bolded thesis sentence."""
        lead = module_text[:600]
        assert "**" in lead, "Lead must contain bolded text marking the thesis"

    @pytest.mark.unit
    def test_module_defines_three_checks(self, module_text: str) -> None:
        """Module must define thesis, sentence-weight, and repetition checks."""
        assert "Thesis-first" in module_text
        assert "Sentence weight" in module_text
        assert "repetition" in module_text.lower()

    @pytest.mark.unit
    def test_module_provides_scoring_rubric(self, module_text: str) -> None:
        """A scoring rubric must be present so reviewers can score docs."""
        assert "score" in module_text.lower()
        assert "rubric" in module_text.lower() or "0-2" in module_text

    @pytest.mark.unit
    def test_module_includes_worked_example(self, module_text: str) -> None:
        """A before/after example anchors the rule in practice."""
        text_lower = module_text.lower()
        assert "before" in text_lower and "after" in text_lower, (
            "Module must show a before/after pairing"
        )

    @pytest.mark.unit
    def test_module_references_reader_time_budget(self, module_text: str) -> None:
        """The reader-time budget concept must be explicit."""
        assert "reader-time budget" in module_text.lower() or (
            "reader" in module_text.lower() and "budget" in module_text.lower()
        )


class TestSkillFileEatsItsOwnDogfood:
    """Feature: slop-detector SKILL.md follows document-economy itself.

    The skill that teaches document economy cannot itself violate it.
    """

    @pytest.fixture
    def skill_text(self) -> str:
        """Read the slop-detector SKILL.md."""
        return SKILL_FILE.read_text()

    @pytest.mark.unit
    def test_skill_references_document_economy_step(self, skill_text: str) -> None:
        """SKILL.md must point readers at the document-economy module."""
        assert "document-economy" in skill_text or ("Document Economy" in skill_text), (
            "SKILL.md must reference the document-economy module so "
            "readers know to load it"
        )
