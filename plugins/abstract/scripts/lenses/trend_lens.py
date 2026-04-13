"""TrendLens: detects degradation and improvement trends.

Uses PerformanceTracker history to identify skills with
declining or improving scores over time. Also synthesizes
insights from ImprovementMemory when available.
"""

from __future__ import annotations

from typing import Any

from insight_types import AnalysisContext, Finding

LENS_META = {
    "name": "trend-lens",
    "insight_types": ["Trend"],
    "weight": "lightweight",
    "description": "Detects degradation/improvement over time windows",
}

# Trend thresholds
DEGRADATION_THRESHOLD = -0.1
IMPROVEMENT_THRESHOLD = 0.1
SEVERE_DEGRADATION = -0.3
LOW_SUCCESS_RATE = 0.3
MIN_ATTEMPTS_FOR_RATE = 5
MIN_FAILED_FOR_SUMMARY = 3


def analyze(context: AnalysisContext) -> list[Finding]:
    """Analyze performance history for trends."""
    findings: list[Finding] = []

    # Trends from PerformanceTracker
    if context.performance_history is not None:
        findings.extend(_analyze_performance_trends(context.performance_history))

    # Meta-insights from ImprovementMemory
    if context.improvement_memory is not None:
        findings.extend(_analyze_improvement_memory(context.improvement_memory))

    return findings


def _analyze_performance_trends(tracker: Any) -> list[Finding]:
    """Extract trend findings from PerformanceTracker."""
    findings: list[Finding] = []

    if not hasattr(tracker, "history") or not tracker.history:
        return findings

    seen: set[str] = set()
    for entry in tracker.history:
        ref = entry.get("skill_ref")
        if not ref or ref in seen:
            continue
        seen.add(ref)

        trend = tracker.get_improvement_trend(ref)
        if trend is None:
            continue

        if trend <= DEGRADATION_THRESHOLD:
            findings.append(
                Finding(
                    type="Trend",
                    severity=("high" if trend <= SEVERE_DEGRADATION else "medium"),
                    skill=ref,
                    summary=f"declining performance (trend: {trend:+.3f})",
                    evidence=f"Performance trend score: {trend:+.3f}",
                    recommendation=(
                        "Investigate recent changes. Check error logs "
                        "and consider reverting recent modifications."
                    ),
                    source="trend-lens",
                )
            )
        elif trend >= IMPROVEMENT_THRESHOLD:
            findings.append(
                Finding(
                    type="Trend",
                    severity="info",
                    skill=ref,
                    summary=f"improving performance (trend: {trend:+.3f})",
                    evidence=f"Performance trend score: {trend:+.3f}",
                    recommendation="Positive trend. Document effective changes.",
                    source="trend-lens",
                )
            )

    return findings


def _analyze_improvement_memory(memory: Any) -> list[Finding]:
    """Extract meta-insights from ImprovementMemory."""
    findings: list[Finding] = []

    try:
        effective = memory.get_effective_strategies()
        failed = memory.get_failed_strategies()
    except (AttributeError, TypeError):
        return findings

    if not effective and not failed:
        return findings

    total = len(effective) + len(failed)
    rate = len(effective) / total if total else 0

    if rate < LOW_SUCCESS_RATE and total >= MIN_ATTEMPTS_FOR_RATE:
        findings.append(
            Finding(
                type="Trend",
                severity="high",
                skill="",
                summary=(
                    f"low improvement success rate ({rate:.0%} of {total} attempts)"
                ),
                evidence=(
                    f"Only {len(effective)}/{total} improvement attempts "
                    f"succeeded. The improvement process itself may need "
                    f"revision."
                ),
                recommendation=(
                    "Review failed strategies for common patterns. "
                    "Consider smaller, more targeted changes."
                ),
                source="trend-lens",
            )
        )

    if failed and len(failed) >= MIN_FAILED_FOR_SUMMARY:
        # Summarize worst failures
        worst = failed[:3]
        lines = []
        for f in worst:
            summary = f.get("change_summary", "unknown")
            imp = f.get("improvement", 0)
            lines.append(f"- {summary} ({imp:+.3f})")
        findings.append(
            Finding(
                type="Improvement",
                severity="medium",
                skill="",
                summary=f"{len(failed)} improvement strategies caused regressions",
                evidence="\n".join(lines),
                recommendation="Avoid repeating these approaches.",
                source="trend-lens",
            )
        )

    return findings
