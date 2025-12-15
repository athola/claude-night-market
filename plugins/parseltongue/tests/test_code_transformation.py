"""Unit tests for code transformation skill.

Tests the CodeTransformationSkill functionality.
"""

from __future__ import annotations

import pytest


class TestCodeTransformation:
    """Tests for CodeTransformationSkill."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_transform_code_with_loop_optimization(
        self, code_transformation_skill
    ) -> None:
        """Given code with loops and optimize_performance pattern, detect optimization."""
        # Given: Python code with a for loop
        code = """
for item in items:
    process(item)
"""

        # When: Transform is called with optimize_performance pattern
        result = await code_transformation_skill.transform_code(
            code, "optimize_performance"
        )

        # Then: Returns transformation result
        assert "transformed_code" in result
        assert "transformations" in result
        assert "improvements" in result

        # Then: Detects loop optimization opportunity
        assert len(result["transformations"]) >= 1
        assert result["transformations"][0]["type"] == "optimization"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_transform_code_without_loops(
        self, code_transformation_skill
    ) -> None:
        """Given code without loops, return empty transformations."""
        # Given: Simple code without loops
        code = "x = 1 + 2"

        # When: Transform is called
        result = await code_transformation_skill.transform_code(
            code, "optimize_performance"
        )

        # Then: No transformations detected
        assert result["transformations"] == []
        assert result["transformed_code"] == code

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_transform_code_different_pattern(
        self, code_transformation_skill
    ) -> None:
        """Given a different pattern than optimize_performance, skip optimization."""
        # Given: Code with a loop but different pattern
        code = "for i in range(10): pass"

        # When: Transform is called with different pattern
        result = await code_transformation_skill.transform_code(code, "refactor")

        # Then: No transformations for this pattern
        assert result["transformations"] == []
