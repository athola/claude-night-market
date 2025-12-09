#!/usr/bin/env python3
"""Automated changelog update script.

This script helps maintain the CHANGELOG.md file by:
- Detecting new changes since last release
- Suggesting changelog entries
- Validating changelog format
"""

import argparse
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

# Constants
COMMIT_PARTS_COUNT = 2
MAX_DISPLAY_ITEMS = 3


def get_last_tag() -> str | None:
    """Get the most recent git tag."""
    try:
        result = subprocess.run(
            ["/usr/bin/git", "describe", "--tags", "--abbrev=0"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None


def get_commits_since_tag(tag: str | None = None) -> list[tuple[str, str]]:
    """Get all commit messages since the specified tag.

    Args:
        tag: Git tag to get commits since (None for all commits)

    Returns:
        List of (commit_hash, message) tuples

    """
    try:
        if tag:
            result = subprocess.run(
                ["/usr/bin/git", "log", f"{tag}..HEAD", "--oneline"],
                capture_output=True,
                text=True,
                check=True,
            )
        else:
            result = subprocess.run(
                ["/usr/bin/git", "log", "--oneline"],
                capture_output=True,
                text=True,
                check=True,
            )

        commits = []
        for line in result.stdout.strip().split("\n"):
            if line:
                parts = line.split(" ", 1)
                if len(parts) == COMMIT_PARTS_COUNT:
                    commits.append((parts[0], parts[1]))

        return commits
    except subprocess.CalledProcessError:
        return []


def categorize_commit(message: str) -> str:
    """Categorize a commit message into a changelog section.

    Args:
        message: The commit message

    Returns:
        Category name (Added, Changed, Deprecated, Removed, Fixed, Security)

    """
    message_lower = message.lower()

    # Category mappings
    category_patterns = {
        "Added": ["add", "new", "create", "introduce", "implement"],
        "Fixed": ["fix", "bug", "issue", "error", "problem"],
        "Changed": ["update", "change", "modify", "improve", "refactor"],
        "Removed": ["remove", "delete"],
        "Security": ["security", "vulnerability", "auth", "permission"],
        "Deprecated": ["deprecat", "obsolete"],
    }

    # Check patterns for each category
    for category, patterns in category_patterns.items():
        if any(word in message_lower for word in patterns):
            return category

    return "Changed"  # Default category


def generate_changelog_entry(commits: list[tuple[str, str]]) -> dict[str, list[str]]:
    """Generate a changelog entry from commits.

    Args:
        commits: List of (hash, message) tuples

    Returns:
        Dictionary mapping sections to lists of entries

    """
    sections: dict[str, list[str]] = {
        "Added": [],
        "Changed": [],
        "Deprecated": [],
        "Removed": [],
        "Fixed": [],
        "Security": [],
    }

    for _, commit_message in commits:
        # Skip merge commits and version bumps
        if commit_message.startswith(("Merge ", "bump:")):
            continue

        # Clean up the message
        cleaned_message = _clean_commit_message(commit_message)

        if cleaned_message:
            category = categorize_commit(cleaned_message)
            formatted_message = _format_changelog_entry(cleaned_message)
            sections[category].append(formatted_message)

    # Remove empty sections
    return {k: v for k, v in sections.items() if v}


def _clean_commit_message(message: str) -> str:
    """Clean up a commit message for changelog entry.

    Args:
        message: Raw commit message

    Returns:
        Cleaned commit message

    """
    # Remove common prefixes
    message = re.sub(
        r"^(feat|fix|docs|style|refactor|test|chore)(\(.+\))?:\s*",
        "",
        message,
    )
    # Remove PR numbers
    message = re.sub(r"\(#\d+\)", "", message).strip()
    # Remove commit hash if present at start
    return re.sub(r"^[a-f0-9]+\s+", "", message).strip()


def _format_changelog_entry(message: str) -> str:
    """Format a changelog entry.

    Args:
        message: Cleaned commit message

    Returns:
        Formatted changelog entry

    """
    # Capitalize first letter
    message = message[0].upper() + message[1:] if message else message
    # Ensure it ends with a period
    if not message.endswith("."):
        message += "."
    return message


def update_changelog(entries: dict[str, list[str]], version: str | None = None) -> None:
    """Update the CHANGELOG.md file with new entries.

    Args:
        entries: Dictionary of section entries to add
        version: Version number for this release

    """
    changelog_path = Path("CHANGELOG.md")

    if not changelog_path.exists():
        return

    content = changelog_path.read_text()

    # Find where to insert the new entry (after ## [Unreleased] section)
    unreleased_match = re.search(r"## \[Unreleased\]\s*\n", content)
    if not unreleased_match:
        return

    # Generate the new entry
    today = datetime.now(UTC).strftime("%Y-%m-%d")
    version = version or "Unreleased"

    new_entry_parts = [f"## [{version}] - {today}"]

    for section in ["Added", "Changed", "Deprecated", "Removed", "Fixed", "Security"]:
        if entries.get(section):
            new_entry_parts.append(f"\n### {section}")
            for item in sorted(set(entries[section])):  # Remove duplicates and sort
                new_entry_parts.append(f"- {item}")

    new_entry = "\n".join(new_entry_parts) + "\n\n"

    # Insert the new entry after the Unreleased section
    insert_pos = unreleased_match.end()
    content = content[:insert_pos] + new_entry + content[insert_pos:]

    # Write back to file
    changelog_path.write_text(content)


def validate_changelog() -> bool:
    """Validate that the CHANGELOG.md follows the correct format."""
    changelog_path = Path("CHANGELOG.md")

    if not changelog_path.exists():
        return False

    content = changelog_path.read_text()

    # Check for required sections
    required_patterns = [
        r"# Changelog",
        r"## \[Unreleased\]",
        r"## \[\d+\.\d+\.\d+\]",  # At least one versioned section
    ]

    return all(re.search(pattern, content) for pattern in required_patterns)


def main() -> None:
    """Run the changelog updater."""
    parser = argparse.ArgumentParser(description="Update the project changelog")
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate the changelog format",
    )
    parser.add_argument("--since-tag", help="Generate entries since this git tag")
    parser.add_argument("--version", help="Version number for the new release")

    args = parser.parse_args()

    if args.validate_only:
        success = validate_changelog()
        sys.exit(0 if success else 1)

    # Get commits
    last_tag = args.since_tag or get_last_tag()
    if last_tag:
        pass
    else:
        pass

    commits = get_commits_since_tag(last_tag)

    if not commits:
        return

    # Generate entries
    entries = generate_changelog_entry(commits)

    if not any(entries.values()):
        return

    # Show summary
    for items in entries.values():
        if items:
            for _item in items[:MAX_DISPLAY_ITEMS]:  # Show first few
                pass
            if len(items) > MAX_DISPLAY_ITEMS:
                pass

    # Update changelog
    update_changelog(entries, args.version)

    # Validate after update
    validate_changelog()


if __name__ == "__main__":
    main()
