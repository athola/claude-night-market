"""Test quality evaluation mixin for TestingGuideSkill."""

from __future__ import annotations

import re
from typing import Any


class TestQualityMixin:
    """Evaluation of test quality and maintainability metrics."""

    def evaluate_test_quality(self, code: str) -> dict[str, Any]:
        """Evaluate the overall quality of test code.

        Args:
            code: Test code to evaluate

        Returns:
            Dictionary containing quality assessment
        """
        quality: dict[str, Any] = {
            "score": 50,
            "aspects": {
                "readability": 50,
                "maintainability": 50,
                "coverage": 50,
                "organization": 50,
            },
            "strengths": [],
            "weaknesses": [],
            "improvements": [],
        }

        if not code:
            return {"quality_assessment": quality}

        score = 50

        # Check for fixtures
        if "@pytest.fixture" in code or "@fixture" in code:
            score += 10
            quality["aspects"]["maintainability"] = 70
            quality["strengths"].append("Uses pytest fixtures")

        # Check for test classes
        if re.search(r"class\s+Test\w+", code):
            score += 10
            quality["aspects"]["organization"] = 70
            quality["strengths"].append("Organized in test classes")

        # Check for docstrings
        if re.search(r'""".*"""', code, re.DOTALL):
            score += 5
            quality["aspects"]["readability"] = 70
            quality["strengths"].append("Has docstrings")

        # Check for assertions
        assert_count = len(re.findall(r"\bassert\b", code))
        if assert_count > 0:
            score += 10
            quality["aspects"]["coverage"] = 70
        else:
            quality["weaknesses"].append("No assertions found")
            quality["improvements"].append("Add assertions")

        # Check for parametrize
        if "parametrize" in code:
            score += 5
            quality["strengths"].append("Uses parametrize")

        quality["score"] = min(100, score)

        return {"quality_assessment": quality}

    def evaluate_maintainability(self, code: str) -> dict[str, Any]:
        """Evaluate the maintainability of test code.

        Args:
            code: Test code to evaluate

        Returns:
            Dictionary containing maintainability analysis
        """
        maintainability: dict[str, Any] = {
            "score": 50,
            "factors": {
                "fixture_usage": False,
                "data_driven_testing": False,
                "test_organization": False,
                "readability": False,
            },
            "recommendations": [],
        }

        if not code:
            return {"maintainability_analysis": maintainability}

        score = 50

        # Check fixture usage
        if "@pytest.fixture" in code or "@fixture" in code:
            maintainability["factors"]["fixture_usage"] = True
            score += 15

        # Check for data-driven testing
        if "parametrize" in code:
            maintainability["factors"]["data_driven_testing"] = True
            score += 10

        # Check test organization
        if re.search(r"class\s+Test\w+", code):
            maintainability["factors"]["test_organization"] = True
            score += 10

        # Check readability
        if re.search(r'""".*"""', code, re.DOTALL):
            maintainability["factors"]["readability"] = True
            score += 10

        maintainability["score"] = min(100, score)

        if not maintainability["factors"]["fixture_usage"]:
            maintainability["recommendations"].append(
                "Add fixtures for reusable test setup"
            )
        if not maintainability["factors"]["readability"]:
            maintainability["recommendations"].append("Add docstrings to test methods")

        return {"maintainability_analysis": maintainability}

    def validate_async_testing(self, code: str) -> dict[str, Any]:
        """Validate async testing patterns.

        Args:
            code: Async test code to validate

        Returns:
            Dictionary containing async test validation
        """
        validation: dict[str, Any] = {
            "uses_pytest_asyncio": False,
            "async_test_count": 0,
            "uses_asyncmock": False,
        }

        if not code:
            return {"async_validation": validation}

        validation["uses_pytest_asyncio"] = "pytest.mark.asyncio" in code

        # Count async test functions
        validation["async_test_count"] = len(
            re.findall(r"async\s+def\s+test_\w+", code)
        )

        validation["uses_asyncmock"] = "AsyncMock" in code

        return {"async_validation": validation}
