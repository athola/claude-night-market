#!/usr/bin/env python3
"""Update version strings across all version files in the repository.

Finds and updates pyproject.toml, Cargo.toml, package.json, plugin.json,
and marketplace.json files, excluding virtual environments and build directories.
"""

import argparse
import re
import sys
from pathlib import Path


def find_version_files(root: Path, include_cache: bool = False) -> list[Path]:
    """Find all version files, excluding venvs and build dirs unless explicitly requested.

    Args:
        root: Root directory to search
        include_cache: If True, include cache/temp directories. Use with caution.

    Returns:
        Sorted list of paths to version files
    """
    version_files = []

    # Patterns to match
    patterns = [
        "**/pyproject.toml",
        "**/Cargo.toml",
        "**/package.json",
        "**/.claude-plugin/plugin.json",
        "**/.claude-plugin/metadata.json",
        "**/.claude-plugin/marketplace.json",
    ]

    # Directories to exclude from scan by default
    # Cache, temp, and build directories are skipped unless --include-cache is set.
    excludes = {
        # Python
        ".venv",
        "venv",
        ".virtualenv",
        "virtualenv",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        ".tox",
        ".eggs",
        "*.egg-info",
        ".uv-cache",
        # JavaScript/Node
        "node_modules",
        ".npm",
        ".yarn",
        ".pnp",
        ".cache",
        # Rust
        "target",
        ".cargo",
        ".rustup",
        # Build artifacts
        "dist",
        "build",
        "_build",
        "out",
        # Version control
        ".git",
        ".hg",
        ".svn",
        ".worktrees",
        # IDEs and editors
        ".vscode",
        ".idea",
        ".vs",
        # OS
        ".DS_Store",
        "Thumbs.db",
    }

    for pattern in patterns:
        for file in root.rglob(pattern):
            # Skip exclusions unless --include-cache is specified
            if not include_cache:
                if any(exclude in file.parts for exclude in excludes):
                    continue
            version_files.append(file)

    return sorted(version_files)


def update_pyproject_version(content: str, new_version: str) -> str:
    """Update version in pyproject.toml content."""
    # Match: version = "1.2.3"
    pattern = r'^version\s*=\s*"[0-9]+\.[0-9]+\.[0-9]+"'
    replacement = f'version = "{new_version}"'
    return re.sub(pattern, replacement, content, flags=re.MULTILINE)


def update_cargo_version(content: str, new_version: str) -> str:
    """Update version in Cargo.toml content."""
    # Match: version = "1.2.3"
    pattern = r'^version\s*=\s*"[0-9]+\.[0-9]+\.[0-9]+"'
    replacement = f'version = "{new_version}"'
    return re.sub(pattern, replacement, content, flags=re.MULTILINE)


def update_package_json_version(content: str, new_version: str) -> str:
    """Update version in package.json content."""
    # Match: "version": "1.2.3"
    pattern = r'"version"\s*:\s*"[0-9]+\.[0-9]+\.[0-9]+"'
    replacement = f'"version": "{new_version}"'
    return re.sub(pattern, replacement, content)


def update_plugin_json_version(content: str, new_version: str) -> str:
    """Update version in plugin.json or marketplace.json content."""
    # Match: "version": "1.2.3"
    pattern = r'"version"\s*:\s*"[0-9]+\.[0-9]+\.[0-9]+"'
    replacement = f'"version": "{new_version}"'
    return re.sub(pattern, replacement, content)


def update_version_file(
    file_path: Path, new_version: str, dry_run: bool = True
) -> bool:
    """Update version in a single file."""
    try:
        content = file_path.read_text(encoding="utf-8")
        original = content

        if file_path.name == "pyproject.toml":
            content = update_pyproject_version(content, new_version)
        elif file_path.name == "Cargo.toml":
            content = update_cargo_version(content, new_version)
        elif file_path.name == "package.json":
            content = update_package_json_version(content, new_version)
        elif file_path.name in ("plugin.json", "metadata.json", "marketplace.json"):
            content = update_plugin_json_version(content, new_version)

        if content != original:
            if not dry_run:
                file_path.write_text(content, encoding="utf-8")
            return True
        return False

    except Exception as e:
        print(f"ERROR updating {file_path}: {e}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Update versions across all version files",
        epilog="By default, cache/temp directories are excluded. Use --include-cache to override.",
    )
    parser.add_argument("version", help="New version (e.g., 1.2.5)")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would change without modifying files",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Repository root (default: current directory)",
    )
    parser.add_argument(
        "--include-cache",
        action="store_true",
        help="Include cache/temp directories (.venv, node_modules, etc.). Use with caution!",
    )

    args = parser.parse_args()

    # Validate version format
    if not re.match(r"^\d+\.\d+\.\d+$", args.version):
        print(
            f"ERROR: Invalid version format '{args.version}'. Expected: MAJOR.MINOR.PATCH",
            file=sys.stderr,
        )
        return 1

    root = args.root.resolve()
    if not root.exists():
        print(f"ERROR: Root directory does not exist: {root}", file=sys.stderr)
        return 1

    if args.include_cache:
        print(
            "⚠️  WARNING: Searching cache directories. This may be slow and find unwanted files."
        )

    print(f"Searching for version files in: {root}")
    version_files = find_version_files(root, include_cache=args.include_cache)

    if not version_files:
        print("No version files found.")
        return 0

    print(f"\nFound {len(version_files)} version file(s):")
    for file in version_files:
        print(f"  - {file.relative_to(root)}")

    if args.dry_run:
        print("\n[DRY RUN] Would update to version:", args.version)
    else:
        print(f"\nUpdating to version: {args.version}")

    updated = 0
    for file in version_files:
        if update_version_file(file, args.version, dry_run=args.dry_run):
            status = "[DRY RUN] Would update" if args.dry_run else "✓ Updated"
            print(f"  {status}: {file.relative_to(root)}")
            updated += 1
        else:
            print(f"  - No change: {file.relative_to(root)}")

    print(
        f"\n{'Would update' if args.dry_run else 'Updated'} {updated}/{len(version_files)} file(s)"
    )

    if args.dry_run:
        print("\nRun without --dry-run to apply changes.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
