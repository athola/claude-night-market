# ruff: noqa: D101,D102,D103,PLR2004,E501
"""Tests for agent validation helpers."""

from sanctum.validators import AgentValidationResult, AgentValidator


def test_valid_result_creation() -> None:
    result = AgentValidationResult(
        is_valid=False,
        errors=["Missing main heading"],
        warnings=[],
        agent_name="broken-agent",
        has_capabilities=False,
        has_tools=False,
    )

    assert not result.is_valid


def test_validates_valid_agent(sample_agent_content: str) -> None:
    result = AgentValidator.validate_content(sample_agent_content)
    assert not result.is_valid
    assert any("heading" in error.lower() for error in result.errors)


def test_warns_when_missing_capabilities() -> None:
    content = """
An agent without capabilities section.

## Tools
- Bash
"""
    result = AgentValidator.validate_content(content)
    assert any("capabilities" in warning.lower() for warning in result.warnings)
    assert not result.has_capabilities


def test_warns_when_missing_tools() -> None:
    content = """
An agent without tools section.

## Capabilities
- Do things
"""
    result = AgentValidator.validate_content(content)
    assert any("tools" in warning.lower() for warning in result.warnings)
    assert not result.has_tools


def test_validates_existing_agent_file(tmp_path, sample_agent_content: str) -> None:
    agent_file = tmp_path / "agent.md"
    agent_file.write_text(sample_agent_content)

    result = AgentValidator.validate_file(agent_file)

    assert result.agent_name == "Agent"
    assert result.has_capabilities is True
    assert result.has_tools is True


def test_validate_file_missing(tmp_path) -> None:
    missing_file = tmp_path / "missing.md"
    result = AgentValidator.validate_file(missing_file)

    assert result.is_valid is False
    assert "not found" in result.errors[0].lower()
    assert result.agent_name == "missing"


def test_extracts_tools_from_list() -> None:
    content = """# Agent

## Tools
- Bash
- Docker
"""
    tools = AgentValidator.extract_tools(content)
    assert tools == ["Bash", "Docker"]


def test_extracts_capabilities() -> None:
    content = """# Agent

## Capabilities
- Analyze logs
- Generate reports
"""
    caps = AgentValidator.extract_capabilities(content)
    assert caps == ["Analyze logs", "Generate reports"]


def test_validate_content_sets_agent_name_from_heading() -> None:
    content = """# Data Agent

## Capabilities
- Parse data

## Tools
- SQL
"""
    result = AgentValidator.validate_content(content)

    assert result.agent_name == "Data Agent"
    assert result.is_valid is True
