"""Tests for markdown-formatting skill structure and content.

Validates the shared formatting module contains all required
rules, exemptions, and examples for diff-friendly markdown.

Following BDD principles with Given/When/Then scenarios.
"""

from pathlib import Path

import pytest

MAX_PROSE_LINE_LENGTH = 80


class TestMarkdownFormattingSkillStructure:
    """Feature: Markdown-formatting skill provides shared conventions.

    As a plugin developer
    I want a canonical formatting reference
    So that all documentation follows consistent wrapping rules
    """

    @pytest.fixture
    def skill_path(self) -> Path:
        """Path to the markdown-formatting skill."""
        return Path(__file__).parents[3] / "skills" / "markdown-formatting" / "SKILL.md"

    @pytest.fixture
    def skill_content(self, skill_path: Path) -> str:
        """Load the markdown-formatting skill content."""
        return skill_path.read_text()

    @pytest.fixture
    def wrapping_module_path(self) -> Path:
        """Path to the wrapping-rules module."""
        return (
            Path(__file__).parents[3]
            / "skills"
            / "markdown-formatting"
            / "modules"
            / "wrapping-rules.md"
        )

    @pytest.fixture
    def wrapping_content(self, wrapping_module_path: Path) -> str:
        """Load the wrapping-rules module content."""
        return wrapping_module_path.read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_file_exists(self, skill_path: Path) -> None:
        """Scenario: Skill file exists at expected location.

        Given the leyline plugin
        When checking for markdown-formatting skill
        Then SKILL.md should exist
        """
        assert skill_path.exists()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_wrapping_module_exists(self, wrapping_module_path: Path) -> None:
        """Scenario: Wrapping rules module exists.

        Given the markdown-formatting skill
        When checking for the wrapping-rules module
        Then the module file should exist
        """
        assert wrapping_module_path.exists()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_has_frontmatter(self, skill_content: str) -> None:
        """Scenario: Skill has valid frontmatter.

        Given the markdown-formatting SKILL.md
        When reading the file
        Then it should have YAML frontmatter with name field
        """
        assert skill_content.startswith("---")
        assert "name: markdown-formatting" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_references_module(self, skill_content: str) -> None:
        """Scenario: Skill references wrapping-rules module.

        Given the markdown-formatting SKILL.md
        When reading the modules list
        Then it should reference wrapping-rules
        """
        assert "wrapping-rules" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_frontmatter_has_required_fields(self, skill_content: str) -> None:
        """Scenario: Frontmatter includes all required metadata.

        Given the markdown-formatting SKILL.md
        When reading the frontmatter
        Then it should have category, tags, complexity,
        and estimated_tokens fields
        """
        assert "category:" in skill_content
        assert "tags:" in skill_content
        assert "complexity:" in skill_content
        assert "estimated_tokens:" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_documents_structural_rules(self, skill_content: str) -> None:
        """Scenario: Skill documents core structural rules.

        Given the markdown-formatting SKILL.md
        When reading the content
        Then it should cover blank lines, ATX headings,
        list spacing, and reference-style links
        """
        content_lower = skill_content.lower()
        assert "blank line" in content_lower
        assert "atx" in content_lower
        assert "reference-style" in content_lower or "reference" in content_lower


class TestWrappingRulesContent:
    """Feature: Wrapping rules define the hybrid algorithm.

    As a documentation author
    I want clear wrapping priority rules
    So that I produce diff-friendly markdown consistently
    """

    @pytest.fixture
    def wrapping_content(self) -> str:
        """Load the wrapping-rules module content."""
        path = (
            Path(__file__).parents[3]
            / "skills"
            / "markdown-formatting"
            / "modules"
            / "wrapping-rules.md"
        )
        return path.read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_defines_sentence_boundary_rule(self, wrapping_content: str) -> None:
        """Scenario: Module defines sentence boundary wrapping.

        Given the wrapping-rules module
        When reviewing priority rules
        Then sentence boundaries should be highest priority
        """
        assert "sentence" in wrapping_content.lower()
        assert "boundary" in wrapping_content.lower()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_defines_clause_boundary_rule(self, wrapping_content: str) -> None:
        """Scenario: Module defines clause boundary wrapping.

        Given the wrapping-rules module
        When reviewing priority rules
        Then clause boundaries should be second priority
        """
        assert "clause" in wrapping_content.lower()
        assert "comma" in wrapping_content.lower()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_defines_conjunction_rule(self, wrapping_content: str) -> None:
        """Scenario: Module defines conjunction wrapping.

        Given the wrapping-rules module
        When reviewing priority rules
        Then conjunctions should be third priority
        """
        assert "conjunction" in wrapping_content.lower()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_defines_exempt_content_types(self, wrapping_content: str) -> None:
        """Scenario: Module lists all exempt content types.

        Given the wrapping-rules module
        When reviewing exemptions
        Then it should list tables, code blocks, headings,
        frontmatter, HTML, link defs, and images
        """
        content_lower = wrapping_content.lower()
        assert "table" in content_lower
        assert "code block" in content_lower
        assert "heading" in content_lower
        assert "frontmatter" in content_lower
        assert "html" in content_lower
        assert "link def" in content_lower
        assert "image" in content_lower

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_includes_before_after_examples(self, wrapping_content: str) -> None:
        """Scenario: Module includes before/after examples.

        Given the wrapping-rules module
        When reviewing documentation quality
        Then it should show before and after examples
        """
        assert "BEFORE" in wrapping_content
        assert "AFTER" in wrapping_content
        assert "```" in wrapping_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_covers_reference_style_links(self, wrapping_content: str) -> None:
        """Scenario: Module covers reference-style links.

        Given the wrapping-rules module
        When reviewing link handling
        Then it should explain reference-style link conversion
        """
        assert "reference" in wrapping_content.lower()
        assert "[" in wrapping_content and "]:" in wrapping_content


class TestProseCompliance:
    """Feature: Skill files follow their own formatting rules.

    As a documentation consumer
    I want the formatting spec to practice what it preaches
    So that the module is a credible reference
    """

    @pytest.fixture
    def skill_content(self) -> str:
        """Load SKILL.md content."""
        path = Path(__file__).parents[3] / "skills" / "markdown-formatting" / "SKILL.md"
        return path.read_text()

    @pytest.fixture
    def wrapping_content(self) -> str:
        """Load wrapping-rules module content."""
        path = (
            Path(__file__).parents[3]
            / "skills"
            / "markdown-formatting"
            / "modules"
            / "wrapping-rules.md"
        )
        return path.read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_prose_under_80_chars(self, skill_content: str) -> None:
        """Scenario: SKILL.md prose lines stay under 80 chars.

        Given the markdown-formatting SKILL.md
        When checking line lengths outside code blocks
        Then all prose lines should be 80 chars or fewer
        """
        in_code = False
        in_frontmatter = False
        violations = []
        for i, line in enumerate(skill_content.split("\n"), 1):
            if line.startswith("```"):
                in_code = not in_code
                continue
            # Track YAML frontmatter delimiter (first --- opens, second closes).
            if line == "---":
                in_frontmatter = not in_frontmatter if i > 1 else True
                continue
            if not in_code and not in_frontmatter and len(line) > MAX_PROSE_LINE_LENGTH:
                if line.startswith("|"):
                    continue
                violations.append((i, len(line), line[:60]))
        assert violations == [], f"Lines exceeding 80 chars: {violations}"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_wrapping_module_prose_under_80_chars(self, wrapping_content: str) -> None:
        """Scenario: wrapping-rules.md prose lines under 80 chars.

        Given the wrapping-rules module
        When checking line lengths outside code blocks
        Then all prose lines should be 80 chars or fewer
        """
        in_code = False
        violations = []
        for i, line in enumerate(wrapping_content.split("\n"), 1):
            if line.startswith("```"):
                in_code = not in_code
                continue
            if not in_code and len(line) > MAX_PROSE_LINE_LENGTH:
                if line.startswith("|") or line.startswith("---"):
                    continue
                violations.append((i, len(line), line[:60]))
        assert violations == [], f"Lines exceeding 80 chars: {violations}"
