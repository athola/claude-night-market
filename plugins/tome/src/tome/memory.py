"""Cross-session research memory.

Finds related past sessions and imports their top findings into
new research sessions so that research builds on itself.
"""

from __future__ import annotations

import re
from dataclasses import replace

from tome.models import Finding, ResearchSession

_PUNCTUATION_RE = re.compile(r"[^\w\s]")
_TOPIC_OVERLAP_THRESHOLD = 0.3


def _topic_words(topic: str) -> set[str]:
    """Extract a set of lowercase words from a topic string."""
    cleaned = _PUNCTUATION_RE.sub("", topic.lower())
    return set(cleaned.split())


def find_related_sessions(
    topic: str,
    history: list[ResearchSession],
    min_overlap: float = _TOPIC_OVERLAP_THRESHOLD,
) -> list[ResearchSession]:
    """Find past sessions with topic overlap.

    Uses Jaccard similarity on topic words. Sessions with overlap
    above *min_overlap* are returned, sorted by descending overlap.

    Args:
        topic: The new research topic.
        history: List of past sessions.
        min_overlap: Minimum Jaccard similarity (default 0.3).

    Returns:
        Related sessions sorted by topic similarity.
    """
    target_words = _topic_words(topic)
    if not target_words:
        return []

    scored: list[tuple[float, ResearchSession]] = []
    for session in history:
        session_words = _topic_words(session.topic)
        if not session_words:
            continue
        intersection = target_words & session_words
        union = target_words | session_words
        jaccard = len(intersection) / len(union)
        if jaccard >= min_overlap:
            scored.append((jaccard, session))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [s for _, s in scored]


def import_prior_findings(
    sessions: list[ResearchSession],
    max_per_session: int = 5,
) -> list[Finding]:
    """Import top findings from related past sessions.

    For each session, takes the top *max_per_session* findings by
    relevance and marks them with ``from_prior_session=True`` in
    metadata.

    Args:
        sessions: Related past sessions.
        max_per_session: Max findings to import per session.

    Returns:
        List of imported findings with prior-session metadata.
    """
    imported: list[Finding] = []

    for session in sessions:
        if not session.findings:
            continue

        # Sort by relevance descending, take top N
        top = sorted(
            session.findings,
            key=lambda f: f.relevance,
            reverse=True,
        )[:max_per_session]

        for finding in top:
            # Create a copy with the prior-session marker
            new_meta = dict(finding.metadata)
            new_meta["from_prior_session"] = True
            new_meta["prior_session_id"] = session.id
            imported.append(replace(finding, metadata=new_meta))

    return imported
