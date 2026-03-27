"""Pure functions for extracting content features from markdown knowledge.

Provides keyword extraction and query inference used by MarginalValueFilter
to compare new content against the existing corpus.
"""

from __future__ import annotations

import re

_STOP_WORDS = frozenset(
    {
        "the",
        "and",
        "for",
        "that",
        "this",
        "with",
        "from",
        "are",
        "was",
        "were",
        "been",
        "have",
        "has",
        "had",
        "not",
        "but",
        "can",
        "will",
        "what",
        "when",
        "where",
        "who",
        "why",
        "how",
        "all",
        "each",
        "which",
        "their",
        "said",
        "them",
        "these",
        "than",
        "into",
        "very",
        "her",
        "our",
        "out",
        "only",
    }
)


def extract_keywords(content: str, title: str, tags: list[str]) -> set[str]:
    """Extract keywords from content for corpus comparison.

    Uses multiple strategies: provided tags, title words, hyphenated
    technical terms, emphasized text, and heading words. Stop words are
    removed from the final set.

    Args:
        content: Content text (markdown).
        title: Content title or summary.
        tags: Optional tags already associated with the content.

    Returns:
        Set of lowercase keyword strings.

    """
    keywords: set[str] = set()

    keywords.update(tag.lower() for tag in tags)

    title_words = re.findall(r"\b[a-z]{3,}\b", title.lower())
    keywords.update(title_words)

    technical_terms = re.findall(r"\b[a-z]+(?:-[a-z]+)+\b", content.lower())
    keywords.update(technical_terms)

    emphasized = re.findall(r"\*\*([^*]+)\*\*|\*([^*]+)\*", content)
    for match in emphasized:
        term = match[0] or match[1]
        term_words = re.findall(r"\b[a-z]{3,}\b", term.lower())
        keywords.update(term_words)

    headings = re.findall(r"^#{1,3}\s+(.+)$", content, re.MULTILINE)
    for heading in headings:
        heading_words = re.findall(r"\b[a-z]{3,}\b", heading.lower())
        keywords.update(heading_words)

    return {k for k in keywords if k not in _STOP_WORDS}


def infer_queries(content: str, title: str) -> list[str]:
    """Infer potential search queries this content could answer.

    Scans the title and markdown headings for common question patterns
    (how-to, pattern/approach, best-practices) and generates
    representative query strings.

    Args:
        content: Content text (markdown).
        title: Content title or summary.

    Returns:
        List of inferred query strings.

    """
    queries: list[str] = []

    headings = [title, *re.findall(r"^#{1,3}\s+(.+)$", content, re.MULTILINE)]

    for heading in headings:
        heading_lower = heading.lower()

        if "how" in heading_lower:
            queries.append(heading_lower)

        if "pattern" in heading_lower or "approach" in heading_lower:
            queries.append(f"what is {heading_lower}")

        if "practice" in heading_lower or "tip" in heading_lower:
            queries.append(f"best practices for {heading_lower}")

    return queries
