#!/usr/bin/env python3
"""Export night-market skills to Cursor in a token-efficient format.

The default export creates 551 skill directories totaling 4.5 MB
(~780k tokens). Cursor loads skill descriptions into the system
prompt on every message, creating a massive "token tax."

This script creates a lean export with three strategies:

1. **Tiered export**: only export top-N skills by usage tier
2. **Trimmed content**: strip modules, examples, troubleshooting
3. **Index mode**: generate a single index file instead of
   551 separate directories (for Cursor .mdc rules)

Usage:
    python scripts/cursor_lean_export.py --output ~/.cursor/skills-lean/
    python scripts/cursor_lean_export.py --tier top50
    python scripts/cursor_lean_export.py --index-only --output ~/.cursor/rules/
    python scripts/cursor_lean_export.py --stats
"""

from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path
from typing import Any

PLUGINS_DIR = Path(__file__).resolve().parent.parent / "plugins"
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)

# Tier definitions: skills most useful in Cursor context
TIER_TOP20 = [
    "sanctum:commit-messages",
    "sanctum:pr-prep",
    "sanctum:git-workspace-review",
    "pensive:code-refinement",
    "pensive:bug-review",
    "pensive:architecture-review",
    "pensive:test-review",
    "conserve:bloat-detector",
    "conserve:token-conservation",
    "scribe:slop-detector",
    "scribe:doc-generator",
    "parseltongue:python-testing",
    "parseltongue:python-performance",
    "imbue:proof-of-work",
    "imbue:scope-guard",
    "imbue:catchup",
    "abstract:skill-authoring",
    "abstract:skills-eval",
    "attune:project-brainstorming",
    "pensive:unified-review",
]

TIER_TOP50 = TIER_TOP20 + [
    "sanctum:pr-review",
    "sanctum:test-updates",
    "sanctum:doc-updates",
    "sanctum:version-updates",
    "pensive:shell-review",
    "pensive:makefile-review",
    "parseltongue:python-async",
    "parseltongue:python-packaging",
    "conserve:clear-context",
    "conserve:context-optimization",
    "imbue:diff-analysis",
    "imbue:review-core",
    "imbue:rigorous-reasoning",
    "imbue:structured-output",
    "abstract:create-skill",
    "abstract:create-hook",
    "abstract:validate-plugin",
    "attune:project-specification",
    "attune:project-planning",
    "attune:project-execution",
    "scribe:tech-tutorial",
    "leyline:markdown-formatting",
    "leyline:progressive-loading",
    "leyline:git-platform",
    "leyline:testing-quality-standards",
    "sanctum:do-issue",
    "sanctum:workflow-improvement",
    "pensive:api-review",
    "conserve:cpu-gpu-performance",
    "imbue:feature-review",
]

TIERS = {
    "top20": TIER_TOP20,
    "top50": TIER_TOP50,
    "all": None,  # no filter
}

# Sections to strip for lean export (navigational/meta only).
# Troubleshooting, Testing, Verification, Technical Integration
# are preserved because they contain task-relevant content.
STRIP_SECTIONS_RE = re.compile(
    r"^##\s+(?:Supporting Modules|See Also|Table of Contents)"
    r".*?(?=^##\s|\Z)",
    re.MULTILINE | re.DOTALL,
)


def parse_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    """Parse YAML frontmatter from SKILL.md."""
    match = FRONTMATTER_RE.match(content)
    if not match:
        return {}, content
    raw = match.group(1)
    body = content[match.end() :]
    fm = _parse_yaml_simple(raw)
    return fm, body


def _parse_yaml_simple(text: str) -> dict[str, Any]:
    """Minimal YAML parser for frontmatter."""
    result: dict[str, Any] = {}
    current_key = ""
    for line in text.split("\n"):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("- ") and current_key:
            existing = result.get(current_key, [])
            if not isinstance(existing, list):
                existing = []
            existing.append(stripped[2:].strip().strip("'\""))
            result[current_key] = existing
            continue
        kv = re.match(r"^([a-zA-Z_-]+)\s*:\s*(.*)", line)
        if kv and not line[0].isspace():
            current_key = kv.group(1).strip()
            val = kv.group(2).strip().strip("'\"")
            if val.lower() in ("true", "false"):
                result[current_key] = val.lower() == "true"
            elif val.isdigit():
                result[current_key] = int(val)
            elif val.startswith("[") and val.endswith("]"):
                result[current_key] = [
                    s.strip().strip("'\"") for s in val[1:-1].split(",") if s.strip()
                ]
            elif val:
                result[current_key] = val
            else:
                result[current_key] = ""
            continue
        # Multiline continuation
        if current_key and line[0].isspace():
            prev = result.get(current_key, "")
            if isinstance(prev, str):
                result[current_key] = (prev + " " + stripped).strip()
    return result


def trim_body(body: str) -> str:
    """Strip non-essential sections from skill body."""
    trimmed = STRIP_SECTIONS_RE.sub("", body)
    # Remove module references (lines with modules/*.md links)
    trimmed = re.sub(
        r"^-\s*\[.*?\]\(modules/.*?\).*$\n?",
        "",
        trimmed,
        flags=re.MULTILINE,
    )
    # Collapse multiple blank lines
    trimmed = re.sub(r"\n{3,}", "\n\n", trimmed)
    return trimmed.strip()


def discover_skills() -> list[tuple[str, str, Path]]:
    """Find all SKILL.md files. Returns (plugin, skill_name, path)."""
    results = []
    for skill_md in sorted(PLUGINS_DIR.glob("*/skills/*/SKILL.md")):
        plugin = skill_md.parent.parent.parent.name
        skill_name = skill_md.parent.name
        results.append((plugin, skill_name, skill_md))
    return results


def generate_cursor_mdc(
    fm: dict[str, Any],
    body: str,
    plugin: str,
    skill_name: str,
) -> str:
    """Generate a Cursor .mdc rule file from a skill."""
    desc = fm.get("description", "")
    if isinstance(desc, str):
        # Clean for Cursor: take first sentence only
        desc = re.split(r"(?:Use when|Do not use|DO NOT)", desc)[0].strip()

    globs = fm.get("globs", "")
    always = fm.get("alwaysApply", False)
    model = fm.get("model_hint", "standard")

    lines = [
        "---",
        f"description: {desc}",
        f"globs: {globs}" if globs else "globs:",
        f"alwaysApply: {'true' if always else 'false'}",
        f"# model_hint: {model}",
        f"# source: night-market/{plugin}:{skill_name}",
        "---",
        "",
        body,
    ]
    return "\n".join(lines)


def export_lean(
    output_dir: Path,
    tier: str = "all",
    index_only: bool = False,
    trim: bool = True,
) -> dict[str, Any]:
    """Export skills in lean format. Returns stats."""
    skills = discover_skills()
    tier_filter = TIERS.get(tier)

    if tier_filter is not None:
        filter_set = set(tier_filter)
        skills = [(p, s, path) for p, s, path in skills if f"{p}:{s}" in filter_set]

    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    total_bytes = 0
    exported = 0

    if index_only:
        # Single index file with all skill descriptions
        index_lines = ["# Night Market Skills Index\n"]
        for plugin, skill_name, path in skills:
            content = path.read_text()
            fm, _ = parse_frontmatter(content)
            desc = fm.get("description", "")
            if isinstance(desc, str):
                desc = re.split(r"(?:Use when|Do not use|DO NOT)", desc)[0].strip()
            model = fm.get("model_hint", "standard")
            index_lines.append(f"- **{plugin}:{skill_name}** ({model}): {desc}")
            exported += 1

        index_content = "\n".join(index_lines) + "\n"
        (output_dir / "night-market-skills-index.md").write_text(index_content)
        total_bytes = len(index_content.encode())
    else:
        # Individual skill directories (lean)
        for plugin, skill_name, path in skills:
            content = path.read_text()
            fm, body = parse_frontmatter(content)

            if trim:
                body = trim_body(body)

            mdc_content = generate_cursor_mdc(fm, body, plugin, skill_name)
            skill_dir = output_dir / skill_name
            skill_dir.mkdir(exist_ok=True)
            (skill_dir / "SKILL.md").write_text(mdc_content)
            total_bytes += len(mdc_content.encode())
            exported += 1

    return {
        "exported": exported,
        "total_bytes": total_bytes,
        "total_words": total_bytes // 5,  # rough estimate
        "estimated_tokens": total_bytes // 4,
    }


def show_stats() -> None:
    """Show current vs optimized token costs."""
    skills = discover_skills()

    # Current: full content
    full_bytes = 0
    full_with_modules = 0
    for _, _, path in skills:
        full_bytes += path.stat().st_size
        for md in path.parent.glob("**/*.md"):
            full_with_modules += md.stat().st_size

    # Lean: trimmed content
    lean_bytes = 0
    for _, _, path in skills:
        content = path.read_text()
        _, body = parse_frontmatter(content)
        lean_bytes += len(trim_body(body).encode())

    # Index only: descriptions
    index_bytes = 0
    for _, skill_name, path in skills:
        content = path.read_text()
        fm, _ = parse_frontmatter(content)
        desc = str(fm.get("description", ""))[:100]
        index_bytes += len(f"- {skill_name}: {desc}\n".encode())

    print(f"Skills found: {len(skills)}")
    print()
    print("Token cost comparison:")
    print(
        f"  Full (SKILL.md only):     {full_bytes:>10,} bytes  "
        f"~{full_bytes // 4:>8,} tokens"
    )
    print(
        f"  Full (with modules):      {full_with_modules:>10,} bytes  "
        f"~{full_with_modules // 4:>8,} tokens"
    )
    print(
        f"  Lean (trimmed):           {lean_bytes:>10,} bytes  "
        f"~{lean_bytes // 4:>8,} tokens"
    )
    print(
        f"  Index only:               {index_bytes:>10,} bytes  "
        f"~{index_bytes // 4:>8,} tokens"
    )
    print(
        f"  Top 20 index:             ~{index_bytes * 20 // len(skills):>8,} bytes  "
        f"~{index_bytes * 20 // len(skills) // 4:>6,} tokens"
    )
    print()
    print("Reduction from full+modules to lean:")
    if full_with_modules:
        pct = (1 - lean_bytes / full_with_modules) * 100
        print(f"  {pct:.0f}% reduction")
    print("Reduction from full+modules to index:")
    if full_with_modules:
        pct = (1 - index_bytes / full_with_modules) * 100
        print(f"  {pct:.0f}% reduction")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path.home() / ".cursor" / "skills-lean",
        help="Output directory",
    )
    parser.add_argument(
        "--tier",
        choices=["top20", "top50", "all"],
        default="all",
        help="Skill tier to export",
    )
    parser.add_argument(
        "--index-only",
        action="store_true",
        help="Generate single index file instead of directories",
    )
    parser.add_argument(
        "--no-trim",
        action="store_true",
        help="Skip body trimming (keep full content)",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show token cost comparison without exporting",
    )
    args = parser.parse_args()

    if args.stats:
        show_stats()
        return

    result = export_lean(
        output_dir=args.output,
        tier=args.tier,
        index_only=args.index_only,
        trim=not args.no_trim,
    )

    print(f"Exported {result['exported']} skills to {args.output}/")
    print(f"  Total: {result['total_bytes']:,} bytes")
    print(f"  Est. tokens: ~{result['estimated_tokens']:,}")

    if args.tier != "all":
        print(f"  Tier: {args.tier}")
    if args.index_only:
        print("  Mode: index-only (single file)")


if __name__ == "__main__":
    main()
