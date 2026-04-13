"""HealthLens: identifies unused and unhealthy components.

Finds skills with 0 executions in the analysis period,
skills with extremely high failure rates, and other
systemic health indicators.
"""

from __future__ import annotations

from typing import Any

from insight_types import AnalysisContext, Finding

LENS_META = {
    "name": "health-lens",
    "insight_types": ["Health Check"],
    "weight": "lightweight",
    "description": "Identifies unused skills and systemic health issues",
}

# Thresholds
CRITICAL_FAILURE_RATE = 20.0  # success rate below this
MIN_EXECUTIONS_FOR_FAILURE = 5
UNUSED_SEVERITY_THRESHOLD = 5  # >= this many unused = "medium"


def analyze(context: AnalysisContext) -> list[Finding]:
    """Check overall system health."""
    if not context.metrics:
        return []

    findings: list[Finding] = []
    findings.extend(_find_unused_skills(context.metrics))
    findings.extend(_find_critical_failures(context.metrics))
    return findings


def _find_unused_skills(metrics: dict[str, Any]) -> list[Finding]:
    """Find skills with zero executions."""
    unused = [
        skill_key
        for skill_key, summary in metrics.items()
        if summary.total_executions == 0
    ]

    if not unused:
        return []

    return [
        Finding(
            type="Health Check",
            severity=("info" if len(unused) < UNUSED_SEVERITY_THRESHOLD else "medium"),
            skill="",
            summary=f"{len(unused)} skills have 0 executions in 30 days",
            evidence=(
                "Unused skills:\n" + "\n".join(f"- `{s}`" for s in sorted(unused)[:20])
            ),
            recommendation=(
                "Consider whether these skills are still needed. "
                "Remove unused skills to reduce maintenance burden, "
                "or investigate why they are not being triggered."
            ),
            source="health-lens",
        )
    ]


def _find_critical_failures(metrics: dict[str, Any]) -> list[Finding]:
    """Find skills with critically low success rates."""
    findings: list[Finding] = []

    for skill_key, summary in metrics.items():
        if (
            summary.total_executions >= MIN_EXECUTIONS_FOR_FAILURE
            and summary.success_rate < CRITICAL_FAILURE_RATE
        ):
            findings.append(
                Finding(
                    type="Health Check",
                    severity="high",
                    skill=skill_key,
                    summary=(
                        f"critical failure rate: {summary.success_rate:.0f}% "
                        f"({summary.failure_count} failures)"
                    ),
                    evidence=(
                        f"- Success rate: {summary.success_rate:.1f}%\n"
                        f"- Total executions: {summary.total_executions}\n"
                        f"- Failures: {summary.failure_count}"
                    ),
                    recommendation=(
                        "This skill is failing more often than succeeding. "
                        "Investigate error logs and consider disabling until fixed."
                    ),
                    source="health-lens",
                )
            )

    return findings
