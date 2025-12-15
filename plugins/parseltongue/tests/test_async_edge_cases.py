"""Edge case tests for async analysis skill.

Tests empty input, syntax errors, and specific code paths
to improve coverage.
"""

from __future__ import annotations

import pytest


class TestAsyncAnalysisEdgeCases:
    """Edge case tests for AsyncAnalysisSkill."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_analyze_async_functions_empty_code(
        self, async_analysis_skill
    ) -> None:
        """Given empty code, return empty async functions list."""
        result = await async_analysis_skill.analyze_async_functions("")
        assert result["async_functions"] == []

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_analyze_async_functions_syntax_error(
        self, async_analysis_skill
    ) -> None:
        """Given invalid Python syntax, return error."""
        result = await async_analysis_skill.analyze_async_functions("def broken(")
        assert "error" in result
        assert result["async_functions"] == []

    @pytest.mark.unit
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "method,expected_key",
        [
            ("analyze_context_managers", "context_managers"),
            ("analyze_concurrency_patterns", "concurrency_patterns"),
            ("detect_blocking_calls", "blocking_patterns"),
            ("detect_missing_await", "missing_awaits"),
            ("analyze_error_handling", "error_handling"),
            ("analyze_timeouts", "timeout_analysis"),
            ("analyze_resource_management", "resource_management"),
            ("analyze_performance", "performance_analysis"),
            ("analyze_testing_patterns", "testing_analysis"),
            ("suggest_improvements", "improvements"),
        ],
    )
    async def test_empty_code_returns_expected_keys(
        self, async_analysis_skill, method, expected_key
    ) -> None:
        """Given empty code, all analysis methods should return expected keys in results."""
        result = await getattr(async_analysis_skill, method)("")
        assert expected_key in result


class TestRaceConditionClassPatterns:
    """Tests for race condition detection in class patterns."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_detect_class_shared_state_without_lock(
        self, async_analysis_skill
    ) -> None:
        """Given class with shared state but no lock, flag as unsafe."""
        code = """
import asyncio

class UnsafeCounter:
    count = 0  # Shared class attribute

    async def increment(self):
        self.count += 1
"""
        result = await async_analysis_skill.detect_race_conditions(code)
        race_conditions = result["race_conditions"]
        assert "unsynchronized_shared_state" in race_conditions

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_detect_class_with_lock_as_safe(self, async_analysis_skill) -> None:
        """Given class with shared state and Lock, identify as safe."""
        code = """
import asyncio

class SafeCounter:
    count = 0  # Shared class attribute

    async def increment(self):
        lock = asyncio.Lock()
        async with lock:
            self.count += 1
"""
        result = await async_analysis_skill.detect_race_conditions(code)
        race_conditions = result["race_conditions"]
        assert "safe_patterns" in race_conditions

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_detect_race_conditions_empty(self, async_analysis_skill) -> None:
        """Given empty code, return empty race conditions."""
        result = await async_analysis_skill.detect_race_conditions("")
        assert "race_conditions" in result
