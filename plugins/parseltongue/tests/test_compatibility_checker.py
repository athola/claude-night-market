"""Unit tests for compatibility checker skill.

Tests the CompatibilityChecker functionality.
"""

from __future__ import annotations

import pytest


class TestCompatibilityChecker:
    """Tests for CompatibilityChecker."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_check_compatibility_with_future_annotations(
        self, compatibility_checker
    ) -> None:
        """Given code with future annotations, detect compatibility."""
        # Given: Code with __future__ import
        code = """
from __future__ import annotations

def func(x: int) -> str:
    return str(x)
"""

        # When: Checking compatibility
        result = await compatibility_checker.check_compatibility(
            code, ["3.8", "3.9", "3.10"]
        )

        # Then: Reports future annotations compatibility
        assert "compatible_versions" in result
        assert "issues" in result
        assert len(result["issues"]) >= 1
        assert result["issues"][0]["feature"] == "from __future__ import annotations"
        assert result["issues"][0]["status"] == "compatible"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_check_compatibility_with_empty_versions(
        self, compatibility_checker
    ) -> None:
        """Given empty target versions, use defaults."""
        # Given: Code and empty version list
        code = "x = 1"

        # When: Checking compatibility with empty list
        result = await compatibility_checker.check_compatibility(code, [])

        # Then: Uses default versions
        assert len(result["compatible_versions"]) >= 5
        assert "3.8" in result["compatible_versions"]
        assert "3.12" in result["compatible_versions"]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_check_compatibility_simple_code(self, compatibility_checker) -> None:
        """Given simple code, return compatibility report."""
        # Given: Simple code without special features
        code = "print('hello')"

        # When: Checking compatibility
        result = await compatibility_checker.check_compatibility(code, ["3.10"])

        # Then: Returns report structure
        assert result["compatible_versions"] == ["3.10"]
        assert "recommendations" in result
        assert len(result["recommendations"]) > 0
