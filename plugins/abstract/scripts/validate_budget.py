#!/usr/bin/env python3
"""Validate skill and command description budget for Claude Code system prompt."""

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

# Configuration
BUDGET_LIMIT = 15000  # Default Claude Code budget
WARN_THRESHOLD = 14500  # Warn at 96.7% usage
DESCRIPTION_MAX = 150  # Max chars per description (recommendation)
VERBOSE_DISPLAY_LIMIT = 5  # Number of verbose items to display


@dataclass
class Component:
    """Represents a plugin component with its description metadata."""

    name: str
    type: str
    plugin: str
    desc_length: int
    file_path: str


def extract_description(content: str) -> str:
    """Extract description field from YAML frontmatter."""
    # Match multi-line description field
    match = re.search(r"^description:\s*\|?\s*\n((?:  .+\n)*)", content, re.MULTILINE)
    if match:
        desc = match.group(1)
        # Remove leading spaces from each line
        lines = [line.lstrip() for line in desc.split("\n")]
        return "\n".join(lines).strip()

    # Try single-line description
    match = re.search(r"^description:\s*(.+)$", content, re.MULTILINE)
    if match:
        return match.group(1).strip()

    return ""


def analyze_file(file_path: Path, component_type: str) -> Component:
    """Analyze a single skill or command file."""
    content = file_path.read_text()
    desc = extract_description(content)

    # Extract name from frontmatter
    name_match = re.search(r"^name:\s*(.+)$", content, re.MULTILINE)
    name = name_match.group(1).strip() if name_match else file_path.stem

    # Determine plugin from path
    parts = file_path.parts
    plugin_idx = parts.index("plugins") + 1 if "plugins" in parts else -1
    plugin = (
        parts[plugin_idx] if plugin_idx > 0 and plugin_idx < len(parts) else "unknown"
    )

    return Component(
        name=name,
        type=component_type,
        plugin=plugin,
        desc_length=len(desc),
        file_path=str(file_path),
    )


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Validate skill and command description budget for Claude Code.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Validate from current directory
  %(prog)s --path /path/to/repo  # Validate from specified path
        """,
    )
    parser.add_argument(
        "--path",
        type=str,
        default=".",
        help="Base path for plugin skill/command files (default: current directory)",
    )
    return parser.parse_args()


def main() -> None:  # noqa: PLR0912, PLR0915
    """Validate description budget across all plugins."""
    args = parse_args()
    base = Path(args.path)
    components: list[Component] = []

    # Find all skills
    for skill_file in base.rglob("plugins/*/skills/*/SKILL.md"):
        if ".worktrees" not in str(skill_file) and ".git" not in str(skill_file):
            try:
                comp = analyze_file(skill_file, "skill")
                components.append(comp)
            except Exception as e:
                print(f"Warning: Error processing {skill_file}: {e}", file=sys.stderr)

    # Find all commands
    for cmd_file in base.rglob("plugins/*/commands/*.md"):
        if ".worktrees" not in str(cmd_file) and ".git" not in str(cmd_file):
            try:
                comp = analyze_file(cmd_file, "command")
                components.append(comp)
            except Exception as e:
                print(f"Warning: Error processing {cmd_file}: {e}", file=sys.stderr)

    # Calculate totals
    total_chars = sum(c.desc_length for c in components)

    # Check verbose descriptions
    verbose = [c for c in components if c.desc_length > DESCRIPTION_MAX]

    # Determine exit status
    failed = total_chars > BUDGET_LIMIT
    warn_only = not failed and total_chars > WARN_THRESHOLD

    # Output results
    print(f"📊 Total description characters: {total_chars:,}")
    usage_pct = total_chars / BUDGET_LIMIT * 100
    print(f"   Budget limit: {BUDGET_LIMIT:,} ({usage_pct:.1f}% used)")

    if failed:
        print(f"\n❌ BUDGET EXCEEDED by {total_chars - BUDGET_LIMIT:,} characters!")
        print("\nTop offenders:")
        sorted_comps = sorted(components, key=lambda c: c.desc_length, reverse=True)[
            :10
        ]
        for comp in sorted_comps:
            print(
                f"  - {comp.plugin}/{comp.name} ({comp.type}): {comp.desc_length} chars"
            )
        print(
            f"\n⚠️  Please optimize descriptions to get under "
            f"{BUDGET_LIMIT:,} characters."
        )
        print("   See: docs/action-plan-budget-crisis.md for optimization guidelines")
        print("\n💡 Optimization tips:")
        print("   - Remove implementation details (move to skill body)")
        print("   - Condense trigger lists to essential keywords")
        print("   - Eliminate redundancy with tags/category")
        print("   - Focus on discoverability, not explanations")
        sys.exit(1)

    if warn_only:
        print("\n⚠️  WARNING: Approaching budget limit")
        warn_pct = total_chars / BUDGET_LIMIT * 100
        print(f"   Usage: {total_chars:,} / {BUDGET_LIMIT:,} ({warn_pct:.1f}%)")
        print(f"   Recommended headroom: < {WARN_THRESHOLD:,} chars (96.7%)")

    if verbose:
        print(
            f"\n⚠️  {len(verbose)} descriptions exceed "
            f"{DESCRIPTION_MAX} chars (recommended max):"
        )
        top_verbose = sorted(verbose, key=lambda c: c.desc_length, reverse=True)
        for comp in top_verbose[:VERBOSE_DISPLAY_LIMIT]:
            print(f"  - {comp.plugin}/{comp.name}: {comp.desc_length} chars")
        if len(verbose) > VERBOSE_DISPLAY_LIMIT:
            remaining = len(verbose) - VERBOSE_DISPLAY_LIMIT
            print(f"  ... and {remaining} more")

    if not warn_only and not verbose:
        print(
            f"✅ Budget check passed! ({BUDGET_LIMIT - total_chars:,} chars headroom)"
        )
    elif not failed:
        print("\n✅ Budget check passed (with warnings)")

    sys.exit(0)


if __name__ == "__main__":
    main()
