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
import sys
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
    category: str | None
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
        if len(item) >= _MIN_ITEM_LENGTH and item not in items:
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


def classify_technique(description: str) -> str | None:
    """Classify a review technique into a category, or None when no keywords match."""
    lower = description.lower()
    scores: dict[str, int] = {}

    for category, keywords in _CATEGORY_KEYWORDS.items():
        # Anchor each keyword at a word start, so "ci" does not match inside
        # "special" while "test" still matches "tests".
        score = sum(1 for kw in keywords if re.search(rf"\b{re.escape(kw)}", lower))
        if score > 0:
            scores[category] = score

    if not scores:
        return None

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
    by_category: dict[str | None, list[ReviewTechnique]] = {}
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

    # classify_technique returns None when no keyword matches; list those
    # last under their own heading.
    for category in sorted(by_category, key=lambda c: (c is None, c or "")):
        heading = category.title() if category else "Uncategorized"
        lines.append(f"## {heading}")
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
_DEFAULT_DISCUSSION_CATEGORY_ID = "DIC_kwDOQbN88M4C2zJv"  # Knowledge
_DEFAULT_REPO_OWNER = "athola"
_DEFAULT_REPO_NAME = "claude-night-market"


def fetch_contributing_guide(
    owner: str,
    repo: str,
) -> str | None:
    """Fetch CONTRIBUTING.md from a GitHub repo via gh api.

    Returns None when the guide cannot be read. A 404 means the repo has
    no guide and is expected; any other failure is written to stderr,
    because an unauthenticated or rate-limited ``gh`` otherwise looks
    identical to a repo without a guide.
    """
    context = f"fetching CONTRIBUTING.md from {owner}/{repo}"
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
            if "HTTP 404" not in result.stderr:
                _report(context, result.stderr)
            return None
        content = base64.b64decode(result.stdout.strip()).decode(
            "utf-8", errors="replace"
        )
        return content
    except (subprocess.TimeoutExpired, OSError, ValueError) as exc:
        _report(context, exc)
        return None


def _report(context: str, detail: object) -> None:
    """Write a failed ``gh`` call to stderr, where an operator sees it."""
    print(f"scout: {context} failed: {str(detail).strip()}", file=sys.stderr)


def post_discussion(
    title: str,
    body: str,
    category_id: str,
    repo_owner: str,
    repo_name: str,
) -> str | None:
    """Post a GitHub Discussion via GraphQL.

    Returns the discussion URL on success, None on failure, with the
    reason written to stderr.
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
            _report("looking up the repository id", result.stderr)
            return None

        repo_data = json.loads(result.stdout)
        repo_id = repo_data["data"]["repository"]["id"]
    except (subprocess.TimeoutExpired, OSError, KeyError) as exc:
        _report("looking up the repository id", exc)
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
            _report("creating the discussion", result.stderr)
            return None

        data = json.loads(result.stdout)
        url: str = data["data"]["createDiscussion"]["discussion"]["url"]
        return url
    except (subprocess.TimeoutExpired, OSError, KeyError) as exc:
        _report("creating the discussion", exc)
        return None


def run_scout(
    exemplars: list[ExemplarProject] | None = None,
    post_to_discussions: bool = True,
    category_id: str = _DEFAULT_DISCUSSION_CATEGORY_ID,
    repo_owner: str = _DEFAULT_REPO_OWNER,
    repo_name: str = _DEFAULT_REPO_NAME,
) -> list[ReviewTechnique]:
    """Run the full scout pipeline.

    1. Iterate through exemplar projects
    2. Fetch their contributing guides
    3. Extract review techniques
    4. Post findings to GitHub Discussions

    Returns all discovered techniques. Raises ``RuntimeError`` when
    posting was requested and failed, so a caller's exit status says the
    findings went nowhere.
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
        if post_discussion(title, body, category_id, repo_owner, repo_name) is None:
            raise RuntimeError(
                f"posting the scout Discussion to {repo_owner}/{repo_name} "
                "failed; the reason is on stderr"
            )

    return all_techniques
