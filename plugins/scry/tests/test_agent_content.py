"""Tests for agent content validation in scry plugin.

This module tests agent file content validation:
- Agent schema compliance
- Tool availability references

Issue #53: Add skill/agent/command content validation tests

Following TDD/BDD principles with Given/When/Then docstrings.
"""

import re
from pathlib import Path

import pytest

# ============================================================================
# Agent Schema Validation
# ============================================================================


class TestAgentSchemaValidation:
    """Feature: Validate agent file schema.

    As a plugin developer
    I want agent files to follow a consistent schema
    So that agents are reliable and well-documented
    """

    REQUIRED_SECTIONS = ["Capabilities", "Tools"]
    VALID_TOOLS = [
        "Bash",
        "Read",
        "Write",
        "Edit",
        "Glob",
        "Grep",
        "WebFetch",
        "WebSearch",
        "TodoWrite",
        "TodoRead",
        "Task",
        "Skill",
    ]

    def extract_sections(self, content: str) -> list[str]:
        """Extract section headings from markdown content."""
        pattern = r"^##\s+(.+)$"
        matches = re.findall(pattern, content, re.MULTILINE)
        return matches

    def extract_tool_list(self, content: str) -> list[str]:
        """Extract tools from Tools section."""
        tools_match = re.search(
            r"##\s+Tools\s*\n((?:[-*]\s+\w+\n?)+)", content, re.IGNORECASE
        )
        if not tools_match:
            return []

        tools_text = tools_match.group(1)
        return re.findall(r"[-*]\s+(\w+)", tools_text)

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_agent_has_capabilities_section(self, tmp_path: Path) -> None:
        """Scenario: Agent file has Capabilities section.

        Given an agent file
        When checking for required sections
        Then it should have a Capabilities section.
        """
        agent_content = """# Test Agent

## Capabilities
- Analyze code
- Generate reports

## Tools
- Bash
- Read
"""
        agent_file = tmp_path / "test-agent.md"
        agent_file.write_text(agent_content)

        sections = self.extract_sections(agent_content)
        assert "Capabilities" in sections

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_agent_has_tools_section(self) -> None:
        """Scenario: Agent file has Tools section.

        Given an agent file
        When checking for required sections
        Then it should have a Tools section.
        """
        agent_content = """# Test Agent

## Capabilities
- Analyze code

## Tools
- Bash
"""
        sections = self.extract_sections(agent_content)
        assert "Tools" in sections

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_agent_tools_are_valid(self) -> None:
        """Scenario: Agent tools reference valid Claude Code tools.

        Given an agent with tools listed
        When validating tool names
        Then all tools should be recognized.
        """
        agent_content = """# Test Agent

## Capabilities
- Do things

## Tools
- Bash
- Read
- Write
- InvalidTool
"""
        tools = self.extract_tool_list(agent_content)
        invalid = [t for t in tools if t not in self.VALID_TOOLS]

        assert "InvalidTool" in invalid
        assert "Bash" not in invalid

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_agent_without_tools_section_fails(self) -> None:
        """Scenario: Agent without Tools section fails validation.

        Given an agent file without Tools section
        When validating
        Then it should fail.
        """
        agent_content = """# Test Agent

## Capabilities
- Analyze code
"""
        sections = self.extract_sections(agent_content)
        assert "Tools" not in sections


class TestAgentCapabilities:
    """Feature: Validate agent capabilities.

    As a plugin developer
    I want agent capabilities to be well-defined
    So that users understand what the agent can do
    """

    def extract_capabilities(self, content: str) -> list[str]:
        """Extract capabilities from Capabilities section."""
        caps_match = re.search(
            r"##\s+Capabilities\s*\n((?:[-*]\s+.+\n?)+)", content, re.IGNORECASE
        )
        if not caps_match:
            return []

        caps_text = caps_match.group(1)
        return re.findall(r"[-*]\s+(.+)", caps_text)

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_agent_has_at_least_one_capability(self) -> None:
        """Scenario: Agent has at least one capability.

        Given an agent file
        When checking capabilities
        Then it should have at least one.
        """
        agent_content = """# Test Agent

## Capabilities
- Analyze code patterns
- Generate documentation

## Tools
- Read
"""
        capabilities = self.extract_capabilities(agent_content)
        assert len(capabilities) >= 1

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_empty_capabilities_fails(self) -> None:
        """Scenario: Agent with empty capabilities fails.

        Given an agent file with empty Capabilities section
        When validating
        Then it should have no capabilities extracted.
        """
        agent_content = """# Test Agent

## Capabilities

## Tools
- Read
"""
        capabilities = self.extract_capabilities(agent_content)
        assert len(capabilities) == 0


# ============================================================================
# Agent File Discovery
# ============================================================================


class TestAgentDiscovery:
    """Feature: Discover and validate all agents in plugin.

    As a plugin maintainer
    I want to validate all agent files
    So that the plugin is consistent
    """

    @pytest.fixture
    def agents_dir(self, plugin_root: Path) -> Path:
        """Return the agents directory."""
        return plugin_root / "agents"

    @pytest.mark.bdd
    @pytest.mark.integration
    def test_agents_directory_structure(self, agents_dir: Path) -> None:
        """Scenario: Agents directory follows expected structure.

        Given the agents/ directory
        When checking structure
        Then it should contain markdown files.
        """
        if not agents_dir.exists():
            pytest.skip("No agents directory in scry plugin")

        agent_files = list(agents_dir.glob("*.md"))
        # May have 0 agents, which is valid
        for agent_file in agent_files:
            assert agent_file.suffix == ".md"

    @pytest.mark.bdd
    @pytest.mark.integration
    def test_all_agents_have_required_sections(self, agents_dir: Path) -> None:
        """Scenario: All agents have required sections.

        Given all agent files
        When validating each
        Then each should have Capabilities section and tools defined.
        """
        if not agents_dir.exists():
            pytest.skip("No agents directory in scry plugin")

        agent_files = list(agents_dir.glob("*.md"))
        for agent_file in agent_files:
            content = agent_file.read_text()
            sections = re.findall(r"^##\s+(.+)$", content, re.MULTILINE)

            assert "Capabilities" in sections, (
                f"Missing Capabilities in {agent_file.name}"
            )
            # Tools can be in frontmatter or as a section
            has_tools = "Tools" in sections or re.search(
                r"^tools:\s*\[", content, re.MULTILINE
            )
            assert has_tools, f"Missing tools definition in {agent_file.name}"
