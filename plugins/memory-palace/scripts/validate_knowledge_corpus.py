#!/usr/bin/env python3
"""Validate memory palace knowledge corpus entries have proper YAML frontmatter."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import cast

import yaml

# Required fields for knowledge corpus entries
REQUIRED_FIELDS = {
    "title",
    "source",
    "palace",
    "district",
    "maturity",
    "tags",
    "queries",
}
VALID_MATURITY = {"seedling", "budding", "evergreen"}

# Paths
CORPUS_DIR = Path("plugins/memory-palace/docs/knowledge-corpus")
EXCLUDED_FILES = {"README.md"}


def extract_frontmatter(content: str) -> dict | None:
    """Extract YAML frontmatter from markdown content."""
    if not content.startswith("---"):
        return None

    try:
        # Find the closing ---
        end_idx = content.index("---", 3)
        frontmatter_str = content[3:end_idx].strip()
        result = yaml.safe_load(frontmatter_str)
        return cast(dict | None, result)
    except (ValueError, yaml.YAMLError):
        return None


def validate_entry(file_path: Path) -> list[str]:
    """Validate a single knowledge corpus entry. Returns list of errors."""
    errors = []
    content = file_path.read_text()

    # Check frontmatter exists
    frontmatter = extract_frontmatter(content)
    if frontmatter is None:
        errors.append(f"{file_path}: Missing or invalid YAML frontmatter")
        return errors

    # Check required fields
    missing = REQUIRED_FIELDS - set(frontmatter.keys())
    if missing:
        errors.append(
            f"{file_path}: Missing required fields: {', '.join(sorted(missing))}"
        )

    # Validate maturity value
    maturity = frontmatter.get("maturity")
    if maturity and maturity not in VALID_MATURITY:
        errors.append(
            f"{file_path}: Invalid maturity '{maturity}'. "
            f"Must be one of: {', '.join(sorted(VALID_MATURITY))}"
        )

    # Validate tags is a list
    tags = frontmatter.get("tags")
    if tags is not None and not isinstance(tags, list):
        errors.append(f"{file_path}: 'tags' must be a list")

    # Validate queries is a list
    queries = frontmatter.get("queries")
    if queries is not None and not isinstance(queries, list):
        errors.append(f"{file_path}: 'queries' must be a list")

    # Warn if queries list is empty or too short
    if isinstance(queries, list) and len(queries) < 3:  # noqa: PLR2004
        errors.append(
            f"{file_path}: 'queries' should have at least 3 entries for good retrieval coverage"
        )

    return errors


def main() -> int:
    """Validate all knowledge corpus markdown files."""
    # Find all markdown files in knowledge corpus
    if not CORPUS_DIR.exists():
        print(f"Warning: Knowledge corpus directory not found: {CORPUS_DIR}")
        return 0

    md_files = [
        f
        for f in CORPUS_DIR.glob("*.md")
        if f.name not in EXCLUDED_FILES and not f.name.startswith(".")
    ]

    if not md_files:
        print("No knowledge corpus entries to validate")
        return 0

    all_errors = []
    for file_path in sorted(md_files):
        errors = validate_entry(file_path)
        all_errors.extend(errors)

    if all_errors:
        print("Knowledge corpus validation failed:")
        for error in all_errors:
            print(f"  ✗ {error}")
        return 1

    print(f"✓ Validated {len(md_files)} knowledge corpus entries")
    return 0


if __name__ == "__main__":
    sys.exit(main())
