"""Merge and deduplicate findings across channels."""

from __future__ import annotations

from tome.models import Finding


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
