"""Reporting mixin: bug report creation, dependency check, and analyze."""

from __future__ import annotations

from typing import Any


class ReportingMixin:
    """Creates bug reports, checks external dependencies, and runs full analysis."""

    def create_bug_report(
        self,
        bug_analysis: dict[str, Any],
    ) -> str:
        """Create a formatted bug summary report."""
        total = bug_analysis.get("total_bugs", 0)
        critical = bug_analysis.get("critical_bugs", 0)
        high = bug_analysis.get("high_priority_bugs", 0)
        medium = bug_analysis.get("medium_priority_bugs", 0)
        low = bug_analysis.get("low_priority_bugs", 0)
        categories = bug_analysis.get("bug_categories", {})

        report_lines = [
            "## Bug Analysis Summary",
            "",
            f"Total bugs: {total}",
            f"- Critical: {critical}",
            f"- High: {high}",
            f"- Medium: {medium}",
            f"- Low: {low}",
            "",
            "## Critical Issues",
            "",
            f"Critical bugs: {critical}",
            "",
            "## Bug Categories",
            "",
        ]

        for category, count in categories.items():
            report_lines.append(f"- {category}: {count}")

        report_lines.extend(
            [
                "",
                "## Recommendations",
                "",
                "1. Address critical security vulnerabilities first",
                "2. Review high-priority memory and null pointer issues",
                "3. Fix medium-priority logic errors",
                "4. Consider low-priority optimizations",
            ]
        )

        return "\n".join(report_lines)

    def check_external_dependencies(self, _context: Any) -> dict[str, Any]:
        """Stub: external-dependency checking is not implemented.

        Returns a fixed empty result. Subclasses or future
        implementations should override to perform real checks
        (and their own timeout handling). The base class never
        makes a network call, so the previous "handles network
        timeouts gracefully" comment was misleading and was
        removed (B-15).

        Args:
            _context: Skill context (unused; reserved for overrides).

        Returns:
            ``{"status": "ok", "checked": [], "issues": []}``.
        """
        return {
            "status": "ok",
            "checked": [],
            "issues": [],
        }
