"""Drift detection, recommendations, and report formatting (AR-01)."""

from __future__ import annotations

from typing import Any


class ReportingMixin:
    """Architectural drift, recommendations, and report formatting."""

    def detect_architectural_drift(self, context: Any) -> dict[str, Any]:
        """Detect architectural drift from intended design."""
        intended_patterns = context.get_intended_architecture()
        detected_patterns = context.get_detected_patterns()

        deviations = []
        drift_detected = False

        for pattern in detected_patterns:
            if pattern not in intended_patterns:
                deviations.append(
                    {
                        "pattern": pattern,
                        "type": "unintended",
                        "issue": f"Pattern '{pattern}' detected but not intended",
                    }
                )
                drift_detected = True

        for pattern in intended_patterns:
            if pattern not in detected_patterns:
                deviations.append(
                    {
                        "pattern": pattern,
                        "type": "missing",
                        "issue": f"Pattern '{pattern}' intended but not detected",
                    }
                )
                drift_detected = True

        return {
            "drift_detected": drift_detected,
            "deviations": deviations,
        }

    def generate_recommendations(
        self,
        findings: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Generate actionable architecture recommendations."""
        recommendations = []
        for finding in findings:
            recommendations.append(
                {
                    "priority": finding.get("severity", "medium"),
                    "action": f"Address {finding.get('type', 'issue')}",
                    "rationale": finding.get("issue", "Improve architecture quality"),
                }
            )
        return recommendations

    def create_architecture_report(self, analysis_results: dict[str, Any]) -> str:
        """Create a structured architecture quality report."""
        patterns = analysis_results.get("patterns_detected", [])
        score = analysis_results.get("architecture_score", 0.0)
        violations = analysis_results.get("violations", [])
        recommendations = analysis_results.get("recommendations", [])
        debt_score = analysis_results.get("technical_debt_score", 0.0)

        report_lines = [
            "# Architecture Quality Report",
            "",
            "## Architecture Assessment",
            "",
            f"**Overall Score:** {score}/10",
            f"**Technical Debt Score:** {debt_score}/10",
            "",
            "## Patterns Identified",
            "",
        ]

        if patterns:
            for pattern in patterns:
                report_lines.append(f"- {pattern}")
        else:
            report_lines.append("- No clear patterns detected")

        report_lines.extend(
            [
                "",
                "## Issues Found",
                "",
            ]
        )

        if violations:
            for violation in violations:
                severity = violation.get("severity", "unknown")
                message = violation.get("message", "No description")
                report_lines.append(f"- [{severity.upper()}] {message}")
        else:
            report_lines.append("- No issues found")

        report_lines.extend(
            [
                "",
                "## Recommendations",
                "",
            ]
        )

        if recommendations:
            for rec in recommendations:
                report_lines.append(f"- {rec}")
        else:
            report_lines.append("- Continue following current architecture patterns")

        report_lines.extend(
            [
                "",
                "## Summary",
                "",
                "This report provides an overview of the architecture quality. "
                "Address high-priority issues first and maintain architectural "
                "consistency across the codebase.",
                "",
            ]
        )

        return "\n".join(report_lines)


__all__ = ["ReportingMixin"]
