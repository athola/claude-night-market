#!/usr/bin/env python3
"""Add @pytest.mark.bdd markers to all BDD-style test files.

This script scans test files for BDD patterns (Scenario docstrings with
Given/When/Then structure) and adds @pytest.mark.bdd decorators where missing.

Usage:
    python add_bdd_markers.py [--dry-run] [--plugin PLUGIN_NAME]

Options:
    --dry-run    Show changes without applying them
    --plugin     Only process specific plugin (default: all plugins)
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# BDD pattern detection
BDD_PATTERNS = [
    r"Scenario:",
    r"Given\s+\w+",
    r"When\s+\w+",
    r"Then\s+\w+",
]

DD_PATTERN = r"^\s*def test_\w+\(.*?\)\s*->\s*None:"
INDENT_PATTERN = r"^\s*@pytest\.mark\."


def is_bdd_test_function(lines: list[str], start_idx: int) -> bool:
    """Check if a test function follows BDD patterns."""
    # Look ahead for docstring and BDD patterns
    for i in range(start_idx, min(start_idx + 20, len(lines))):
        line = lines[i]
        if '"""' in line or "'''" in line:
            # Found docstring start, check for BDD patterns
            for j in range(i, min(i + 10, len(lines))):
                for pattern in BDD_PATTERNS:
                    if re.search(pattern, lines[j]):
                        return True
            break
    return False


def needs_bdd_marker(lines: list[str], test_def_idx: int) -> bool:
    """Check if test definition already has @pytest.mark.bdd."""
    # Look backwards for existing marker
    for i in range(test_def_idx - 1, max(0, test_def_idx - 5), -1):
        if "@pytest.mark.bdd" in lines[i]:
            return False  # Already has BDD marker
        if lines[i].strip() and not lines[i].strip().startswith("@"):
            break  # Hit non-decorator line
    return True


def add_bdd_marker_to_file(file_path: Path, dry_run: bool = False) -> bool:
    """Add @pytest.mark.bdd markers to BDD tests in a file.

    Returns:
        True if file was modified, False otherwise

    """
    try:
        with open(file_path) as f:
            original_lines = f.readlines()

        modified_lines = original_lines.copy()
        insertions = []  # (line_idx, line_to_insert)

        for i, line in enumerate(original_lines):
            # Find test function definitions
            match = re.match(DD_PATTERN, line)
            if match:
                # Check if it's a BDD test
                if is_bdd_test_function(original_lines, i):
                    # Check if it needs BDD marker
                    if needs_bdd_marker(original_lines, i):
                        # Calculate indentation
                        indent_match = re.match(r"^(\s*)def test_", line)
                        indent = indent_match.group(1) if indent_match else "    "

                        # Find where to insert (before any existing decorators)
                        insert_idx = i
                        for j in range(i - 1, max(0, i - 5), -1):
                            if original_lines[j].strip().startswith("@"):
                                insert_idx = j
                            else:
                                break

                        insertions.append((insert_idx, indent + "@pytest.mark.bdd"))

        # Apply insertions in reverse order to maintain line numbers
        if insertions:
            for idx, line_to_insert in reversed(insertions):
                modified_lines.insert(idx, line_to_insert + "\n")

            # Write back if modified
            if modified_lines != original_lines:
                if not dry_run:
                    with open(file_path, "w") as f:
                        f.writelines(modified_lines)
                return True

    except Exception as e:
        print(f"Warning: Error processing {file_path}: {e}", file=sys.stderr)

    return False


def find_test_files(plugin_dir: Path | None = None) -> list[Path]:
    """Find all Python test files in the project."""
    base = Path.cwd()
    if plugin_dir:
        test_files = list(base.glob(f"plugins/{plugin_dir}/**/test_*.py"))
    else:
        test_files = list(base.glob("plugins/*/tests/**/test_*.py"))
        # Also find tests in plugin root
        test_files.extend(list(base.glob("plugins/*/test_*.py")))

    # Filter out .venv and cache directories
    test_files = [
        f
        for f in test_files
        if ".venv" not in str(f)
        and "__pycache__" not in str(f)
        and ".git" not in str(f)
    ]

    return sorted(test_files)


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Add @pytest.mark.bdd markers to BDD-style test files"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show changes without applying them",
    )
    parser.add_argument(
        "--plugin",
        type=str,
        help="Only process specific plugin (default: all plugins)",
    )
    args = parser.parse_args()

    # Find all test files
    test_files = find_test_files(plugin_dir=args.plugin)

    print(f"Found {len(test_files)} test files to check")

    # Process each file
    modified_count = 0
    for test_file in test_files:
        if add_bdd_marker_to_file(test_file, dry_run=args.dry_run):
            relative_path = test_file.relative_to(Path.cwd())
            status = "[DRY RUN] Would modify:" if args.dry_run else "Modified:"
            print(f"  {status} {relative_path}")
            modified_count += 1

    # Summary
    print(f"\n{'[DRY RUN] ' if args.dry_run else ''}Summary:")
    print(f"  Total files checked: {len(test_files)}")
    print(f"  Files {'to be ' if args.dry_run else ''}modified: {modified_count}")

    if args.dry_run:
        print("\nTo apply changes, re-run without --dry-run")
        sys.exit(0)
    elif modified_count > 0:
        print(f"\n✅ Added @pytest.mark.bdd to {modified_count} test files")
    else:
        print("\n✅ All files already have @pytest.mark.bdd markers")


if __name__ == "__main__":
    main()
