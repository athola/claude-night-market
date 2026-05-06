"""Plugin.json structure validator (AR-06)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ._results import PluginValidationResult


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
        """Validate plugin directory (alias)."""
        return PluginValidator.validate_plugin_dir(path)
