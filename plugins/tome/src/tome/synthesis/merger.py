"""Merge and deduplicate findings across channels."""

from __future__ import annotations

import itertools
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


def fuzzy_deduplicate(
    findings: list[Finding],
    cross_channel: bool = False,
) -> list[Finding]:
    """Remove duplicate findings by title similarity using union-find.

    Compares normalized titles using Jaccard similarity. Within the same
    channel, requires similarity >= 0.8. Across channels (when
    *cross_channel* is True), uses a lower threshold of 0.6.

    Union-find groups transitive duplicates correctly: if A duplicates B
    and B duplicates C, all three are in the same group. The
    highest-relevance finding survives from each group, appearing at the
    first-encounter position of any group member.

    Args:
        findings: List of findings to deduplicate.
        cross_channel: If True, also compare across different channels.

    Returns:
        Deduplicated list preserving encounter order of first group member.
    """
    if not findings:
        return []

    normals = [normalize_title(f.title) for f in findings]
    roots = _cluster_duplicates(findings, normals, cross_channel)

    # Select highest-relevance representative per group
    best_idx: dict[int, int] = {}
    for i, root in enumerate(roots):
        if (
            root not in best_idx
            or findings[i].relevance > findings[best_idx[root]].relevance
        ):
            best_idx[root] = i

    # Emit one finding per group in first-encounter order
    seen_roots: set[int] = set()
    result: list[Finding] = []
    for root in roots:
        if root not in seen_roots:
            seen_roots.add(root)
            result.append(findings[best_idx[root]])

    return result


def _cluster_duplicates(
    findings: list[Finding],
    normals: list[str],
    cross_channel: bool,
) -> list[int]:
    """Group title-duplicate findings via union-find.

    Returns a per-index list of group representatives (roots): findings sharing
    a root are duplicates. When *cross_channel* is False, only same-channel
    pairs are compared, at the stricter same-channel Jaccard threshold.
    """
    n = len(findings)
    parent = list(range(n))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x: int, y: int) -> None:
        parent[find(y)] = find(x)

    if cross_channel:
        for i in range(n):
            for j in range(i + 1, n):
                same_channel = findings[i].channel == findings[j].channel
                threshold = (
                    _JACCARD_THRESHOLD_SAME_CHANNEL
                    if same_channel
                    else _JACCARD_THRESHOLD_CROSS_CHANNEL
                )
                if _jaccard_similarity(normals[i], normals[j]) >= threshold:
                    union(i, j)
    else:
        # Group by channel first to skip cross-channel pairs entirely.
        # O(n) grouping + O(within-channel pairs) instead of O(n²) all-pairs.
        channel_groups: dict[str | None, list[int]] = {}
        for idx, finding in enumerate(findings):
            channel_groups.setdefault(finding.channel, []).append(idx)
        for indices in channel_groups.values():
            for a, b in itertools.combinations(indices, 2):
                if (
                    _jaccard_similarity(normals[a], normals[b])
                    >= _JACCARD_THRESHOLD_SAME_CHANNEL
                ):
                    union(a, b)

    return [find(i) for i in range(n)]


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
