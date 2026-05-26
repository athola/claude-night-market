"""Reporting mixin: test quality report and recommendations."""

from __future__ import annotations

from typing import Any

from ._constants import (
    ACCEPTABLE_COVERAGE_RATIO,
    MAX_ANTI_PATTERNS,
    MAX_AVG_TEST_DURATION,
    MIN_COVERAGE_PERCENT,
    MIN_MOCK_RATIO,
)


class ReportingMixin:
    """Generate test quality reports and improvement recommendations."""

    def create_test_quality_report(self, analysis: dict[str, Any]) -> str:
        """Create a detailed test quality report."""
        report_lines = [
            "## Test Quality Assessment",
            "",
            f"**Overall Score**: {analysis['overall_score']}/10",
            f"**Test Count**: {analysis['test_count']}",
            "",
            "## Coverage Analysis",
            "",
            f"**Coverage**: {analysis['coverage_percentage']}%",
            f"**Total Tests**: {analysis['test_count']}",
            "",
            "## Test Pyramid",
            "",
            f"- Unit Tests: {analysis['unit_tests']}",
            f"- Integration Tests: {analysis['integration_tests']}",
            f"- End-to-End Tests: {analysis['end_to_end_tests']}",
            "",
            "## Quality Issues",
            "",
            f"- Slow Tests: {analysis['slow_tests']}",
            f"- Flaky Tests: {analysis['flaky_tests']}",
            f"- Anti-patterns: {analysis['anti_patterns']}",
            f"- TDD Compliance: {int(analysis['tdd_compliance'] * 100)}%",
            "",
            "## Recommendations",
            "",
        ]

        if "findings" in analysis:
            for finding in analysis["findings"]:
                report_lines.append(f"- {finding}")

        return "\n".join(report_lines)

    def generate_testing_recommendations(
        self, current_state: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Generate recommendations for improving test quality."""
        recommendations = []

        if current_state["coverage"] < MIN_COVERAGE_PERCENT:
            recommendations.append(
                {
                    "category": "coverage",
                    "priority": "high",
                    "action": "Increase test coverage to at least 80%",
                    "benefit": "Reduce bugs and improve code quality",
                    "implementation": "Add tests for uncovered functions/branches",
                }
            )

        if current_state["tdd_compliance"] < ACCEPTABLE_COVERAGE_RATIO:
            recommendations.append(
                {
                    "category": "tdd",
                    "priority": "medium",
                    "action": "Adopt test-first development practices",
                    "benefit": "Better test coverage and design",
                    "implementation": "Write failing tests before implementation",
                }
            )

        if current_state["integration_ratio"] < MIN_MOCK_RATIO:
            recommendations.append(
                {
                    "category": "integration",
                    "priority": "medium",
                    "action": "Add more integration tests",
                    "benefit": "Catch integration issues early",
                    "implementation": "Write tests that verify component interactions",
                }
            )

        if current_state["avg_test_duration"] > MAX_AVG_TEST_DURATION:
            recommendations.append(
                {
                    "category": "performance",
                    "priority": "high",
                    "action": "Optimize slow tests",
                    "benefit": "Faster feedback and CI/CD pipeline",
                    "implementation": "Mock external deps and use in-memory DBs",
                }
            )

        if current_state["flaky_tests"] > 0:
            recommendations.append(
                {
                    "category": "reliability",
                    "priority": "high",
                    "action": f"Fix {current_state['flaky_tests']} flaky tests",
                    "benefit": "Improve CI/CD reliability and developer confidence",
                    "implementation": "Remove non-deterministic behavior and deps",
                }
            )

        if current_state["anti_patterns"] > MAX_ANTI_PATTERNS:
            recommendations.append(
                {
                    "category": "quality",
                    "priority": "medium",
                    "action": "Refactor tests to remove anti-patterns",
                    "benefit": "More maintainable and reliable tests",
                    "implementation": "Follow testing best practices and patterns",
                }
            )

        return recommendations
