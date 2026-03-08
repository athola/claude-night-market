"""Convention harvester: extract review patterns from PR comments.

Reads human review comments, classifies them against known
convention patterns, and writes suggestions that can be
promoted to the codex.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ConventionSuggestion:
    """A suggested convention extracted from review comments."""

    pattern_id: str
    description: str
    evidence: str
    source_prs: list[int] = field(default_factory=list)
    occurrence_count: int = 1
    proposed_codex_id: str | None = None
    promoted: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {
            "pattern_id": self.pattern_id,
            "description": self.description,
            "evidence": self.evidence,
            "source_prs": self.source_prs,
            "occurrence_count": self.occurrence_count,
            "proposed_codex_id": self.proposed_codex_id,
            "promoted": self.promoted,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ConventionSuggestion:
        """Deserialize from dict."""
        return cls(
            pattern_id=data["pattern_id"],
            description=data.get("description", ""),
            evidence=data.get("evidence", ""),
            source_prs=data.get("source_prs", []),
            occurrence_count=data.get("occurrence_count", 1),
            proposed_codex_id=data.get("proposed_codex_id"),
            promoted=data.get("promoted", False),
        )


# ── Pattern definitions ─────────────────────────────────

# Each pattern: (id, description, trigger_regex)
# Trigger regex matches human review comments that indicate
# the convention. Agent responses (starting with "Fixed in")
# are filtered out before matching.

_PATTERNS: list[tuple[str, str, re.Pattern[str]]] = [
    (
        "import-discipline",
        "All imports must be at module top level",
        re.compile(
            r"(do not |don.t |never )import outside|"
            r"import.*(top.?level|outside of top)",
            re.IGNORECASE,
        ),
    ),
    (
        "destructive-git",
        "No git checkout, reset --hard, or unguarded stash",
        re.compile(
            r"(never|do not|don.t).*(git checkout|git reset|"
            r"destructive)|avoid.*(git checkout)",
            re.IGNORECASE,
        ),
    ),
    (
        "no-suppression",
        "Fix lint issues instead of suppressing with noqa",
        re.compile(
            r"(instead of|not|don.t).*(noqa|ignoring|suppress)|"
            r"fix.*(instead of|rather than).*(noqa|ignor)",
            re.IGNORECASE,
        ),
    ),
    (
        "consolidate-docs",
        "Consolidate into existing docs rather than adding new files",
        re.compile(
            r"consolidate.*(?:into|with).*(?:existing|docs)|"
            r"remove.*consolidate",
            re.IGNORECASE,
        ),
    ),
    (
        "no-artifacts",
        "Ephemeral planning artifacts must not be committed",
        re.compile(
            r"(artifact|ephemeral|planning.doc).*(gitignore|"
            r"remove|not.commit)|make sure.*(gitignored)",
            re.IGNORECASE,
        ),
    ),
]

# Agent response filter: lines starting with common agent
# response patterns (commit hash references, "Fixed in", etc.)
_AGENT_RESPONSE = re.compile(
    r"^(Fixed in [0-9a-f]|Applied|Moved all|Replaced|Lowered|"
    r"Added|Changed|Removed|Updated|Set |Also )",
)

# Codex ID mapping for known patterns
_CODEX_MAP: dict[str, str] = {
    "import-discipline": "C1",
    "no-artifacts": "C2",
    "destructive-git": "C3",
    "no-suppression": "C4",
    "consolidate-docs": "C5",
}


def map_to_codex_id(pattern_id: str) -> str | None:
    """Map a pattern ID to an existing codex convention ID."""
    return _CODEX_MAP.get(pattern_id)


def _is_agent_response(body: str) -> bool:
    """Check if a comment is an automated agent response."""
    return bool(_AGENT_RESPONSE.match(body.strip()))


def extract_patterns(
    comments: list[dict[str, Any]],
) -> list[ConventionSuggestion]:
    """Extract convention patterns from PR review comments.

    Filters out agent responses, then matches remaining
    human comments against known pattern triggers.
    Deduplicates by pattern_id, merging occurrence counts.
    """
    # Filter out agent responses
    human_comments = [
        c for c in comments if not _is_agent_response(c.get("body", ""))
    ]

    # Match against patterns
    found: dict[str, ConventionSuggestion] = {}

    for comment in human_comments:
        body = comment.get("body", "")
        if not body:
            continue

        for pattern_id, description, regex in _PATTERNS:
            if regex.search(body):
                if pattern_id in found:
                    found[pattern_id].occurrence_count += 1
                else:
                    found[pattern_id] = ConventionSuggestion(
                        pattern_id=pattern_id,
                        description=description,
                        evidence=body[:200],
                        proposed_codex_id=map_to_codex_id(pattern_id),
                        occurrence_count=1,
                    )

    return list(found.values())


def save_suggestions(
    suggestions: list[ConventionSuggestion],
    path: Path,
) -> None:
    """Save suggestions to a JSON file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = [s.to_dict() for s in suggestions]
    path.write_text(json.dumps(data, indent=2))


def load_suggestions(path: Path) -> list[ConventionSuggestion]:
    """Load suggestions from a JSON file.

    Returns empty list if file doesn't exist.
    """
    path = Path(path)
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text())
        return [ConventionSuggestion.from_dict(d) for d in data]
    except (json.JSONDecodeError, KeyError):
        return []


def merge_suggestion(
    new: ConventionSuggestion,
    path: Path,
) -> None:
    """Merge a suggestion into an existing suggestions file.

    If the pattern_id already exists, increments the count
    and adds any new source PRs. Otherwise appends.
    """
    existing = load_suggestions(path)

    for s in existing:
        if s.pattern_id == new.pattern_id:
            s.occurrence_count += new.occurrence_count
            new_prs = set(new.source_prs) - set(s.source_prs)
            s.source_prs.extend(sorted(new_prs))
            save_suggestions(existing, path)
            return

    existing.append(new)
    save_suggestions(existing, path)
