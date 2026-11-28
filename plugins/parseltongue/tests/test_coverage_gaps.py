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
    @pytest.mark.parametrize(
        "method,code,path,expected",
        [
            (
                "analyze_test_structure",
                "class TestX:\n    def test_a(self):\n        assert True\n",
                ("test_structure", "test_classes"),
                ["TestX"],
            ),
            (
                "identify_anti_patterns",
                "def test_a():\n    pass\n",
                ("anti_patterns", "no_assertions"),
                True,
            ),
            (
                "suggest_improvements",
                "obj._helper()\nassert ok  # fixture\n",
                ("suggestions", 0, "issue"),
                "private_method testing detected",
            ),
            (
                "recommend_tdd_workflow",
                "- login works\n",
                ("tdd_workflow", "steps", 0, "test_name"),
                "test_login_works",
            ),
            (
                "evaluate_test_quality",
                "assert x\n",
                ("quality_assessment", "aspects", "coverage"),
                70,
            ),
            (
                "generate_test_fixtures",
                "class User:\n    def __init__(self, name):\n        pass\n",
                ("fixtures", "user_fixture", "minimal_fixture"),
                '@pytest.fixture\ndef user():\n    return User("name")',
            ),
            (
                "analyze_mock_usage",
                "m = Mock()\n",
                ("mock_analysis", "mock_objects"),
                ["m"],
            ),
            (
                "recommend_test_types",
                "user/models.py # user model\n",
                ("test_recommendations", "unit_tests", "user_models_test"),
                {"description": "user model"},
            ),
            (
                "validate_async_testing",
                "async def test_a():\n    pass\n",
                ("async_validation", "async_test_count"),
                1,
            ),
            (
                "analyze_test_performance",
                "time.sleep(1)\n",
                ("performance_analysis", "issues", "time_sleep"),
                True,
            ),
            (
                "recommend_testing_tools",
                {"async": True},
                ("tool_recommendations", "async_testing", "tools"),
                ["pytest-asyncio", "anyio"],
            ),
            (
                "evaluate_maintainability",
                "@pytest.fixture\ndef f():\n    pass\n",
                ("maintainability_analysis", "factors", "fixture_usage"),
                True,
            ),
        ],
    )
    def test_each_analysis_reaches_the_branch_it_names(
        self, testing_guide_skill, method, code, path, expected
    ) -> None:
        """Each snippet reaches one detector and checks a value only it sets.

        These cases passed ``("",)`` to ``analyze_testing``, which every
        method returns early on, so deleting a detector left them green
        (#1068). The label now names the method that is called.
        """
        result = getattr(testing_guide_skill, method)(code)
        for key in path:
            result = result[key]
        assert result == expected

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_analyze_coverage_gaps_empty(self, testing_guide_skill) -> None:
        """Given empty code, return coverage gaps analysis."""
        result = await testing_guide_skill.analyze_testing("", "")
        assert result == {
            "recommendations": [],
            "findings": {
                "source_analysis": {"public_functions": [], "classes": []},
                "test_analysis": {},
            },
        }
