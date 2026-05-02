"""Sanctum validators package (AR-06).

Public API preserved verbatim from the prior 777-line
``validators.py`` module so existing imports keep working:

    from sanctum.validators import (
        AgentValidator, AgentValidationResult,
        SkillValidator, SkillValidationResult,
        CommandValidator, CommandValidationResult,
        PluginValidator, PluginValidationResult,
        SanctumValidator, SanctumValidationReport,
        parse_frontmatter,
    )
"""

from __future__ import annotations

from ._frontmatter import parse_frontmatter
from ._results import (
    AgentValidationResult,
    CommandValidationResult,
    PluginValidationResult,
    SanctumValidationReport,
    SkillValidationResult,
)
from .agent import AgentValidator
from .command import CommandValidator
from .plugin import PluginValidator
from .sanctum import SanctumValidator
from .skill import SkillValidator, _extract_skill_refs_from_content

__all__ = [
    "AgentValidationResult",
    "AgentValidator",
    "CommandValidationResult",
    "CommandValidator",
    "PluginValidationResult",
    "PluginValidator",
    "SanctumValidationReport",
    "SanctumValidator",
    "SkillValidationResult",
    "SkillValidator",
    "_extract_skill_refs_from_content",
    "parse_frontmatter",
]
