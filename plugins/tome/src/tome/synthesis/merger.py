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
    """Compute Jaccard similarity between two normalized title strings."""
    words_a = set(a.split())
    words_b = set(b.split())
    if not words_a and not words_b:
        return 1.0
    if not words_a or not words_b:
        return 0.0
    intersection = words_a & words_b
    union = words_a | words_b
    return len(intersection) / len(union)


def fuzzy_deduplicate(
    findings: list[Finding],
    cross_channel: bool = False,
) -> list[Finding]:
    """Remove duplicate findings by title similarity.

    Compares normalized titles using Jaccard similarity. Within the
    same channel, requires similarity >= 0.8. Across channels (when
    *cross_channel* is True), uses a lower threshold of 0.6.

    When duplicates are found, keeps the higher-relevance finding.

    Args:
        findings: List of findings to deduplicate.
        cross_channel: If True, also compare across different channels.

    Returns:
        Deduplicated list preserving encounter order.
    """
    if not findings:
        return []

    # Pre-compute normalized titles
    normals = [normalize_title(f.title) for f in findings]

    # Track which indices are superseded
    removed: set[int] = set()

    for i in range(len(findings)):
        if i in removed:
            continue
        for j in range(i + 1, len(findings)):
            if j in removed:
                continue

            same_channel = findings[i].channel == findings[j].channel

            if not cross_channel and not same_channel:
                continue

            threshold = (
                _JACCARD_THRESHOLD_SAME_CHANNEL
                if same_channel
                else _JACCARD_THRESHOLD_CROSS_CHANNEL
            )

            sim = _jaccard_similarity(normals[i], normals[j])
            if sim >= threshold:
                # Remove the lower-relevance one
                if findings[i].relevance >= findings[j].relevance:
                    removed.add(j)
                else:
                    removed.add(i)
                    break  # i is removed, stop comparing it

    return [f for idx, f in enumerate(findings) if idx not in removed]


def deduplicate(findings: list[Finding]) -> list[Finding]:
    """Remove duplicate findings by URL, keeping the higher-relevance one.

    Findings with empty or falsy URLs are always kept (no dedup key).
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
    # Preserve original encounter order using first occurrence of winner.
    seen: dict[str, bool] = {}
    result: list[Finding] = []
    for finding in findings:
        url = finding.url
        if not url:
            continue  # added separately
        if url not in seen and best[url] is finding:
            seen[url] = True
            result.append(finding)
    result.extend(no_url)
    return result


def merge_findings(channel_results: list[list[Finding]]) -> list[Finding]:
    """Merge findings from multiple channels into one deduplicated list."""
    flat: list[Finding] = []
    for channel in channel_results:
        flat.extend(channel)
    return deduplicate(flat)
