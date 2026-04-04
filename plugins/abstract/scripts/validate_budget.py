#!/usr/bin/env python3
"""Validate skill and command description budget for Claude Code system prompt."""

import argparse
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

# Claude Code has an undocumented ~16,000 character budget for skill
# metadata in the available_skills section. Each skill costs
# description_length + ~109 chars overhead (XML tags, name, location).
# See: https://gist.github.com/alexey-pelykh/faa3c304f731d6a962efc5fa2a43abe1
# and github.com/anthropics/claude-code #11045.
DEFAULT_BUDGET = 15700  # Empirical budget for available_skills
OVERHEAD_PER_COMPONENT = 109  # XML tags, name, location per skill/cmd
BUDGET_LIMIT = int(os.environ.get("SLASH_COMMAND_TOOL_CHAR_BUDGET", DEFAULT_BUDGET))
WARN_THRESHOLD = int(BUDGET_LIMIT * 0.90)  # Warn at 90% usage
DESCRIPTION_MAX = 130  # Max chars per description (optimal for 60+ skills)
VERBOSE_DISPLAY_LIMIT = 10  # Number of verbose items to display


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


def collect_components(base: Path) -> list[Component]:
    """Collect all skill and command components from plugins."""
    components: list[Component] = []

    # Find all skills
    for skill_file in base.rglob("plugins/*/skills/*/SKILL.md"):
        if "worktrees" not in str(skill_file) and ".git" not in str(skill_file):
            try:
                comp = analyze_file(skill_file, "skill")
                components.append(comp)
            except Exception as e:
                print(f"Warning: Error processing {skill_file}: {e}", file=sys.stderr)

    # Find all commands
    for cmd_file in base.rglob("plugins/*/commands/*.md"):
        if "worktrees" not in str(cmd_file) and ".git" not in str(cmd_file):
            try:
                comp = analyze_file(cmd_file, "command")
                components.append(comp)
            except Exception as e:
                print(f"Warning: Error processing {cmd_file}: {e}", file=sys.stderr)

    return components


def calculate_budget_status(
    components: list[Component],
) -> tuple[int, int, int, int, bool, bool, list[Component]]:
    """Calculate budget totals and status.

    Returns:
        Tuple of (total_chars, total_with_overhead, visible_estimate,
                  verbose_count, failed, warn_only, verbose_list)

    """
    total_chars = sum(c.desc_length for c in components)
    total_with_overhead = total_chars + len(components) * OVERHEAD_PER_COMPONENT
    verbose = [c for c in components if c.desc_length > DESCRIPTION_MAX]
    # Estimate how many skills would be visible at ~130 char avg desc
    visible_estimate = BUDGET_LIMIT // (DESCRIPTION_MAX + OVERHEAD_PER_COMPONENT)
    failed = len(verbose) > 0  # Fail if any description exceeds max
    warn_only = not failed and total_with_overhead > WARN_THRESHOLD

    return (
        total_chars,
        total_with_overhead,
        visible_estimate,
        len(verbose),
        failed,
        warn_only,
        verbose,
    )


def format_offenders_list(components: list[Component], limit: int = 10) -> str:
    """Format sorted list of budget offenders."""
    sorted_comps = sorted(components, key=lambda c: c.desc_length, reverse=True)[:limit]
    lines = []
    for comp in sorted_comps:
        lines.append(
            f"  - {comp.plugin}/{comp.name} ({comp.type}): {comp.desc_length} chars"
        )
    return "\n".join(lines)


def print_budget_report(
    total_chars: int,
    total_with_overhead: int,
    visible_estimate: int,
    verbose_count: int,
    failed: bool,
    warn_only: bool,
    verbose: list[Component],
    component_count: int,
) -> None:
    """Print full budget validation report."""
    usage_pct = total_with_overhead / BUDGET_LIMIT * 100
    overhead_total = component_count * OVERHEAD_PER_COMPONENT
    print(f"Components: {component_count} ({overhead_total:,} chars overhead)")
    print(f"Description chars: {total_chars:,}")
    print(
        f"Total with overhead: {total_with_overhead:,} / "
        f"{BUDGET_LIMIT:,} ({usage_pct:.1f}% used)"
    )
    print(
        f"Estimated visible at {DESCRIPTION_MAX} char avg: "
        f"~{visible_estimate} of {component_count}"
    )

    if failed:
        print(f"\n❌ BUDGET EXCEEDED by {total_with_overhead - BUDGET_LIMIT:,} chars!")
        print("\nTop offenders:")
        print(format_offenders_list(verbose))
        print(
            f"\n⚠️  Total must be under "
            f"{BUDGET_LIMIT:,} chars "
            f"(with {OVERHEAD_PER_COMPONENT}/skill overhead)."
        )
        print(
            "   See: https://gist.github.com/alexey-pelykh/faa3c304f731d6a962efc5fa2a43abe1"
        )
        print("\nOptimization tips:")
        print("   - Keep descriptions <= 130 chars (optimal for 60+ skills)")
        print("   - Front-load trigger keywords in first 50 chars")
        print("   - Use template: [Verb] [domain]. Use when: [trigger1], [trigger2].")
        print("   - Move details to SKILL.md body -- descriptions are for discovery")

    if warn_only:
        print("\n⚠️  WARNING: Approaching budget limit")
        warn_pct = total_with_overhead / BUDGET_LIMIT * 100
        print(f"   Usage: {total_with_overhead:,} / {BUDGET_LIMIT:,} ({warn_pct:.1f}%)")

    if verbose:
        print(
            f"\n⚠️  {verbose_count} descriptions exceed "
            f"{DESCRIPTION_MAX} chars (recommended max):"
        )
        top_verbose = sorted(verbose, key=lambda c: c.desc_length, reverse=True)
        for comp in top_verbose[:VERBOSE_DISPLAY_LIMIT]:
            print(f"  - {comp.plugin}/{comp.name}: {comp.desc_length} chars")
        if len(verbose) > VERBOSE_DISPLAY_LIMIT:
            remaining = len(verbose) - VERBOSE_DISPLAY_LIMIT
            print(f"  ... and {remaining} more")

    if not failed and not warn_only and not verbose:
        headroom = BUDGET_LIMIT - total_with_overhead
        print(f"✅ Budget check passed! ({headroom:,} chars headroom)")
    elif not failed:
        print("\n✅ Budget check passed (with warnings)")


def main() -> None:
    """Validate description budget across all plugins."""
    args = parse_args()
    base = Path(args.path)

    # Collect all components
    components = collect_components(base)

    # Calculate budget status
    (
        total_chars,
        total_with_overhead,
        visible_estimate,
        verbose_count,
        failed,
        warn_only,
        verbose,
    ) = calculate_budget_status(components)

    # Print report and exit appropriately
    print_budget_report(
        total_chars,
        total_with_overhead,
        visible_estimate,
        verbose_count,
        failed,
        warn_only,
        verbose,
        len(components),
    )

    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
