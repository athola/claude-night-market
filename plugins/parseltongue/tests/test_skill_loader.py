"""Unit tests for skill loader.

Tests the SkillLoader utility class.
"""

from __future__ import annotations

import pytest


class TestSkillLoader:
    """Tests for SkillLoader."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_load_skill_creates_new_entry(self, skill_loader) -> None:
        """Given a skill name not yet loaded, create and cache it."""
        # Given: A fresh skill loader with no loaded skills
        assert len(skill_loader.loaded_skills) == 0

        # When: Loading a skill for the first time
        result = await skill_loader.load_skill("test_skill")

        # Then: Skill is loaded and cached
        assert result == "Skill_test_skill"
        assert "test_skill" in skill_loader.loaded_skills

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_load_skill_returns_cached(self, skill_loader) -> None:
        """Given a skill already loaded, return cached instance."""
        # Given: A skill already in cache
        skill_loader.loaded_skills["cached_skill"] = "CachedInstance"

        # When: Loading the same skill
        result = await skill_loader.load_skill("cached_skill")

        # Then: Returns cached instance without creating new
        assert result == "CachedInstance"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_list_available_skills(self, skill_loader) -> None:
        """Given a skill loader, return list of available skills."""
        # When: Listing available skills
        skills = await skill_loader.list_available_skills()

        # Then: Returns expected skill names
        assert isinstance(skills, list)
        assert "language_detection" in skills
        assert "pattern_matching" in skills
        assert "testing_guide" in skills
        assert len(skills) >= 6

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_validate_skill_with_none(self, skill_loader) -> None:
        """Given None skill, return invalid result."""
        # When: Validating None
        result = await skill_loader.validate_skill(None)

        # Then: Returns invalid with issues
        assert result["valid"] is False
        assert "Skill is None" in result["issues"]
        assert len(result["recommendations"]) > 0

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_validate_skill_with_valid_skill(self, skill_loader) -> None:
        """Given a valid skill instance, return valid result."""
        # Given: A non-None skill instance
        skill = object()

        # When: Validating the skill
        result = await skill_loader.validate_skill(skill)

        # Then: Returns valid
        assert result["valid"] is True
        assert result["issues"] == []
