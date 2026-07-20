"""Deterministic corpus-quality metrics over a set of findings.

Diversity (a creativity proxy) and efficiency (performance proxies).
All pure functions: no network, no model, no cross-plugin backend.
"""

from __future__ import annotations

from collections import Counter

from tome.models import Finding


def source_diversity(findings: list[Finding]) -> float:
    """Return ``1 - Herfindahl`` over channels, in ``[0.0, 1.0)``.

    0.0 when every finding shares one channel; approaches 1.0 as the set
    spreads evenly across many channels. This is the same diversity term
    the synthesis quality score uses, exposed as a standalone metric.
    """
    if not findings:
        return 0.0
    counts = Counter(finding.channel for finding in findings)
    total = len(findings)
    herfindahl = sum((count / total) ** 2 for count in counts.values())
    return 1.0 - herfindahl


def dedup_ratio(before: int, after: int) -> float:
    """Fraction of findings removed by deduplication; 0.0 if ``before`` is 0."""
    if before <= 0:
        return 0.0
    return (before - after) / before


def findings_per_1k_tokens(count: int, tokens: int) -> float:
    """Findings yielded per 1000 tokens spent; 0.0 when no tokens spent."""
    if tokens <= 0:
        return 0.0
    return count / (tokens / 1000)
