"""Review scout: learn PR review techniques from exemplar projects.

Reads contributing guidelines and PR review culture from
well-maintained open-source projects, extracts actionable
techniques, and formats them for posting to GitHub Discussions.
"""

from __future__ import annotations

import base64
import json
import re
import subprocess
from dataclasses import dataclass


@dataclass
class ExemplarProject:
    """A well-maintained project to study."""

    owner: str
    repo: str
    language: str
    why: str = ""

    @property
    def full_name(self) -> str:
        """Return owner/repo format."""
        return f"{self.owner}/{self.repo}"


@dataclass
class ReviewTechnique:
    """A concrete review technique extracted from an exemplar."""

    description: str
    category: str
    source: str
    confidence: float = 0.5
    raw_text: str = ""


def default_exemplars() -> list[ExemplarProject]:
    """Curated list of projects known for strong review culture."""
    return [
        ExemplarProject(
            owner="astral-sh",
            repo="ruff",
            language="python",
            why="Python linter; strict CI and review standards",
        ),
        ExemplarProject(
            owner="pydantic",
            repo="pydantic",
            language="python",
            why="Data validation; thorough type checking culture",
        ),
        ExemplarProject(
            owner="encode",
            repo="httpx",
            language="python",
            why="HTTP client; clean review process, good PR templates",
        ),
        ExemplarProject(
            owner="tiangolo",
            repo="fastapi",
            language="python",
            why="Web framework; strong contributing guidelines",
        ),
        ExemplarProject(
            owner="python-poetry",
            repo="poetry",
            language="python",
            why="Package manager; strict changelog and test culture",
        ),
        ExemplarProject(
            owner="pallets",
            repo="flask",
            language="python",
            why="Web microframework; mature review process",
        ),
        ExemplarProject(
            owner="psf",
            repo="requests",
            language="python",
            why="HTTP library; well-established contribution norms",
        ),
    ]


# ── Parsing contributing guidelines ─────────────────────

# Section header patterns
_SECTION_PATTERNS: dict[str, re.Pattern[str]] = {
    "review": re.compile(
        r"^#{1,3}\s.*(review|pull request|pr process|merge"
        r"|approval|code quality)",
        re.IGNORECASE | re.MULTILINE,
    ),
    "style": re.compile(
        r"^#{1,3}\s.*(style|format|lint|coding standard"
        r"|conventions|type hint)",
        re.IGNORECASE | re.MULTILINE,
    ),
    "testing": re.compile(
        r"^#{1,3}\s.*(test|coverage|ci|continuous)",
        re.IGNORECASE | re.MULTILINE,
    ),
    "docs": re.compile(
        r"^#{1,3}\s.*(doc|changelog|release note)",
        re.IGNORECASE | re.MULTILINE,
    ),
}

_CHECKLIST_ITEM = re.compile(r"^[-*]\s*(?:\[.\]\s*)?(.+)$", re.MULTILINE)
_NUMBERED_ITEM = re.compile(r"^\d+\.\s+(.+)$", re.MULTILINE)

_MIN_ITEM_LENGTH = 10


def _extract_items_from_section(text: str) -> list[str]:
    """Extract list items from a markdown section."""
    items: list[str] = []
    for match in _CHECKLIST_ITEM.finditer(text):
        item = match.group(1).strip()
        if len(item) >= _MIN_ITEM_LENGTH:
            items.append(item)
    for match in _NUMBERED_ITEM.finditer(text):
        item = match.group(1).strip()
        if len(item) > _MIN_ITEM_LENGTH and item not in items:
            items.append(item)
    return items


def parse_contributing_guide(
    content: str,
) -> dict[str, list[str]]:
    """Parse a CONTRIBUTING.md into categorized sections.

    Returns a dict mapping section types (review, style,
    testing, docs) to lists of extracted items.
    """
    if not content.strip():
        return {}

    sections: dict[str, list[str]] = {}

    for section_type, pattern in _SECTION_PATTERNS.items():
        match = pattern.search(content)
        if not match:
            continue

        # Extract text from this header to the next header
        start = match.end()
        next_header = re.search(r"^#{1,3}\s", content[start:], re.MULTILINE)
        if next_header:
            section_text = content[start : start + next_header.start()]
        else:
            section_text = content[start:]

        items = _extract_items_from_section(section_text)
        if items:
            sections[section_type] = items

    return sections


# ── Technique classification ────────────────────────────

_CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "testing": [
        "test",
        "coverage",
        "pytest",
        "unittest",
        "ci",
        "continuous integration",
        "tox",
        "nox",
    ],
    "linting": [
        "lint",
        "ruff",
        "flake8",
        "pylint",
        "mypy",
        "type check",
        "black",
        "isort",
        "format",
    ],
    "documentation": [
        "doc",
        "changelog",
        "readme",
        "docstring",
        "release note",
        "comment",
    ],
    "style": [
        "style",
        "convention",
        "naming",
        "import",
        "line length",
        "pep",
        "type hint",
    ],
    "security": [
        "security",
        "vulnerability",
        "cve",
        "secret",
        "credential",
        "auth",
    ],
}


def classify_technique(description: str) -> str:
    """Classify a review technique into a category."""
    lower = description.lower()
    scores: dict[str, int] = {}

    for category, keywords in _CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in lower)
        if score > 0:
            scores[category] = score

    if not scores:
        return "general"

    return max(scores, key=scores.get)


def extract_techniques_from_guidelines(
    sections: dict[str, list[str]],
    source: str,
) -> list[ReviewTechnique]:
    """Convert parsed guideline sections into techniques."""
    techniques: list[ReviewTechnique] = []

    for section_type, items in sections.items():
        for item in items:
            category = classify_technique(item)
            techniques.append(
                ReviewTechnique(
                    description=item,
                    category=category,
                    source=source,
                    confidence=0.7 if section_type == "review" else 0.5,
                    raw_text=item,
                )
            )

    return techniques


# ── GitHub Discussion formatting ────────────────────────


def format_discussion_body(
    techniques: list[ReviewTechnique],
) -> str:
    """Format techniques as a GitHub Discussion body.

    Groups by category, credits sources, and includes
    a note about human oversight.
    """
    if not techniques:
        return (
            "No new review techniques found in this scan.\n\n"
            "The exemplar projects examined did not yield "
            "actionable techniques beyond what we already use."
        )

    # Group by category
    by_category: dict[str, list[ReviewTechnique]] = {}
    for t in techniques:
        by_category.setdefault(t.category, []).append(t)

    lines: list[str] = []
    lines.append(
        "Review techniques discovered by scanning exemplar "
        "open-source projects. Each technique is extracted "
        "from contributing guidelines, PR templates, or "
        "review practices of well-maintained repositories."
    )
    lines.append("")
    lines.append(
        "> **Human oversight required.** These are suggestions "
        "for review. Evaluate each technique for applicability "
        "to our codebase before adopting."
    )
    lines.append("")

    for category in sorted(by_category):
        lines.append(f"## {category.title()}")
        lines.append("")
        for t in by_category[category]:
            lines.append(f"- {t.description}")
            lines.append(f"  *Source: {t.source}*")
        lines.append("")

    # Source summary
    sources = sorted({t.source for t in techniques})
    lines.append("## Sources")
    lines.append("")
    for s in sources:
        lines.append(f"- [{s}](https://github.com/{s})")
    lines.append("")

    return "\n".join(lines)


# ── GitHub Discussion posting ───────────────────────────


_GH_CLI = "gh"


def fetch_contributing_guide(
    owner: str,
    repo: str,
) -> str | None:
    """Fetch CONTRIBUTING.md from a GitHub repo via gh api."""
    try:
        result = subprocess.run(
            [
                _GH_CLI,
                "api",
                f"repos/{owner}/{repo}/contents/CONTRIBUTING.md",
                "--jq",
                ".content",
            ],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        if result.returncode != 0:
            return None
        content = base64.b64decode(result.stdout.strip()).decode(
            "utf-8", errors="replace"
        )
        return content
    except (subprocess.TimeoutExpired, OSError, ValueError):
        return None


def post_discussion(
    title: str,
    body: str,
    category_id: str,
    repo_owner: str,
    repo_name: str,
) -> str | None:
    """Post a GitHub Discussion via GraphQL.

    Returns the discussion URL on success, None on failure.
    """
    repo_query = (
        f'{{ repository(owner: "{repo_owner}", name: "{repo_name}") {{ id }} }}'
    )
    try:
        result = subprocess.run(
            [_GH_CLI, "api", "graphql", "-f", f"query={repo_query}"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        if result.returncode != 0:
            return None

        repo_data = json.loads(result.stdout)
        repo_id = repo_data["data"]["repository"]["id"]
    except (subprocess.TimeoutExpired, OSError, KeyError):
        return None

    # Escape body for inline GraphQL string literal
    escaped_body = (
        body.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "\\r")
    )
    escaped_title = (
        title.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "\\r")
    )

    mutation = (
        "mutation {"
        "  createDiscussion(input: {"
        f'    repositoryId: "{repo_id}",'
        f'    categoryId: "{category_id}",'
        f'    title: "{escaped_title}",'
        f'    body: "{escaped_body}"'
        "  }) {"
        "    discussion { url }"
        "  }"
        "}"
    )

    try:
        result = subprocess.run(
            [_GH_CLI, "api", "graphql", "-f", f"query={mutation}"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        if result.returncode != 0:
            return None

        data = json.loads(result.stdout)
        url: str = data["data"]["createDiscussion"]["discussion"]["url"]
        return url
    except (subprocess.TimeoutExpired, OSError, KeyError):
        return None


def run_scout(
    exemplars: list[ExemplarProject] | None = None,
    post_to_discussions: bool = True,
    category_id: str = "DIC_kwDOQbN88M4C2zJv",  # Knowledge
    repo_owner: str = "athola",
    repo_name: str = "claude-night-market",
) -> list[ReviewTechnique]:
    """Run the full scout pipeline.

    1. Iterate through exemplar projects
    2. Fetch their contributing guides
    3. Extract review techniques
    4. Post findings to GitHub Discussions

    Returns all discovered techniques.
    """
    if exemplars is None:
        exemplars = default_exemplars()

    all_techniques: list[ReviewTechnique] = []

    for exemplar in exemplars:
        content = fetch_contributing_guide(exemplar.owner, exemplar.repo)
        if content is None:
            continue

        sections = parse_contributing_guide(content)
        techniques = extract_techniques_from_guidelines(
            sections, source=exemplar.full_name
        )
        all_techniques.extend(techniques)

    if post_to_discussions and all_techniques:
        title = "[egregore:scout] Review techniques from exemplar projects"
        body = format_discussion_body(all_techniques)
        post_discussion(title, body, category_id, repo_owner, repo_name)

    return all_techniques
