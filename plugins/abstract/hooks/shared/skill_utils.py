"""Shared skill name parsing utilities for hooks."""

from __future__ import annotations

import re

_SAFE_COMPONENT = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]*$")


def parse_skill_name(tool_input: dict) -> tuple[str, str]:
    """Parse plugin:skill from tool input, with path-traversal sanitization.

    Args:
        tool_input: Skill tool input dictionary

    Returns:
        Tuple of (plugin_name, skill_name)

    """
    skill_ref = tool_input.get("skill", "unknown:unknown")

    if ":" in skill_ref:
        plugin, skill = skill_ref.split(":", 1)
        plugin = plugin.strip()
        skill = skill.strip()
    else:
        plugin, skill = "unknown", skill_ref.strip()

    # Sanitize to prevent path traversal
    if not _SAFE_COMPONENT.match(plugin):
        plugin = "unknown"
    if not _SAFE_COMPONENT.match(skill):
        skill = "unknown"

    return plugin, skill
