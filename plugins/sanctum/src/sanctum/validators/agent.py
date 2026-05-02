"""Agent markdown file validator (AR-06)."""

from __future__ import annotations

import re
from pathlib import Path

from ._results import AgentValidationResult


class AgentValidator:
    """Validator for agent markdown files."""

    @staticmethod
    def validate_content(content: str) -> AgentValidationResult:
        """Validate agent markdown content."""
        errors: list[str] = []
        warnings: list[str] = []
        agent_name = None

        # Check for main heading
        heading_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if not heading_match:
            errors.append("Missing main heading (# Agent Name)")
        else:
            agent_name = heading_match.group(1).strip()

        # Check for capabilities section
        has_capabilities = bool(
            re.search(r"^##\s+Capabilities", content, re.MULTILINE | re.IGNORECASE),
        )
        if not has_capabilities:
            warnings.append("Missing Capabilities section")

        # Check for tools section
        has_tools = bool(
            re.search(r"^##\s+Tools", content, re.MULTILINE | re.IGNORECASE),
        )
        if not has_tools:
            warnings.append("Missing Tools section")

        return AgentValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            agent_name=agent_name,
            has_capabilities=has_capabilities,
            has_tools=has_tools,
        )

    @staticmethod
    def validate_file(path: Path) -> AgentValidationResult:
        """Validate agent file from disk."""
        path = Path(path)

        if not path.exists():
            return AgentValidationResult(
                is_valid=False,
                errors=["File not found: " + str(path)],
                agent_name=path.stem,
            )

        content = path.read_text()
        result = AgentValidator.validate_content(content)

        # Use filename as agent name if not extracted from heading
        if result.agent_name is None:
            result.agent_name = path.stem

        return result

    @staticmethod
    def extract_tools(content: str) -> list[str]:
        """Extract tool names from agent content."""
        tools = []
        # Find Tools section and extract list items
        tools_match = re.search(
            r"^##\s+Tools\s*\n((?:[-*]\s+.+\n?)+)",
            content,
            re.MULTILINE | re.IGNORECASE,
        )
        if tools_match:
            tool_section = tools_match.group(1)
            for line in tool_section.split("\n"):
                match = re.match(r"^[-*]\s+(\w+)", line)
                if match:
                    tools.append(match.group(1))
        return tools

    @staticmethod
    def extract_capabilities(content: str) -> list[str]:
        """Extract capabilities from agent content."""
        capabilities = []
        # Find Capabilities section and extract list items
        caps_match = re.search(
            r"^##\s+Capabilities\s*\n((?:[-*]\s+.+\n?)+)",
            content,
            re.MULTILINE | re.IGNORECASE,
        )
        if caps_match:
            caps_section = caps_match.group(1)
            for line in caps_section.split("\n"):
                match = re.match(r"^[-*]\s+(.+)", line)
                if match:
                    capabilities.append(match.group(1).strip())
        return capabilities
