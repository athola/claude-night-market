"""Agent-facing query API for cross-plugin integration."""

from __future__ import annotations

from pathlib import Path

from gauntlet.knowledge_store import KnowledgeStore
from gauntlet.models import KnowledgeEntry


def query_knowledge(
    gauntlet_dir: Path,
    files: list[str] | None = None,
    categories: list[str] | None = None,
    tags: list[str] | None = None,
    min_difficulty: int = 1,
    max_difficulty: int = 4,
) -> list[KnowledgeEntry]:
    """Return knowledge entries matching the supplied filters.

    Wraps KnowledgeStore.query() for external callers.
    """
    store = KnowledgeStore(gauntlet_dir)
    return store.query(
        files=files,
        categories=categories,
        tags=tags,
        min_difficulty=min_difficulty,
        max_difficulty=max_difficulty,
    )


def get_context_for_files(gauntlet_dir: Path, files: list[str]) -> str:
    """Return a markdown summary of knowledge entries related to *files*.

    Format per entry:

        ### {concept}
        **Module:** `{module}`
        **Category:** {category}
        **Difficulty:** {difficulty}/4

        {detail}

        **Related:** `file1`, `file2`

    Returns a "No knowledge entries found..." message when no entries match.
    """
    entries = query_knowledge(gauntlet_dir, files=files)
    if not entries:
        return "No knowledge entries found for the specified files."

    lines: list[str] = ["## Gauntlet Knowledge Context"]
    for entry in entries:
        lines.append("")
        lines.append(f"### {entry.concept}")
        lines.append(f"**Module:** `{entry.module}`")
        lines.append(f"**Category:** {entry.category}")
        lines.append(f"**Difficulty:** {entry.difficulty}/4")
        lines.append("")
        lines.append(entry.detail)
        if entry.related_files:
            related = ", ".join(f"`{f}`" for f in entry.related_files)
            lines.append("")
            lines.append(f"**Related:** {related}")

    return "\n".join(lines)


def validate_understanding(
    gauntlet_dir: Path, files: list[str], claim: str
) -> dict[str, object]:
    """Score a claim against knowledge entries related to *files*.

    Returns a dict with:
    - ``score``: float average word-overlap across all matching entries,
      capped at 1.0.
    - ``gaps``: list of concept names where overlap < 0.3.
    """
    entries = query_knowledge(gauntlet_dir, files=files)
    if not entries:
        return {"score": 0.0, "gaps": []}

    claim_words = set(claim.lower().split())
    overlaps: list[float] = []
    gaps: list[str] = []

    for entry in entries:
        detail_words = set(entry.detail.lower().split())
        if not detail_words:
            overlap = 0.0
        else:
            overlap = len(claim_words & detail_words) / len(detail_words)
        overlap = min(overlap, 1.0)
        overlaps.append(overlap)
        if overlap < 0.3:
            gaps.append(entry.concept)

    score = sum(overlaps) / len(overlaps) if overlaps else 0.0
    score = min(score, 1.0)
    return {"score": score, "gaps": gaps}
