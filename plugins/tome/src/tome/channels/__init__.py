"""Research channel implementations."""

from __future__ import annotations

import re


def deduplicate_queries(queries: list[str], limit: int | None = None) -> list[str]:
    """Remove duplicate queries while preserving order, keeping at most ``limit``.

    Raises:
        ValueError: If ``limit`` is below 1. A negative slice would drop
            queries from the tail and 0 would return nothing, silently.
    """
    if limit is not None and limit < 1:
        raise ValueError(f"query limit must be at least 1, got {limit}")
    seen: set[str] = set()
    unique: list[str] = []
    for q in queries:
        if q not in seen:
            seen.add(q)
            unique.append(q)
    return unique if limit is None else unique[:limit]


def estimate_relevance(text: str, topic: str) -> tuple[float, str]:
    """Score text relevance to topic on [0.1, 0.95] by keyword overlap.

    Returns ``(score, basis)``. ``basis`` is ``"measured"`` for a real
    overlap measurement, and ``"abstained"`` when the topic yields no
    scoreable words (short topics like ``AI vs ML`` whose words are all
    filtered by the length floor), so an abstention's 0.5 is
    distinguishable from an honest 0.5 via
    ``metadata["relevance_basis"]``.
    """
    # Tokenize on letters and digits so "Kafka:" and "(Streams," still
    # match the topic words they contain.
    topic_words = {w for w in re.findall(r"[a-z0-9]+", topic.lower()) if len(w) > 2}
    if not topic_words:
        return 0.5, "abstained"
    text_words = {w for w in re.findall(r"[a-z0-9]+", text.lower()) if len(w) > 2}
    overlap = len(topic_words & text_words) / len(topic_words)
    # Map to [0.1, 0.95] so heuristic scoring never emits 0.0 or 1.0
    return round(0.1 + overlap * 0.85, 4), "measured"
