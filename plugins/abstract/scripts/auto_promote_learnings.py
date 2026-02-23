#!/usr/bin/env python3
"""Severity-based auto-promotion of learnings to GitHub Issues.

Reads LEARNINGS.md and promotes items based on priority score instead
of requiring reaction voting (which doesn't work for single-developer use).

Priority formula: (Frequency × Impact) / Ease
- Score > 5.0 → auto-create GitHub Issue (label: improvement:auto-promoted)
- Score 2.0-5.0 → post to Discussions (Learnings category) for deliberation
- Score < 2.0 → skip (low priority)

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

# Hardcoded target repository
TARGET_REPO = "athola/claude-night-market"

# Thresholds for severity tiers
HIGH_PRIORITY_THRESHOLD = 5.0
MEDIUM_PRIORITY_THRESHOLD = 2.0

# Slow execution reference (10s = threshold from aggregate_skill_logs.py)
SLOW_THRESHOLD_MS = 10000


def get_learnings_path() -> Path:
    """Get path to LEARNINGS.md file."""
    return Path.home() / ".claude" / "skills" / "LEARNINGS.md"


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
            except (json.JSONDecodeError, OSError):
                pass
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
        impact = max(0, (100.0 - success_rate) / 10.0)
    elif issue_type == "low_rating":
        avg_rating = item.get("avg_rating", 5.0)
        # Impact = gap from perfect score × 2
        impact = (5.0 - avg_rating) * 2.0
    elif issue_type == "slow_execution":
        avg_duration_ms = item.get("avg_duration_ms", 0)
        # Impact = seconds over threshold / 10
        seconds_over = max(0, (avg_duration_ms - SLOW_THRESHOLD_MS)) / 1000.0
        impact = seconds_over / 10.0
    elif issue_type == "excessive_failures":
        impact = 8.0  # High fixed impact
    else:
        # Unknown or healthy — minimal impact
        impact = 0.1

    # Estimate ease based on severity
    ease_map = {"high": 2.0, "medium": 3.0, "low": 5.0}
    ease = ease_map.get(severity, 5.0)

    return float((frequency * impact) / ease)


# ---------------------------------------------------------------------------
# LEARNINGS.md parsing
# ---------------------------------------------------------------------------


def _extract_section(content: str, heading: str) -> str | None:
    """Extract content between a heading and the next same-level heading or ---."""
    pattern = re.escape(heading) + r"\n(.*?)(?=\n## |\n---|\Z)"
    match = re.search(pattern, content, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None


def _extract_bold_field(text: str, field_name: str) -> str:
    """Extract a bold field value from text."""
    match = re.search(rf"\*\*{re.escape(field_name)}\*\*:\s*(.+)", text)
    return match.group(1).strip() if match else ""


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


def parse_improvement_items(content: str) -> list[dict[str, Any]]:  # noqa: PLR0912
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
            issue_type = _extract_bold_field(body, "Type")
            severity = _extract_bold_field(body, "Severity")
            metric = _extract_bold_field(body, "Metric")
            detail = _extract_bold_field(body, "Detail")

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


def promote_to_issue(item: dict[str, Any]) -> str | None:
    """Create a GitHub Issue for a high-priority item.

    Args:
        item: The improvement item to promote.

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
            TARGET_REPO,
            "--title",
            title,
            "--body",
            body,
            "--label",
            "improvement:auto-promoted",
        ]
        result = subprocess.run(  # noqa: S603, S607  # nosec B603
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


def _post_single_discussion(item: dict[str, Any]) -> str | None:
    """Post a single item to Discussions for deliberation.

    Args:
        item: The improvement item to post.

    Returns:
        Discussion URL if posted, None on failure.

    """
    try:
        from post_learnings_to_discussions import (  # type: ignore[import-not-found]  # noqa: PLC0415
            LEARNINGS_CATEGORY_ID,
            PostedRecord,
            create_discussion,
            get_repo_node_id,
        )

        record = PostedRecord.load()
        repo_id = get_repo_node_id(record)

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

        url: str | None = create_discussion(repo_id, LEARNINGS_CATEGORY_ID, title, body)
        return url
    except Exception as e:
        print(f"Warning: Discussion posting failed: {e}", file=sys.stderr)
        return None


def post_to_discussion(item: dict[str, Any]) -> str | None:
    """Post a medium-severity item to Discussions.

    Args:
        item: The improvement item.

    Returns:
        Discussion URL if posted, None on failure.

    """
    return _post_single_discussion(item)


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

    record = PromotedIssueRecord.load()
    created_urls: list[str] = []

    for item in items:
        key = f"{item['skill']}:{item.get('type', 'unknown')}"

        if record.is_promoted(key):
            continue

        score = calculate_priority(item)

        url: str | None = None
        if score >= HIGH_PRIORITY_THRESHOLD:
            url = promote_to_issue(item)
        elif score >= MEDIUM_PRIORITY_THRESHOLD:
            url = post_to_discussion(item)
        # else: score < 2.0, skip

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
