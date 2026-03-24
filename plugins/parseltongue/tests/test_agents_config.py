"""Tests for SkillLoader.validate_metadata."""

from __future__ import annotations

import pytest

from parseltongue.analysis.skill_loader import SkillLoader


class TestSkillLoaderValidateMetadata:
    """Tests for SkillLoader.validate_metadata (sync method)."""

    @pytest.mark.unit
    def test_valid_metadata(self) -> None:
        """Given complete metadata, return valid result."""
        loader = SkillLoader()
        result = loader.validate_metadata(
            {"name": "my-skill", "description": "does things", "tools": []}
        )
        assert result["valid"] is True
        assert result["errors"] == []

    @pytest.mark.unit
    def test_missing_name(self) -> None:
        """Given metadata without name, report error."""
        loader = SkillLoader()
        result = loader.validate_metadata({"description": "ok"})
        assert result["valid"] is False
        assert any("name" in e for e in result["errors"])

    @pytest.mark.unit
    def test_none_description(self) -> None:
        """Given description=None, report error."""
        loader = SkillLoader()
        result = loader.validate_metadata({"name": "x", "description": None})
        assert result["valid"] is False
        assert any("description" in e for e in result["errors"])

    @pytest.mark.unit
    def test_tools_not_list(self) -> None:
        """Given tools as non-list, report error."""
        loader = SkillLoader()
        result = loader.validate_metadata(
            {"name": "x", "description": "ok", "tools": "not-a-list"}
        )
        assert result["valid"] is False
        assert any("tools" in e for e in result["errors"])
