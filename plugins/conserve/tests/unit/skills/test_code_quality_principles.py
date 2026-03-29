"""Tests for code-quality-principles skill.

This module validates the code quality principles skill structure
and content following TDD/BDD patterns.
"""

import re
from pathlib import Path

import pytest


class TestCodeQualityPrinciplesStructure:
    """Feature: Code quality principles skill structure.

    As a plugin developer
    I want the skill to have proper structure
    So that it can be discovered and loaded correctly
    """

    @pytest.fixture
    def skill_dir(self) -> Path:
        """Return the skill directory path."""
        return Path(__file__).parents[3] / "skills" / "code-quality-principles"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_file_exists(self, skill_dir: Path) -> None:
        """Scenario: SKILL.md file exists.

        Given the code-quality-principles skill directory
        When checking for SKILL.md
        Then the file should exist.
        """
        skill_file = skill_dir / "SKILL.md"
        assert skill_file.exists(), f"SKILL.md not found at {skill_file}"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_has_frontmatter(self, skill_dir: Path) -> None:
        """Scenario: SKILL.md has valid frontmatter.

        Given the SKILL.md file
        When parsing the file
        Then it should have YAML frontmatter.
        """
        skill_file = skill_dir / "SKILL.md"
        content = skill_file.read_text()

        # Check for frontmatter delimiters
        assert content.startswith("---"), "SKILL.md should start with frontmatter"
        assert content.count("---") >= 2, "SKILL.md should have closing frontmatter"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_frontmatter_has_required_fields(self, skill_dir: Path) -> None:
        """Scenario: Frontmatter has required fields.

        Given the SKILL.md frontmatter
        When checking required fields
        Then name, description, and category should be present.
        """
        skill_file = skill_dir / "SKILL.md"
        content = skill_file.read_text()

        # Extract frontmatter
        parts = content.split("---", 2)
        assert len(parts) >= 3, "Could not extract frontmatter"
        frontmatter = parts[1]

        assert "name:" in frontmatter, "Frontmatter missing 'name' field"
        assert "description:" in frontmatter, "Frontmatter missing 'description' field"
        assert "category:" in frontmatter, "Frontmatter missing 'category' field"


class TestCodeQualityPrinciplesContent:
    """Feature: Code quality principles content.

    As a developer
    I want the skill to cover KISS, YAGNI, and SOLID principles
    So that I have guidance on code quality
    """

    @pytest.fixture
    def skill_content(self) -> str:
        """Return the skill file content."""
        skill_dir = Path(__file__).parents[3] / "skills" / "code-quality-principles"
        skill_file = skill_dir / "SKILL.md"
        return skill_file.read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_covers_kiss_principle(self, skill_content: str) -> None:
        """Scenario: Skill covers KISS principle.

        Given the skill content
        When checking for KISS coverage
        Then KISS principle should be documented.
        """
        assert re.search(r"\bKISS\b", skill_content), "KISS principle not covered"
        assert re.search(r"Keep\s+It\s+Simple", skill_content, re.IGNORECASE), (
            "KISS expansion not present"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_covers_yagni_principle(self, skill_content: str) -> None:
        """Scenario: Skill covers YAGNI principle.

        Given the skill content
        When checking for YAGNI coverage
        Then YAGNI principle should be documented.
        """
        assert re.search(r"\bYAGNI\b", skill_content), "YAGNI principle not covered"
        assert re.search(
            r"You\s+Aren'?t\s+Gonna\s+Need", skill_content, re.IGNORECASE
        ), "YAGNI expansion not present"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_covers_solid_principles(self, skill_content: str) -> None:
        """Scenario: Skill covers SOLID principles.

        Given the skill content
        When checking for SOLID coverage
        Then all 5 SOLID principles should be mentioned.
        """
        assert re.search(r"\bSOLID\b", skill_content), "SOLID not mentioned"

        solid_principles = [
            "Single Responsibility",
            "Open.Closed",  # Open/Closed or Open-Closed
            "Liskov Substitution",
            "Interface Segregation",
            "Dependency Inversion",
        ]

        for principle in solid_principles:
            assert re.search(principle, skill_content, re.IGNORECASE), (
                f"SOLID principle '{principle}' not covered"
            )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_has_code_examples(self, skill_content: str) -> None:
        """Scenario: Skill includes code examples.

        Given the skill content
        When checking for examples
        Then there should be code blocks.
        """
        # Check for code blocks
        code_block_pattern = r"```(python|rust|typescript)"
        matches = re.findall(code_block_pattern, skill_content, re.IGNORECASE)
        assert len(matches) >= 2, "Skill should have at least 2 code examples"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_has_anti_patterns(self, skill_content: str) -> None:
        """Scenario: Skill documents anti-patterns.

        Given the skill content
        When checking for anti-patterns
        Then bad examples should be marked.
        """
        # Check for anti-pattern indicators
        anti_pattern_indicators = [
            r"# Bad",
            r"# Wrong",
            r"# Anti-pattern",
            r"# Avoid",
            r"# Don't",
        ]

        has_anti_patterns = any(
            re.search(pattern, skill_content, re.IGNORECASE)
            for pattern in anti_pattern_indicators
        )
        assert has_anti_patterns, (
            "Skill should document anti-patterns with 'Bad' or 'Avoid' markers"
        )


class TestCodeQualityPrinciplesTriggers:
    """Feature: Skill trigger patterns.

    As a skill loader
    I want proper trigger patterns
    So that the skill activates at appropriate times
    """

    @pytest.fixture
    def skill_content(self) -> str:
        """Return the skill file content."""
        skill_dir = Path(__file__).parents[3] / "skills" / "code-quality-principles"
        skill_file = skill_dir / "SKILL.md"
        return skill_file.read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_has_trigger_keywords(self, skill_content: str) -> None:
        """Scenario: Skill has trigger keywords in description.

        Given the skill frontmatter
        When checking description
        Then it should contain trigger keywords.
        """
        # Extract frontmatter
        parts = skill_content.split("---", 2)
        frontmatter = parts[1]

        # Check for trigger keywords in description
        trigger_keywords = ["KISS", "YAGNI", "SOLID", "code quality", "clean code"]
        has_trigger = any(
            keyword.lower() in frontmatter.lower() for keyword in trigger_keywords
        )
        assert has_trigger, "Frontmatter description should contain trigger keywords"
