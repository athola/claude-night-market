#!/usr/bin/env python3
"""Validate skill and command description budget for Claude Code system prompt."""

import argparse
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

# Claude Code budgets a portion of the context window for skill metadata
# in the available_skills section. With 1M context, the original 2%
# allocation gave 16,000 chars, but at 326 components in this marketplace
# the per-component overhead alone (326 * 109 = 35,534 chars) consumes
# most of a 6% budget before a single description is counted. The
# realistic ceiling, with every component at the 160-char description
# cap, is 326 * (160 + 109) = 87,694 chars. The budget is set to ~9% of
# 1M (90,000) to cover that ceiling with modest headroom. The real
# quality gate stays the per-description 160-char cap (DESCRIPTION_MAX),
# which is the only hard-fail condition; the total is a warning so a
# growing component count never silently blocks unrelated commits.
# See: https://gist.github.com/alexey-pelykh/faa3c304f731d6a962efc5fa2a43abe1
# and github.com/anthropics/claude-code #11045.
DEFAULT_BUDGET = 90000  # ~9% of 1M context, covers 326 components at 160-char cap
OVERHEAD_PER_COMPONENT = 109  # XML tags, name, location per skill/cmd
BUDGET_LIMIT = int(os.environ.get("SLASH_COMMAND_TOOL_CHAR_BUDGET", DEFAULT_BUDGET))
WARN_THRESHOLD = int(BUDGET_LIMIT * 0.90)  # Warn at 90% usage
DESCRIPTION_MAX = 160  # Max chars per description
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
    """Extract description field from YAML frontmatter.

    Handles three YAML scalar styles:

    - Single-line: ``description: text`` (with or without quotes)
    - Literal block: ``description: |`` followed by indented lines
      (newlines preserved)
    - Folded block: ``description: >`` or ``description: >-`` followed
      by indented lines (newlines collapsed to spaces)

    Folded-block detection was missing from the original parser, which
    caused 5 SKILL.md files using ``description: >`` to be flagged
    as "malformed" by length-budget tooling. Audit doc 2026-04-25
    captures the false-positive set.
    """
    # Match block-scalar styles (literal `|` or folded `>`, optional `-`)
    block_match = re.search(
        r"^description:\s*([|>])(-?)\s*\n((?:  .+\n)*)", content, re.MULTILINE
    )
    if block_match:
        indicator = block_match.group(1)
        body = block_match.group(3)
        # Strip the 2-space leading indent from each line
        lines = [
            line[2:] if line.startswith("  ") else line.lstrip()
            for line in body.split("\n")
        ]
        joined = (
            "\n".join(lines).strip() if indicator == "|" else " ".join(lines).strip()
        )
        # Collapse multiple internal spaces from folded joins
        return re.sub(r"\s+", " ", joined).strip() if indicator == ">" else joined

    # Single-line description (with or without surrounding quotes)
    match = re.search(r"^description:\s*(.+)$", content, re.MULTILINE)
    if match:
        text = match.group(1).strip()
        # Strip surrounding single or double quotes if present
        if (text.startswith("'") and text.endswith("'")) or (
            text.startswith('"') and text.endswith('"')
        ):
            text = text[1:-1]
        return text

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
    # Estimate how many skills would be visible at ~160 char avg desc
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


@dataclass(frozen=True)
class BudgetReport:
    """Tallies for a full budget validation report."""

    total_chars: int
    total_with_overhead: int
    visible_estimate: int
    verbose_count: int
    failed: bool
    warn_only: bool
    verbose: list[Component]
    component_count: int

    @property
    def usage_pct(self) -> float:
        """Percent of the budget consumed, overhead included."""
        return self.total_with_overhead / BUDGET_LIMIT * 100

    @property
    def overhead_total(self) -> int:
        """Total fixed per-component overhead charged against the budget."""
        return self.component_count * OVERHEAD_PER_COMPONENT


def print_budget_report(report: BudgetReport) -> None:
    """Print full budget validation report."""
    print(
        f"Components: {report.component_count} "
        f"({report.overhead_total:,} chars overhead)"
    )
    print(f"Description chars: {report.total_chars:,}")
    print(
        f"Total with overhead: {report.total_with_overhead:,} / "
        f"{BUDGET_LIMIT:,} ({report.usage_pct:.1f}% used)"
    )
    print(
        f"Estimated visible at {DESCRIPTION_MAX} char avg: "
        f"~{report.visible_estimate} of {report.component_count}"
    )

    if report.failed:
        print(
            f"\n❌ BUDGET EXCEEDED by "
            f"{report.total_with_overhead - BUDGET_LIMIT:,} chars!"
        )
        print("\nTop offenders:")
        print(format_offenders_list(report.verbose))
        print(
            f"\n⚠️  Total must be under "
            f"{BUDGET_LIMIT:,} chars "
            f"(with {OVERHEAD_PER_COMPONENT}/skill overhead)."
        )
        print(
            "   See: https://gist.github.com/alexey-pelykh/faa3c304f731d6a962efc5fa2a43abe1"
        )
        print("\nOptimization tips:")
        print("   - Keep descriptions <= 160 chars (budget for 1M context)")
        print("   - Front-load trigger keywords in first 50 chars")
        print("   - Use template: [Verb] [domain]. Use when: [trigger1], [trigger2].")
        print("   - Move details to SKILL.md body -- descriptions are for discovery")

    if report.warn_only:
        print("\n⚠️  WARNING: Approaching budget limit")
        print(
            f"   Usage: {report.total_with_overhead:,} / "
            f"{BUDGET_LIMIT:,} ({report.usage_pct:.1f}%)"
        )

    if report.verbose:
        print(
            f"\n⚠️  {report.verbose_count} descriptions exceed "
            f"{DESCRIPTION_MAX} chars (recommended max):"
        )
        top_verbose = sorted(report.verbose, key=lambda c: c.desc_length, reverse=True)
        for comp in top_verbose[:VERBOSE_DISPLAY_LIMIT]:
            print(f"  - {comp.plugin}/{comp.name}: {comp.desc_length} chars")
        if len(report.verbose) > VERBOSE_DISPLAY_LIMIT:
            remaining = len(report.verbose) - VERBOSE_DISPLAY_LIMIT
            print(f"  ... and {remaining} more")

    if not report.failed and not report.warn_only and not report.verbose:
        headroom = BUDGET_LIMIT - report.total_with_overhead
        print(f"✅ Budget check passed! ({headroom:,} chars headroom)")
    elif not report.failed:
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
        BudgetReport(
            total_chars=total_chars,
            total_with_overhead=total_with_overhead,
            visible_estimate=visible_estimate,
            verbose_count=verbose_count,
            failed=failed,
            warn_only=warn_only,
            verbose=verbose,
            component_count=len(components),
        )
    )

    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
