"""Formatting utilities for cached knowledge entries."""

from __future__ import annotations

from typing import Any


def format_cached_entry_context(entry: dict[str, Any]) -> str:
    """Format a cached entry for context injection."""
    title = entry.get("title", "Untitled")
    file_path = entry.get("file", "unknown")
    match_score = entry.get("match_score", 0.0)

    excerpt = ""
    if "content" in entry:
        content = entry["content"]
        excerpt = content[:200].strip()
        if len(content) > 200:
            excerpt += "..."

    parts = [
        f"\n--- Cached Knowledge: {title} ({match_score:.0%} match) ---",
        f"Source: {file_path}",
    ]

    if excerpt:
        parts.append(f"Excerpt: {excerpt}")

    parts.append("---")
    return "\n".join(parts)
