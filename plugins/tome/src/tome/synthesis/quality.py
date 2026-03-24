"""Research quality assessment: gap analysis and quality scoring."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from tome.models import Finding

_CURRENT_YEAR: int = datetime.now(tz=timezone.utc).year  # noqa: UP017

# A channel is "skewed" if it holds more than this fraction of findings
_SKEW_THRESHOLD = 0.75

# Findings older than this many years trigger a recency gap
_RECENCY_GAP_YEARS = 3


def identify_gaps(
    findings: list[Finding],
    planned_channels: list[str],
) -> dict[str, Any]:
    """Identify gaps in research coverage.

    Checks for:
    - Channels that returned no findings
    - Source diversity (one channel dominating)
    - Recency gaps (all findings are old)

    Args:
        findings: The merged findings list.
        planned_channels: Channels that were part of the research plan.

    Returns:
        Dict with keys: empty_channels, source_diversity_warning,
        recency_gap.
    """
    # Which planned channels got no results?
    channels_with_results: set[str] = {f.channel for f in findings}
    empty_channels = [ch for ch in planned_channels if ch not in channels_with_results]

    # Source diversity: does one channel dominate?
    source_diversity_warning = False
    if findings:
        channel_counts: dict[str, int] = {}
        for f in findings:
            channel_counts[f.channel] = channel_counts.get(f.channel, 0) + 1
        max_count = max(channel_counts.values())
        if max_count / len(findings) > _SKEW_THRESHOLD:
            source_diversity_warning = True

    # Recency gap: are all findings old?
    recency_gap = False
    years: list[int] = [
        int(f.metadata["year"]) for f in findings if f.metadata.get("year") is not None
    ]
    if years and all((_CURRENT_YEAR - y) > _RECENCY_GAP_YEARS for y in years):
        recency_gap = True

    return {
        "empty_channels": empty_channels,
        "source_diversity_warning": source_diversity_warning,
        "recency_gap": recency_gap,
    }


def compute_quality_score(
    findings: list[Finding],
    planned_channels: list[str],
) -> float:
    """Compute a composite research quality score.

    Blends three dimensions:
    - Channel coverage (what fraction of planned channels produced results)
    - Source diversity (how evenly distributed across channels)
    - Average relevance (mean relevance of all findings)

    Args:
        findings: The merged findings list.
        planned_channels: Channels that were part of the plan.

    Returns:
        Score in [0.0, 1.0].
    """
    if not findings:
        return 0.0

    # Channel coverage: fraction of planned channels with results
    channels_hit = {f.channel for f in findings}
    coverage = len(channels_hit & set(planned_channels)) / len(planned_channels)

    # Source diversity: 1 - Herfindahl index (concentration measure)
    channel_counts: dict[str, int] = {}
    for f in findings:
        channel_counts[f.channel] = channel_counts.get(f.channel, 0) + 1
    total = len(findings)
    herfindahl = sum((c / total) ** 2 for c in channel_counts.values())
    diversity = 1.0 - herfindahl

    # Average relevance
    avg_relevance = sum(f.relevance for f in findings) / len(findings)

    # Weighted blend
    score = 0.4 * coverage + 0.3 * diversity + 0.3 * avg_relevance

    return min(score, 1.0)
