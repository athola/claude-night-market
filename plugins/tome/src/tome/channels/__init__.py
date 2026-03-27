"""Research channel implementations."""

from __future__ import annotations


def deduplicate_queries(queries: list[str]) -> list[str]:
    """Remove duplicate queries while preserving order."""
    seen: set[str] = set()
    unique: list[str] = []
    for q in queries:
        if q not in seen:
            seen.add(q)
            unique.append(q)
    return unique
