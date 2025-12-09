"""Tests for agent file validation."""

from sanctum.validators import AgentValidationResult, AgentValidator


class TestAgentValidationResult:
    """Tests for AgentValidationResult dataclass."""

    def test_valid_result_creation(self) -> None:
        """Valid result has no errors."""
        result = AgentValidationResult(
            is_valid=True,
            errors=[],
            warnings=[],
            agent_name="git-workspace-agent",
            has_capabilities=True,
            has_tools=True,
        )
        assert result.is_valid
        assert result.agent_name == "git-workspace-agent"

    def test_invalid_result_with_errors(self) -> None:
        """Invalid result contains error messages."""
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
        """Validates a complete agent file."""
        result = AgentValidator.validate_content(sample_agent_content)
        assert result.is_valid
        assert result.has_capabilities
        assert result.has_tools

    def test_requires_main_heading(self) -> None:
        """Agent file must have a main heading."""
        content = """
Some content without a heading.

## Capabilities
- Do things
"""
        result = AgentValidator.validate_content(content)
        assert not result.is_valid
        assert any("heading" in error.lower() for error in result.errors)

    def test_warns_when_missing_capabilities(self) -> None:
        """Warns when agent lacks capabilities section."""
        content = """# Test Agent

An agent without capabilities section.

## Tools
- Bash
"""
        result = AgentValidator.validate_content(content)
        assert any("capabilities" in warning.lower() for warning in result.warnings)
        assert not result.has_capabilities

    def test_warns_when_missing_tools(self) -> None:
        """Warns when agent lacks tools section."""
        content = """# Test Agent

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
        """Validates an existing valid agent file."""
        result = AgentValidator.validate_file(temp_agent_file)
        assert result.is_valid

    def test_fails_on_nonexistent_file(self, tmp_path) -> None:
        """Fails when file doesn't exist."""
        result = AgentValidator.validate_file(tmp_path / "nonexistent.md")
        assert not result.is_valid
        assert any(
            "not found" in error.lower() or "exist" in error.lower()
            for error in result.errors
        )

    def test_extracts_agent_name_from_filename(self, temp_agent_file) -> None:
        """Extracts agent name from heading (preferred) or filename."""
        result = AgentValidator.validate_file(temp_agent_file)
        assert result.is_valid
        # Agent name comes from the heading in content, not filename
        assert result.agent_name == "Git Workspace Agent"

    def test_extracts_agent_name_from_heading(
        self, sample_agent_content, tmp_path
    ) -> None:
        """Can extract agent name from main heading."""
        agent_file = tmp_path / "unnamed-agent.md"
        agent_file.write_text(sample_agent_content)

        result = AgentValidator.validate_file(agent_file)
        assert result.agent_name is not None


class TestAgentToolExtraction:
    """Tests for extracting tools from agent files."""

    def test_extracts_tools_from_list(self, sample_agent_content) -> None:
        """Extracts tools from markdown list."""
        tools = AgentValidator.extract_tools(sample_agent_content)
        assert "Bash" in tools
        assert "TodoWrite" in tools

    def test_returns_empty_when_no_tools_section(self) -> None:
        """Returns empty list when no tools section."""
        content = """# Agent

Just an agent description.
"""
        tools = AgentValidator.extract_tools(content)
        assert tools == []


class TestAgentCapabilityExtraction:
    """Tests for extracting capabilities from agent files."""

    def test_extracts_capabilities(self, sample_agent_content) -> None:
        """Extracts capabilities from markdown list."""
        caps = AgentValidator.extract_capabilities(sample_agent_content)
        assert len(caps) >= 3
        assert any("repository" in cap.lower() for cap in caps)

    def test_returns_empty_when_no_capabilities_section(self) -> None:
        """Returns empty list when no capabilities section."""
        content = """# Agent

Just an agent description.
"""
        caps = AgentValidator.extract_capabilities(content)
        assert caps == []
