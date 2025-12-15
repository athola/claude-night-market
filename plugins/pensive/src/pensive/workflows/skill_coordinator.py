"""Skill coordinator for pensive workflows."""

from __future__ import annotations

from typing import Any


class SkillCoordinator:
    """Coordinates execution of multiple skills."""

    def __init__(self) -> None:
        """Initialize skill coordinator."""
        self._skills: list[Any] = []

    def register_skill(self, skill: Any) -> None:
        """Register a skill for coordination."""
        self._skills.append(skill)

    async def execute_all(self, context: Any) -> list[dict[str, Any]]:
        """Execute all registered skills."""
        return []

    def get_registered_skills(self) -> list[Any]:
        """Get list of registered skills."""
        return self._skills
