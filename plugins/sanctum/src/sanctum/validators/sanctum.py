"""Whole-plugin orchestrator validator (AR-06)."""

from __future__ import annotations

from pathlib import Path

from ._results import (
    AgentValidationResult,
    CommandValidationResult,
    SanctumValidationReport,
    SkillValidationResult,
)
from .agent import AgentValidator
from .command import CommandValidator
from .plugin import PluginValidator
from .skill import SkillValidator


class SanctumValidator:
    """Detailed validator for the sanctum plugin."""

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
