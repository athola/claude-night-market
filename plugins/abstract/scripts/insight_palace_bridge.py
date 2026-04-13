"""Bridge between the insight engine and memory palace.

Converts Finding objects into palace staging entries and
queries the palace index for historical insight data.
All memory-palace imports are guarded so the abstract
plugin works independently when memory-palace is absent.
"""

from __future__ import annotations

import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from insight_types import Finding, finding_hash

# ---------------------------------------------------------------------------
# Memory-palace shared module imports (soft dependency)
# ---------------------------------------------------------------------------
_palace_hooks = (
    Path(__file__).resolve().parents[2] / "memory-palace" / "hooks" / "shared"
)
if _palace_hooks.is_dir() and str(_palace_hooks) not in sys.path:
    sys.path.insert(0, str(_palace_hooks))

try:
    from deduplication import (  # type: ignore[import-not-found]  # cross-plugin soft dep via sys.path
        _load_index,
        get_content_hash,
        is_known,
        update_index,
    )

    _HAS_PALACE = True
except ImportError:
    _HAS_PALACE = False

# Palace staging directory
_PALACE_STAGING = (
    Path(__file__).resolve().parents[2] / "memory-palace" / "data" / "staging"
)

# Severity-to-score mapping (from project brief)
_SEVERITY_SCORES: dict[str, int] = {
    "high": 75,
    "medium": 55,
    "low": 35,
    "info": 20,
}


def score_finding(finding: Finding) -> int:
    """Compute palace importance score for a finding.

    Base score from severity mapping, plus bonuses:
    +10 if related_files is non-empty, +5 if skill is
    non-empty. Capped at 100.
    """
    base = _SEVERITY_SCORES.get(finding.severity, 0)
    bonus = 0
    if finding.related_files:
        bonus += 10
    if finding.skill:
        bonus += 5
    return min(base + bonus, 100)


def finding_to_markdown(finding: Finding) -> str:
    """Convert a Finding to markdown with YAML frontmatter.

    The frontmatter includes source, type, severity, skill,
    and hash for palace indexing and search.
    """
    fhash = finding_hash(finding)
    score = score_finding(finding)
    lines: list[str] = []

    # YAML frontmatter
    lines.append("---")
    lines.append("source: insight-engine")
    lines.append(f"finding_type: {finding.type}")
    lines.append(f"severity: {finding.severity}")
    if finding.skill:
        lines.append(f'skill: "{finding.skill}"')
    lines.append(f'finding_hash: "{fhash}"')
    lines.append(f"importance_score: {score}")
    lines.append("---")
    lines.append("")

    # Title
    lines.append(f"# {finding.title()}")
    lines.append("")

    # Body
    lines.append("## Finding")
    lines.append("")
    lines.append(finding.summary)
    lines.append("")
    lines.append("## Evidence")
    lines.append("")
    lines.append(finding.evidence)
    lines.append("")
    lines.append("## Recommended Action")
    lines.append("")
    lines.append(finding.recommendation)
    lines.append("")

    if finding.related_files:
        lines.append("## Related Files")
        lines.append("")
        for f in finding.related_files:
            lines.append(f"- `{f}`")
        lines.append("")

    return "\n".join(lines)


def _slugify(text: str) -> str:
    """Simple slug: lowercase, replace non-alnum with dash."""
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:60]


def ingest_findings(
    findings: list[Finding],
    budget_remaining: float | None = None,
) -> int:
    """Write findings as palace staging entries.

    Returns the number of findings successfully ingested.
    Skips silently if memory-palace is not available.
    """
    if not _HAS_PALACE or not findings:
        return 0

    if budget_remaining is not None and budget_remaining < 1.0:
        return 0

    _PALACE_STAGING.mkdir(parents=True, exist_ok=True)
    ingested = 0

    for finding in findings[:10]:  # Cap at 10 per session
        fhash = finding_hash(finding)
        key = f"insight://{fhash}"

        if is_known(url=key):
            continue

        try:
            content = finding_to_markdown(finding)
            content_hash = get_content_hash(content)
            score = score_finding(finding)

            # Build filename
            date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            skill_slug = _slugify(finding.skill) if finding.skill else "cross-cutting"
            type_slug = _slugify(finding.type)
            filename = f"insight-{type_slug}-{skill_slug}-{date_str}.md"
            filepath = _PALACE_STAGING / filename

            filepath.write_text(content, encoding="utf-8")

            update_index(
                content_hash=content_hash,
                stored_at=f"data/staging/{filename}",
                importance_score=score,
                url=key,
                title=finding.title(),
                maturity="seedling",
                routing_type="meta",
            )
            ingested += 1
        except Exception as exc:
            print(
                f"insight_palace_bridge: ingest failed: {type(exc).__name__}: {exc}",
                file=sys.stderr,
            )

    return ingested


def query_palace_insights() -> list[dict[str, Any]]:
    """Query palace index for historical insight entries.

    Returns metadata dicts for entries keyed with
    ``insight://``. Returns empty list if palace is
    unavailable.
    """
    if not _HAS_PALACE:
        return []

    try:
        index = _load_index()
        entries = index.get("entries", {})
        results: list[dict[str, Any]] = []

        for key, entry in entries.items():
            if not isinstance(key, str) or not key.startswith("insight://"):
                continue
            results.append(
                {
                    "key": key,
                    "title": entry.get("title", ""),
                    "importance_score": entry.get("importance_score", 0),
                    "last_updated": entry.get("last_updated", ""),
                    "maturity": entry.get("maturity", "seedling"),
                    "finding_type": entry.get("finding_type", ""),
                    "severity": entry.get("severity", ""),
                    "skill": entry.get("skill", ""),
                }
            )

        return results
    except Exception:
        return []
