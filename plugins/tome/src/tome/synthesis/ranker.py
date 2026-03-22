"""Score, rank, and group research findings."""

from __future__ import annotations

from datetime import datetime, timezone

from tome.models import Finding

# Computed once at import time; stable for the lifetime of the process.
_CURRENT_YEAR: int = datetime.now(tz=timezone.utc).year  # noqa: UP017


def compute_relevance_score(finding: Finding) -> float:
    """Compute composite relevance from base relevance + source authority.

    Authority bonuses:
    - github: stars > 1000 -> +0.1, stars > 5000 -> +0.2
    - hn: score > 100 -> +0.1, score > 500 -> +0.2
    - arxiv/academic: citations > 50 -> +0.1, citations > 200 -> +0.2
    - reddit: score > 50 -> +0.05, score > 200 -> +0.1

    Recency bonus: metadata "year" within 2 calendar years -> +0.05

    Result is capped at 1.0.
    """
    score = finding.relevance
    meta = finding.metadata
    source = finding.source.lower()

    if source == "github":
        stars = int(meta.get("stars", 0) or 0)
        if stars > 5000:
            score += 0.2
        elif stars > 1000:
            score += 0.1
    elif source == "hn":
        hn_score = int(meta.get("score", 0) or 0)
        if hn_score > 500:
            score += 0.2
        elif hn_score > 100:
            score += 0.1
    elif source in ("arxiv", "academic", "semantic_scholar"):
        citations = int(meta.get("citations", 0) or 0)
        if citations > 200:
            score += 0.2
        elif citations > 50:
            score += 0.1
    elif source == "reddit":
        reddit_score = int(meta.get("score", 0) or 0)
        if reddit_score > 200:
            score += 0.1
        elif reddit_score > 50:
            score += 0.05

    year = meta.get("year")
    if year is not None and (_CURRENT_YEAR - int(year or 0)) <= 2:
        score += 0.05

    return min(score, 1.0)


def rank_findings(findings: list[Finding]) -> list[Finding]:
    """Return findings sorted by composite relevance score, descending."""
    return sorted(findings, key=compute_relevance_score, reverse=True)


def group_by_theme(findings: list[Finding]) -> dict[str, list[Finding]]:
    """Group findings by channel (code/discourse/academic/triz)."""
    groups: dict[str, list[Finding]] = {}
    for finding in findings:
        channel = finding.channel
        if channel not in groups:
            groups[channel] = []
        groups[channel].append(finding)
    return groups
