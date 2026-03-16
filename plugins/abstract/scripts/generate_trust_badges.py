#!/usr/bin/env python3
"""Generate trust badge URLs from GitHub Actions workflow status.

Produces shields.io-compatible badge URLs and optional markdown
snippets for embedding in plugin README files.

Usage:
    python generate_trust_badges.py <plugin-name>
    python generate_trust_badges.py sanctum --repo athola/claude-night-market
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess  # noqa: S404  # nosec: B404
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import quote

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

DEFAULT_REPO = "athola/claude-night-market"
DEFAULT_WORKFLOW = "trust-attestation.yml"


@dataclass
class BadgeData:
    """Trust badge data for a single plugin."""

    plugin_name: str
    l1_rate: float = 0.0
    l2_rate: float = 0.0
    l3_rate: float = 0.0


# ---------------------------------------------------------------------------
# Color logic
# ---------------------------------------------------------------------------

GREEN_THRESHOLD = 0.9
YELLOW_THRESHOLD = 0.7


def badge_color(rate: float) -> str:
    """Select badge color based on pass rate.

    Args:
        rate: Pass rate as a float between 0.0 and 1.0.

    Returns:
        Shields.io color string: "brightgreen", "yellow", or "red".

    """
    if rate >= GREEN_THRESHOLD:
        return "brightgreen"
    if rate >= YELLOW_THRESHOLD:
        return "yellow"
    return "red"


# ---------------------------------------------------------------------------
# URL and markdown generation
# ---------------------------------------------------------------------------


def _format_rate(rate: float) -> str:
    """Format a rate as an integer percentage string."""
    return f"{int(rate * 100)}%"


def generate_badge_url(data: BadgeData) -> str:
    """Generate a shields.io badge URL for a plugin.

    Badge format: ``trust | L1:98% L2:95% L3:90%``
    Color is derived from the worst (minimum) non-zero rate,
    or the L1 rate if all are zero.

    Args:
        data: Badge data containing per-level pass rates.

    Returns:
        A shields.io endpoint URL string.

    """
    parts: list[str] = []
    rates: list[float] = []

    if data.l1_rate > 0 or data.l2_rate == 0 and data.l3_rate == 0:
        parts.append(f"L1:{_format_rate(data.l1_rate)}")
        rates.append(data.l1_rate)
    if data.l2_rate > 0:
        parts.append(f"L2:{_format_rate(data.l2_rate)}")
        rates.append(data.l2_rate)
    if data.l3_rate > 0:
        parts.append(f"L3:{_format_rate(data.l3_rate)}")
        rates.append(data.l3_rate)

    # Always show at least L1
    if not parts:
        parts.append(f"L1:{_format_rate(data.l1_rate)}")
        rates.append(data.l1_rate)

    message = " ".join(parts)
    worst_rate = min(rates) if rates else 0.0
    color = badge_color(worst_rate)

    label = "trust"
    encoded_message = quote(message, safe="")
    return f"https://img.shields.io/badge/{label}-{encoded_message}-{color}"


def generate_badge_markdown(data: BadgeData) -> str:
    """Generate a markdown badge snippet for README insertion.

    Args:
        data: Badge data for one plugin.

    Returns:
        Single-line markdown image string.

    """
    url = generate_badge_url(data)
    alt = f"{data.plugin_name} trust"
    return f"![{alt}]({url})"


# ---------------------------------------------------------------------------
# Badge data from GitHub Actions
# ---------------------------------------------------------------------------


def _query_latest_workflow_status(
    repo: str,
    workflow: str = DEFAULT_WORKFLOW,
) -> str | None:
    """Query the latest workflow run conclusion from GitHub.

    Args:
        repo: GitHub repository in "owner/repo" format.
        workflow: Workflow filename.

    Returns:
        The conclusion string ("success", "failure", etc.)
        or None if the query fails.

    """
    endpoint = (
        f"repos/{repo}/actions/workflows/{workflow}/runs?status=completed&per_page=1"
    )
    result = subprocess.run(  # noqa: S603, S607  # nosec: B603, B607
        ["gh", "api", endpoint],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return None

    data = json.loads(result.stdout)
    runs = data.get("workflow_runs", [])
    if not runs:
        return None

    return runs[0].get("conclusion")  # type: ignore[no-any-return]


def generate_badges_for_plugin(
    verify_result: dict[str, Any],
) -> BadgeData:
    """Create BadgeData from a verify_plugin result dict.

    Args:
        verify_result: Dict returned by verify_plugin() or
            verify_plugin_offline(), containing ``plugin_name``
            and ``level_scores``.

    Returns:
        BadgeData with per-level rates populated.

    """
    scores = verify_result.get("level_scores", [])
    rate_map: dict[str, float] = {}
    for s in scores:
        rate_map[s["level"]] = s.get("rate", 0.0)

    return BadgeData(
        plugin_name=verify_result.get("plugin_name", "unknown"),
        l1_rate=rate_map.get("L1", 0.0),
        l2_rate=rate_map.get("L2", 0.0),
        l3_rate=rate_map.get("L3", 0.0),
    )


def generate_workflow_badge_url(
    repo: str = DEFAULT_REPO,
    workflow: str = DEFAULT_WORKFLOW,
) -> str:
    """Generate a GitHub Actions workflow status badge URL.

    Args:
        repo: GitHub repository in "owner/repo" format.
        workflow: Workflow filename.

    Returns:
        A shields.io GitHub Actions workflow status URL.

    """
    return (
        f"https://img.shields.io/github/actions/workflow/status/"
        f"{repo}/{workflow}?label=trust"
    )


# ---------------------------------------------------------------------------
# README update
# ---------------------------------------------------------------------------

# Pattern matches any existing trust badge line produced by this script.
_BADGE_PATTERN = re.compile(
    r"!\[.*?trust.*?\]\(https://img\.shields\.io/badge/trust-.*?\)"
)


def update_plugin_readme(
    readme_path: Path,
    badge_markdown: str,
) -> bool:
    """Insert or update a trust badge in a plugin README.

    The badge is placed on the line immediately after the first
    ``# Heading``. If an existing trust badge is found, it is
    replaced. If the badge is already identical, no write occurs.

    Args:
        readme_path: Path to the README.md file.
        badge_markdown: The markdown image string to insert.

    Returns:
        True if the file was modified, False otherwise.

    """
    if not readme_path.exists():
        return False

    content = readme_path.read_text()

    # If the exact badge already exists, skip
    if badge_markdown in content:
        return False

    # Replace existing trust badge
    if _BADGE_PATTERN.search(content):
        new_content = _BADGE_PATTERN.sub(badge_markdown, content)
        readme_path.write_text(new_content)
        return True

    # Insert after first heading
    lines = content.split("\n")
    insert_idx = 0
    for i, line in enumerate(lines):
        if line.startswith("# "):
            insert_idx = i + 1
            break

    # Insert badge with surrounding blank lines
    if insert_idx > 0:
        # Ensure blank line between heading and badge
        while insert_idx < len(lines) and lines[insert_idx].strip() == "":
            insert_idx += 1
        lines.insert(insert_idx, "")
        lines.insert(insert_idx + 1, badge_markdown)
        lines.insert(insert_idx + 2, "")
    else:
        # No heading found; prepend badge
        lines.insert(0, badge_markdown)
        lines.insert(1, "")

    new_content = "\n".join(lines)
    readme_path.write_text(new_content)
    return True


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser."""
    parser = argparse.ArgumentParser(
        description=("Generate trust badges from GitHub Actions workflow status."),
    )
    parser.add_argument(
        "plugin_name",
        help="Plugin name to generate badge for.",
    )
    parser.add_argument(
        "--repo",
        default=DEFAULT_REPO,
        help=f"GitHub repository (default: {DEFAULT_REPO}).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point.

    Args:
        argv: Command-line arguments (defaults to sys.argv[1:]).

    Returns:
        Exit code: 0 on success, 1 on error.

    """
    parser = build_parser()
    args = parser.parse_args(argv)

    conclusion = _query_latest_workflow_status(args.repo)

    if conclusion is None:
        rate = 0.0
    elif conclusion == "success":
        rate = 1.0
    else:
        rate = 0.0

    data = BadgeData(
        plugin_name=args.plugin_name,
        l1_rate=rate,
    )

    md = generate_badge_markdown(data)
    workflow_url = generate_workflow_badge_url(args.repo)

    print(f"{args.plugin_name}: {md}")
    print(f"Workflow badge: {workflow_url}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
