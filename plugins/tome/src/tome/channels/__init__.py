"""Research channel implementations."""

from __future__ import annotations


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
