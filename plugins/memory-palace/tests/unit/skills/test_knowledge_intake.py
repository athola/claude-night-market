"""BDD tests for knowledge-intake document conversion integration.

Feature: Knowledge Intake Document Format Detection
  As a knowledge curator
  I want the intake skill to detect document formats
  So that PDFs, DOCX, and other documents are converted
  to markdown before evaluation
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

SKILL_FILE = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "skills"
    / "knowledge-intake"
    / "SKILL.md"
)


def _parse_frontmatter(content: str) -> dict:
    """Extract YAML frontmatter from a SKILL.md file."""
    if not content.startswith("---"):
        return {}
    end = content.index("---", 3)
    return yaml.safe_load(content[3:end])


class TestKnowledgeIntakeDocConversionDep:
    """Feature: Document conversion dependency added.

    As a plugin validator
    I want knowledge-intake to depend on document-conversion
    So that it can convert documents before evaluation
    """

    @pytest.mark.bdd
    def test_depends_on_document_conversion(self) -> None:
        """Scenario: Dependency declared
        Given the knowledge-intake SKILL.md
        When reading the dependencies
        Then leyline:document-conversion should be listed.
        """
        fm = _parse_frontmatter(SKILL_FILE.read_text())
        deps = fm.get("dependencies", [])
        assert "leyline:document-conversion" in deps


class TestKnowledgeIntakeFormatDetection:
    """Feature: FETCH step includes format detection.

    As a user sharing a PDF link
    I want the intake to detect the format
    So that it uses the right conversion method
    """

    @pytest.mark.bdd
    def test_fetch_step_mentions_format_detection(self) -> None:
        """Scenario: Format detection documented
        Given the knowledge-intake SKILL.md
        When reading the FETCH step
        Then it should mention format detection.
        """
        content = SKILL_FILE.read_text()
        assert "Format Detection" in content or "format detection" in content

    @pytest.mark.bdd
    def test_fetch_step_mentions_document_conversion(self) -> None:
        """Scenario: Document conversion protocol referenced
        Given the knowledge-intake SKILL.md
        When reading the FETCH step
        Then it should reference leyline:document-conversion.
        """
        content = SKILL_FILE.read_text()
        assert "document-conversion" in content

    @pytest.mark.bdd
    def test_fetch_step_has_heuristics_table(self) -> None:
        """Scenario: Format heuristics table present
        Given the knowledge-intake SKILL.md
        When reading the FETCH step
        Then it should have a table mapping URL patterns to formats.
        """
        content = SKILL_FILE.read_text()
        assert "*.pdf" in content or ".pdf" in content
        assert "*.docx" in content or ".docx" in content
