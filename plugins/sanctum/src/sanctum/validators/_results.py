"""Validation result dataclasses shared across validator modules (AR-06)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


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
    """Detailed validation report for sanctum plugin."""

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
