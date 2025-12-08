#!/usr/bin/env python3
"""Categorize files that need frontmatter vs those that should be exceptions.

This script uses the centralized frontmatter processing from abstract.base.
"""

import os
import sys
from pathlib import Path

# Set up imports before using abstract package
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from abstract.base import find_markdown_files, has_frontmatter_file


def categorize_files(
    files_without_frontmatter: list[Path],
) -> tuple[list[Path], list[Path]]:
    """Categorize files into those needing frontmatter vs exceptions."""
    # Files that should have frontmatter (skill-related content)
    needs_frontmatter = []

    # Files that should be exceptions (documentation, examples, etc.)
    should_be_exceptions = []

    for file_path in files_without_frontmatter:
        rel_path = str(file_path)

        # README files are typically documentation and don't need frontmatter
        if "README.md" in rel_path:
            should_be_exceptions.append(file_path)

        # Files in examples/ directories are typically documentation
        elif "/examples/" in rel_path:
            should_be_exceptions.append(file_path)

        # Files in sample-migration/modules/ are typically case studies/examples
        elif "/sample-migration/modules/" in rel_path:
            should_be_exceptions.append(file_path)

        # Files in scripts/ directories are typically documentation
        elif "/scripts/" in rel_path:
            should_be_exceptions.append(file_path)

        # Skills-eval modules are typically framework documentation
        elif "/skills-eval/modules/" in rel_path:
            should_be_exceptions.append(file_path)

        # Core skill modules should have frontmatter
        elif "/modules/" in rel_path and any(
            x in rel_path
            for x in [
                "core-workflow",
                "implementation-patterns",
                "design-philosophy",
                "troubleshooting",
                "antipatterns-and-migration",
            ]
        ):
            needs_frontmatter.append(file_path)

        # Guide files might benefit from frontmatter
        elif rel_path.endswith("guide.md"):
            needs_frontmatter.append(file_path)

        else:
            # Default to needing frontmatter for skill content
            needs_frontmatter.append(file_path)

    return needs_frontmatter, should_be_exceptions


def main() -> tuple[int, int]:
    """Categorize files."""
    skills_dir = "skills"
    skills_path = Path(skills_dir)

    # Find files without frontmatter using centralized functions
    files_without_frontmatter = [
        f for f in find_markdown_files(skills_path) if not has_frontmatter_file(f)
    ]

    needs_frontmatter, should_be_exceptions = categorize_files(
        files_without_frontmatter
    )

    print("Files that should have YAML frontmatter added:")
    print(f"Total: {len(needs_frontmatter)}")
    for file_path in sorted(needs_frontmatter):
        rel_path = os.path.relpath(file_path, skills_dir)
        print(f"  - {rel_path}")

    print("\nFiles that should remain as exceptions (documentation/examples):")
    print(f"Total: {len(should_be_exceptions)}")
    for file_path in sorted(should_be_exceptions):
        rel_path = os.path.relpath(file_path, skills_dir)
        print(f"  - {rel_path}")

    return len(needs_frontmatter), len(should_be_exceptions)


if __name__ == "__main__":
    main()
