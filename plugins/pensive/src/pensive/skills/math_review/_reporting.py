"""Reporting mixin: math correctness reports and recommendations."""

from __future__ import annotations

from typing import Any


class ReportingMixin:
    """Generates mathematical correctness reports and improvement recommendations."""

    def create_math_correctness_report(self, math_analysis: dict[str, Any]) -> str:
        correctness_score = math_analysis.get("correctness_score", 0.0)
        precision_issues = math_analysis.get("precision_issues", 0)
        stability_problems = math_analysis.get("stability_problems", 0)
        algorithm_errors = math_analysis.get("algorithm_errors", 0)
        complexity_issues = math_analysis.get("complexity_issues", 0)
        statistical_fallacies = math_analysis.get("statistical_fallacies", 0)
        total_algorithms = math_analysis.get("total_algorithms", 0)
        high_risk_algorithms = math_analysis.get("high_risk_algorithms", 0)

        report_lines = [
            "## Mathematical Correctness Assessment",
            "",
            f"Overall correctness score: {correctness_score}/10",
            f"Total algorithms analyzed: {total_algorithms}",
            f"High-risk algorithms: {high_risk_algorithms}",
            "",
            "## Numerical Precision Analysis",
            "",
            f"Precision issues found: {precision_issues}",
            f"Stability problems: {stability_problems}",
            "",
            "## Algorithm Correctness",
            "",
            f"Algorithm errors: {algorithm_errors}",
            f"Complexity issues: {complexity_issues}",
            "",
            "## Statistical Validity",
            "",
            f"Statistical fallacies: {statistical_fallacies}",
            "",
            "## Recommendations",
            "",
            "- Review precision-critical operations",
            "- Add stability checks to matrix operations",
            "- Validate algorithm correctness",
            "- Consider computational complexity",
        ]

        return "\n".join(report_lines)

    def generate_mathematical_recommendations(
        self,
        analysis_results: dict[str, Any],
    ) -> list[dict[str, Any]]:
        recommendations = []

        if analysis_results.get("has_precision_issues"):
            recommendations.append(
                {
                    "category": "precision",
                    "technique": "Use appropriate numeric types",
                    "benefit": "Reduce precision errors",
                    "implementation": "Use decimal types for financial calculations",
                    "examples": ["decimal.Decimal", "BigDecimal"],
                }
            )

        if analysis_results.get("has_stability_problems"):
            recommendations.append(
                {
                    "category": "stability",
                    "technique": "Use numerically stable algorithms",
                    "benefit": "Improve accuracy for ill-conditioned problems",
                    "implementation": "Replace direct inversion with LU decomposition",
                    "examples": ["np.linalg.solve", "scipy.linalg.lu"],
                }
            )

        if analysis_results.get("uses_unstable_algorithms"):
            recommendations.append(
                {
                    "category": "algorithms",
                    "technique": "Use proven stable implementations",
                    "benefit": "Better convergence and accuracy",
                    "implementation": "Use library implementations when available",
                    "examples": ["scipy.optimize", "numpy.linalg"],
                }
            )

        if analysis_results.get("lacks_error_bounds"):
            recommendations.append(
                {
                    "category": "validation",
                    "technique": "Add error bounds and convergence checks",
                    "benefit": "Detect and handle numerical issues",
                    "implementation": "Check condition numbers and tolerances",
                    "examples": ["np.linalg.cond", "convergence criteria"],
                }
            )

        if analysis_results.get("missing_convergence_checks"):
            recommendations.append(
                {
                    "category": "validation",
                    "technique": "Add convergence monitoring",
                    "benefit": "validate iterative algorithms terminate correctly",
                    "implementation": "Track iteration count and residuals",
                    "examples": ["max_iterations", "tolerance checks"],
                }
            )

        return recommendations
