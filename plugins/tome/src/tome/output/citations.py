"""Format individual findings as citations and produce bibliographies."""

from __future__ import annotations

import re
from urllib.parse import parse_qsl, urlencode, urlsplit

from tome.models import Finding

# Stops at whitespace, brackets, quotes and markdown emphasis (backtick,
# asterisk). Parentheses are allowed, because a URL can hold a balanced
# pair (`Foo_(bar)`); `_trim_url` drops an unbalanced closing one.
_URL_PATTERN = re.compile(r"https?://[^\s<>\[\]\"'`*]+", re.IGNORECASE)

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

    Host is case-insensitive and a ``www.`` prefix names the same site.
    ``http`` and ``https`` serve the same document, a fragment never
    selects a different one, a trailing slash is stylistic, and query
    parameter order carries no meaning. A URL too malformed to split is
    compared as written, so one bad finding cannot abort the check.
    """
    try:
        parts = urlsplit(url)
    except ValueError:
        return url
    host = parts.netloc.lower()
    host = host[4:] if host.startswith("www.") else host
    path = parts.path.rstrip("/")
    params = sorted(parse_qsl(parts.query, keep_blank_values=True))
    query = f"?{urlencode(params)}" if params else ""
    return f"{host}{path}{query}"


def _trim_url(url: str) -> str:
    """Drop sentence punctuation and a `)` that closes a markdown link."""
    while True:
        trimmed = url.rstrip(".,;:!?")
        if trimmed.endswith(")") and trimmed.count("(") < trimmed.count(")"):
            trimmed = trimmed[:-1]
        if trimmed == url:
            return url
        url = trimmed


def _urls_in(text: str) -> list[str]:
    return [_trim_url(match.group()) for match in _URL_PATTERN.finditer(text)]


def find_ungrounded_urls(report_text: str, findings: list[Finding]) -> list[str]:
    """Return URLs cited in ``report_text`` that no finding carries.

    A model editing a report can write a plausible URL it never
    retrieved. Checking every cited URL against the session's findings
    catches that without a model call, the same way a SQL answer is
    rejected for naming a table no earlier retrieve showed.

    URLs come back as written, once each, in first-appearance order.
    """
    # A URL a finding's summary quotes was retrieved with that finding.
    grounded = {_normalize_url(f.url) for f in findings}
    grounded.update(_normalize_url(u) for f in findings for u in _urls_in(f.summary))
    ungrounded: dict[str, str] = {}
    for url in _urls_in(report_text):
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
