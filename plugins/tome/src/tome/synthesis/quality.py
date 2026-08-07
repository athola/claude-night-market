"""Research quality assessment: gap analysis, outcomes, quality scoring.

A note on what the two families here measure, because conflating them
is the defect this module was extended to fix.

``compute_quality_score`` measures the *search*: how many planned
channels answered, how evenly findings spread across them, how relevant
they were judged. Every term describes the retrieval process.

``channel_outcomes`` measures what the *sources* did: whether a channel
was asked and answered, asked and returned nothing, or never
successfully asked at all. Only that second family can say anything
about the field being researched, and only for channels that ran
cleanly.

A low quality score and a thin field look identical from the outside.
They are not the same claim, and a report that prints one next to the
other invites a reader to treat a bad search as a finding about the
world.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from tome.models import Finding

if TYPE_CHECKING:
    from tome.models import ResearchSession

_CURRENT_YEAR: int = datetime.now(tz=timezone.utc).year

# A channel is "skewed" if it holds more than this fraction of findings.
# unvalidated: no source, never calibrated against labeled topics.
_SKEW_THRESHOLD = 0.75

# Findings older than this many years trigger a recency gap.
# unvalidated: no source, never calibrated against labeled topics.
_RECENCY_GAP_YEARS = 3

# Error kind meaning "the source refused us for volume, not for cause".
# It is separated from other failures because it carries a different
# instruction: re-run, rather than investigate.
RATE_LIMIT = "rate_limit"


def channel_outcomes(session: ResearchSession) -> dict[str, str]:
    """Derive what each planned channel actually did.

    Returns one of six statuses per planned channel:

    ``unknown``
        No query record. The session predates query logging, or the
        agent returned no envelope. Nothing may be concluded.
    ``error``
        Every query failed, none on a rate limit.
    ``rate_limited``
        A rate limit was hit and nothing came back. Distinguished from
        ``error`` because it tells the reader to re-run rather than to
        investigate.
    ``degraded``
        Some query failed but results still arrived, typically via a
        fallback source. The findings are real; the coverage is not
        what was asked for, so the channel is not a clean probe.
    ``empty``
        Every query succeeded and none returned a result. This is the
        only status under which absence says something about the field
        rather than about the search.
    ``ok``
        Every query succeeded and results arrived.

    The status is computed, never stored. A session carries the logs;
    anything derived from them is derived on demand, so a stored status
    can never contradict the evidence sitting next to it.
    """
    outcomes: dict[str, str] = {}
    for channel in session.channels:
        logs = [q for q in session.query_log if q.channel == channel]
        if not logs:
            outcomes[channel] = "unknown"
            continue
        results = sum(q.result_count for q in logs)
        failed = [q for q in logs if not q.succeeded]
        if not failed:
            outcomes[channel] = "ok" if results else "empty"
        elif results:
            outcomes[channel] = "degraded"
        elif any(q.error == RATE_LIMIT for q in failed):
            outcomes[channel] = "rate_limited"
        else:
            outcomes[channel] = "error"
    return outcomes


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
    if planned_channels:
        coverage = len(channels_hit & set(planned_channels)) / len(planned_channels)
    else:
        coverage = 0.0

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
