"""Format individual findings as citations and produce bibliographies."""

from __future__ import annotations

from tome.models import Finding

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
}


def format_citation(finding: Finding) -> str:
    """Format a single finding as a citation string.

    Academic: Author(s). "Title". Venue, Year. URL
    GitHub:   Owner/Repo. "Title". GitHub, Stars stars. URL
    Discourse: Username. "Title". Platform, Score points. URL
    """
    source = finding.source.lower()

    if source in ("arxiv", "academic"):
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


def generate_bibliography(findings: list[Finding]) -> str:
    """Generate a numbered bibliography from all findings."""
    if not findings:
        return ""
    lines: list[str] = []
    for i, finding in enumerate(findings, start=1):
        lines.append(f"[{i}] {format_citation(finding)}")
    return "\n".join(lines)
