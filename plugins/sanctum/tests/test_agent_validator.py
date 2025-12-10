"""Tests for agent file validation."""

from sanctum.validators import AgentValidationResult, AgentValidator


class TestAgentValidationResult:
    """Tests for AgentValidationResult dataclass."""

    def test_valid_result_creation(self) -> None:
        result = AgentValidationResult(
            is_valid=False,
            errors=["Missing main heading"],
            warnings=[],
            agent_name="broken-agent",
            has_capabilities=False,
            has_tools=False,
        )
        assert not result.is_valid


class TestAgentContentValidation:
    """Tests for agent markdown content validation."""

    def test_validates_valid_agent(self, sample_agent_content) -> None:
        content = """
Some content without a heading.

## Capabilities
- Do things
"""
        result = AgentValidator.validate_content(content)
        assert not result.is_valid
        assert any("heading" in error.lower() for error in result.errors)

    def test_warns_when_missing_capabilities(self) -> None:

An agent without capabilities section.

## Tools
- Bash
"""
        result = AgentValidator.validate_content(content)
        assert any("capabilities" in warning.lower() for warning in result.warnings)
        assert not result.has_capabilities

    def test_warns_when_missing_tools(self) -> None:

An agent without tools section.

## Capabilities
- Do things
"""
        result = AgentValidator.validate_content(content)
        assert any("tools" in warning.lower() for warning in result.warnings)
        assert not result.has_tools


class TestAgentFileValidation:
    """Tests for validating agent files from disk."""

    def test_validates_existing_agent_file(self, temp_agent_file) -> None:
        result = AgentValidator.validate_file(tmp_path / "nonexistent.md")
        assert not result.is_valid
        assert any(
            "not found" in error.lower() or "exist" in error.lower()
            for error in result.errors
        )

    def test_extracts_agent_name_from_filename(self, temp_agent_file) -> None:
        agent_file = tmp_path / "unnamed-agent.md"
        agent_file.write_text(sample_agent_content)

        result = AgentValidator.validate_file(agent_file)
        assert result.agent_name is not None


class TestAgentToolExtraction:
    """Tests for extracting tools from agent files."""

    def test_extracts_tools_from_list(self, sample_agent_content) -> None:
        content = """# Agent

Just an agent description.
"""
        tools = AgentValidator.extract_tools(content)
        assert tools == []


class TestAgentCapabilityExtraction:
    """Tests for extracting capabilities from agent files."""

    def test_extracts_capabilities(self, sample_agent_content) -> None:
        content = """# Agent

Just an agent description.
"""
        caps = AgentValidator.extract_capabilities(content)
        assert caps == []
