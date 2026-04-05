"""Tests for the class-diagram skill.

Feature: Class diagram generation skill

As a developer using cartograph
I want a class diagram skill with valid structure
So that Claude can generate OOP/type hierarchy visualizations.
"""

from __future__ import annotations

from pathlib import Path

import pytest

_SKILL_DIR = Path(__file__).parents[3] / "skills" / "class-diagram"
_SKILL_FILE = _SKILL_DIR / "SKILL.md"


class TestClassDiagramSkillExists:
    """Feature: Class diagram skill file exists and is loadable.

    As a plugin consumer
    I want the class-diagram skill to exist
    So that /visualize class routes to a real skill.
    """

    @pytest.mark.unit
    def test_skill_directory_exists(self) -> None:
        """Scenario: Skill directory is present
        Given the cartograph plugin
        When checking for class-diagram skill
        Then the skill directory exists.
        """
        assert _SKILL_DIR.exists(), "skills/class-diagram/ missing"

    @pytest.mark.unit
    def test_skill_file_exists(self) -> None:
        """Scenario: SKILL.md is present
        Given the class-diagram skill directory
        When checking for SKILL.md
        Then the file exists.
        """
        assert _SKILL_FILE.exists(), "SKILL.md missing"


class TestClassDiagramFrontmatter:
    """Feature: Valid YAML frontmatter for skill discovery.

    As a skill loader
    I want valid frontmatter with name and description
    So that the skill is discoverable and described.
    """

    @pytest.fixture
    def content(self) -> str:
        return _SKILL_FILE.read_text()

    @pytest.mark.unit
    def test_has_frontmatter_delimiters(self, content: str) -> None:
        """Scenario: Frontmatter is delimited
        Given the SKILL.md file
        When reading its content
        Then it starts with --- and has a closing ---.
        """
        assert content.startswith("---")
        parts = content.split("---")
        assert len(parts) >= 3, "Missing closing --- delimiter"

    @pytest.mark.unit
    def test_has_name_field(self, content: str) -> None:
        """Scenario: Frontmatter contains name
        Given the SKILL.md frontmatter
        When checking for name field
        Then name is 'class-diagram'.
        """
        fm = content.split("---")[1]
        assert "name: class-diagram" in fm

    @pytest.mark.unit
    def test_has_description_field(self, content: str) -> None:
        """Scenario: Frontmatter contains description
        Given the SKILL.md frontmatter
        When checking for description field
        Then a description is present.
        """
        fm = content.split("---")[1]
        assert "description:" in fm


class TestClassDiagramContent:
    """Feature: Skill content follows cartograph conventions.

    As a diagram skill consumer
    I want consistent structure across diagram skills
    So that all skills follow the same explore-generate-render
    pattern.
    """

    @pytest.fixture
    def content(self) -> str:
        return _SKILL_FILE.read_text()

    @pytest.mark.unit
    def test_has_mcp_rendering_section(self, content: str) -> None:
        """Scenario: Skill includes MCP rendering instructions
        Given the class-diagram skill
        When checking for render step
        Then it references the Mermaid Chart MCP tool.
        """
        assert "validate_and_render_mermaid_diagram" in content

    @pytest.mark.unit
    def test_has_mermaid_example(self, content: str) -> None:
        """Scenario: Skill includes a Mermaid syntax example
        Given the class-diagram skill
        When checking for examples
        Then it contains a mermaid code block.
        """
        assert "```mermaid" in content

    @pytest.mark.unit
    def test_has_explorer_dispatch(self, content: str) -> None:
        """Scenario: Skill dispatches the codebase explorer
        Given the class-diagram skill
        When checking for agent dispatch
        Then it references the codebase-explorer agent.
        """
        assert "codebase-explorer" in content

    @pytest.mark.unit
    def test_uses_class_diagram_type(self, content: str) -> None:
        """Scenario: Uses classDiagram type
        Given the class-diagram skill
        When checking the diagram type
        Then it uses classDiagram for class visualization.
        """
        assert "classDiagram" in content

    @pytest.mark.unit
    def test_has_relationship_notation_guide(self, content: str) -> None:
        """Scenario: Skill documents relationship notation
        Given the class-diagram skill
        When checking for relationship guidance
        Then it includes inheritance and composition notation.
        """
        assert "<|--" in content, "Missing inheritance notation"
        assert "*--" in content, "Missing composition notation"

    @pytest.mark.unit
    def test_has_stereotype_guidance(self, content: str) -> None:
        """Scenario: Skill documents class stereotypes
        Given the class-diagram skill
        When checking for stereotype guidance
        Then it mentions protocol and dataclass stereotypes.
        """
        assert "<<protocol>>" in content
        assert "<<dataclass>>" in content
