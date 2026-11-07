"""Merge and deduplicate findings across channels."""

from __future__ import annotations

import re

from tome.models import Finding

# ---------------------------------------------------------------------------
# Fuzzy Semantic Deduplication
# ---------------------------------------------------------------------------

_PUNCTUATION_RE = re.compile(r"[^\w\s]")
_JACCARD_THRESHOLD_SAME_CHANNEL = 0.8
_JACCARD_THRESHOLD_CROSS_CHANNEL = 0.6


def normalize_title(title: str) -> str:
    """Reduce a title to a canonical form for comparison.

    Lowercases, strips punctuation, and sorts words so that minor
    differences in casing, punctuation, or word order do not prevent
    matching.

    Args:
        title: Raw title string.

    Returns:
        Normalized string with sorted lowercase words.
    """
    if not title:
        return ""
    lowered = title.lower()
    stripped = _PUNCTUATION_RE.sub("", lowered)
    words = sorted(stripped.split())
    return " ".join(words)


def _jaccard_similarity(a: str, b: str) -> float:
    """Compute Jaccard similarity between two normalized title strings.

    Two titleless findings score ``0.0``, not ``1.0``: an empty word set
    is an absence of evidence, and treating it as a perfect match made
    every untitled finding a duplicate of every other, dropping distinct
    results that merely lacked a title.
    """
    words_a = set(a.split())
    words_b = set(b.split())
    if not words_a or not words_b:
        return 0.0
    intersection = words_a & words_b
    union = words_a | words_b
    return len(intersection) / len(union)


def deduplicate(findings: list[Finding]) -> list[Finding]:
    """Remove duplicate findings by URL, keeping the higher-relevance one.

    Findings with empty or falsy URLs are always kept (no dedup key).
    Output order follows first URL encounter; dict insertion order is stable
    in Python 3.7+.
    """
    best: dict[str, Finding] = {}
    no_url: list[Finding] = []
    for finding in findings:
        url = finding.url
        if not url:
            no_url.append(finding)
            continue
        if url not in best or finding.relevance > best[url].relevance:
            best[url] = finding
    return list(best.values()) + no_url


def merge_findings(channel_results: list[list[Finding]]) -> list[Finding]:
    """Merge findings from multiple channels into one deduplicated list."""
    flat: list[Finding] = []
    for channel in channel_results:
        flat.extend(channel)
    return deduplicate(flat)
