"""Discourse channel: HN, Lobsters, Reddit, and tech blog query builders
and response parsers.

These functions do NOT make HTTP calls. They prepare query strings and
URLs for WebSearch/WebFetch tool calls, and parse the results those
tools return into Finding objects.
"""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import quote_plus

from tome.channels import deduplicate_queries
from tome.models import Finding

# ---------------------------------------------------------------------------
# Query Expansion
# ---------------------------------------------------------------------------


def expand_discourse_queries(topic: str, max_variants: int = 4) -> list[str]:
    """Generate diverse community search query variants.

    Produces variants aimed at discussion forums and tech blogs.

    Args:
        topic: Free-text research topic.
        max_variants: Maximum total queries to return (default 4).

    Returns:
        List of distinct query strings.
    """
    queries: list[str] = [
        topic,
        f"{topic} best practices",
        f"{topic} experience production",
        f"{topic} comparison alternatives",
    ]

    return deduplicate_queries(queries)[:max_variants]


_LOBSTERS_BASE_RELEVANCE = 0.6
_BLOG_BASE_RELEVANCE = 0.65

# ---------------------------------------------------------------------------
# Hacker News (Algolia API)
# ---------------------------------------------------------------------------

_HN_API_BASE = "https://hn.algolia.com/api/v1/search"
_HN_ITEM_BASE = "https://news.ycombinator.com/item?id="


def build_hn_search_url(topic: str, hits_per_page: int = 10) -> str:
    """Build an Algolia HN search URL for story results.

    Args:
        topic: Free-text research topic.
        hits_per_page: Number of results to request (default 10).

    Returns:
        URL string suitable for a WebFetch tool call. Response will be
        JSON with a ``hits`` array.
    """
    encoded = quote_plus(topic)
    return f"{_HN_API_BASE}?query={encoded}&tags=story&hitsPerPage={hits_per_page}"


def parse_hn_response(
    data: dict[str, Any],
    min_score: int = 5,
) -> list[Finding]:
    """Parse an Algolia HN API response into Findings.

    Hits with ``points`` strictly below ``min_score`` are excluded.
    Hits at exactly ``min_score`` are included.

    Expected shape::

        {
            "hits": [
                {
                    "title": "...",
                    "url": "https://...",
                    "points": 250,
                    "num_comments": 80,
                    "objectID": "99001"
                },
                ...
            ]
        }

    Args:
        data: Parsed JSON response from the Algolia HN API.
        min_score: Minimum points threshold (inclusive). Default 5.

    Returns:
        List of Findings with ``source="hn"`` and ``channel="discourse"``.
    """
    findings: list[Finding] = []
    hits = data.get("hits", [])
    if not isinstance(hits, list):
        return findings

    for hit in hits:
        if not isinstance(hit, dict):
            continue
        points: int = hit.get("points", 0) or 0
        if points < min_score:
            continue

        title: str = hit.get("title", "")
        object_id: str = str(hit.get("objectID", ""))
        url: str = hit.get("url", "") or (
            f"{_HN_ITEM_BASE}{object_id}" if object_id else ""
        )
        num_comments: int = hit.get("num_comments", 0) or 0

        # Relevance: normalise points on a soft scale (capped at 0.95)
        relevance = round(min(0.3 + points / 1_000, 0.95), 4)

        summary_parts = [f"{points} points"]
        if num_comments:
            summary_parts.append(f"{num_comments} comments")

        findings.append(
            Finding(
                source="hn",
                channel="discourse",
                title=title or url,
                url=url,
                relevance=relevance,
                summary=". ".join(summary_parts),
                metadata={
                    "score": points,
                    "comments": num_comments,
                    "object_id": object_id,
                },
            )
        )

    return findings


# ---------------------------------------------------------------------------
# Lobste.rs
# ---------------------------------------------------------------------------

_LOBSTERS_SEARCH_BASE = "https://lobste.rs/search"


def build_lobsters_search_url(topic: str) -> str:
    """Build a lobste.rs search URL (for WebFetch).

    The response is HTML so callers may prefer the WebSearch fallback
    via :func:`build_lobsters_websearch_query` if HTML parsing is not
    available.

    Args:
        topic: Free-text research topic.

    Returns:
        URL string for the lobste.rs search endpoint.
    """
    encoded = quote_plus(topic)
    return f"{_LOBSTERS_SEARCH_BASE}?q={encoded}&what=stories&order=relevance"


def build_lobsters_websearch_query(topic: str) -> str:
    """Build a WebSearch fallback query targeting lobste.rs.

    Args:
        topic: Free-text research topic.

    Returns:
        Query string using the ``site:`` operator.
    """
    return f"site:lobste.rs {topic}"


def parse_lobsters_result(result: dict[str, Any]) -> Finding:
    """Parse a lobste.rs WebSearch result dict into a Finding.

    Args:
        result: Dict with ``title``, ``url``, and optionally ``snippet``.

    Returns:
        A Finding with ``source="lobsters"`` and ``channel="discourse"``.
    """
    url: str = result.get("url", "")
    title: str = result.get("title", url or "lobste.rs result")
    snippet: str = result.get("snippet", result.get("description", ""))

    return Finding(
        source="lobsters",
        channel="discourse",
        title=title,
        url=url,
        relevance=_LOBSTERS_BASE_RELEVANCE,
        summary=snippet or title,
        metadata={},
    )


# ---------------------------------------------------------------------------
# Reddit
# ---------------------------------------------------------------------------

_REDDIT_SUBREDDITS: dict[str, list[str]] = {
    "algorithm": ["programming", "compsci", "algorithms"],
    "data-structure": ["programming", "compsci", "algorithms"],
    "architecture": ["programming", "softwarearchitecture", "ExperiencedDevs"],
    "ui-ux": ["webdev", "reactjs", "frontend"],
    "scientific": ["programming", "MachineLearning", "datascience"],
    "financial": ["algotrading", "quantfinance"],
    "devops": ["devops", "kubernetes", "sysadmin"],
    "security": ["netsec", "AskNetsec", "cybersecurity"],
    "general": ["programming", "coding", "learnprogramming"],
}

_REDDIT_GENERAL = _REDDIT_SUBREDDITS["general"]


def build_reddit_search_url(
    topic: str,
    subreddit: str = "programming",
) -> str:
    """Build a Reddit JSON search URL.

    Args:
        topic: Free-text research topic.
        subreddit: Subreddit name without the ``r/`` prefix (default
            ``"programming"``).

    Returns:
        URL string for old.reddit.com JSON search endpoint.
    """
    encoded = quote_plus(topic)
    return (
        f"https://old.reddit.com/r/{subreddit}/search.json"
        f"?q={encoded}&restrict_sr=on&sort=relevance&t=all"
    )


def suggest_subreddits(topic: str, domain: str) -> list[str]:
    """Suggest relevant subreddits based on topic domain.

    The ``topic`` parameter is accepted for future keyword-based
    overrides but is not used in the current implementation.

    Args:
        topic: Free-text research topic (reserved for future use).
        domain: Domain string from :class:`~tome.models.DomainClassification`.

    Returns:
        List of subreddit name strings (without ``r/`` prefix). Falls
        back to the general list for unknown domains.
    """
    return list(_REDDIT_SUBREDDITS.get(domain, _REDDIT_GENERAL))


def parse_reddit_response(
    data: dict[str, Any],
    min_score: int = 10,
) -> list[Finding]:
    """Parse a Reddit JSON search response into Findings.

    Posts with ``score`` strictly below ``min_score`` are excluded.

    Expected shape::

        {
            "data": {
                "children": [
                    {
                        "data": {
                            "title": "...",
                            "url": "https://...",
                            "score": 500,
                            "selftext": "...",
                            "permalink": "/r/.../comments/..."
                        }
                    },
                    ...
                ]
            }
        }

    Args:
        data: Parsed JSON response from the Reddit API.
        min_score: Minimum score threshold (inclusive). Default 10.

    Returns:
        List of Findings with ``source="reddit"`` and
        ``channel="discourse"``.
    """
    findings: list[Finding] = []

    try:
        children = data["data"]["children"]
    except (KeyError, TypeError):
        return findings

    if not isinstance(children, list):
        return findings

    for child in children:
        if not isinstance(child, dict):
            continue
        post = child.get("data", {})
        if not isinstance(post, dict):
            continue

        score: int = post.get("score", 0) or 0
        if score < min_score:
            continue

        title: str = post.get("title", "")
        permalink: str = post.get("permalink", "")
        external_url: str = post.get("url", "")

        # Prefer external URL; fall back to reddit permalink
        if external_url and not external_url.startswith(
            ("https://www.reddit.com", "https://old.reddit.com", "/r/")
        ):
            url = external_url
        elif permalink:
            url = f"https://www.reddit.com{permalink}"
        else:
            url = external_url

        selftext: str = post.get("selftext", "") or ""
        relevance = round(min(0.3 + score / 2_000, 0.95), 4)
        summary = selftext[:200].strip() if selftext else f"{score} upvotes"

        findings.append(
            Finding(
                source="reddit",
                channel="discourse",
                title=title or url,
                url=url,
                relevance=relevance,
                summary=summary,
                metadata={"score": score, "permalink": permalink},
            )
        )

    return findings


# ---------------------------------------------------------------------------
# Tech blogs
# ---------------------------------------------------------------------------

_BLOG_DOMAINS = [
    "martinfowler.com",
    "blog.pragmaticengineer.com",
    "danluu.com",
    "jvns.ca",
    "rachelbythebay.com",
    "eli.thegreenplace.net",
    "brandur.org",
]


def build_blog_search_queries(topic: str, max_queries: int = 3) -> list[str]:
    """Build WebSearch queries targeting high-quality tech blogs.

    Each query uses a ``site:`` operator against a known domain so that
    only posts from that blog are returned.

    Args:
        topic: Free-text research topic.
        max_queries: Maximum number of query strings to return (default 3).

    Returns:
        List of query strings, each of the form
        ``"site:<domain> <topic>"``.
    """
    max_queries = max(1, min(max_queries, len(_BLOG_DOMAINS)))
    return [f"site:{domain} {topic}" for domain in _BLOG_DOMAINS[:max_queries]]


def _domain_from_url(url: str) -> str:
    """Extract the bare domain from a URL string."""
    match = re.search(r"https?://(?:www\.)?([^/]+)", url)
    if match:
        return match.group(1)
    return "blog"


def parse_blog_result(result: dict[str, Any]) -> Finding:
    """Parse a tech-blog WebSearch result dict into a Finding.

    The ``source`` field is set to the bare domain extracted from the
    URL (e.g. ``"danluu.com"``), or ``"blog"`` when the URL is absent.

    Args:
        result: Dict with ``title``, ``url``, and optionally ``snippet``.

    Returns:
        A Finding with ``channel="discourse"``.
    """
    url: str = result.get("url", "")
    title: str = result.get("title", url or "blog result")
    snippet: str = result.get("snippet", result.get("description", ""))
    source = _domain_from_url(url) if url else "blog"

    return Finding(
        source=source,
        channel="discourse",
        title=title,
        url=url,
        relevance=_BLOG_BASE_RELEVANCE,
        summary=snippet or title,
        metadata={"domain": source},
    )
