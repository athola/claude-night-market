#!/usr/bin/env python3
"""
Fix skill descriptions to follow Claude Code official format.

Format: "[What it does]. Use when [scenarios]. Do not use when [anti-patterns]."

All discovery info must be in the `description` field - custom fields like
`triggers`, `use_when`, `do_not_use_when` are ignored by Claude Code.
"""

import re
from pathlib import Path

import yaml


def consolidate_description(frontmatter: dict) -> str:
    """
    Consolidate description, triggers, use_when, do_not_use_when into single description.

    Format: "[What it does]. Use when [scenarios]. Do not use when [anti-patterns]."
    """
    desc = frontmatter.get("description", "").strip()
    triggers = frontmatter.get("triggers", "")
    use_when = frontmatter.get("use_when", "")
    do_not_use_when = frontmatter.get("do_not_use_when", "")

    # Handle list-type triggers
    if isinstance(triggers, list):
        triggers = ", ".join(triggers)

    # Build consolidated description
    parts = []

    # 1. Main description (what it does) - first
    if desc:
        # Remove any existing "Use when:" or "Triggers:" from description
        desc = re.sub(r"\s*Use when:.*$", "", desc, flags=re.IGNORECASE)
        desc = re.sub(r"\s*Triggers:.*$", "", desc, flags=re.IGNORECASE)
        desc = re.sub(r"\s*Do not use when:.*$", "", desc, flags=re.IGNORECASE)
        desc = desc.strip().rstrip(".")
        if desc:
            parts.append(desc)

    # 2. Use when (or triggers if no use_when)
    if use_when:
        use_when = use_when.strip().rstrip(".")
        parts.append(f"Use when {use_when}")
    elif triggers:
        triggers = triggers.strip().rstrip(",")
        parts.append(f"Use when: {triggers}")

    # 3. Do not use when
    if do_not_use_when:
        do_not = do_not_use_when.strip().rstrip(".")
        parts.append(f"Do not use when {do_not}")

    return ". ".join(parts) + "." if parts else ""


def process_skill_file(filepath: Path, dry_run: bool = True) -> dict | None:
    """Process a single SKILL.md file."""
    content = filepath.read_text()

    # Split frontmatter and body
    parts = content.split("---", 2)
    if len(parts) < 3:
        return None

    frontmatter_text = parts[1]
    body = parts[2]

    # Parse frontmatter
    try:
        frontmatter = yaml.safe_load(frontmatter_text)
    except yaml.YAMLError as e:
        print(f"⚠️  YAML error in {filepath}: {e}")
        return None

    if not frontmatter:
        return None

    # Check if needs consolidation (has custom fields or messy description)
    has_custom = any(
        k in frontmatter for k in ["triggers", "use_when", "do_not_use_when"]
    )
    desc = frontmatter.get("description", "")
    has_truncated_do_not = bool(re.search(r"\bDO NOT\.\s*$", desc))

    if not has_custom and not has_truncated_do_not:
        return None

    # Flag truncated "DO NOT." as needing manual fix (cannot auto-generate)
    if has_truncated_do_not and not has_custom:
        return {
            "file": str(filepath),
            "old_description": desc[:80] if desc else "(empty)",
            "new_description": "(MANUAL FIX NEEDED: truncated 'DO NOT.')",
            "truncated": True,
        }

    # Consolidate
    old_desc = desc
    new_desc = consolidate_description(frontmatter)

    if not new_desc or new_desc == old_desc:
        return None

    # Update frontmatter - remove custom fields, update description
    frontmatter["description"] = new_desc
    for field in ["triggers", "use_when", "do_not_use_when"]:
        frontmatter.pop(field, None)

    # Rebuild file
    new_frontmatter = yaml.dump(
        frontmatter, default_flow_style=False, sort_keys=False, allow_unicode=True
    )
    new_content = f"---\n{new_frontmatter}---{body}"

    if not dry_run:
        filepath.write_text(new_content)

    return {
        "file": str(filepath),
        "old_description": old_desc[:80] if old_desc else "(empty)",
        "new_description": new_desc[:80],
    }


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Consolidate skill descriptions")
    parser.add_argument("--dry-run", action="store_true", default=True)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--path", type=Path, default=Path("plugins"))
    parser.add_argument(
        "--check", action="store_true", help="Check mode for pre-commit"
    )

    args = parser.parse_args()
    dry_run = not args.apply

    # Find all SKILL.md and agent files
    skill_files = list(args.path.glob("*/skills/*/SKILL.md"))
    agent_files = list(args.path.glob("*/agents/*.md"))

    if args.check:
        # Pre-commit check mode - fail if any files need fixing
        issues = []
        truncated = []
        for f in skill_files + agent_files:
            result = process_skill_file(f, dry_run=True)
            if result:
                if result.get("truncated"):
                    truncated.append(f)
                else:
                    issues.append(f)
        if issues or truncated:
            total = len(issues) + len(truncated)
            print(f"❌ {total} files need description fixes:")
            for f in truncated:
                print(f"   {f} (truncated 'DO NOT.' - needs completion)")
            for f in issues[:10]:
                print(f"   {f}")
            return 1
        print("✅ All descriptions follow official format")
        return 0

    if dry_run:
        print("🔍 DRY RUN\n")
    else:
        print("✍️  APPLYING\n")

    changes = []
    for f in skill_files + agent_files:
        result = process_skill_file(f, dry_run)
        if result:
            changes.append(result)
            print(f"✅ {f.parent.name}")
            print(f"   OLD: {result['old_description']}...")
            print(f"   NEW: {result['new_description']}...")
            print()

    print(f"📊 {len(changes)} files updated")
    return 0


if __name__ == "__main__":
    exit(main())
