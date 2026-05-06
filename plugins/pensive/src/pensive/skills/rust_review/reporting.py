"""Security reporting and recommendation generation for Rust review."""

from __future__ import annotations

from typing import Any

__all__ = ["ReportingMixin"]

# Rust analysis thresholds
MIN_TEST_COVERAGE = 0.8  # Minimum acceptable test coverage
MAX_DEPENDENCIES = 20  # Maximum recommended dependencies

# A-11: severity buckets as frozensets so each call avoids list allocation.
_CRITICAL_TYPES = frozenset({"buffer_overflow", "data_race"})
_HIGH_TYPES = frozenset({"deprecated_dependency"})
_MEDIUM_TYPES = frozenset({"unwrap_usage", "missing_docs"})


class ReportingMixin:
    """Mixin providing report generation and recommendation logic."""

    def create_rust_security_report(
        self,
        analysis: dict[str, Any],
    ) -> str:
        """Generate a Rust security-focused report.

        Args:
            analysis: Complete Rust analysis results

        Returns:
            Markdown formatted security report
        """
        unsafe_code = analysis.get("unsafe_code", {})
        unsafe_block_list = unsafe_code.get("unsafe_blocks", [])
        unsafe_blocks = len(unsafe_block_list)
        unsafe_documented = sum(
            1 for b in unsafe_block_list if not b.get("lacks_documentation", True)
        )

        ownership = analysis.get("ownership", {})
        ownership_violations = len(ownership.get("violations", []))

        data_race_info = analysis.get("data_races", 0)
        data_races = (
            data_race_info
            if isinstance(data_race_info, int)
            else len(data_race_info.get("data_races", []))
        )

        memory_safety = analysis.get("memory_safety", {})
        memory_safety_issues = (
            len(memory_safety.get("unsafe_operations", []))
            + len(memory_safety.get("buffer_overflows", []))
            + len(memory_safety.get("use_after_free", []))
        )

        deps = analysis.get("dependencies", {})
        dependency_vulnerabilities = len(deps.get("security_concerns", []))

        panic_info = analysis.get("panic_propagation", {})
        panic_points = len(panic_info.get("panic_points", []))

        security_score = analysis.get("security_score", 0.0)

        report = f"""## Rust Security Assessment

Security Score: {security_score}/10

## Unsafe Code Analysis

Total unsafe blocks: {unsafe_blocks}
Documented unsafe blocks: {unsafe_documented}
Undocumented unsafe blocks: {unsafe_blocks - unsafe_documented}

## Memory Safety

Memory safety issues detected: {memory_safety_issues}
Ownership violations: {ownership_violations}

## Concurrency Safety

Potential data races: {data_races}

## Dependency Security

Dependency vulnerabilities: {dependency_vulnerabilities}

## Error Handling

Panic points detected: {panic_points}
"""

        findings = analysis.get("findings", [])
        if findings:
            report += "\n## Detailed Findings\n\n"
            for finding in findings:
                report += f"- {finding}\n"

        return report

    def categorize_rust_severity(
        self,
        issues: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Assign severity levels to Rust issues.

        Args:
            issues: List of Rust issues to categorize

        Returns:
            List of issues with severity added
        """
        categorized = []
        for issue in issues:
            issue_copy = issue.copy()
            issue_type = issue.get("type", "")

            if issue_type in _CRITICAL_TYPES:
                issue_copy["severity"] = "critical"
            elif issue_type in _HIGH_TYPES:
                issue_copy["severity"] = "high"
            elif issue_type in _MEDIUM_TYPES:
                issue_copy["severity"] = "medium"
            else:
                issue_copy["severity"] = "low"

            categorized.append(issue_copy)

        return categorized

    def generate_rust_recommendations(
        self,
        analysis: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Generate Rust best practice recommendations.

        Args:
            analysis: Codebase analysis results

        Returns:
            List of recommendation dictionaries
        """
        recommendations = []

        if analysis.get("uses_unsafe"):
            recommendations.append(
                {
                    "category": "unsafe",
                    "practice": "Document all unsafe code blocks",
                    "benefit": "Improves code review and maintenance",
                    "implementation": ("Add safety documentation to all unsafe blocks"),
                }
            )

        if analysis.get("async_code"):
            recommendations.append(
                {
                    "category": "async",
                    "practice": ("Use tokio::time instead of std::thread::sleep"),
                    "benefit": "Prevents blocking the async runtime",
                    "implementation": ("Replace blocking ops with async equivalents"),
                }
            )

        if analysis.get("test_coverage", 1.0) < MIN_TEST_COVERAGE:
            recommendations.append(
                {
                    "category": "testing",
                    "practice": "Increase test coverage",
                    "benefit": "Catches bugs earlier in development",
                    "implementation": ("Add unit tests for uncovered code paths"),
                }
            )

        if analysis.get("dependency_count", 0) > MAX_DEPENDENCIES:
            recommendations.append(
                {
                    "category": "dependencies",
                    "practice": "Audit and minimize dependencies",
                    "benefit": "Reduces attack surface and build times",
                    "implementation": ("Review dependencies and remove unused ones"),
                }
            )

        if analysis.get("macro_heavy"):
            recommendations.append(
                {
                    "category": "macros",
                    "practice": "Document complex macros",
                    "benefit": "Makes code easier to understand",
                    "implementation": ("Add doc comments to all custom macros"),
                }
            )

        return recommendations
