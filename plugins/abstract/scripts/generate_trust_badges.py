#!/usr/bin/env python3
"""Generate trust badge SVGs from ERC-8004 reputation data.

Produces shields.io-compatible badge URLs and optional markdown
snippets for embedding in plugin README files.

Usage:
    python generate_trust_badges.py <plugin-name>
    python generate_trust_badges.py --all
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import quote

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


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
# Badge data from verification result
# ---------------------------------------------------------------------------


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
        description="Generate trust badges from ERC-8004 reputation data.",
    )
    parser.add_argument(
        "plugin_name",
        nargs="?",
        help="Plugin name to generate badge for.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        dest="all_plugins",
        help="Generate badges for all plugins.",
    )
    parser.add_argument(
        "--update-readmes",
        action="store_true",
        help="Insert/update badges in plugin README files.",
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

    if not args.plugin_name and not args.all_plugins:
        parser.error("Provide a plugin name or use --all")

    # Lazy import: verify_plugin may not be on path in all environments
    try:
        sys.path.insert(
            0,
            str(Path(__file__).parent.parent.parent / "leyline" / "scripts"),
        )
        from verify_plugin import (  # noqa: PLC0415
            verify_plugin,  # type: ignore[import-untyped,import-not-found]
        )
    except ImportError:
        print(
            "Error: verify_plugin not found. Ensure leyline plugin is available.",
            file=sys.stderr,
        )
        return 1

    plugins = [args.plugin_name] if args.plugin_name else []

    if args.all_plugins:
        plugins_dir = Path(__file__).parent.parent.parent
        plugins = [
            d.name
            for d in plugins_dir.iterdir()
            if d.is_dir() and (d / "README.md").exists()
        ]

    for name in plugins:
        result = verify_plugin(name)
        badge = generate_badges_for_plugin(result)
        md = generate_badge_markdown(badge)
        print(f"{name}: {md}")

        if args.update_readmes:
            plugins_dir = Path(__file__).parent.parent.parent
            readme = plugins_dir / name / "README.md"
            if update_plugin_readme(readme, md):
                print(f"  Updated {readme}")
            else:
                print(f"  No changes to {readme}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
