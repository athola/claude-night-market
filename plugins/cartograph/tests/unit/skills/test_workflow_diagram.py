"""Tests for the workflow-diagram skill.

Feature: Workflow diagram generation skill

As a developer using cartograph
I want a workflow diagram skill with valid structure
So that Claude can generate process/pipeline visualizations.
"""

from __future__ import annotations

from pathlib import Path

import pytest

_SKILL_DIR = Path(__file__).parents[3] / "skills" / "workflow-diagram"
_SKILL_FILE = _SKILL_DIR / "SKILL.md"


class TestWorkflowDiagramSkillExists:
    """Feature: Workflow diagram skill file exists and is loadable.

    As a plugin consumer
    I want the workflow-diagram skill to exist
    So that /visualize workflow routes to a real skill.
    """

    @pytest.mark.unit
    def test_skill_directory_exists(self) -> None:
        """Scenario: Skill directory is present
        Given the cartograph plugin
        When checking for workflow-diagram skill
        Then the skill directory exists.
        """
        assert _SKILL_DIR.exists(), "skills/workflow-diagram/ missing"

    @pytest.mark.unit
    def test_skill_file_exists(self) -> None:
        """Scenario: SKILL.md is present
        Given the workflow-diagram skill directory
        When checking for SKILL.md
        Then the file exists.
        """
        assert _SKILL_FILE.exists(), "SKILL.md missing"


class TestWorkflowDiagramFrontmatter:
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
        Then name is 'workflow-diagram'.
        """
        fm = content.split("---")[1]
        assert "name: workflow-diagram" in fm

    @pytest.mark.unit
    def test_has_description_field(self, content: str) -> None:
        """Scenario: Frontmatter contains description
        Given the SKILL.md frontmatter
        When checking for description field
        Then a description is present.
        """
        fm = content.split("---")[1]
        assert "description:" in fm


class TestWorkflowDiagramContent:
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
        Given the workflow-diagram skill
        When checking for render step
        Then it references the Mermaid Chart MCP tool.
        """
        assert "validate_and_render_mermaid_diagram" in content

    @pytest.mark.unit
    def test_has_mermaid_example(self, content: str) -> None:
        """Scenario: Skill includes a Mermaid syntax example
        Given the workflow-diagram skill
        When checking for examples
        Then it contains a mermaid code block.
        """
        assert "```mermaid" in content

    @pytest.mark.unit
    def test_has_explorer_dispatch(self, content: str) -> None:
        """Scenario: Skill dispatches the codebase explorer
        Given the workflow-diagram skill
        When checking for agent dispatch
        Then it references the codebase-explorer agent.
        """
        assert "codebase-explorer" in content

    @pytest.mark.unit
    def test_uses_flowchart_diagram_type(self, content: str) -> None:
        """Scenario: Workflow uses flowchart type
        Given the workflow-diagram skill
        When checking the diagram type
        Then it uses flowchart for process visualization.
        """
        assert "flowchart" in content.lower()

    @pytest.mark.unit
    def test_has_decision_node_guidance(self, content: str) -> None:
        """Scenario: Skill guides decision point rendering
        Given the workflow-diagram skill
        When checking for decision node rules
        Then it mentions diamond shapes for decisions.
        """
        assert "Diamond" in content or "diamond" in content
