"""Web search channel: query builders and result parsers.

The web channel is the general-knowledge retrieval channel. Where the
code, discourse, and academic channels each target one slice of the
internet, this one searches the open web at large, so a session can
pick up vendor documentation, news, standards, and blog posts that no
domain-specific channel indexes.

These functions do NOT make HTTP calls. Retrieval goes through either
the You.com MCP server (preferred, when configured) or the built-in
WebSearch tool as a fallback: the same tool the other channels already
use. The functions here prepare query strings and parse the results
those tools return into Finding objects.

The You.com MCP server is opt-in: the channel works without it, and
the fallback needs no configuration at all.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any

from tome.channels import deduplicate_queries
from tome.models import Finding
from tome.synthesis.ranker import compute_relevance_score

# Computed at import the way synthesis.ranker and synthesis.quality do,
# so the recent-status query variant never carries a stale year.
_CURRENT_YEAR: int = datetime.now(tz=timezone.utc).year

# ---------------------------------------------------------------------------
# Query Expansion
# ---------------------------------------------------------------------------


def expand_web_queries(topic: str, max_variants: int = 5) -> list[str]:
    """Generate diverse general-web search query variants.

    Produces the original topic plus documentation, comparison,
    tutorial, and recent-status variants, which are the framings that
    surface vendor docs, benchmarks, how-tos, and news pages a bare
    topic query misses.

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
        f"{topic} {_CURRENT_YEAR}",
    ]

    return deduplicate_queries(queries)[:max_variants]


# ---------------------------------------------------------------------------
# MCP dispatch
# ---------------------------------------------------------------------------

# The You.com MCP server's search tool name and endpoint. The free
# profile needs no API key; the authenticated endpoint accepts a
# YDC_API_KEY bearer token for higher limits.
_YOU_MCP_ENDPOINT = "https://api.you.com/mcp"
# Tool names on the You.com MCP server use hyphens: tools/list on the
# live endpoint reports "you-search" (and "you-discover"), not
# "you_search".
_YOU_MCP_TOOL = "you-search"


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
            f"for higher rate limits; its search tool is {_YOU_MCP_TOOL}."
        )
    return (
        "Add the You.com MCP server to your client config "
        f"({_YOU_MCP_ENDPOINT}?profile=free); the free profile needs "
        f"no API key, and its search tool is {_YOU_MCP_TOOL}."
    )


# ---------------------------------------------------------------------------
# Response parsers
# ---------------------------------------------------------------------------

_YEAR_RE = re.compile(r"\b(?:19|20)\d{2}\b")


def _extract_year(page_age: Any) -> int | None:
    """Pull a 4-digit year out of a you-search ``page_age`` value.

    Args:
        page_age: The ``page_age`` field of a you-search web item,
            which may be a year, a date, or a relative age.

    Returns:
        The year as an int, or None if no year is present.
    """
    if not isinstance(page_age, str):
        return None
    match = _YEAR_RE.search(page_age)
    return int(match.group(0)) if match else None


def _unwrap_you_mcp_items(result: Any) -> list[Any]:
    """Extract the web result items from a you-search tool response.

    The server wraps the payload three levels deep::

        {"_meta": ..., "content": [{"type": "text", "text": "<json>"}],
         "structuredContent": ...}

    with ``content[0].text`` parsing to
    ``{"metadata": ..., "results": {"web": [...]}}``. A bare list of
    result dicts is also accepted, for callers whose client already
    unwrapped the envelope.

    Args:
        result: Parsed JSON response from the you-search tool.

    Returns:
        The list of web result dicts.

    Raises:
        ValueError: if the response is neither shape, naming the type
            and keys received. A malformed response must not degrade
            to "no findings": per ``models.QueryLog``, a failure with
            no named cause is indistinguishable from a channel that
            searched properly and found nothing, and a silent empty
            list would tell the report exactly that.
    """
    if isinstance(result, list):
        return result
    if isinstance(result, dict):
        content = result.get("content")
        if isinstance(content, list) and content and isinstance(content[0], dict):
            text = content[0].get("text")
            if isinstance(text, str):
                try:
                    inner = json.loads(text)
                except ValueError as exc:
                    raise ValueError(
                        "you-search content[0].text is not valid JSON; "
                        f"starts with {text[:80]!r}"
                    ) from exc
                if isinstance(inner, dict):
                    web = (inner.get("results") or {}).get("web")
                    if isinstance(web, list):
                        return web
        structured = result.get("structuredContent")
        if isinstance(structured, dict):
            web = (structured.get("results") or {}).get("web")
            if isinstance(web, list):
                return web
    received = (
        f"dict with keys {sorted(result)}"
        if isinstance(result, dict)
        else f"{type(result).__name__}"
    )
    raise ValueError(f"unrecognized you-search response shape; received {received}")


def parse_you_mcp_result(result: Any, topic: str) -> list[Finding]:
    """Parse a You.com MCP you-search tool result into Findings.

    Expected shape, as sent by the live server::

        {
            "_meta": {...},
            "content": [
                {"type": "text", "text": "...json..."}
            ],
            "structuredContent": {...}
        }

    where ``content[0].text`` parses to
    ``{"metadata": ..., "results": {"web": [...]}}`` and each web item
    carries ``title``, ``url``, ``description``, and ``page_age``
    (there is no ``snippet`` key).

    Args:
        result: Parsed JSON response from the you-search tool.
        topic: Original research topic used to score relevance.

    Returns:
        List of Findings, one per result. Items with no URL are
        skipped. A ``page_age`` carrying a year is recorded in
        ``metadata["year"]`` so the shared recency scoring can see it.

    Raises:
        ValueError: if the response is not a recognized you-search
            envelope (see ``_unwrap_you_mcp_items``), so a malformed
            response surfaces as a channel failure instead of being
            scored as "the open web has nothing on this topic".
    """
    items = _unwrap_you_mcp_items(result)
    findings: list[Finding] = []

    for item in items:
        if not isinstance(item, dict):
            continue
        url: str = item.get("url") or ""
        if not url:
            continue

        title: str = item.get("title") or url
        snippet: str = item.get("snippet") or item.get("description") or ""
        relevance, basis = _estimate_relevance(title + " " + snippet, topic)
        metadata: dict[str, Any] = {
            "retrieved_via": "you-mcp",
            "relevance_basis": basis,
        }
        year = _extract_year(item.get("page_age"))
        if year is not None:
            metadata["year"] = year

        findings.append(
            Finding(
                source="you-web",
                channel="web",
                title=title,
                url=url,
                relevance=relevance,
                summary=snippet or title,
                metadata=metadata,
            ),
        )

    return findings


def parse_websearch_result(result: dict[str, Any], topic: str) -> Finding:
    """Parse a single WebSearch result dict into a web Finding.

    The result dict is expected to have the keys WebSearch returns:
    ``title``, ``url``, and one of ``snippet`` or ``description``. A
    null or empty ``snippet`` falls through to ``description``, and a
    missing key behaves the same way.

    Args:
        result: Dict with ``title``, ``url``, and optionally
            ``snippet``/``description``.
        topic: Original research topic used to score relevance.

    Returns:
        A Finding with ``source="web"`` and ``channel="web"``.

    Raises:
        ValueError: if the result has no URL, which is the same
            contract ``parse_you_mcp_result`` enforces per item: a
            result with nothing to cite is refused loudly rather than
            filed as a blank Finding that survives deduplication.
    """
    url: str = result.get("url") or ""
    if not url:
        raise ValueError(
            f"WebSearch result has no URL; keys present = {sorted(result)}"
        )
    title: str = result.get("title") or url
    snippet: str = result.get("snippet") or result.get("description") or ""
    relevance, basis = _estimate_relevance(title + " " + snippet, topic)

    return Finding(
        source="web",
        channel="web",
        title=title,
        url=url,
        relevance=relevance,
        summary=snippet or title,
        metadata={"retrieved_via": "websearch", "relevance_basis": basis},
    )


def _estimate_relevance(text: str, topic: str) -> tuple[float, str]:
    """Score text relevance to topic on [0.1, 0.95] by keyword overlap.

    Returns ``(score, basis)``. ``basis`` is ``"measured"`` for a real
    overlap measurement, and ``"abstained"`` when the topic yields no
    scoreable words (short topics like ``AI vs ML`` whose words are all
    filtered by the length floor), so an abstention's 0.5 is
    distinguishable from an honest 0.5 via
    ``metadata["relevance_basis"]``.
    """
    topic_words = {w for w in topic.lower().split() if len(w) > 2}
    if not topic_words:
        return 0.5, "abstained"
    text_words = {w for w in text.lower().split() if len(w) > 2}
    overlap = len(topic_words & text_words) / len(topic_words)
    # Map to [0.1, 0.95] so heuristic scoring never emits 0.0 or 1.0
    return round(0.1 + overlap * 0.85, 4), "measured"


# ---------------------------------------------------------------------------
# Ranking
# ---------------------------------------------------------------------------


def rank_web_findings(findings: list[Finding]) -> list[Finding]:
    """Rank web findings using the shared relevance scorer.

    Delegates entirely to ``synthesis.ranker.compute_relevance_score``:
    unlike the GitHub channel there is no per-source recency signal to
    blend in, so the composite score stands on its own.

    Args:
        findings: Unordered list of web Findings.

    Returns:
        New list sorted descending by composite score. The input list
        is not mutated.
    """
    return sorted(findings, key=compute_relevance_score, reverse=True)
