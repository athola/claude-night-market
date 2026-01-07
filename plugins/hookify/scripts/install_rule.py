#!/usr/bin/env python3
"""Install hookify rules from the catalog to a project's .claude directory.

This script uses __file__ to locate its own directory, making it work
regardless of where the plugin is installed.

Usage:
    python3 install_rule.py git:block-force-push
    python3 install_rule.py --category python
    python3 install_rule.py --all
    python3 install_rule.py --list
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

# Locate the rules directory relative to this script
SCRIPT_DIR = Path(__file__).parent
RULES_DIR = SCRIPT_DIR.parent / "skills" / "rule-catalog" / "rules"


def get_available_rules() -> dict[str, list[str]]:
    """Get all available rules organized by category.

    Returns:
        Dict mapping category names to lists of rule names.
    """
    rules: dict[str, list[str]] = {}

    if not RULES_DIR.exists():
        return rules

    for category_dir in RULES_DIR.iterdir():
        if category_dir.is_dir():
            category = category_dir.name
            rules[category] = []
            for rule_file in category_dir.glob("*.md"):
                rules[category].append(rule_file.stem)

    return rules


def list_rules() -> None:
    """Print all available rules."""
    rules = get_available_rules()

    if not rules:
        print("No rules found in catalog.")
        print(f"Expected location: {RULES_DIR}")
        return

    print("Available Hookify Rules")
    print("=" * 50)

    total = 0
    for category in sorted(rules.keys()):
        print(f"\n{category}/")
        for rule in sorted(rules[category]):
            print(f"  - {rule}")
            total += 1

    print(f"\nTotal: {total} rules in {len(rules)} categories")
    print("\nInstall with:")
    print(f"  python3 {Path(__file__).name} <category>:<rule>")


def get_rule_path(category: str, rule_name: str) -> Path | None:
    """Get the path to a rule file.

    Args:
        category: Rule category (git, python, etc.)
        rule_name: Name of the rule

    Returns:
        Path to rule file, or None if not found.
    """
    rule_path = RULES_DIR / category / f"{rule_name}.md"
    if rule_path.exists():
        return rule_path
    return None


def install_rule(
    category: str,
    rule_name: str,
    target_dir: Path,
    force: bool = False,
) -> bool:
    """Install a single rule to the target directory.

    Args:
        category: Rule category
        rule_name: Name of the rule
        target_dir: Directory to install to (typically .claude/)
        force: Overwrite existing rules

    Returns:
        True if installed successfully.
    """
    source = get_rule_path(category, rule_name)
    if not source:
        print(f"Rule not found: {category}:{rule_name}")
        return False

    target = target_dir / f"hookify.{rule_name}.local.md"

    if target.exists() and not force:
        print(f"Rule already exists: {target}")
        print("  Use --force to overwrite")
        return False

    # Ensure target directory exists
    target_dir.mkdir(parents=True, exist_ok=True)

    # Copy the rule
    shutil.copy(source, target)
    print(f"Installed: {category}:{rule_name} -> {target}")
    return True


def install_category(category: str, target_dir: Path, force: bool = False) -> int:
    """Install all rules in a category.

    Args:
        category: Category name
        target_dir: Installation directory
        force: Overwrite existing

    Returns:
        Number of rules installed.
    """
    rules = get_available_rules()
    if category not in rules:
        print(f"Category not found: {category}")
        print(f"Available: {', '.join(sorted(rules.keys()))}")
        return 0

    installed = 0
    for rule_name in rules[category]:
        if install_rule(category, rule_name, target_dir, force):
            installed += 1

    return installed


def install_all(target_dir: Path, force: bool = False) -> int:
    """Install all rules from all categories.

    Args:
        target_dir: Installation directory
        force: Overwrite existing

    Returns:
        Number of rules installed.
    """
    rules = get_available_rules()
    installed = 0

    for category in sorted(rules.keys()):
        for rule_name in rules[category]:
            if install_rule(category, rule_name, target_dir, force):
                installed += 1

    return installed


def parse_rule_spec(spec: str) -> tuple[str, str] | None:
    """Parse a rule specification like 'git:block-force-push'.

    Args:
        spec: Rule specification string

    Returns:
        Tuple of (category, rule_name) or None if invalid.
    """
    if ":" not in spec:
        return None

    parts = spec.split(":", 1)
    if len(parts) != 2:
        return None

    return parts[0], parts[1]


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Install hookify rules from the catalog",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s git:block-force-push     Install a specific rule
  %(prog)s --category python        Install all Python rules
  %(prog)s --all                    Install all rules
  %(prog)s --list                   List available rules
        """,
    )

    parser.add_argument(
        "rule",
        nargs="?",
        help="Rule to install (format: category:rule-name)",
    )
    parser.add_argument(
        "--category",
        "-c",
        help="Install all rules in a category",
    )
    parser.add_argument(
        "--all",
        "-a",
        action="store_true",
        help="Install all available rules",
    )
    parser.add_argument(
        "--list",
        "-l",
        action="store_true",
        help="List available rules",
    )
    parser.add_argument(
        "--target",
        "-t",
        type=Path,
        default=Path.cwd() / ".claude",
        help="Target directory (default: ./.claude)",
    )
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Overwrite existing rules",
    )

    args = parser.parse_args()

    # Handle --list
    if args.list:
        list_rules()
        return 0

    # Handle --all
    if args.all:
        count = install_all(args.target, args.force)
        print(f"\nInstalled {count} rules to {args.target}")
        return 0 if count > 0 else 1

    # Handle --category
    if args.category:
        count = install_category(args.category, args.target, args.force)
        print(f"\nInstalled {count} rules from '{args.category}' to {args.target}")
        return 0 if count > 0 else 1

    # Handle single rule
    if args.rule:
        parsed = parse_rule_spec(args.rule)
        if not parsed:
            print(f"Invalid rule format: {args.rule}")
            print("Expected format: category:rule-name")
            print("Example: git:block-force-push")
            return 1

        category, rule_name = parsed
        success = install_rule(category, rule_name, args.target, args.force)
        return 0 if success else 1

    # No action specified
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
