"""Validate sanctum plugin components.

Verify agents, skills, commands, and plugins following a consistent
validation pattern with dataclass results.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


def _parse_yaml_frontmatter(content: str) -> dict[str, Any] | None:
    """Parse YAML frontmatter from markdown content."""
    if not content.strip().startswith("---"):
        return None

    # Find the closing ---
    lines = content.split("\n")
    end_index = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_index = i
            break

    if end_index is None:
        return None

    frontmatter_text = "\n".join(lines[1:end_index])
    try:
        return yaml.safe_load(frontmatter_text) or {}
    except yaml.YAMLError:
        return None


@dataclass
class AgentValidationResult:
    """Result of agent validation."""

    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    agent_name: str | None = None
    has_capabilities: bool = False
    has_tools: bool = False


@dataclass
class SkillValidationResult:
    """Result of skill validation."""

    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    skill_name: str | None = None
    has_frontmatter: bool = False
    has_workflow: bool = False
    frontmatter: dict[str, Any] | None = None


@dataclass
class CommandValidationResult:
    """Result of command validation."""

    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    command_name: str | None = None
    has_description: bool = False
    has_usage: bool = False
    description: str | None = None


@dataclass
class PluginValidationResult:
    """Result of plugin validation."""

    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    plugin_name: str | None = None
    plugin_version: str | None = None
    has_skills: bool = False
    has_commands: bool = False
    has_agents: bool = False


@dataclass
class SanctumValidationReport:
    """detailed validation report for sanctum plugin."""

    is_valid: bool
    plugin_result: PluginValidationResult | None = None
    agent_results: list[AgentValidationResult] = field(default_factory=list)
    skill_results: list[SkillValidationResult] = field(default_factory=list)
    command_results: list[CommandValidationResult] = field(default_factory=list)
    total_errors: int = 0
    total_warnings: int = 0

    def all_errors(self) -> list[str]:
        """Get all errors from all validations."""
        errors: list[str] = []
        if self.plugin_result:
            errors.extend(self.plugin_result.errors)
        for agent_result in self.agent_results:
            errors.extend(agent_result.errors)
        for skill_result in self.skill_results:
            errors.extend(skill_result.errors)
        for command_result in self.command_results:
            errors.extend(command_result.errors)
        return errors


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


class SkillValidator:
    """Validator for skill markdown files."""

    @staticmethod
    def parse_frontmatter(content: str) -> SkillValidationResult:
        """Parse and validate skill frontmatter."""
        errors: list[str] = []
        warnings: list[str] = []
        skill_name = None
        frontmatter = None

        # Check for frontmatter
        has_frontmatter = content.strip().startswith("---")
        if not has_frontmatter:
            errors.append("Missing YAML frontmatter")
            return SkillValidationResult(
                is_valid=False,
                errors=errors,
                warnings=warnings,
                skill_name=None,
                has_frontmatter=False,
                frontmatter=None,
            )

        # Parse frontmatter
        frontmatter = _parse_yaml_frontmatter(content)
        if frontmatter is None:
            errors.append("Invalid YAML frontmatter")
            return SkillValidationResult(
                is_valid=False,
                errors=errors,
                warnings=warnings,
                skill_name=None,
                has_frontmatter=True,
                frontmatter=None,
            )

        # Validate required fields
        skill_name = frontmatter.get("name")
        if not skill_name:
            errors.append("Missing 'name' field in frontmatter")

        if not frontmatter.get("description"):
            errors.append("Missing 'description' field in frontmatter")

        # Validate recommended fields (warnings)
        if not frontmatter.get("category"):
            warnings.append("Missing 'category' field in frontmatter")

        if not frontmatter.get("tags"):
            warnings.append("Missing 'tags' field in frontmatter")

        if not frontmatter.get("tools"):
            warnings.append("Missing 'tools' field in frontmatter")

        # Check for workflow section
        has_workflow = bool(
            re.search(
                r"^##\s+(Workflow|When to Use|Steps)",
                content,
                re.MULTILINE | re.IGNORECASE,
            ),
        )

        return SkillValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            skill_name=skill_name,
            has_frontmatter=True,
            has_workflow=has_workflow,
            frontmatter=frontmatter,
        )

    @staticmethod
    def validate_content(content: str) -> SkillValidationResult:
        """Validate skill markdown content."""
        result = SkillValidator.parse_frontmatter(content)

        # Additional content validation
        warnings = list(result.warnings)

        # Check for main heading
        heading_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if not heading_match:
            warnings.append("Missing main heading in skill body")

        # Check for When to Use section
        if not re.search(r"^##\s+When to Use", content, re.MULTILINE | re.IGNORECASE):
            warnings.append("Missing 'When to Use' section")

        return SkillValidationResult(
            is_valid=result.is_valid,
            errors=result.errors,
            warnings=warnings,
            skill_name=result.skill_name,
            has_frontmatter=result.has_frontmatter,
            has_workflow=result.has_workflow,
            frontmatter=result.frontmatter,
        )

    @staticmethod
    def validate_file(path: Path) -> SkillValidationResult:
        """Validate skill file from disk."""
        path = Path(path)

        if not path.exists():
            return SkillValidationResult(
                is_valid=False,
                errors=["File not found: " + str(path)],
                skill_name=path.stem,
            )

        content = path.read_text()
        result = SkillValidator.validate_content(content)

        if result.skill_name is None:
            result.skill_name = path.stem

        return result

    @staticmethod
    def validate_directory(path: Path) -> SkillValidationResult:
        """Validate a skill directory containing SKILL.md."""
        path = Path(path)

        if not path.is_dir():
            return SkillValidationResult(
                is_valid=False,
                errors=[f"Not a directory: {path}"],
                skill_name=path.name,
            )

        skill_file = path / "SKILL.md"
        if not skill_file.exists():
            return SkillValidationResult(
                is_valid=False,
                errors=["Missing SKILL.md file in skill directory"],
                skill_name=path.name,
            )

        return SkillValidator.validate_file(skill_file)

    @staticmethod
    def validate_references(content: str) -> SkillValidationResult:
        """Validate skill references in content."""
        errors: list[str] = []
        warnings: list[str] = []

        # Find all Skill() references
        refs = re.findall(r"Skill\(([^)]+)\)", content)
        for ref in refs:
            # Valid format: plugin:skill-name or just skill-name
            if not re.match(r"^[\w-]+(:[\w-]+)?$", ref):
                warnings.append(f"Potentially invalid skill reference format: {ref}")

        # Parse frontmatter to get skill name
        frontmatter = _parse_yaml_frontmatter(content)
        skill_name = frontmatter.get("name") if frontmatter else None

        return SkillValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            skill_name=skill_name,
            has_frontmatter=frontmatter is not None,
            frontmatter=frontmatter,
        )

    @staticmethod
    def extract_skill_references(content: str) -> list[str]:
        """Extract skill references from content."""
        refs = []
        # Find Skill(plugin:skill-name) patterns
        matches = re.findall(r"Skill\(([^)]+)\)", content)
        for match in matches:
            # Extract skill name (after : if present)
            if ":" in match:
                refs.append(match.split(":")[1])
            else:
                refs.append(match)

        # Also check frontmatter dependencies
        frontmatter = _parse_yaml_frontmatter(content)
        if frontmatter and "dependencies" in frontmatter:
            deps = frontmatter["dependencies"]
            if isinstance(deps, list):
                refs.extend(deps)

        return refs

    @staticmethod
    def extract_dependencies(content: str) -> list[str]:
        """Extract skill dependencies from content."""
        deps = []
        deps_match = re.search(
            r"^##\s+Dependencies\s*\n((?:[-*]\s+.+\n?)+)",
            content,
            re.MULTILINE | re.IGNORECASE,
        )
        if deps_match:
            deps_section = deps_match.group(1)
            for line in deps_section.split("\n"):
                match = re.match(r"^[-*]\s+(.+)", line)
                if match:
                    deps.append(match.group(1).strip())
        return deps


class CommandValidator:
    """Validator for command markdown files."""

    @staticmethod
    def parse_frontmatter(content: str) -> CommandValidationResult:
        """Parse and validate command frontmatter."""
        errors: list[str] = []
        warnings: list[str] = []
        command_name = None
        description = None

        # Check for frontmatter
        has_frontmatter = content.strip().startswith("---")
        if not has_frontmatter:
            errors.append("Missing YAML frontmatter")
            return CommandValidationResult(
                is_valid=False,
                errors=errors,
                warnings=warnings,
                command_name=None,
                has_description=False,
                description=None,
            )

        # Parse frontmatter
        frontmatter = _parse_yaml_frontmatter(content)
        if frontmatter is None:
            errors.append("Invalid YAML frontmatter")
            return CommandValidationResult(
                is_valid=False,
                errors=errors,
                warnings=warnings,
                command_name=None,
                has_description=False,
                description=None,
            )

        # Extract description (required)
        description = frontmatter.get("description")
        if not description:
            errors.append("Missing 'description' field in frontmatter")

        # Extract command name from heading
        heading_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if heading_match:
            command_name = heading_match.group(1).strip()

        return CommandValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            command_name=command_name,
            has_description=description is not None,
            description=description,
        )

    @staticmethod
    def validate_content(content: str) -> CommandValidationResult:
        """Validate command markdown content."""
        result = CommandValidator.parse_frontmatter(content)
        warnings = list(result.warnings)

        # Check for main heading
        heading_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if not heading_match:
            warnings.append("Missing main heading in command body")

        # Check for usage section
        has_usage = bool(
            re.search(
                r"^##\s+(Usage|Arguments|Options)",
                content,
                re.MULTILINE | re.IGNORECASE,
            ),
        )
        if not has_usage:
            warnings.append("Missing usage section")

        return CommandValidationResult(
            is_valid=result.is_valid,
            errors=result.errors,
            warnings=warnings,
            command_name=result.command_name,
            has_description=result.has_description,
            has_usage=has_usage,
            description=result.description,
        )

    @staticmethod
    def validate_file(path: Path) -> CommandValidationResult:
        """Validate command file from disk."""
        path = Path(path)

        if not path.exists():
            return CommandValidationResult(
                is_valid=False,
                errors=["File not found: " + str(path)],
                command_name=path.stem,
            )

        content = path.read_text()
        result = CommandValidator.validate_content(content)

        if result.command_name is None:
            result.command_name = path.stem

        return result

    @staticmethod
    def extract_skill_references(content: str) -> list[str]:
        """Extract skill references from command content."""
        refs = []
        # Find Skill(plugin:skill-name) patterns
        matches = re.findall(r"Skill\(([^)]+)\)", content)
        for match in matches:
            # Extract skill name (after : if present)
            if ":" in match:
                refs.append(match.split(":")[1])
            else:
                refs.append(match)
        return refs

    @staticmethod
    def validate_skill_references(
        content: str,
        plugin_path: Path,
    ) -> CommandValidationResult:
        """Validate that referenced skills exist in the plugin."""
        errors: list[str] = []
        warnings: list[str] = []

        refs = CommandValidator.extract_skill_references(content)
        skills_dir = plugin_path / "skills"

        for ref in refs:
            skill_dir = skills_dir / ref
            if not skill_dir.exists():
                # It might be a different plugin reference
                if ":" not in ref:
                    warnings.append(f"Referenced skill '{ref}' not found locally")

        # Parse for command name
        frontmatter = _parse_yaml_frontmatter(content)
        description = frontmatter.get("description") if frontmatter else None

        heading_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        command_name = heading_match.group(1).strip() if heading_match else None

        return CommandValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            command_name=command_name,
            has_description=description is not None,
            description=description,
        )


class PluginValidator:
    """Validator for plugin.json and plugin structure."""

    @staticmethod
    def validate_structure(content: dict[str, Any]) -> PluginValidationResult:
        """Validate plugin.json structure."""
        errors: list[str] = []
        warnings: list[str] = []

        plugin_name = content.get("name")
        plugin_version = content.get("version")

        if not plugin_name:
            errors.append("Missing 'name' field in plugin.json")

        if not plugin_version:
            errors.append("Missing 'version' field in plugin.json")

        if not content.get("description"):
            errors.append("Missing 'description' field in plugin.json")

        # Validate empty arrays
        commands = content.get("commands")
        if commands is not None and len(commands) == 0:
            warnings.append("Empty commands array defined")

        skills = content.get("skills")
        if skills is not None and len(skills) == 0:
            warnings.append("Empty skills array defined")

        # Check path format for commands
        for cmd_path in content.get("commands", []):
            if not cmd_path.startswith("./"):
                warnings.append(f"Path should start with ./: {cmd_path}")

        has_skills = bool(content.get("skills") or content.get("skillsDir"))
        has_commands = bool(content.get("commands") or content.get("commandsDir"))
        has_agents = bool(content.get("agents") or content.get("agentsDir"))

        return PluginValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            plugin_name=plugin_name,
            plugin_version=plugin_version,
            has_skills=has_skills,
            has_commands=has_commands,
            has_agents=has_agents,
        )

    @staticmethod
    def validate_plugin_json(content: dict[str, Any]) -> PluginValidationResult:
        """Alias for validate_structure for backward compatibility."""
        return PluginValidator.validate_structure(content)

    @staticmethod
    def validate_plugin_dir(path: Path) -> PluginValidationResult:
        """Validate plugin directory with file existence checks."""
        path = Path(path)
        errors: list[str] = []
        warnings: list[str] = []

        # Check for plugin.json
        plugin_json_path = path / ".claude-plugin" / "plugin.json"
        if not plugin_json_path.exists():
            return PluginValidationResult(
                is_valid=False,
                errors=["Missing .claude-plugin/plugin.json"],
                plugin_name=path.name,
            )

        try:
            content = json.loads(plugin_json_path.read_text())
        except json.JSONDecodeError as e:
            return PluginValidationResult(
                is_valid=False,
                errors=[f"Invalid JSON in plugin.json: {e}"],
                plugin_name=path.name,
            )

        # First validate structure
        result = PluginValidator.validate_structure(content)
        errors.extend(result.errors)
        warnings.extend(result.warnings)

        # Check that referenced commands exist
        for cmd_path in content.get("commands", []):
            # Normalize path
            cmd_full_path = path / cmd_path.lstrip("./")
            if not cmd_full_path.exists():
                errors.append(f"Referenced command file not found: {cmd_path}")

        # Check that referenced skills exist and have SKILL.md
        for skill_path in content.get("skills", []):
            skill_dir = path / skill_path.lstrip("./")
            if not skill_dir.exists():
                errors.append(f"Referenced skill directory not found: {skill_path}")
            elif not (skill_dir / "SKILL.md").exists():
                errors.append(f"SKILL.md not found in skill directory: {skill_path}")

        # Check that referenced agents exist
        for agent_path in content.get("agents", []):
            agent_full_path = path / agent_path.lstrip("./")
            if not agent_full_path.exists():
                errors.append(f"Referenced agent file not found: {agent_path}")

        return PluginValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            plugin_name=result.plugin_name,
            plugin_version=result.plugin_version,
            has_skills=result.has_skills,
            has_commands=result.has_commands,
            has_agents=result.has_agents,
        )

    @staticmethod
    def validate_directory(path: Path) -> PluginValidationResult:
        """Alias for validate_plugin_dir."""
        return PluginValidator.validate_plugin_dir(path)


class SanctumValidator:
    """detailed validator for the sanctum plugin."""

    @staticmethod
    def validate_plugin(path: Path) -> SanctumValidationReport:
        """Validate entire plugin structure."""
        path = Path(path)

        # Validate plugin structure
        plugin_result = PluginValidator.validate_plugin_dir(path)

        agent_results: list[AgentValidationResult] = []
        skill_results: list[SkillValidationResult] = []
        command_results: list[CommandValidationResult] = []

        # Validate agents
        agents_dir = path / "agents"
        if agents_dir.exists():
            for agent_file in agents_dir.glob("*.md"):
                agent_results.append(AgentValidator.validate_file(agent_file))

        # Validate skills
        skills_dir = path / "skills"
        if skills_dir.exists():
            for skill_dir in skills_dir.iterdir():
                if skill_dir.is_dir():
                    skill_file = skill_dir / "SKILL.md"
                    if skill_file.exists():
                        skill_results.append(SkillValidator.validate_file(skill_file))

        # Validate commands
        commands_dir = path / "commands"
        if commands_dir.exists():
            for command_file in commands_dir.glob("*.md"):
                command_results.append(CommandValidator.validate_file(command_file))

        # Calculate totals
        total_errors = len(plugin_result.errors)
        total_warnings = len(plugin_result.warnings)

        for agent_result in agent_results:
            total_errors += len(agent_result.errors)
            total_warnings += len(agent_result.warnings)

        for skill_result in skill_results:
            total_errors += len(skill_result.errors)
            total_warnings += len(skill_result.warnings)

        for command_result in command_results:
            total_errors += len(command_result.errors)
            total_warnings += len(command_result.warnings)

        is_valid = total_errors == 0

        return SanctumValidationReport(
            is_valid=is_valid,
            plugin_result=plugin_result,
            agent_results=agent_results,
            skill_results=skill_results,
            command_results=command_results,
            total_errors=total_errors,
            total_warnings=total_warnings,
        )
