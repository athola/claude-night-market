"""DeltaLens: surfaces changes since the last-posted snapshot.

Compares current metrics to a stored snapshot and only
produces findings for meaningful changes: new skills,
threshold crossings, significant metric shifts. Produces
nothing if metrics are stable.
"""

from __future__ import annotations

from insight_types import AnalysisContext, Finding

LENS_META = {
    "name": "delta-lens",
    "insight_types": ["Trend"],
    "weight": "lightweight",
    "description": "Detects metric changes since last snapshot",
}

# Significance thresholds
SUCCESS_RATE_SHIFT = 10.0  # percent
DURATION_SHIFT_MS = 2000  # 2 seconds
NEW_SKILL_ALERT_THRESHOLD = 70.0  # success rate below this for new skills
SEVERE_DROP_THRESHOLD = -20  # rate delta below this is "high" severity


def analyze(context: AnalysisContext) -> list[Finding]:
    """Compare current metrics to previous snapshot.

    Returns findings only for meaningful changes.
    """
    if context.previous_snapshot is None:
        return []

    findings: list[Finding] = []
    prev = context.previous_snapshot

    for skill_key, summary in context.metrics.items():
        prev_data = prev.get(skill_key)

        if prev_data is None:
            # New skill appeared
            if summary.success_rate < NEW_SKILL_ALERT_THRESHOLD:
                findings.append(
                    Finding(
                        type="Trend",
                        severity="medium",
                        skill=skill_key,
                        summary=(
                            f"new skill with {summary.success_rate:.0f}% success rate"
                        ),
                        evidence=(
                            f"First seen in this analysis period with "
                            f"{summary.total_executions} executions and "
                            f"{summary.success_rate:.1f}% success rate."
                        ),
                        recommendation="Monitor this skill and investigate failures.",
                        source="delta-lens",
                    )
                )
            continue

        # Check success rate shift
        prev_rate = prev_data.get("success_rate", 100.0)
        curr_rate = summary.success_rate
        rate_delta = curr_rate - prev_rate

        if abs(rate_delta) >= SUCCESS_RATE_SHIFT:
            direction = "dropped" if rate_delta < 0 else "improved"
            severity = "high" if rate_delta < SEVERE_DROP_THRESHOLD else "medium"
            findings.append(
                Finding(
                    type="Trend",
                    severity=severity,
                    skill=skill_key,
                    summary=(
                        f"success rate {direction} "
                        f"from {prev_rate:.0f}% to {curr_rate:.0f}%"
                    ),
                    evidence=(
                        f"- Previous: {prev_rate:.1f}%\n"
                        f"- Current: {curr_rate:.1f}%\n"
                        f"- Delta: {rate_delta:+.1f}%"
                    ),
                    recommendation=(
                        "Investigate recent changes to this skill."
                        if rate_delta < 0
                        else "Positive trend. Document what changed."
                    ),
                    source="delta-lens",
                )
            )

        # Check duration shift
        prev_dur = prev_data.get("avg_duration_ms", 0)
        curr_dur = summary.avg_duration_ms
        dur_delta = curr_dur - prev_dur

        if dur_delta >= DURATION_SHIFT_MS:
            findings.append(
                Finding(
                    type="Trend",
                    severity="medium",
                    skill=skill_key,
                    summary=f"avg duration increased by {dur_delta / 1000:.1f}s",
                    evidence=(
                        f"- Previous avg: {prev_dur / 1000:.1f}s\n"
                        f"- Current avg: {curr_dur / 1000:.1f}s"
                    ),
                    recommendation="Profile execution to find bottleneck.",
                    source="delta-lens",
                )
            )

    return findings
