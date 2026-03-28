#!/usr/bin/env python3
"""Add model_hint frontmatter to SKILL.md files based on complexity.

Maps skill complexity to a model routing hint:
  - fast:     low, basic, beginner, lightweight -> Haiku/Sonnet
  - standard: intermediate, medium, foundational -> Sonnet (default)
  - deep:     advanced, high -> Opus

These hints let downstream tools (Cursor, Copilot, Claude Code)
route simple skills to cheaper/faster models.

Usage:
    python scripts/add_model_hints.py            # dry-run
    python scripts/add_model_hints.py --write     # apply changes
    python scripts/add_model_hints.py --stats     # show summary
"""

from __future__ import annotations

import argparse
import re
from collections import Counter
from pathlib import Path

PLUGINS_DIR = Path(__file__).resolve().parent.parent / "plugins"
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)

# Complexity -> model_hint mapping
COMPLEXITY_TO_HINT: dict[str, str] = {
    "low": "fast",
    "basic": "fast",
    "beginner": "fast",
    "lightweight": "fast",
    "intermediate": "standard",
    "medium": "standard",
    "foundational": "standard",
    "advanced": "deep",
    "high": "deep",
}

# Skills that should always be fast regardless of complexity
FORCE_FAST: set[str] = {
    "commit-messages",
    "git-workspace-review",
    "slop-detector",
    "catchup",
    "commit-msg",
}

# Skills that should always be deep regardless of complexity
FORCE_DEEP: set[str] = {
    "war-room",
    "architecture-review",
    "rigorous-reasoning",
}


def get_model_hint(skill_name: str, complexity: str) -> str:
    """Determine model_hint from skill name and complexity."""
    if skill_name in FORCE_FAST:
        return "fast"
    if skill_name in FORCE_DEEP:
        return "deep"
    return COMPLEXITY_TO_HINT.get(complexity.strip(), "standard")


def process_skill(path: Path, write: bool) -> tuple[str, str, bool]:
    """Process a single SKILL.md file. Returns (name, hint, changed)."""
    content = path.read_text()
    match = FRONTMATTER_RE.match(content)
    if not match:
        return ("unknown", "skip", False)

    fm_text = match.group(1)

    # Extract skill name
    name_match = re.search(r"^name:\s*(.+)$", fm_text, re.MULTILINE)
    skill_name = name_match.group(1).strip() if name_match else path.parent.name

    # Skip if model_hint already present
    if re.search(r"^model_hint:", fm_text, re.MULTILINE):
        hint_match = re.search(r"^model_hint:\s*(.+)$", fm_text, re.MULTILINE)
        existing = hint_match.group(1).strip() if hint_match else "unknown"
        return (skill_name, existing, False)

    # Extract complexity
    comp_match = re.search(r"^complexity:\s*(.+)$", fm_text, re.MULTILINE)
    complexity = comp_match.group(1).strip() if comp_match else "intermediate"

    hint = get_model_hint(skill_name, complexity)

    # Insert model_hint after complexity line (or after estimated_tokens)
    if comp_match:
        insert_after = f"complexity: {complexity}"
        new_line = f"complexity: {complexity}\nmodel_hint: {hint}"
        new_content = content.replace(insert_after, new_line, 1)
    else:
        # No complexity field; insert before the closing ---
        new_content = content.replace(
            "\n---\n",
            f"\nmodel_hint: {hint}\n---\n",
            1,
        )

    if write:
        path.write_text(new_content)

    return (skill_name, hint, True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="Apply changes")
    parser.add_argument("--stats", action="store_true", help="Show summary")
    args = parser.parse_args()

    skills = sorted(PLUGINS_DIR.glob("*/skills/*/SKILL.md"))
    results: list[tuple[str, str, bool]] = []

    for skill_path in skills:
        name, hint, changed = process_skill(skill_path, args.write)
        results.append((name, hint, changed))

    if args.stats:
        hint_counts = Counter(hint for _, hint, _ in results)
        print("Model hint distribution:")
        for hint, count in hint_counts.most_common():
            print(f"  {hint}: {count}")
        print(f"\nTotal skills: {len(results)}")
        print(f"Would change: {sum(1 for _, _, c in results if c)}")
        return

    updated = [(n, h) for n, h, c in results if c]
    skipped = [(n, h) for n, h, c in results if not c]

    if updated:
        action = "Updated" if args.write else "Would update"
        print(f"{action} {len(updated)} skills:")
        for name, hint in updated:
            print(f"  {name}: {hint}")
    else:
        print("No skills need updating.")

    if skipped:
        print(f"\nSkipped {len(skipped)} (already have model_hint)")

    if not args.write and updated:
        print("\nDry run. Use --write to apply.")


if __name__ == "__main__":
    main()
