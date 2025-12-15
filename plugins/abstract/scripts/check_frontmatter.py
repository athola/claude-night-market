#!/usr/bin/env python3
"""Script to check which markdown files in skills directory lack YAML frontmatter.

This script uses the centralized frontmatter processing from abstract.base.
"""

import os
import sys
from pathlib import Path

# Set up imports before using abstract package
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from abstract.base import find_markdown_files, has_frontmatter_file


def find_markdown_files_without_frontmatter(skills_dir: str) -> list[Path]:
    """Find all markdown files in skills directory that lack YAML frontmatter."""
    skills_path = Path(skills_dir)
    return [f for f in find_markdown_files(skills_path) if not has_frontmatter_file(f)]


def main() -> int:
    """Check for missing frontmatter."""
    skills_dir = "skills"

    if not os.path.exists(skills_dir):
        return 1

    files_without_frontmatter = find_markdown_files_without_frontmatter(skills_dir)

    if files_without_frontmatter:
        for file_path in sorted(files_without_frontmatter):
            os.path.relpath(file_path, skills_dir)

        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
