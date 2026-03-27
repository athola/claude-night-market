"""BDD tests for tome papers document conversion integration.

Feature: Papers Skill PDF Conversion Enhancement
  As a researcher
  I want the papers skill to use markitdown for PDFs
  So that tables, equations, and structure are preserved
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

SKILL_FILE = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "skills"
    / "papers"
    / "SKILL.md"
)


def _parse_frontmatter(content: str) -> dict:
    """Extract YAML frontmatter from a SKILL.md file."""
    if not content.startswith("---"):
        return {}
    end = content.index("---", 3)
    return yaml.safe_load(content[3:end])


class TestPapersDocConversionDep:
    """Feature: Document conversion dependency added.

    As a plugin validator
    I want the papers skill to depend on document-conversion
    So that PDF processing uses the tiered fallback
    """

    @pytest.mark.bdd
    def test_depends_on_document_conversion(self) -> None:
        """Scenario: Dependency declared
        Given the papers SKILL.md
        When reading the dependencies
        Then leyline:document-conversion should be listed.
        """
        fm = _parse_frontmatter(SKILL_FILE.read_text())
        deps = fm.get("dependencies", [])
        assert "leyline:document-conversion" in deps


class TestPapersPdfProcessing:
    """Feature: PDF Processing uses tiered conversion.

    As a researcher reading a paper
    I want markitdown tried first for better extraction
    So that tables and equations are preserved
    """

    @pytest.mark.bdd
    def test_pdf_section_mentions_markitdown(self) -> None:
        """Scenario: markitdown referenced in PDF Processing
        Given the papers SKILL.md
        When reading the PDF Processing section
        Then it should mention markitdown.
        """
        content = SKILL_FILE.read_text()
        assert "markitdown" in content

    @pytest.mark.bdd
    def test_pdf_section_mentions_fallback(self) -> None:
        """Scenario: Read tool fallback documented
        Given the papers SKILL.md
        When reading the PDF Processing section
        Then it should mention falling back to Read tool.
        """
        content = SKILL_FILE.read_text()
        assert "Fall back" in content or "fall back" in content

    @pytest.mark.bdd
    def test_pdf_section_mentions_conversion_protocol(self) -> None:
        """Scenario: References document-conversion protocol
        Given the papers SKILL.md
        When reading the content
        Then it should reference leyline:document-conversion.
        """
        content = SKILL_FILE.read_text()
        assert "document-conversion" in content
