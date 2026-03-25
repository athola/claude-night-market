#!/usr/bin/env python3
"""Add cross-framework frontmatter fields to all SKILL.md files.

Adds fields needed by Copilot (version) and Cursor (globs, alwaysApply)
so that export pipelines can derive the correct instruction/rule mode
for each target framework.

- version: pulled from the parent plugin's plugin.json
- globs: derived from plugin name, category, and tags heuristics
- alwaysApply: true only for always-on behavioral skills

Usage:
    python scripts/add_cross_framework_fields.py            # dry-run
    python scripts/add_cross_framework_fields.py --write    # apply changes
    python scripts/add_cross_framework_fields.py --stats    # show derivation summary
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

PLUGINS_DIR = Path(__file__).resolve().parent.parent / "plugins"
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)

# ---------- globs derivation heuristics ----------

# Plugin-level overrides: if the entire plugin is language-specific
PLUGIN_GLOBS: dict[str, str | None] = {
    "parseltongue": "**/*.py",
    "lean4": "**/*.lean",
}

# Category-level globs
CATEGORY_GLOBS: dict[str, str | None] = {
    "code-review": None,  # generic, agent-requested
    "code-quality": None,
    "testing": None,
    "infrastructure": None,
    "conservation": None,
    "workflow": None,
    "workflow-methodology": None,
    "workflow-automation": None,
    "workflow-orchestration": None,
    "orchestration": None,
    "architecture": None,
    "architecture-decision": None,
    "architectural-pattern": None,
    "meta-skills": None,
    "meta-infrastructure": None,
    "skill-development": None,
    "skill-management": None,
    "plugin-management": None,
    "hook-development": None,
    "hook-management": None,
    "rule-management": None,
    "agent-workflow": None,
    "artifact-generation": None,
    "documentation": "**/*.md",
    "writing-quality": "**/*.md",
    "review": None,
    "review-patterns": None,
    "audit": None,
    "analysis-methods": None,
    "output-patterns": None,
    "media-generation": None,
    "setup": None,
    "async": "**/*.py",
    "packaging": "**/*.py",
    "performance": None,
    "optimization": None,
    "resource-optimization": None,
    "research": None,
    "synthesis": None,
    "governance": None,
    "project-management": None,
    "strategic-planning": None,
    "project-initialization": None,
    "workspace-ops": None,
    "delegation-framework": None,
    "delegation-implementation": None,
    "navigation": None,
    "cultivation": None,
    "session-management": None,
    "cross-plugin-patterns": None,
    "planning": None,
    "specification": None,
    "methodology": None,
    "specialized": None,
    "development": None,
    "build": None,
    "testing-automation": None,
}

# Tag-level overrides (checked if no plugin/category match)
TAG_GLOBS: dict[str, str] = {
    "python": "**/*.py",
    "rust": "**/*.rs",
    "lean": "**/*.lean",
    "lean4": "**/*.lean",
    "shell": "**/*.sh",
    "makefile": "**/Makefile",
    "markdown": "**/*.md",
}

# Skill-specific overrides by plugin:skill-name
SKILL_OVERRIDES: dict[str, dict[str, Any]] = {
    # Rust-specific pensive skill
    "pensive:rust-review": {"globs": "**/*.rs"},
    # Shell-specific pensive skill
    "pensive:shell-review": {"globs": "**/*.sh"},
    # Makefile-specific pensive skill
    "pensive:makefile-review": {"globs": "**/Makefile"},
    # Math review: no specific globs
    "pensive:math-review": {"globs": None},
    # Markdown formatting cross-plugin
    "leyline:markdown-formatting": {"globs": "**/*.md"},
    # Pytest config
    "leyline:pytest-config": {
        "globs": ["**/conftest.py", "**/pytest.ini", "**/pyproject.toml"]
    },
    # Testing quality standards
    "leyline:testing-quality-standards": {"globs": "**/test_*.py"},
    # Attune makefile generation
    "attune:makefile-generation": {"globs": "**/Makefile"},
    # Attune precommit
    "attune:precommit-setup": {"globs": "**/.pre-commit-config.yaml"},
    # Attune workflow setup (CI files)
    "attune:workflow-setup": {"globs": "**/.github/workflows/*.yml"},
    # Scribe skills target markdown
    "scribe:slop-detector": {"globs": "**/*.md"},
    "scribe:doc-generator": {"globs": "**/*.md"},
    "scribe:style-learner": {"globs": "**/*.md"},
    "scribe:tech-tutorial": {"globs": "**/*.md"},
    # Git-related sanctum skills
    "sanctum:commit-messages": {"globs": None},
    "sanctum:pr-prep": {"globs": None},
    "sanctum:pr-review": {"globs": None},
}

# Skills that should be alwaysApply: true
# These are behavioral modifiers that shape every interaction
ALWAYS_APPLY_SKILLS: set[str] = {
    "conserve:token-conservation",
    "conserve:response-compression",
    "conserve:decisive-action",
    "conserve:code-quality-principles",
    "conserve:smart-sourcing",
    "leyline:stewardship",
}


# ---------- frontmatter manipulation ----------


def parse_frontmatter_raw(content: str) -> tuple[str, str]:
    """Split content into raw frontmatter YAML and body."""
    match = FRONTMATTER_RE.match(content)
    if not match:
        return "", content
    return match.group(1), content[match.end() :]


def parse_yaml_value(raw: str) -> Any:
    """Parse a single YAML value (minimal)."""
    raw = raw.strip()
    if not raw:
        return ""
    if raw.lower() == "true":
        return True
    if raw.lower() == "false":
        return False
    if raw.isdigit():
        return int(raw)
    if raw.startswith("'") and raw.endswith("'"):
        return raw[1:-1]
    if raw.startswith('"') and raw.endswith('"'):
        return raw[1:-1]
    return raw


def get_fm_field(raw_yaml: str, field: str) -> str | None:
    """Extract a top-level field value from raw YAML text."""
    pattern = re.compile(rf"^{re.escape(field)}\s*:\s*(.+)$", re.MULTILINE)
    m = pattern.search(raw_yaml)
    if m:
        return m.group(1).strip()
    return None


def get_fm_tags(raw_yaml: str) -> list[str]:
    """Extract tags list from raw YAML."""
    tags: list[str] = []
    in_tags = False
    for line in raw_yaml.split("\n"):
        if re.match(r"^tags\s*:", line):
            in_tags = True
            # Check inline list
            inline = re.match(r"^tags\s*:\s*\[(.+)\]", line)
            if inline:
                return [
                    t.strip().strip("'\"")
                    for t in inline.group(1).split(",")
                    if t.strip()
                ]
            continue
        if in_tags:
            if line.startswith("- "):
                tags.append(line[2:].strip().strip("'\""))
            elif line.startswith("  - "):
                tags.append(line[4:].strip().strip("'\""))
            elif line.strip() and not line[0].isspace():
                break
    return tags


def derive_globs(
    plugin_name: str,
    skill_name: str,
    category: str,
    tags: list[str],
) -> Any | None:
    """Derive globs value from heuristics. Returns str, list, or None."""
    key = f"{plugin_name}:{skill_name}"

    # 1. Explicit skill override
    if key in SKILL_OVERRIDES:
        return SKILL_OVERRIDES[key].get("globs")

    # 2. Plugin-level
    if plugin_name in PLUGIN_GLOBS:
        return PLUGIN_GLOBS[plugin_name]

    # 3. Category-level
    if category in CATEGORY_GLOBS:
        return CATEGORY_GLOBS[category]

    # 4. Tag-level: first matching tag wins
    for tag in tags:
        if tag in TAG_GLOBS:
            return TAG_GLOBS[tag]

    return None


def derive_always_apply(plugin_name: str, skill_name: str) -> bool:
    """Determine if skill should be alwaysApply: true."""
    return f"{plugin_name}:{skill_name}" in ALWAYS_APPLY_SKILLS


def format_globs_yaml(globs: Any) -> str:
    """Format globs value for YAML frontmatter."""
    if globs is None:
        return ""
    if isinstance(globs, list):
        items = ", ".join(f'"{g}"' for g in globs)
        return f"globs: [{items}]"
    return f'globs: "{globs}"'


def insert_fields(
    raw_yaml: str,
    version: str,
    globs: Any,
    always_apply: bool,
) -> str:
    """Insert version, globs, and alwaysApply into raw YAML frontmatter.

    Inserts after the 'name' line (or 'description' block) to keep
    the frontmatter logically grouped: identity fields first, then
    cross-framework fields, then existing metadata.
    """
    lines = raw_yaml.split("\n")
    new_lines: list[str] = []

    # Fields to insert
    fields_to_add: list[str] = []
    fields_to_add.append(f"version: {version}")
    if globs is not None:
        fields_to_add.append(format_globs_yaml(globs))
    fields_to_add.append(f"alwaysApply: {'true' if always_apply else 'false'}")

    # Find insertion point: after description block ends
    # (description can be multiline with quotes or >)
    inserted = False
    i = 0
    while i < len(lines):
        line = lines[i]
        new_lines.append(line)

        # Skip if these fields already exist (update them)
        if re.match(r"^version\s*:", line):
            new_lines[-1] = f"version: {version}"
            i += 1
            continue
        if re.match(r"^globs\s*:", line):
            if globs is not None:
                new_lines[-1] = format_globs_yaml(globs)
            else:
                # Remove the line
                new_lines.pop()
            i += 1
            continue
        if re.match(r"^alwaysApply\s*:", line):
            new_lines[-1] = f"alwaysApply: {'true' if always_apply else 'false'}"
            inserted = True
            i += 1
            continue

        # Insert after description block
        if not inserted and re.match(r"^description\s*:", line):
            # Description might be multiline (quoted or block scalar)
            desc_val = re.match(r"^description\s*:\s*(.*)", line)
            if desc_val:
                val = desc_val.group(1).strip()
                if val.startswith("'") and not val.endswith("'"):
                    # Multi-line single-quoted
                    i += 1
                    while i < len(lines) and not lines[i].rstrip().endswith("'"):
                        new_lines.append(lines[i])
                        i += 1
                    if i < len(lines):
                        new_lines.append(lines[i])
                elif val.startswith('"') and not val.endswith('"'):
                    # Multi-line double-quoted
                    i += 1
                    while i < len(lines) and not lines[i].rstrip().endswith('"'):
                        new_lines.append(lines[i])
                        i += 1
                    if i < len(lines):
                        new_lines.append(lines[i])
                elif val in (">", "|", ">-", "|-"):
                    # Block scalar
                    i += 1
                    while i < len(lines) and (
                        lines[i].startswith("  ") or not lines[i].strip()
                    ):
                        new_lines.append(lines[i])
                        i += 1
                    i -= 1  # Back up; outer loop will increment

            # Now insert our fields
            for field in fields_to_add:
                # Don't insert if already handled above
                field_name = field.split(":")[0]
                if not any(
                    re.match(rf"^{re.escape(field_name)}\s*:", ln) for ln in lines
                ):
                    new_lines.append(field)
            inserted = True

        i += 1

    # Fallback: insert at end if description wasn't found
    if not inserted:
        for field in fields_to_add:
            field_name = field.split(":")[0]
            if not any(re.match(rf"^{re.escape(field_name)}\s*:", ln) for ln in lines):
                new_lines.append(field)

    return "\n".join(new_lines)


# ---------- plugin version lookup ----------


def get_plugin_version(plugin_dir: Path) -> str:
    """Read version from .claude-plugin/plugin.json."""
    pj = plugin_dir / ".claude-plugin" / "plugin.json"
    if pj.exists():
        try:
            data = json.loads(pj.read_text())
            return data.get("version", "1.0.0")
        except (json.JSONDecodeError, OSError) as e:
            print(
                f"Warning: Could not read version from {pj}: {e}. "
                f"Using default '1.0.0'.",
                file=sys.stderr,
            )
    return "1.0.0"


# ---------- main logic ----------


def process_skill(
    skill_path: Path,
    plugin_name: str,
    version: str,
    write: bool = False,
) -> dict[str, Any]:
    """Process a single SKILL.md file. Returns info dict."""
    content = skill_path.read_text(encoding="utf-8")
    raw_yaml, body = parse_frontmatter_raw(content)

    if not raw_yaml:
        return {"path": str(skill_path), "status": "no-frontmatter"}

    skill_name = get_fm_field(raw_yaml, "name") or skill_path.parent.name
    category = get_fm_field(raw_yaml, "category") or ""
    tags = get_fm_tags(raw_yaml)

    globs = derive_globs(plugin_name, skill_name, category, tags)
    always_apply = derive_always_apply(plugin_name, skill_name)

    # Check if fields already present
    has_version = get_fm_field(raw_yaml, "version") is not None
    has_globs = get_fm_field(raw_yaml, "globs") is not None
    has_always = get_fm_field(raw_yaml, "alwaysApply") is not None

    new_yaml = insert_fields(raw_yaml, version, globs, always_apply)
    new_content = f"---\n{new_yaml}\n---\n{body}"

    changed = new_content != content

    if write and changed:
        skill_path.write_text(new_content, encoding="utf-8")

    return {
        "path": str(skill_path),
        "plugin": plugin_name,
        "skill": skill_name,
        "version": version,
        "globs": globs,
        "alwaysApply": always_apply,
        "had_version": has_version,
        "had_globs": has_globs,
        "had_alwaysApply": has_always,
        "changed": changed,
        "status": "updated"
        if (write and changed)
        else ("unchanged" if not changed else "dry-run"),
    }


def discover_skills(plugins_dir: Path) -> list[tuple[str, Path]]:
    """Discover all SKILL.md files. Returns (plugin_name, path) pairs."""
    results = []
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
                results.append((plugin_dir.name, skill_md))
    return results


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Add cross-framework frontmatter fields to SKILL.md files"
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write changes (default: dry-run)",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show derivation summary",
    )
    parser.add_argument(
        "--plugins-dir",
        type=Path,
        default=PLUGINS_DIR,
        help="Plugins directory",
    )
    args = parser.parse_args()

    skills = discover_skills(args.plugins_dir)
    results: list[dict[str, Any]] = []

    for plugin_name, skill_path in skills:
        version = get_plugin_version(args.plugins_dir / plugin_name)
        info = process_skill(skill_path, plugin_name, version, write=args.write)
        results.append(info)

    # Print summary
    changed = [r for r in results if r.get("changed")]
    unchanged = [r for r in results if not r.get("changed")]

    if args.stats:
        # Globs distribution
        globs_dist: dict[str, int] = {}
        for r in results:
            g = str(r.get("globs") or "None (agent-requested)")
            globs_dist[g] = globs_dist.get(g, 0) + 1

        print("Globs distribution:")
        for g, count in sorted(globs_dist.items(), key=lambda x: -x[1]):
            print(f"  {g:40s} {count:3d} skills")

        print()
        always_count = sum(1 for r in results if r.get("alwaysApply"))
        print(f"alwaysApply: true  = {always_count}")
        print(f"alwaysApply: false = {len(results) - always_count}")
        print()

    mode = "WRITTEN" if args.write else "DRY-RUN"
    print(f"[{mode}] {len(results)} skills processed")
    print(f"  {len(changed)} would change")
    print(f"  {len(unchanged)} already up-to-date")

    if not args.write and changed:
        print()
        print("Run with --write to apply changes.")

    # Show first few changes for review
    if changed and not args.write:
        print()
        print("Sample changes:")
        for r in changed[:5]:
            g = r.get("globs") or "None"
            a = r.get("alwaysApply")
            print(
                f"  {r['plugin']}:{r['skill']}"
                f"  version={r['version']}"
                f"  globs={g}"
                f"  alwaysApply={a}"
            )
        if len(changed) > 5:
            print(f"  ... and {len(changed) - 5} more")


if __name__ == "__main__":
    main()
