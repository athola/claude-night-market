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

    Returns dict with:
    - description: Main description (first paragraph or non-trigger content)
    - triggers: Comma-separated trigger keywords
    - use_when: Usage guidance
    - do_not_use_when: Anti-patterns
    """
    lines = description.strip().split("\n")
    result = {"description": "", "triggers": "", "use_when": "", "do_not_use_when": ""}

    current_section = "description"
    description_lines = []

    for line in lines:
        line_stripped = line.strip()

        # Skip empty lines
        if not line_stripped:
            continue

        # Detect section headers
        if line_stripped.startswith("Triggers:"):
            current_section = "triggers"
            # Extract triggers from this line and merge with existing
            triggers_text = line_stripped.replace("Triggers:", "").strip()
            if triggers_text:
                if result["triggers"]:
                    result["triggers"] += ", " + triggers_text
                else:
                    result["triggers"] = triggers_text
            continue
        elif line_stripped.startswith("Use when:"):
            current_section = "use_when"
            # Extract from this line
            use_when_text = line_stripped.replace("Use when:", "").strip()
            if use_when_text:
                result["use_when"] = use_when_text
            continue
        elif line_stripped.startswith("DO NOT use when:") or line_stripped.startswith(
            "Do not use when:"
        ):
            # Extract from this line and append to existing
            do_not_text = re.sub(
                r"^DO NOT use when:|^Do not use when:", "", line_stripped
            ).strip()
            if do_not_text:
                if result["do_not_use_when"]:
                    result["do_not_use_when"] += " " + do_not_text
                else:
                    result["do_not_use_when"] = do_not_text
            current_section = "do_not_use_when"
            continue

        # Check if this line looks like a trigger continuation vs a description sentence
        if current_section == "triggers":
            # Heuristics to detect description vs trigger continuation:
            # 1. Ends with period = sentence = description
            # 2. Starts with action verb (Analyze, Review, Create, etc.) = description
            # 3. Contains 'the', 'and', 'for', 'with' but no commas = sentence = description
            is_sentence = (
                line_stripped.endswith(".")
                or line_stripped.endswith(":")
                or any(
                    line_stripped.startswith(verb)
                    for verb in [
                        "Analyze",
                        "Review",
                        "Create",
                        "Update",
                        "Generate",
                        "Validate",
                        "Check",
                        "Verify",
                        "Improve",
                        "Refactor",
                        "Build",
                        "Test",
                        "Debug",
                        "Fix",
                        "Implement",
                        "Configure",
                        "Install",
                        "Setup",
                        "Provides",
                        "Enables",
                        "Supports",
                        "Manages",
                    ]
                )
                or ("the " in line_stripped.lower() and "," not in line_stripped)
            )

            if is_sentence:
                current_section = "description"
                description_lines.append(line_stripped)
            else:
                # Continue triggers
                if result["triggers"]:
                    result["triggers"] += " " + line_stripped.rstrip(",").strip()
                else:
                    result["triggers"] = line_stripped.rstrip(",").strip()
        elif current_section == "description":
            description_lines.append(line_stripped)
        elif current_section == "use_when":
            if result["use_when"]:
                result["use_when"] += " " + line_stripped
            else:
                result["use_when"] = line_stripped
        elif current_section == "do_not_use_when":
            if result["do_not_use_when"]:
                result["do_not_use_when"] += " " + line_stripped
            else:
                result["do_not_use_when"] = line_stripped

    # Clean up description - take only the main description paragraph
    result["description"] = " ".join(description_lines).strip()

    # Clean up triggers - remove trailing commas and normalize
    result["triggers"] = result["triggers"].rstrip(",").strip()

    return result


def process_malformed_skill_file(
    filepath: Path, content: str, frontmatter_text: str, body: str, dry_run: bool
) -> dict | None:
    """Process SKILL.md files with YAML parsing errors using raw text manipulation."""
    lines = frontmatter_text.split("\n")

    # Find description field
    desc_start = None
    for i, line in enumerate(lines):
        if line.strip().startswith("description:"):
            desc_start = i
            break

    if desc_start is None:
        return None

    # Extract description content (multi-line string)
    desc_lines = []
    i = desc_start + 1
    while i < len(lines):
        line = lines[i]
        # Stop at next top-level field (no indentation)
        if line and not line.startswith(" ") and not line.startswith("\t"):
            break
        desc_lines.append(line)
        i += 1

    description = "\n".join(desc_lines)
    extracted = extract_structured_content(description)

    # Build new frontmatter with raw text replacement
    new_lines = lines[:desc_start]
    new_lines.append(f"description: {repr(extracted['description'])}")
    if extracted["triggers"]:
        new_lines.append(f"triggers: {extracted['triggers']}")
    if extracted["use_when"]:
        new_lines.append(f"use_when: {extracted['use_when']}")
    if extracted["do_not_use_when"]:
        new_lines.append(f"do_not_use_when: {extracted['do_not_use_when']}")
    new_lines.extend(lines[i:])

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
