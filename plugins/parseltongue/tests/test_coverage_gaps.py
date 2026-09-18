"""Targeted tests for coverage gaps.

These tests specifically exercise uncovered code paths
to improve overall test coverage.
"""

from __future__ import annotations

import pytest


class TestPatternMatchingCoverageGaps:
    """Tests for uncovered paths in pattern matching."""

    @pytest.mark.unit
    def test_match_patterns_with_nested_loops(self, pattern_matching_skill) -> None:
        """Given Python code with nested loops, detect pattern."""
        code = """
for i in items:
    for j in other_items:
        process(i, j)
"""
        result = pattern_matching_skill.match_patterns(code, "python")
        assert "patterns" in result
        assert "confidence" in result

    @pytest.mark.unit
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "label,code,expected_pattern",
        [
            (
                "singleton",
                """
class Config:
    _instance = None

    def __new__(cls):
        return cls._instance
""",
                "singleton",
            ),
            (
                "factory",
                """
def make_writer(kind):
    if kind == "json":
        return JsonWriter()
    return YamlWriter()
""",
                "factory",
            ),
            (
                "decorator",
                """
import functools


def trace(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        return fn(*args, **kwargs)

    return wrapper
""",
                "decorator",
            ),
        ],
    )
    async def test_find_patterns_detects_each_supported_pattern(
        self, pattern_matching_skill, label, code, expected_pattern
    ) -> None:
        """Given code containing a pattern, find_patterns names it.

        This replaces seven parametrize cases that all passed ``("",)``.
        Empty code returns at the guard before any detector runs, so every
        case exercised the same two lines, and the ``label`` strings
        ("ddd patterns", "gof patterns", "dsl patterns") named analysis
        paths that find_patterns does not contain at all. The three below
        are the detectors it actually calls.
        """
        result = await pattern_matching_skill.find_patterns(code)
        found = {p.get("pattern") for p in result["patterns"]}
        assert expected_pattern in found, (
            f"{label}: expected '{expected_pattern}' among {sorted(found)}"
        )

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_find_patterns_on_empty_code_returns_the_empty_shape(
        self, pattern_matching_skill
    ) -> None:
        """Empty code short-circuits before parsing, with both keys present."""
        result = await pattern_matching_skill.find_patterns("")
        assert result == {"patterns": [], "optimization_suggestions": []}

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_find_patterns_rejects_a_non_python_language(
        self, pattern_matching_skill
    ) -> None:
        """A non-Python language is declined by name, not silently empty."""
        result = await pattern_matching_skill.find_patterns("SELECT 1", "sql")
        assert result["patterns"] == []
        assert "sql" in result["note"]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_suggest_optimizations_empty(self, pattern_matching_skill) -> None:
        """Given empty code, return empty suggestions."""
        result = await pattern_matching_skill.find_patterns("")
        assert "optimization_suggestions" in result


class TestTestingGuideCoverageGaps:
    """Tests for uncovered paths in testing guide."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "label,args,expected_key",
        [
            ("analyze test structure", ("",), "recommendations"),
            ("identify anti patterns", ("",), "recommendations"),
            ("suggest improvements", ("",), "recommendations"),
        ],
    )
    async def test_analyze_testing_empty_returns_recommendations(
        self, testing_guide_skill, label, args, expected_key
    ) -> None:
        """Given empty code, analyze_testing returns dict with recommendations."""
        result = await testing_guide_skill.analyze_testing(*args)
        assert expected_key in result

    @pytest.mark.unit
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "label,args",
        [
            ("recommend tdd workflow", ("",)),
            ("evaluate test quality", ("",)),
            ("generate test fixtures", ("",)),
            ("analyze mock usage", ("",)),
            ("recommend test types", ("",)),
            ("validate async testing", ("",)),
            ("analyze test performance", ("",)),
            ("recommend testing tools", ("",)),
            ("evaluate maintainability", ("",)),
        ],
    )
    async def test_analyze_testing_empty_returns_dict(
        self, testing_guide_skill, label, args
    ) -> None:
        """Given empty code, analyze_testing returns a dict."""
        result = await testing_guide_skill.analyze_testing(*args)
        assert isinstance(result, dict)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_analyze_coverage_gaps_empty(self, testing_guide_skill) -> None:
        """Given empty code, return coverage gaps analysis."""
        result = await testing_guide_skill.analyze_testing("", "")
        assert isinstance(result, dict)
