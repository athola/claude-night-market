#!/usr/bin/env python3
"""Severity-based auto-promotion of learnings to GitHub Issues.

Reads LEARNINGS.md and promotes items based on priority score instead
of requiring reaction voting (which doesn't work for single-developer use).

Priority formula: (Frequency × Impact) / Ease
- Score > 5.0 → auto-create GitHub Issue (label: improvement:auto-promoted)
- Score <= 5.0 → post to Discussions (Learnings category) for deliberation
Duplication checking prevents redundant issues/discussions.

Part of the improvement feedback loop (Issue #69).
"""

from __future__ import annotations

import json
import re
import subprocess  # nosec B404
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# D-03: pull canonical extract_section from abstract.utils.
_SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from finding_verifier import (  # noqa: E402 - sibling script
    FileRef,
    VerificationResult,
    parse_where_refs,
    repo_root_is_valid,
    resolve_skill_refs,
    should_skip_promotion,
    verify_refs,
)
from post_learnings_to_discussions import (  # noqa: E402 - sibling script
    PostedRecord,
    create_discussion,
    detect_target_repo,
    get_repo_node_id,
    resolve_category_id,
)

from abstract.utils import (
    extract_bold_field,
    get_learnings_path,
)
from abstract.utils import (  # noqa: E402 - import after sys.path setup
    extract_section as _extract_section,
)

# Thresholds for severity tiers
HIGH_PRIORITY_THRESHOLD = 5.0
# Low threshold to avoid missing insights — duplication check prevents spam
MEDIUM_PRIORITY_THRESHOLD = 0.1

# Slow execution reference (10s = threshold from aggregate_skill_logs.py)
SLOW_THRESHOLD_MS = 10000

# Priority model: impact / ease, weighted by how often the skill runs.
# A failure rate of 0% success scores FAILURE_IMPACT_DIVISOR points of
# impact, a rating one star below perfect scores RATING_GAP_WEIGHT, and
# a skill failing outright is worth EXCESSIVE_FAILURE_IMPACT regardless
# of magnitude. Ease is the inverse: the more severe an issue, the
# cheaper it is judged to fix.
FAILURE_IMPACT_DIVISOR = 10.0
RATING_GAP_WEIGHT = 2.0
SLOW_SECONDS_PER_IMPACT_POINT = 10.0
EXCESSIVE_FAILURE_IMPACT = 8.0
HEALTHY_IMPACT = 0.1
EASE_BY_SEVERITY = {"high": 2.0, "medium": 3.0, "low": 5.0}
DEFAULT_EASE = 5.0


def get_repo_root() -> Path:
    """Repo root used to verify a finding's locations still exist."""
    return Path(__file__).resolve().parents[3]


def verify_item_locations(
    item: dict[str, Any],
    repo_root: Path | None = None,
) -> VerificationResult:
    """Resolve an item's referenced locations and check they exist.

    Builds references from the item's ``skill`` id (``plugin:name``)
    and any file paths embedded in its free-text fields, then verifies
    them against HEAD. This is the promotion gate's honest staleness
    check: it confirms the locations still exist, not that the concern
    is unresolved (see ``finding_verifier`` for the scope boundary).
    """
    root = repo_root if repo_root is not None else get_repo_root()
    refs: list[FileRef] = []
    skill = str(item.get("skill", ""))
    if ":" in skill:
        refs.extend(resolve_skill_refs(skill, root))
    for key in ("where", "detail", "metric"):
        refs.extend(parse_where_refs(str(item.get(key, ""))))
    return verify_refs(refs, root)


def stale_skip_reason(
    item: dict[str, Any],
    repo_root: Path | None = None,
) -> str | None:
    """Return a skip rationale if the finding is provably stale, else None.

    The promotion gate must never *silently* drop a real finding, so
    this fails **open** (returns ``None`` -> promote) in every
    uncertain case:

    - the repo root cannot be trusted (``repo_root_is_valid`` is
      False) -- a wrong root would report every finding missing;
    - the location check raises (e.g. an embedded NUL byte makes
      ``Path.exists`` raise ``ValueError``) -- one bad finding must
      not abort the batch and drop the rest.

    It returns a rationale string only for the highest-confidence
    signal (every referenced location gone), matching
    :func:`should_skip_promotion`.
    """
    root = repo_root if repo_root is not None else get_repo_root()
    if not repo_root_is_valid(root):
        print(
            f"[auto_promote] repo root {root} is unverifiable; "
            "promotion gate disabled (promoting normally)",
            file=sys.stderr,
        )
        return None
    try:
        verdict = verify_item_locations(item, root)
    except (OSError, ValueError) as exc:
        print(
            f"[auto_promote] location check failed ({exc}); "
            "promoting (gate fails open)",
            file=sys.stderr,
        )
        return None
    return verdict.rationale if should_skip_promotion(verdict) else None


def get_promoted_record_path() -> Path:
    """Get path to promoted_issues.json deduplication file."""
    return Path.home() / ".claude" / "skills" / "discussions" / "promoted_issues.json"


# ---------------------------------------------------------------------------
# Deduplication record
# ---------------------------------------------------------------------------


@dataclass
class PromotedIssueRecord:
    """Tracks which items have been promoted to avoid duplicates."""

    promoted: dict[str, str] = field(default_factory=dict)  # key -> url

    @classmethod
    def load(cls, path: Path | None = None) -> PromotedIssueRecord:
        """Load record from disk."""
        record_path = path or get_promoted_record_path()
        if record_path.exists():
            try:
                data = json.loads(record_path.read_text())
                return cls(promoted=data.get("promoted", {}))
            except (json.JSONDecodeError, OSError) as exc:
                # A reset re-promotes everything; the gate now hangs more
                # decisions off this record, so make corruption visible
                # instead of silently starting from an empty record.
                print(
                    f"[auto_promote] promoted record {record_path} unreadable "
                    f"({exc}); starting fresh (may re-promote)",
                    file=sys.stderr,
                )
        return cls()

    def save(self, path: Path | None = None) -> None:
        """Save record to disk."""
        record_path = path or get_promoted_record_path()
        record_path.parent.mkdir(parents=True, exist_ok=True)
        record_path.write_text(json.dumps({"promoted": self.promoted}, indent=2))

    def is_promoted(self, key: str) -> bool:
        """Check if an item has already been promoted."""
        return key in self.promoted

    def add(self, key: str, url: str) -> None:
        """Record a promotion."""
        self.promoted[key] = url


# ---------------------------------------------------------------------------
# Priority scoring
# ---------------------------------------------------------------------------


def calculate_priority(item: dict[str, Any]) -> float:
    """Calculate priority score using (Frequency × Impact) / Ease.

    Args:
        item: Parsed improvement item with metrics.

    Returns:
        Priority score (higher = more urgent).

    """
    executions: int = item.get("executions", 1)
    frequency: int = max(1, executions)
    issue_type = item.get("type", "none")
    severity = item.get("severity", "low")

    # Calculate impact based on issue type
    impact = 0.0
    if issue_type == "high_failure_rate":
        success_rate = item.get("success_rate", 100.0)
        # Impact scales with failure severity: 0% success = 10, 50% = 5
        impact = max(0, (100.0 - success_rate) / FAILURE_IMPACT_DIVISOR)
    elif issue_type == "low_rating":
        avg_rating = item.get("avg_rating", 5.0)
        # Impact = gap from perfect score, weighted
        impact = (5.0 - avg_rating) * RATING_GAP_WEIGHT
    elif issue_type == "slow_execution":
        avg_duration_ms = item.get("avg_duration_ms", 0)
        # Impact = seconds over threshold / 10
        seconds_over = max(0, (avg_duration_ms - SLOW_THRESHOLD_MS)) / 1000.0
        impact = seconds_over / SLOW_SECONDS_PER_IMPACT_POINT
    elif issue_type == "excessive_failures":
        impact = EXCESSIVE_FAILURE_IMPACT
    else:
        # Unknown or healthy — minimal impact
        impact = HEALTHY_IMPACT

    # Estimate ease based on severity
    ease = EASE_BY_SEVERITY.get(severity, DEFAULT_EASE)

    return float((frequency * impact) / ease)


# ---------------------------------------------------------------------------
# LEARNINGS.md parsing
# ---------------------------------------------------------------------------


def _parse_summary_table(content: str) -> dict[str, dict[str, Any]]:
    """Parse the Skill Performance Summary table for execution counts."""
    metrics: dict[str, dict[str, Any]] = {}
    table_section = _extract_section(content, "## Skill Performance Summary")
    if not table_section:
        return metrics

    for match in re.finditer(
        r"\|\s*`([^`]+)`\s*\|\s*(\d+)\s*\|\s*([\d.]+)%\s*\|\s*([\d.]+)s\s*\|\s*([^\|]+)\s*\|",
        table_section,
    ):
        skill = match.group(1).strip()
        rating_str = match.group(5).strip()
        rating = None
        if "/" in rating_str:
            try:
                rating = float(rating_str.split("/")[0])
            except ValueError:
                pass

        metrics[skill] = {
            "executions": int(match.group(2)),
            "success_rate": float(match.group(3)),
            "avg_duration_s": float(match.group(4)),
            "avg_rating": rating,
        }

    return metrics


def parse_improvement_items(content: str) -> list[dict[str, Any]]:  # noqa: PLR0912 - markdown parsing requires many conditional branches
    """Parse LEARNINGS.md into a list of promotable improvement items.

    Args:
        content: Raw LEARNINGS.md content.

    Returns:
        List of items with skill, type, severity, metrics.

    """
    if not content or not content.strip():
        return []

    items: list[dict[str, Any]] = []
    summary_metrics = _parse_summary_table(content)

    # Parse high-impact issues
    hi_section = _extract_section(content, "## High-Impact Issues")
    if hi_section:
        for match in re.finditer(
            r"### (.+?)\n(.*?)(?=\n### |\n---|\n## |\Z)",
            hi_section,
            re.DOTALL,
        ):
            skill = match.group(1).strip()
            body = match.group(2).strip()
            issue_type = extract_bold_field(body, "Type")
            severity = extract_bold_field(body, "Severity")
            metric = extract_bold_field(body, "Metric")
            detail = extract_bold_field(body, "Detail")

            item: dict[str, Any] = {
                "skill": skill,
                "type": issue_type,
                "severity": severity,
                "metric": metric,
                "detail": detail,
            }

            # Enrich with summary table data
            if skill in summary_metrics:
                item.update(summary_metrics[skill])

            items.append(item)

    # Parse slow execution table
    slow_section = _extract_section(content, "## Slow Execution")
    if slow_section:
        for match in re.finditer(
            r"\|\s*`([^`]+)`\s*\|\s*([\d.]+)s\s*\|\s*([\d.]+)s\s*\|\s*(\d+)\s*\|",
            slow_section,
        ):
            skill = match.group(1).strip()
            # Skip if already captured as high-impact
            if any(i["skill"] == skill for i in items):
                continue

            avg_s = float(match.group(2))
            items.append(
                {
                    "skill": skill,
                    "type": "slow_execution",
                    "severity": "medium",
                    "metric": f"{avg_s}s avg",
                    "detail": "Exceeds 10s threshold",
                    "executions": int(match.group(4)),
                    "avg_duration_ms": int(avg_s * 1000),
                }
            )

    # Parse low-rated skills
    lr_section = _extract_section(content, "## Low User Ratings")
    if lr_section:
        for match in re.finditer(
            r"### (.+?)\s*-\s*([\d.]+)/5\.0",
            lr_section,
        ):
            skill = match.group(1).strip()
            rating = float(match.group(2))
            # Skip if already captured
            if any(i["skill"] == skill for i in items):
                # Update existing with rating
                for i in items:
                    if i["skill"] == skill and "avg_rating" not in i:
                        i["avg_rating"] = rating
                continue

            item_data: dict[str, Any] = {
                "skill": skill,
                "type": "low_rating",
                "severity": "medium",
                "metric": f"{rating}/5.0 rating",
                "detail": "Low user rating",
                "avg_rating": rating,
            }
            if skill in summary_metrics:
                item_data.update(summary_metrics[skill])
            items.append(item_data)

    return items


# ---------------------------------------------------------------------------
# GitHub issue creation
# ---------------------------------------------------------------------------


def has_existing_issue(
    item: dict[str, Any],
    target_repo: str,
) -> bool:
    """Check if a similar issue or discussion already exists.

    Searches open issues for matching skill name to prevent duplicates.

    Args:
        item: The improvement item to check.
        target_repo: Repository in "owner/name" format.

    Returns:
        True if a duplicate exists.

    """
    skill = item.get("skill", "")
    issue_type = item.get("type", "")
    search_query = f"[Auto-Improvement] {skill}: {issue_type} in:title"
    cmd = [
        "gh",
        "issue",
        "list",
        "--repo",
        target_repo,
        "--search",
        search_query,
        "--json",
        "number",
        "--limit",
        "1",
    ]
    try:
        result = subprocess.run(  # nosec B603
            cmd,
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        if result.returncode == 0:
            issues = json.loads(result.stdout.strip() or "[]")
            return len(issues) > 0
    except Exception as exc:
        print(f"[auto_promote] duplicate check: {exc}", file=sys.stderr)
    return False


def promote_to_issue(
    item: dict[str, Any],
    target_repo: str,
) -> str | None:
    """Create a GitHub Issue for a high-priority item.

    Args:
        item: The improvement item to promote.
        target_repo: Repository in "owner/name" format.

    Returns:
        Issue URL if created, None on failure.

    """
    title = f"[Auto-Improvement] {item['skill']}: {item.get('type', 'improvement')}"
    body_lines = [
        "## Auto-Promoted Improvement",
        "",
        f"**Skill**: `{item['skill']}`",
        f"**Issue Type**: {item.get('type', 'unknown')}",
        f"**Metric**: {item.get('metric', 'N/A')}",
        f"**Detail**: {item.get('detail', 'N/A')}",
        "",
        "## Priority Analysis",
        "",
        f"This item was auto-promoted because its priority score exceeded "
        f"{HIGH_PRIORITY_THRESHOLD:.1f} based on the formula:",
        "```",
        "Priority = (Frequency × Impact) / Ease",
        "```",
        "",
        "## Next Steps",
        "",
        "Run `/abstract:improve-skills --from-issues` to implement this improvement.",
        "",
        "---",
        "*Auto-promoted by auto_promote_learnings.py (Issue #69)*",
    ]
    body = "\n".join(body_lines)

    try:
        cmd = [
            "gh",
            "issue",
            "create",
            "--repo",
            target_repo,
            "--title",
            title,
            "--body",
            body,
            "--label",
            "improvement:auto-promoted",
        ]
        result = subprocess.run(  # nosec B603
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        if result.returncode == 0:
            return result.stdout.strip()
        print(
            f"Warning: gh issue create failed: {result.stderr}",
            file=sys.stderr,
        )
        return None
    except FileNotFoundError:
        print("Warning: gh CLI not found.", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Warning: Issue creation failed: {e}", file=sys.stderr)
        return None


# ---------------------------------------------------------------------------
# Discussion posting (medium severity)
# ---------------------------------------------------------------------------


def _post_single_discussion(
    item: dict[str, Any],
    owner: str,
    name: str,
) -> str | None:
    """Post a single item to Discussions for deliberation.

    Args:
        item: The improvement item to post.
        owner: Repository owner.
        name: Repository name.

    Returns:
        Discussion URL if posted, None on failure.

    """
    try:
        category_id = resolve_category_id(owner, name, "learnings")
        if category_id is None:
            print(
                f'No "learnings" category on {owner}/{name}. Skipping.',
                file=sys.stderr,
            )
            return None

        record = PostedRecord.load()
        repo_id = get_repo_node_id(record, owner, name)

        title = f"[Improvement] {item['skill']}: {item.get('type', 'review')}"
        body = (
            f"## Improvement Opportunity\n\n"
            f"**Skill**: `{item['skill']}`\n"
            f"**Type**: {item.get('type', 'unknown')}\n"
            f"**Metric**: {item.get('metric', 'N/A')}\n"
            f"**Detail**: {item.get('detail', 'N/A')}\n\n"
            f"---\n"
            f"*Auto-posted for deliberation (priority 2.0-5.0)*"
        )

        return create_discussion(repo_id, category_id, title, body)
    except Exception as e:
        print(f"Warning: Discussion posting failed: {e}", file=sys.stderr)
        return None


def post_to_discussion(
    item: dict[str, Any],
    owner: str,
    name: str,
) -> str | None:
    """Post a medium-severity item to Discussions.

    Args:
        item: The improvement item.
        owner: Repository owner.
        name: Repository name.

    Returns:
        Discussion URL if posted, None on failure.

    """
    return _post_single_discussion(item, owner, name)


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------


def run_auto_promote() -> list[str]:
    """Run the auto-promotion pipeline.

    Returns:
        List of created issue/discussion URLs.

    """
    learnings_path = get_learnings_path()
    if not learnings_path.exists():
        return []

    content = learnings_path.read_text()
    items = parse_improvement_items(content)
    if not items:
        return []

    # Detect target repo for issue/discussion creation
    repo = detect_target_repo()
    if repo is None:
        print(
            "Could not detect target repository. Skipping promotion.",
            file=sys.stderr,
        )
        return []
    owner, name = repo
    target_repo = f"{owner}/{name}"

    record = PromotedIssueRecord.load()
    created_urls: list[str] = []

    for item in items:
        key = f"{item['skill']}:{item.get('type', 'unknown')}"

        if record.is_promoted(key):
            continue

        score = calculate_priority(item)

        # Check for duplicates before promoting
        if has_existing_issue(item, target_repo):
            record.add(key, "duplicate-skipped")
            record.save()
            continue

        url: str | None = None
        if score >= HIGH_PRIORITY_THRESHOLD:
            # Promotion gate: do not create an issue for a finding whose
            # every referenced location has already been removed. The
            # gate fails open (promotes) on any error or untrusted root,
            # so a real finding is never silently dropped.
            skip_reason = stale_skip_reason(item)
            if skip_reason is not None:
                print(
                    f"[auto_promote] skipping stale finding for '{key}': {skip_reason}",
                    file=sys.stderr,
                )
                record.add(key, "stale-skipped")
                record.save()
                continue
            url = promote_to_issue(item, target_repo)
        elif score >= MEDIUM_PRIORITY_THRESHOLD:
            url = post_to_discussion(item, owner, name)

        if url:
            record.add(key, url)
            record.save()
            created_urls.append(url)

    return created_urls


def main() -> None:
    """CLI entry point."""
    try:
        urls = run_auto_promote()
        if urls:
            print(f"Promoted {len(urls)} item(s):")
            for url in urls:
                print(f"  {url}")
        else:
            print("No items promoted.")
    except Exception as e:
        print(f"Warning: Auto-promotion failed: {e}", file=sys.stderr)
        sys.exit(0)


if __name__ == "__main__":
    main()
