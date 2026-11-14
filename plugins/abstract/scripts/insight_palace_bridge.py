"""Bridge between the insight engine and memory palace.

Converts Finding objects into palace staging entries and
queries the palace index for historical insight data.
All memory-palace imports are guarded so the abstract
plugin works independently when memory-palace is absent.
"""

from __future__ import annotations

import os
import re
import sys
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from _vendored_leyline_sibling_plugins import sibling_plugin_dir
from insight_types import Finding, finding_hash

# ---------------------------------------------------------------------------
# Memory-palace shared module imports (soft dependency)
# ---------------------------------------------------------------------------
# Beside this plugin in the repo, or the newest install in the plugin cache.
_PALACE_ROOT = (
    sibling_plugin_dir(__file__, "memory-palace")
    or Path(__file__).resolve().parents[2] / "memory-palace"
)
_palace_hooks = _PALACE_ROOT / "hooks" / "shared"
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

_PALACE_DATA_ENV = "MEMORY_PALACE_DATA_DIR"
# cache/<marketplace>/<plugin>/<version>
_INSTALL_DEPTH = 4


def _palace_data_root(palace_root: Path, env: Mapping[str, str]) -> Path:
    """Memory-palace's version-independent data root, seen from abstract.

    ``CLAUDE_PLUGIN_DATA`` is set per plugin, so in abstract's hook
    process it names abstract's directory and must not be used. An
    install at ``<plugins>/cache/<mkt>/memory-palace/<ver>`` keeps its
    data at ``<plugins>/data/memory-palace-<mkt>``, which is where
    memory-palace's own hooks and CLI read captures (issue #661). A
    checkout keeps its own tree.
    """
    override = env.get(_PALACE_DATA_ENV)
    if override:
        return Path(override)
    parts = palace_root.parts[-_INSTALL_DEPTH:]
    if (
        len(parts) == _INSTALL_DEPTH
        and parts[0] == "cache"
        and parts[2] == "memory-palace"
    ):
        plugins_dir = Path(*palace_root.parts[:-_INSTALL_DEPTH])
        return plugins_dir / "data" / f"memory-palace-{parts[1]}"
    return palace_root


@contextmanager
def _palace_index_env() -> Iterator[None]:
    """Point memory-palace's index resolution at ``_PALACE_DATA``.

    The index path is resolved inside memory-palace from the
    environment, where abstract's ``CLAUDE_PLUGIN_DATA`` would win.
    ``MEMORY_PALACE_DATA_DIR`` outranks it and is restored afterward.
    """
    previous = os.environ.get(_PALACE_DATA_ENV)
    os.environ[_PALACE_DATA_ENV] = str(_PALACE_DATA)
    try:
        yield
    finally:
        if previous is None:
            del os.environ[_PALACE_DATA_ENV]
        else:
            os.environ[_PALACE_DATA_ENV] = previous


_PALACE_DATA = _palace_data_root(_PALACE_ROOT.resolve(), os.environ)
_PALACE_STAGING = _PALACE_DATA / "data" / "staging"

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
    with _palace_index_env():
        return _ingest(findings)


def _ingest(findings: list[Finding]) -> int:
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
        with _palace_index_env():
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
    except (OSError, ValueError):
        # An unreadable or corrupt index is "no insights". Anything else is
        # a bug in the entries or the loop above and must not read as empty.
        return []
