"""Score, rank, and group research findings."""

from __future__ import annotations

import re
from datetime import datetime, timezone

from tome.models import Finding

# Computed once at import time; stable for the lifetime of the process.
_CURRENT_YEAR: int = datetime.now(tz=timezone.utc).year  # noqa: UP017

# ---------------------------------------------------------------------------
# Cross-Channel Triangulation
# ---------------------------------------------------------------------------

_PUNCTUATION_RE = re.compile(r"[^\w\s]")
_TRIANGULATION_CAP = 0.15
_TRIANGULATION_PER_CHANNEL = 0.05


def _normalize_for_match(title: str) -> set[str]:
    """Return a set of lowercase words from a title, punctuation stripped."""
    return set(_PUNCTUATION_RE.sub("", title.lower()).split())


def compute_triangulation_bonus(finding: Finding, all_findings: list[Finding]) -> float:
    """Compute a bonus for findings corroborated across channels.

    Checks how many *other* channels contain a finding with a similar
    title (Jaccard word overlap >= 0.6). Each additional channel adds
    +0.05, capped at 0.15.

    Args:
        finding: The finding to score.
        all_findings: The full list of findings for cross-referencing.

    Returns:
        Bonus float in [0.0, 0.15].
    """
    target_words = _normalize_for_match(finding.title)
    if not target_words:
        return 0.0

    corroborating_channels: set[str] = set()

    for other in all_findings:
        if other is finding:
            continue
        if other.channel == finding.channel:
            continue

        other_words = _normalize_for_match(other.title)
        if not other_words:
            continue

        intersection = target_words & other_words
        union = target_words | other_words
        jaccard = len(intersection) / len(union)

        if jaccard >= 0.6:
            corroborating_channels.add(other.channel)

    bonus = len(corroborating_channels) * _TRIANGULATION_PER_CHANNEL
    return min(bonus, _TRIANGULATION_CAP)


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
