#!/usr/bin/env python3
"""Fix very long lines in skill files by breaking them appropriately."""

import argparse
import sys
from pathlib import Path


def fix_long_descriptions(content: str, max_length: int = 80) -> str:
    """Fix long description lines by breaking them at appropriate points."""
    lines = content.split("\n")
    fixed_lines = []

    for line in lines:
        if len(line) <= max_length:
            fixed_lines.append(line)
            continue

        # Special handling for description lines
        if line.strip().startswith("description:"):
            fixed_lines.extend(break_description_line(line, max_length))
        elif line.strip().startswith("- **") and ":" in line:
            fixed_lines.extend(break_list_item_line(line, max_length))
        else:
            # Generic line breaking
            fixed_lines.extend(break_generic_line(line, max_length))

    return "\n".join(fixed_lines)


def break_description_line(line: str, max_length: int) -> list:
    """Break description lines at logical points."""
    prefix = "description:"
    base_text = line[len(prefix) :].strip()

    # Try to break at commas, semicolons, or "and"
    break_points = [", ", "; ", " and ", " through ", " with ", " for "]

    best_break = None
    for break_point in break_points:
        if break_point in base_text:
            idx = base_text.find(break_point) + len(break_point)
            if idx <= max_length - len(prefix) - 5:  # Leave some margin
                best_break = idx
                break

    if best_break:
        first_part = prefix + " " + base_text[:best_break].strip()
        second_part = "    " + base_text[best_break:].strip()
        return [first_part, second_part]
    else:
        # Force break if no logical break point found
        return [line[: max_length - 3] + "...", line[max_length - 3 :]]


def break_list_item_line(line: str, max_length: int) -> list:
    """Break list item lines."""
    stripped = line.strip()

    # Find the colon separator
    colon_idx = stripped.find(":")
    if colon_idx == -1:
        return [line]

    prefix = stripped[: colon_idx + 1]
    content = stripped[colon_idx + 1 :].strip()

    if len(line) <= max_length:
        return [line]

    # Break after the prefix
    return [prefix, "    " + content]


def break_generic_line(line: str, max_length: int) -> list:
    """Break generic lines for non-special cases."""
    if len(line) <= max_length:
        return [line]

    # Try to break at spaces
    break_at = max_length
    while break_at > 0 and line[break_at - 1] not in [" ", "-", ":"]:
        break_at -= 1

    if break_at <= 0:
        # Force break
        return [line[: max_length - 3] + "...", line[max_length - 3 :]]

    first_part = line[:break_at].rstrip()
    second_part = line[break_at:].lstrip()

    if first_part:
        return [first_part, "    " + second_part]
    else:
        return [second_part]


def fix_skill_file(file_path: str, max_length: int = 80) -> bool:
    """Fix a single skill file."""
    try:
        with open(file_path) as f:
            content = f.read()

        original_lines = content.split("\n")
        fixed_content = fix_long_descriptions(content, max_length)

        if content == fixed_content:
            print(f"✓ {file_path}: No long lines to fix")
            return True

        with open(file_path, "w") as f:
            f.write(fixed_content)

        print(f"✓ {file_path}: Fixed long lines")

        # Show improvement
        original_long = sum(1 for line in original_lines if len(line) > max_length)
        new_lines = fixed_content.split("\n")
        new_long = sum(1 for line in new_lines if len(line) > max_length)
        print(f"  Long lines: {original_long} → {new_long}")

        return True

    except Exception as e:
        print(f"✗ {file_path}: Error - {e}")
        return False


def main():
    """Main entry point for fixing long lines in skill files."""
    parser = argparse.ArgumentParser(description="Fix very long lines in skill files")
    parser.add_argument("files", nargs="+", help="Skill files to fix")
    parser.add_argument(
        "--max-length", type=int, default=80, help="Maximum line length (default: 80)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be fixed without making changes",
    )

    args = parser.parse_args()

    success_count = 0
    total_count = len(args.files)

    for file_path in args.files:
        if not Path(file_path).exists():
            print(f"✗ File not found: {file_path}")
            continue

        if args.dry_run:
            print(f"Would fix: {file_path}")
            success_count += 1
        elif fix_skill_file(file_path, args.max_length):
            success_count += 1

    print(f"\nSummary: {success_count}/{total_count} files processed successfully")


if __name__ == "__main__":
    sys.exit(main())
