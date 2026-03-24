#!/usr/bin/env python3
"""Export night-market skills as OpenClaw/ClawHub-compatible packages.

Reads Claude Code SKILL.md files, translates frontmatter to OpenClaw
format, and generates standalone skill directories ready for ClawHub
submission or bridge plugin use.

Usage:
    python scripts/clawhub-export.py [--output clawhub/] [--top N]
    python scripts/clawhub-export.py --validate
    python scripts/clawhub-export.py --stats
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ---------- constants ----------

PLUGINS_DIR = Path(__file__).resolve().parent.parent / "plugins"
DEFAULT_OUTPUT = Path(__file__).resolve().parent.parent / "clawhub"
CLAWHUB_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)

# Skills most likely to attract OpenClaw users (hand-curated top 20)
TOP_SKILLS = [
    "pensive:code-refinement",
    "pensive:bug-review",
    "pensive:architecture-review",
    "pensive:test-review",
    "pensive:unified-review",
    "conserve:bloat-detector",
    "conserve:token-conservation",
    "conserve:clear-context",
    "scribe:slop-detector",
    "scribe:doc-generator",
    "parseltongue:python-testing",
    "parseltongue:python-performance",
    "sanctum:commit-messages",
    "sanctum:pr-prep",
    "sanctum:pr-review",
    "abstract:skill-authoring",
    "abstract:skills-eval",
    "imbue:proof-of-work",
    "imbue:scope-guard",
    "attune:project-brainstorming",
]


# ---------- YAML parsing (minimal, no pyyaml dependency) ----------


def parse_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    """Parse YAML frontmatter from SKILL.md content.

    Returns (frontmatter_dict, body_text). Uses a minimal parser
    to avoid requiring pyyaml as a dependency.
    """
    match = FRONTMATTER_RE.match(content)
    if not match:
        return {}, content

    raw_yaml = match.group(1)
    body = content[match.end() :]
    fm = _parse_yaml_block(raw_yaml)
    return fm, body


def _parse_yaml_block(text: str) -> dict[str, Any]:
    """Minimal YAML parser for skill frontmatter."""
    result: dict[str, Any] = {}
    current_key: str = ""
    current_list: list[str] | None = None
    multiline_value: list[str] | None = None

    for line in text.split("\n"):
        stripped = line.strip()

        # Skip empty lines and comments
        if not stripped or stripped.startswith("#"):
            if multiline_value is not None:
                multiline_value.append("")
            continue

        # List item
        if stripped.startswith("- ") and current_key:
            if current_list is None:
                current_list = []
            item = stripped[2:].strip().strip("'\"")
            current_list.append(item)
            result[current_key] = current_list
            multiline_value = None
            continue

        # Key-value pair
        kv_match = re.match(r"^([a-zA-Z_-]+)\s*:\s*(.*)", line)
        if kv_match and not line[0].isspace():
            # Save previous multiline
            if multiline_value is not None and current_key:
                result[current_key] = " ".join(
                    ln for ln in multiline_value if ln
                ).strip()

            current_key = kv_match.group(1).strip()
            raw_val = kv_match.group(2).strip()
            current_list = None
            multiline_value = None

            if not raw_val:
                # Could be list or multiline block
                result[current_key] = ""
                continue

            if raw_val in ("|", ">"):
                multiline_value = []
                continue

            if raw_val.startswith("'") and raw_val.endswith("'"):
                raw_val = raw_val[1:-1]
            elif raw_val.startswith('"') and raw_val.endswith('"'):
                raw_val = raw_val[1:-1]

            # Detect inline list [a, b, c]
            if raw_val.startswith("[") and raw_val.endswith("]"):
                items = [
                    s.strip().strip("'\"")
                    for s in raw_val[1:-1].split(",")
                    if s.strip()
                ]
                result[current_key] = items
                continue

            # Detect numeric
            if raw_val.isdigit():
                result[current_key] = int(raw_val)
                continue

            # Detect boolean
            if raw_val.lower() in ("true", "false"):
                result[current_key] = raw_val.lower() == "true"
                continue

            result[current_key] = raw_val
            continue

        # Continuation of multiline value
        if multiline_value is not None:
            multiline_value.append(stripped)
            continue

        # Indented continuation of a scalar value
        if current_key and line[0].isspace() and current_list is None:
            prev = result.get(current_key, "")
            if isinstance(prev, str):
                if multiline_value is None:
                    multiline_value = [prev, stripped] if prev else [stripped]
                else:
                    multiline_value.append(stripped)
                continue

    # Flush final multiline
    if multiline_value is not None and current_key:
        result[current_key] = " ".join(ln for ln in multiline_value if ln).strip()

    return result


# ---------- format translation ----------


def to_clawhub_slug(plugin: str, skill_name: str) -> str:
    """Generate a valid ClawHub slug from plugin:skill name."""
    slug = f"nm-{plugin}-{skill_name}"
    slug = slug.lower().replace("_", "-")
    slug = re.sub(r"[^a-z0-9-]", "", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug


def extract_triggers(fm: dict[str, Any]) -> list[str]:
    """Extract semantic triggers from description and tags."""
    triggers = []

    # Use tags directly as triggers
    tags = fm.get("tags", [])
    if isinstance(tags, list):
        triggers.extend(tags)

    # Extract key phrases from description
    desc = fm.get("description", "")
    if isinstance(desc, str):
        # Pull "Use when" phrases
        use_match = re.search(r"Use when[:\s]+(.+?)(?:\.|Do not|$)", desc)
        if use_match:
            phrases = [
                p.strip() for p in use_match.group(1).split(",") if len(p.strip()) > 3
            ]
            triggers.extend(phrases[:5])

    return triggers[:15]  # ClawHub recommends max 15


def translate_frontmatter(
    fm: dict[str, Any],
    plugin_name: str,
    plugin_version: str = "1.7.0",
) -> dict[str, Any]:
    """Translate Claude Code frontmatter to OpenClaw skill format."""
    openclaw_fm: dict[str, Any] = {}

    # Direct mappings
    openclaw_fm["name"] = fm.get("name", "unknown")
    openclaw_fm["description"] = _clean_description(fm.get("description", ""))
    openclaw_fm["version"] = plugin_version

    # Generate triggers from tags + description
    triggers = extract_triggers(fm)
    if triggers:
        openclaw_fm["triggers"] = triggers

    # Map dependencies to metadata.openclaw.requires
    deps = fm.get("dependencies", [])
    metadata: dict[str, Any] = {
        "openclaw": {
            "homepage": (
                f"https://github.com/athola/claude-night-market"
                f"/tree/master/plugins/{plugin_name}"
            ),
            "emoji": _category_emoji(fm.get("category", "")),
        }
    }

    if deps:
        if isinstance(deps, list):
            metadata["openclaw"]["requires"] = {
                "config": [f"night-market.{d}" for d in deps if isinstance(d, str)]
            }

    openclaw_fm["metadata"] = json.dumps(metadata)

    # Provenance
    openclaw_fm["source"] = "claude-night-market"
    openclaw_fm["source_plugin"] = plugin_name

    return openclaw_fm


def _clean_description(desc: str) -> str:
    """Clean description for OpenClaw (single line, no Claude Code hints)."""
    if not isinstance(desc, str):
        return str(desc)
    # Remove "Use when" / "Do not use" guidance (OpenClaw uses triggers)
    cleaned = re.split(r"\s*(?:Use when|Do not use|DO NOT)", desc)[0]
    # Collapse whitespace
    cleaned = " ".join(cleaned.split())
    return cleaned.strip().rstrip(".")


def _category_emoji(category: str) -> str:
    """Map category to emoji for ClawHub display."""
    mapping = {
        "code-review": "🔍",
        "testing": "🧪",
        "writing-quality": "✍️",
        "workflow-automation": "⚙️",
        "architecture": "🏗️",
        "architectural-pattern": "🏗️",
        "meta-skills": "🧠",
        "skill-development": "🛠️",
        "documentation": "📝",
        "performance": "⚡",
        "security": "🔒",
        "git": "🌿",
    }
    return mapping.get(category, "🦞")


# ---------- skill discovery ----------


def discover_skills(
    plugins_dir: Path,
) -> list[tuple[str, str, Path]]:
    """Discover all SKILL.md files across plugins.

    Returns list of (plugin_name, skill_name, skill_path).
    """
    skills = []
    for plugin_dir in sorted(plugins_dir.iterdir()):
        if not plugin_dir.is_dir():
            continue
        skills_dir = plugin_dir / "skills"
        if not skills_dir.is_dir():
            continue
        for skill_dir in sorted(skills_dir.iterdir()):
            if not skill_dir.is_dir():
                continue
            skill_md = skill_dir / "SKILL.md"
            if skill_md.exists():
                skills.append((plugin_dir.name, skill_dir.name, skill_md))
    return skills


def get_plugin_version(plugin_dir: Path) -> str:
    """Read version from .claude-plugin/plugin.json."""
    pj = plugin_dir / ".claude-plugin" / "plugin.json"
    if pj.exists():
        try:
            data = json.loads(pj.read_text())
            return data.get("version", "1.0.0")
        except (json.JSONDecodeError, OSError):
            pass
    return "1.0.0"


# ---------- export ----------


def generate_openclaw_skill_md(
    openclaw_fm: dict[str, Any],
    body: str,
) -> str:
    """Generate OpenClaw-compatible SKILL.md content."""
    lines = ["---"]

    for key in ["name", "description", "version"]:
        val = openclaw_fm.get(key, "")
        if isinstance(val, str) and ("\n" in val or len(val) > 80):
            lines.append(f"{key}: |")
            for subline in val.split("\n"):
                lines.append(f"  {subline}")
        else:
            lines.append(f"{key}: {val}")

    triggers = openclaw_fm.get("triggers", [])
    if triggers:
        lines.append("triggers:")
        for t in triggers:
            lines.append(f"  - {t}")

    metadata = openclaw_fm.get("metadata", "")
    if metadata:
        lines.append(f"metadata: {metadata}")

    # Provenance fields
    lines.append(f"source: {openclaw_fm.get('source', 'claude-night-market')}")
    lines.append(f"source_plugin: {openclaw_fm.get('source_plugin', 'unknown')}")

    lines.append("---")
    lines.append("")

    # Add provenance notice to body
    plugin = openclaw_fm.get("source_plugin", "unknown")
    provenance = (
        f"> **Night Market Skill** — ported from "
        f"[claude-night-market/{plugin}]"
        f"(https://github.com/athola/claude-night-market"
        f"/tree/master/plugins/{plugin}). "
        f"For the full experience with agents, hooks, and commands, "
        f"install the Claude Code plugin.\n\n"
    )
    lines.append(provenance)
    lines.append(body)

    return "\n".join(lines)


def export_skill(
    plugin_name: str,
    skill_name: str,
    skill_path: Path,
    output_dir: Path,
    plugin_version: str,
) -> str | None:
    """Export a single skill to ClawHub format.

    Returns the ClawHub slug or None on failure.
    """
    content = skill_path.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(content)

    if not fm.get("name"):
        return None

    slug = to_clawhub_slug(plugin_name, skill_name)

    if not CLAWHUB_SLUG_RE.match(slug):
        print(f"  WARN: invalid slug '{slug}', skipping", file=sys.stderr)
        return None

    openclaw_fm = translate_frontmatter(fm, plugin_name, plugin_version)

    # Create skill directory
    skill_out = output_dir / slug
    skill_out.mkdir(parents=True, exist_ok=True)

    # Write SKILL.md
    skill_content = generate_openclaw_skill_md(openclaw_fm, body)
    (skill_out / "SKILL.md").write_text(skill_content, encoding="utf-8")

    # Copy supporting modules if they exist
    modules_dir = skill_path.parent / "modules"
    if modules_dir.is_dir():
        dest_modules = skill_out / "modules"
        if dest_modules.exists():
            shutil.rmtree(dest_modules)
        shutil.copytree(
            modules_dir,
            dest_modules,
            ignore=shutil.ignore_patterns("*.pyc", "__pycache__"),
        )

    return slug


def export_all(
    output_dir: Path,
    top_n: int = 0,
    plugins_dir: Path | None = None,
) -> dict[str, Any]:
    """Export all (or top N) skills to ClawHub format.

    Returns manifest dict with export metadata.
    """
    if plugins_dir is None:
        plugins_dir = PLUGINS_DIR

    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    all_skills = discover_skills(plugins_dir)

    # Filter to top skills if requested
    if top_n > 0:
        top_set = set(TOP_SKILLS[:top_n])
        all_skills = [
            (p, s, path) for p, s, path in all_skills if f"{p}:{s}" in top_set
        ]

    exported = []
    errors = []

    for plugin_name, skill_name, skill_path in all_skills:
        version = get_plugin_version(plugins_dir / plugin_name)
        slug = export_skill(plugin_name, skill_name, skill_path, output_dir, version)
        if slug:
            exported.append(
                {
                    "slug": slug,
                    "source": f"{plugin_name}:{skill_name}",
                    "version": version,
                }
            )
        else:
            errors.append(f"{plugin_name}:{skill_name}")

    # Write export manifest
    manifest = {
        "generator": "claude-night-market/clawhub-export",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_exported": len(exported),
        "total_errors": len(errors),
        "skills": exported,
        "errors": errors,
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )

    return manifest


# ---------- validation ----------


def validate_export(output_dir: Path) -> list[str]:
    """Validate exported ClawHub packages."""
    issues = []

    if not output_dir.exists():
        return ["Output directory does not exist. Run export first."]

    manifest_path = output_dir / "manifest.json"
    if not manifest_path.exists():
        return ["No manifest.json found. Run export first."]

    manifest = json.loads(manifest_path.read_text())

    for skill_info in manifest.get("skills", []):
        slug = skill_info["slug"]
        skill_dir = output_dir / slug

        if not skill_dir.is_dir():
            issues.append(f"{slug}: directory missing")
            continue

        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            issues.append(f"{slug}: SKILL.md missing")
            continue

        content = skill_md.read_text()
        fm, _ = parse_frontmatter(content)

        if not fm.get("name"):
            issues.append(f"{slug}: missing 'name' in frontmatter")
        if not fm.get("description"):
            issues.append(f"{slug}: missing 'description' in frontmatter")
        if not fm.get("version"):
            issues.append(f"{slug}: missing 'version' in frontmatter")
        if not CLAWHUB_SLUG_RE.match(slug):
            issues.append(f"{slug}: invalid slug format")

        # Check bundle size
        total_size = sum(f.stat().st_size for f in skill_dir.rglob("*") if f.is_file())
        if total_size > 50 * 1024 * 1024:
            issues.append(f"{slug}: exceeds 50MB bundle limit")

    return issues


# ---------- stats ----------


def print_stats(plugins_dir: Path | None = None) -> None:
    """Print statistics about discoverable skills."""
    if plugins_dir is None:
        plugins_dir = PLUGINS_DIR

    all_skills = discover_skills(plugins_dir)
    plugins: dict[str, int] = {}
    for p, _s, _path in all_skills:
        plugins[p] = plugins.get(p, 0) + 1

    print(f"Total skills:  {len(all_skills)}")
    print(f"Total plugins: {len(plugins)}")
    print()
    print("Per plugin:")
    for name, count in sorted(plugins.items(), key=lambda x: -x[1]):
        top_count = sum(
            1 for p, s, _ in all_skills if f"{p}:{s}" in TOP_SKILLS and p == name
        )
        marker = f" ({top_count} in top-20)" if top_count else ""
        print(f"  {name:20s} {count:3d} skills{marker}")


# ---------- CLI ----------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export night-market skills for ClawHub/OpenClaw"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Output directory (default: clawhub/)",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=0,
        help="Export only top N most marketable skills (default: all)",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate existing export",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Print skill statistics",
    )
    parser.add_argument(
        "--plugins-dir",
        type=Path,
        default=PLUGINS_DIR,
        help="Plugins directory (default: auto-detect)",
    )

    args = parser.parse_args()

    if args.stats:
        print_stats(args.plugins_dir)
        return

    if args.validate:
        issues = validate_export(args.output)
        if issues:
            print(f"Validation found {len(issues)} issues:")
            for issue in issues:
                print(f"  - {issue}")
            sys.exit(1)
        else:
            print("Validation passed.")
        return

    manifest = export_all(args.output, args.top, args.plugins_dir)
    print(f"Exported {manifest['total_exported']} skills to {args.output}/")
    if manifest["total_errors"] > 0:
        print(f"  {manifest['total_errors']} skills had errors (see manifest.json)")


if __name__ == "__main__":
    main()
