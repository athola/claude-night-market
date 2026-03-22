"""GitHub code search channel: query builders and response parsers.

These functions do NOT make HTTP calls. They prepare query strings and
URLs for WebSearch/WebFetch tool calls, and parse the results those
tools return into Finding objects.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote_plus

from tome.models import Finding

# ---------------------------------------------------------------------------
# Query builders
# ---------------------------------------------------------------------------

_SEARCH_SUFFIXES = ["implementation", "library", "example"]


def build_github_search_queries(topic: str, max_queries: int = 3) -> list[str]:
    """Build GitHub-targeted WebSearch query strings.

    Returns up to ``max_queries`` query strings. Each targets GitHub via
    ``site:github.com`` or a stars filter so results stay within the
    GitHub domain.

    Args:
        topic: Free-text research topic.
        max_queries: Maximum number of query strings to return (1-5).

    Returns:
        List of query strings ready to pass to a WebSearch tool call.
    """
    max_queries = max(1, min(max_queries, 5))
    candidates: list[str] = []

    for suffix in _SEARCH_SUFFIXES:
        candidates.append(f"site:github.com {topic} {suffix}")

    # Stars filter as a non-site: alternative for variety
    candidates.append(f"{topic} github stars:>100")
    # Exact repo search phrasing
    candidates.append(f"site:github.com {topic}")

    return candidates[:max_queries]


def build_github_api_search(topic: str) -> str:
    """Build a GitHub REST API repository search URL.

    Args:
        topic: Free-text research topic.

    Returns:
        URL string for the GitHub search/repositories endpoint,
        sorted by stars descending.
    """
    encoded = quote_plus(topic)
    return f"https://api.github.com/search/repositories?q={encoded}&sort=stars&order=desc&per_page=10"


# ---------------------------------------------------------------------------
# Response parsers
# ---------------------------------------------------------------------------


def _extract_repo_name(url: str) -> str:
    """Extract 'owner/repo' from a GitHub URL, falling back to the URL."""
    match = re.search(r"github\.com/([^/]+/[^/?#]+)", url)
    if match:
        return match.group(1).rstrip("/")
    return url


def _estimate_relevance(title: str, topic: str) -> float:
    """Score title relevance to topic on [0.1, 0.95] by keyword overlap."""
    topic_words = set(topic.lower().split())
    title_words = set(title.lower().split())
    if not topic_words:
        return 0.5
    overlap = len(topic_words & title_words) / len(topic_words)
    # Map to [0.1, 0.95] so we never emit 0.0 or 1.0 from pure heuristics
    return round(0.1 + overlap * 0.85, 4)


def parse_github_result(result: dict[str, Any]) -> Finding:
    """Parse a single WebSearch result dict into a GitHub Finding.

    The result dict is expected to have the keys that WebSearch returns:
    ``title``, ``url``, and one of ``snippet`` or ``description``.
    Missing keys are handled gracefully.

    Args:
        result: Dict with ``title``, ``url``, and optionally
            ``snippet``/``description``.

    Returns:
        A Finding with ``source="github"`` and ``channel="code"``.
    """
    url: str = result.get("url", "")
    title: str = result.get("title", "")
    snippet: str = result.get("snippet", result.get("description", ""))
    repo_name = _extract_repo_name(url) if url else ""
    display_title = title or repo_name or url
    topic_guess = repo_name.replace("/", " ").replace("-", " ").replace("_", " ")
    relevance = _estimate_relevance(display_title, topic_guess) if topic_guess else 0.5

    summary: str
    if snippet:
        summary = snippet
    elif repo_name:
        summary = f"GitHub repository: {repo_name}"
    else:
        summary = url or "GitHub result"

    return Finding(
        source="github",
        channel="code",
        title=display_title,
        url=url,
        relevance=relevance,
        summary=summary,
        metadata={"repo_name": repo_name} if repo_name else {},
    )


def parse_github_api_response(data: dict[str, Any], topic: str) -> list[Finding]:
    """Parse a GitHub REST API search/repositories response.

    Expected shape::

        {
            "items": [
                {
                    "full_name": "owner/repo",
                    "html_url": "https://github.com/owner/repo",
                    "stargazers_count": 1234,
                    "description": "...",
                    "language": "Python",
                    "updated_at": "2024-01-15T12:00:00Z"
                },
                ...
            ]
        }

    Args:
        data: Parsed JSON response from the GitHub API.
        topic: Original research topic used to score relevance.

    Returns:
        List of Findings, one per repository item. Items with missing
        ``html_url`` are skipped.
    """
    findings: list[Finding] = []
    items = data.get("items", [])
    if not isinstance(items, list):
        return findings

    for item in items:
        if not isinstance(item, dict):
            continue
        url: str = item.get("html_url", "")
        if not url:
            continue

        full_name: str = item.get("full_name", _extract_repo_name(url))
        description: str = item.get("description") or ""
        stars: int = item.get("stargazers_count", 0) or 0
        language: str | None = item.get("language")
        updated_at: str | None = item.get("updated_at")

        # Relevance: keyword overlap + star bonus (capped at 0.95)
        base_relevance = _estimate_relevance(full_name + " " + description, topic)
        star_bonus = min(stars / 50_000, 0.15)
        relevance = round(min(base_relevance + star_bonus, 0.95), 4)

        summary_parts = (
            [description] if description else [f"GitHub repository: {full_name}"]
        )
        if stars:
            summary_parts.append(f"{stars:,} stars")
        if language:
            summary_parts.append(language)

        metadata: dict[str, Any] = {
            "repo_name": full_name,
            "stars": stars,
        }
        if language:
            metadata["language"] = language
        if updated_at:
            metadata["updated_at"] = updated_at

        findings.append(
            Finding(
                source="github",
                channel="code",
                title=full_name,
                url=url,
                relevance=relevance,
                summary=". ".join(summary_parts),
                metadata=metadata,
            )
        )

    return findings


# ---------------------------------------------------------------------------
# Ranking
# ---------------------------------------------------------------------------


def _parse_updated_at(value: str | None) -> datetime:
    """Parse ISO 8601 datetime string, returning epoch on failure."""
    if not value:
        return datetime(1970, 1, 1, tzinfo=timezone.utc)  # noqa: UP017
    try:
        # GitHub uses Z suffix; fromisoformat requires +00:00 in Python 3.9
        normalised = value.replace("Z", "+00:00")
        return datetime.fromisoformat(normalised)
    except ValueError:
        return datetime(1970, 1, 1, tzinfo=timezone.utc)  # noqa: UP017


def rank_github_findings(findings: list[Finding]) -> list[Finding]:
    """Rank GitHub findings using the shared relevance scorer plus recency.

    Delegates authority scoring to ``synthesis.ranker.compute_relevance_score``
    and blends with a recency factor based on ``updated_at`` metadata.

    Score formula::

        score = compute_relevance_score(f) * 0.8 + recency * 0.2

    where ``recency`` decays from 1.0 (updated today) toward 0.0 for
    repos last updated 5+ years ago.

    Args:
        findings: Unordered list of GitHub Findings.

    Returns:
        New list sorted descending by composite score. The input list
        is not mutated.
    """
    from tome.synthesis.ranker import compute_relevance_score  # noqa: PLC0415

    now = datetime.now(tz=timezone.utc)  # noqa: UP017

    def _score(f: Finding) -> float:
        updated_at = _parse_updated_at(f.metadata.get("updated_at"))
        age_days = max((now - updated_at).days, 0)
        recency = max(1.0 - age_days / (5 * 365), 0.0)
        return compute_relevance_score(f) * 0.8 + recency * 0.2

    return sorted(findings, key=_score, reverse=True)
