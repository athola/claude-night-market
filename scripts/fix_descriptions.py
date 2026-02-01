#!/usr/bin/env python3
"""
Fix skill/agent/command descriptions to show properly in Claude Code UI.

Problem: Descriptions with "Triggers:" first hide the actual description.
Solution: Extract triggers/usage to separate frontmatter fields.
"""

import re
from pathlib import Path

import yaml


def extract_structured_content(description: str) -> dict[str, str]:
    """
    Extract structured content from description string.

    Strategy: Split into paragraphs (blank line separated), then classify each.
    - Paragraphs starting with "Triggers:" → triggers
    - Paragraphs starting with "Use when:" → use_when
    - Paragraphs starting with "DO NOT use when:" → do_not_use_when
    - Other paragraphs → description
    """
    result = {"description": "", "triggers": "", "use_when": "", "do_not_use_when": ""}

    # Split into paragraphs by blank lines
    paragraphs = re.split(r"\n\s*\n", description.strip())
    description_parts = []

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        # Normalize whitespace within paragraph
        para_text = " ".join(para.split())

        # Classify paragraph by its prefix
        if para_text.startswith("Triggers:"):
            triggers = para_text.replace("Triggers:", "").strip()
            if result["triggers"]:
                result["triggers"] += ", " + triggers
            else:
                result["triggers"] = triggers
        elif para_text.startswith("Use when:"):
            use_when = para_text.replace("Use when:", "").strip()
            if result["use_when"]:
                result["use_when"] += " " + use_when
            else:
                result["use_when"] = use_when
        elif para_text.startswith("DO NOT use when:") or para_text.startswith(
            "Do not use when:"
        ):
            do_not = re.sub(
                r"^DO NOT use when:|^Do not use when:", "", para_text
            ).strip()
            if result["do_not_use_when"]:
                result["do_not_use_when"] += " " + do_not
            else:
                result["do_not_use_when"] = do_not
        else:
            # Regular paragraph = part of description
            description_parts.append(para_text)

    # Join description parts
    result["description"] = " ".join(description_parts).strip()

    # Clean up triggers - remove trailing commas
    result["triggers"] = result["triggers"].rstrip(",").strip()

    return result


def process_malformed_skill_file(
    filepath: Path, content: str, frontmatter_text: str, body: str, dry_run: bool
) -> dict | None:
    """Process SKILL.md files with YAML parsing errors using raw text manipulation.

    Handles cases where description block has improper indentation causing
    'Triggers:' to look like a YAML key.
    """
    lines = frontmatter_text.split("\n")

    # Known top-level YAML fields that signal end of description block
    # Excludes triggers/use_when/do_not_use_when since those appear IN descriptions
    top_level_fields = {
        "name:",
        "category:",
        "tags:",
        "tools:",
        "usage_patterns:",
        "complexity:",
        "estimated_tokens:",
        "progressive_loading:",
        "dependencies:",
        "modules:",
        "version:",
        "model:",
        "escalation:",
        "examples:",
    }

    # Find description field
    desc_start = None
    for i, line in enumerate(lines):
        if line.strip().startswith("description:"):
            desc_start = i
            break

    if desc_start is None:
        return None

    # Extract description content - everything until next known top-level field
    desc_lines = []
    i = desc_start + 1
    while i < len(lines):
        line = lines[i]
        line_stripped = line.strip().lower()
        # Stop at next known top-level field
        if any(line_stripped.startswith(field) for field in top_level_fields):
            break
        desc_lines.append(line)
        i += 1
    desc_end = i

    description = "\n".join(desc_lines)
    extracted = extract_structured_content(description)

    if not extracted["description"]:
        return None

    # Build new frontmatter preserving other fields
    new_lines = lines[:desc_start]

    # Quote description properly for YAML
    desc_text = extracted["description"].replace("'", "''")
    new_lines.append(f"description: '{desc_text}'")

    if extracted["triggers"]:
        new_lines.append(f"triggers: {extracted['triggers']}")
    if extracted["use_when"]:
        use_when_text = extracted["use_when"].replace("'", "''")
        new_lines.append(f"use_when: '{use_when_text}'")
    if extracted["do_not_use_when"]:
        do_not_text = extracted["do_not_use_when"].replace("'", "''")
        new_lines.append(f"do_not_use_when: '{do_not_text}'")

    # Add remaining fields
    new_lines.extend(lines[desc_end:])

    new_content = f"---\n{chr(10).join(new_lines)}---{body}"

    if not dry_run:
        filepath.write_text(new_content)

    return {
        "file": str(filepath),
        "old_description": description[:80],
        "new_description": extracted["description"][:80],
        "triggers": extracted["triggers"][:80] if extracted["triggers"] else "",
        "use_when": extracted["use_when"][:80] if extracted["use_when"] else "",
        "do_not_use_when": extracted["do_not_use_when"][:80]
        if extracted["do_not_use_when"]
        else "",
    }


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
    except yaml.YAMLError:
        # YAML parsing failed - use raw text parsing for malformed files
        return process_malformed_skill_file(
            filepath, content, frontmatter_text, body, dry_run
        )

    # Check if description needs fixing
    description = frontmatter.get("description", "")
    if not description or "Triggers:" not in description:
        return None

    # Extract structured content
    extracted = extract_structured_content(description)

    # Update frontmatter
    frontmatter["description"] = extracted["description"]
    if extracted["triggers"]:
        frontmatter["triggers"] = extracted["triggers"]
    if extracted["use_when"]:
        frontmatter["use_when"] = extracted["use_when"]
    if extracted["do_not_use_when"]:
        frontmatter["do_not_use_when"] = extracted["do_not_use_when"]

    # Rebuild file
    new_frontmatter = yaml.dump(
        frontmatter, default_flow_style=False, sort_keys=False, allow_unicode=True
    )
    new_content = f"---\n{new_frontmatter}---{body}"

    if not dry_run:
        filepath.write_text(new_content)

    return {
        "file": str(filepath),
        "old_description": description,
        "new_description": extracted["description"],
        "triggers": extracted["triggers"],
        "use_when": extracted["use_when"],
        "do_not_use_when": extracted["do_not_use_when"],
    }


def process_agent_file(filepath: Path, dry_run: bool = True) -> dict | None:
    """Process a single agent .md file."""
    # Same logic as skill files
    return process_skill_file(filepath, dry_run)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Fix skill/agent descriptions")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Show what would be changed without modifying files",
    )
    parser.add_argument(
        "--apply", action="store_true", help="Actually apply the changes"
    )
    parser.add_argument(
        "--path", type=Path, default=Path("plugins"), help="Path to plugins directory"
    )

    args = parser.parse_args()
    dry_run = not args.apply

    if dry_run:
        print("🔍 DRY RUN - No files will be modified\n")
    else:
        print("✍️  APPLYING CHANGES\n")

    # Find all SKILL.md files
    skill_files = list(args.path.glob("*/skills/*/SKILL.md"))
    agent_files = list(args.path.glob("*/agents/*.md"))

    print(f"Found {len(skill_files)} skill files and {len(agent_files)} agent files\n")

    changes = []

    # Process skills
    for skill_file in skill_files:
        result = process_skill_file(skill_file, dry_run)
        if result:
            changes.append(result)
            print(f"✅ {skill_file.parent.parent.parent.name}:{skill_file.parent.name}")
            print(f"   OLD: {result['old_description'][:80]}...")
            print(f"   NEW: {result['new_description'][:80]}")
            if result["triggers"]:
                print(f"   TRIGGERS: {result['triggers'][:80]}")
            print()

    # Process agents
    for agent_file in agent_files:
        result = process_agent_file(agent_file, dry_run)
        if result:
            changes.append(result)
            print(f"✅ {agent_file.parent.parent.name}:{agent_file.stem}")
            print(f"   OLD: {result['old_description'][:80]}...")
            print(f"   NEW: {result['new_description'][:80]}")
            if result["triggers"]:
                print(f"   TRIGGERS: {result['triggers'][:80]}")
            print()

    print(f"\n📊 Summary: {len(changes)} files would be updated")

    if dry_run:
        print("\n💡 Run with --apply to make changes")


if __name__ == "__main__":
    main()
