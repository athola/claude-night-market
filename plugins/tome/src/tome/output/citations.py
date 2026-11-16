"""Format individual findings as citations and produce bibliographies."""

from __future__ import annotations

import re
from urllib.parse import urlsplit

from tome.models import Finding

# Stops at whitespace and the delimiters that close a markdown link or
# quote; trailing sentence punctuation is trimmed after the match.
_URL_PATTERN = re.compile(r"https?://[^\s<>()\[\]\"']+", re.IGNORECASE)

# Platform display names keyed by source identifier.
_PLATFORM_NAMES = {
    "hn": "Hacker News",
    "reddit": "Reddit",
    "lobsters": "Lobsters",
    "github": "GitHub",
    "arxiv": "arXiv",
    "academic": "Academic",
    "blog": "Blog",
    "triz": "TRIZ Journal",
    "web": "Web",
    "you-web": "You.com",
}


_ACADEMIC_SOURCES = frozenset(
    {"arxiv", "academic", "semantic_scholar", "semantic_scholar_chain", "openalex"}
)


def format_citation(finding: Finding) -> str:
    """Format a single finding as a citation string.

    Academic (arxiv, academic, semantic_scholar, openalex):
        Author(s). "Title". Venue, Year. URL
    GitHub: "Title". GitHub, Stars stars. URL
    Everything else (hn, reddit, lobsters, blog, web, you-web, triz):
        Username. "Title". Platform, Score points. URL
    """
    source = finding.source.lower()

    if source in _ACADEMIC_SOURCES:
        return _format_academic(finding)
    if source == "github":
        return _format_github(finding)
    return _format_discourse(finding)


def _format_academic(finding: Finding) -> str:
    meta = finding.metadata
    authors: list[str] = meta.get("authors", [])
    author_str = ", ".join(authors) if authors else "Unknown Author"
    year = meta.get("year", "n.d.")
    venue = meta.get("venue", "arXiv")
    doi = meta.get("doi")
    doi_part = f" DOI: {doi}." if doi else ""
    return f'{author_str}. "{finding.title}". {venue}, {year}.{doi_part} {finding.url}'


def _format_github(finding: Finding) -> str:
    meta = finding.metadata
    stars = meta.get("stars")
    stars_part = f", {stars} stars" if stars is not None else ""
    return f'"{finding.title}". GitHub{stars_part}. {finding.url}'


def _format_discourse(finding: Finding) -> str:
    meta = finding.metadata
    platform = _PLATFORM_NAMES.get(finding.source.lower(), finding.source)
    score = meta.get("score")
    score_part = f", {score} points" if score is not None else ""
    username = meta.get("username", "")
    author_part = f"{username}. " if username else ""
    return f'{author_part}"{finding.title}". {platform}{score_part}. {finding.url}'


def _normalize_url(url: str) -> str:
    """Reduce formatting-only differences so equal sources compare equal.

    Scheme and host are case-insensitive, a fragment never selects a
    different document, and a trailing slash is stylistic.
    """
    parts = urlsplit(url)
    path = parts.path.rstrip("/")
    query = f"?{parts.query}" if parts.query else ""
    return f"{parts.scheme.lower()}://{parts.netloc.lower()}{path}{query}"


def find_ungrounded_urls(report_text: str, findings: list[Finding]) -> list[str]:
    """Return URLs cited in ``report_text`` that no finding carries.

    A model editing a report can write a plausible URL it never
    retrieved. Checking every cited URL against the session's findings
    catches that without a model call, the same way a SQL answer is
    rejected for naming a table no earlier retrieve showed.

    URLs come back as written, once each, in first-appearance order.
    """
    grounded = {_normalize_url(f.url) for f in findings}
    ungrounded: dict[str, str] = {}
    for match in _URL_PATTERN.finditer(report_text):
        url = match.group().rstrip(".,;:!?")
        key = _normalize_url(url)
        if key not in grounded and key not in ungrounded:
            ungrounded[key] = url
    return list(ungrounded.values())


def generate_bibliography(findings: list[Finding]) -> str:
    """Generate a numbered bibliography from all findings."""
    if not findings:
        return ""
    lines: list[str] = []
    for i, finding in enumerate(findings, start=1):
        lines.append(f"[{i}] {format_citation(finding)}")
    return "\n".join(lines)
