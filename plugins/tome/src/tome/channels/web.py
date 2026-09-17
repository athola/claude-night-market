"""Web search channel: query builders and result parsers.

The web channel is the general-knowledge retrieval channel. Where the
code, discourse, and academic channels each target one slice of the
internet, this one searches the open web at large, so a session can
pick up vendor documentation, news, standards, and blog posts that no
domain-specific channel indexes.

These functions do NOT make HTTP calls. Retrieval goes through either
the You.com MCP server (preferred, when configured) or the built-in
WebSearch tool as a fallback -- the same tool the other channels
already use. The functions here prepare query strings and parse the
results those tools return into Finding objects.

The You.com MCP server is opt-in: the channel works without it, and
the fallback needs no configuration at all.
"""

from __future__ import annotations

from typing import Any

from tome.channels import deduplicate_queries
from tome.models import Finding
from tome.synthesis.ranker import compute_relevance_score

# ---------------------------------------------------------------------------
# Query Expansion
# ---------------------------------------------------------------------------


def expand_web_queries(topic: str, max_variants: int = 5) -> list[str]:
    """Generate diverse general-web search query variants.

    Produces the original topic plus documentation, comparison, and
    recent-status variants, which are the framings that surface vendor
    docs, benchmarks, and news pages a bare topic query misses.

    Args:
        topic: Free-text research topic.
        max_variants: Maximum total queries to return (default 5).

    Returns:
        List of distinct query strings.
    """
    queries: list[str] = [
        topic,
        f"{topic} documentation",
        f"{topic} vs alternatives comparison",
        f"{topic} tutorial guide",
        f"{topic} 2026",
    ]

    return deduplicate_queries(queries)[:max_variants]


# ---------------------------------------------------------------------------
# MCP dispatch
# ---------------------------------------------------------------------------

# The You.com MCP server's search tool name and endpoint. The free
# profile needs no API key; the authenticated endpoint accepts a
# YDC_API_KEY bearer token for higher limits.
_YOU_MCP_ENDPOINT = "https://api.you.com/mcp"
_YOU_MCP_TOOL = "you_search"


def describe_you_mcp_setup(authenticated: bool = False) -> str:
    """Return setup instructions for the You.com MCP server.

    Args:
        authenticated: If True, describe the authenticated endpoint
            (requires ``YDC_API_KEY``); if False, the keyless free
            profile.

    Returns:
        Human-readable setup instructions, one line of prose.
    """
    if authenticated:
        return (
            "Add the You.com MCP server to your client config "
            f"({_YOU_MCP_ENDPOINT}) with a YDC_API_KEY bearer token "
            "for higher rate limits."
        )
    return (
        "Add the You.com MCP server to your client config "
        f"({_YOU_MCP_ENDPOINT}?profile=free) -- the free profile "
        "needs no API key."
    )


# ---------------------------------------------------------------------------
# Response parsers
# ---------------------------------------------------------------------------


def parse_you_mcp_result(result: Any, topic: str) -> list[Finding]:
    """Parse a you.com MCP you_search tool result into Findings.

    The MCP tool returns a list of result objects with the keys
    ``title``, ``url``, and ``snippet``/``description`` -- the same
    shape WebSearch returns, so the fallback path needs no separate
    parser.

    Expected shape::

        [
            {
                "title": "...",
                "url": "https://...",
                "snippet": "...",
                "description": "..."
            },
            ...
        ]

    Args:
        result: Parsed JSON response from the you_search tool.
        topic: Original research topic used to score relevance.

    Returns:
        List of Findings, one per result. Results with no URL are
        skipped; an unexpected shape yields an empty list rather than
        an error, so a malformed tool response degrades to "no
        findings" the way the other channels treat unreachable APIs.
    """
    findings: list[Finding] = []
    if not isinstance(result, list):
        return findings

    for item in result:
        if not isinstance(item, dict):
            continue
        url: str = item.get("url", "")
        if not url:
            continue

        title: str = item.get("title", "") or url
        snippet: str = item.get("snippet", item.get("description", "")) or ""

        relevance = _estimate_relevance(title + " " + snippet, topic)
        findings.append(
            Finding(
                source="you-web",
                channel="web",
                title=title,
                url=url,
                relevance=relevance,
                summary=snippet or title,
                metadata={"retrieved_via": "you-mcp"},
            ),
        )

    return findings


def parse_websearch_result(result: dict[str, Any], topic: str) -> Finding:
    """Parse a single WebSearch result dict into a web Finding.

    The result dict is expected to have the keys WebSearch returns:
    ``title``, ``url``, and one of ``snippet`` or ``description``.
    Missing keys are handled gracefully.

    Args:
        result: Dict with ``title``, ``url``, and optionally
            ``snippet``/``description``.
        topic: Original research topic used to score relevance.

    Returns:
        A Finding with ``source="web"`` and ``channel="web"``.
    """
    url: str = result.get("url", "")
    title: str = result.get("title", "") or url
    snippet: str = result.get("snippet", result.get("description", ""))

    relevance = _estimate_relevance(title + " " + snippet, topic)

    return Finding(
        source="web",
        channel="web",
        title=title,
        url=url,
        relevance=relevance,
        summary=snippet or title,
        metadata={"retrieved_via": "websearch"},
    )


def _estimate_relevance(text: str, topic: str) -> float:
    """Score text relevance to topic on [0.1, 0.95] by keyword overlap."""
    topic_words = {w for w in topic.lower().split() if len(w) > 2}
    text_words = {w for w in text.lower().split() if len(w) > 2}
    if not topic_words:
        return 0.5
    overlap = len(topic_words & text_words) / len(topic_words)
    # Map to [0.1, 0.95] so heuristic scoring never emits 0.0 or 1.0
    return round(0.1 + overlap * 0.85, 4)


# ---------------------------------------------------------------------------
# Ranking
# ---------------------------------------------------------------------------


def rank_web_findings(findings: list[Finding]) -> list[Finding]:
    """Rank web findings using the shared relevance scorer.

    Delegates entirely to ``synthesis.ranker.compute_relevance_score``
    -- unlike the GitHub channel there is no per-source recency signal
    to blend in, so the composite score stands on its own.

    Args:
        findings: Unordered list of web Findings.

    Returns:
        New list sorted descending by composite score. The input list
        is not mutated.
    """
    return sorted(findings, key=compute_relevance_score, reverse=True)
