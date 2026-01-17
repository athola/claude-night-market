#!/usr/bin/env python3
"""Check markdown files for broken internal links.

Validate that all relative markdown links point to existing files
and that anchor links reference valid headings.
"""

import re
import sys
from pathlib import Path


def slugify_heading(heading: str) -> str:
    """Convert a markdown heading to a URL slug.

    Follow GitHub-style heading slugification:
    - Lowercase
    - Replace spaces with hyphens
    - Remove special characters except hyphens
    - Collapse multiple hyphens
    """
    slug = heading.lower()
    # Remove backticks but keep the content inside
    slug = re.sub(r"`([^`]*)`", r"\1", slug)
    # Replace spaces and underscores with hyphens
    slug = re.sub(r"[\s_]+", "-", slug)
    # Remove characters that aren't alphanumeric, hyphens, or unicode letters
    slug = re.sub(r"[^\w\-]", "", slug, flags=re.UNICODE)
    # Collapse multiple hyphens
    slug = re.sub(r"-+", "-", slug)
    # Strip leading/trailing hyphens
    slug = slug.strip("-")
    return slug


def extract_headings(content: str) -> set[str]:
    """Extract all heading anchors from markdown content."""
    headings = set()
    # Match ATX headings (# Heading)
    for match in re.finditer(r"^#{1,6}\s+(.+?)(?:\s*#*)?\s*$", content, re.MULTILINE):
        heading_text = match.group(1).strip()
        slug = slugify_heading(heading_text)
        if slug:
            headings.add(slug)
    return headings


def extract_links(content: str) -> list[tuple[str, int]]:
    """Extract all markdown links with line numbers."""
    links = []
    in_code_block = False
    for i, line in enumerate(content.split("\n"), 1):
        # Track fenced code blocks (``` or ~~~)
        stripped = line.lstrip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue
        # Match [text](url) pattern, excluding images ![...]
        for match in re.finditer(r"(?<!!)\[([^\]]*)\]\(([^)]+)\)", line):
            url = match.group(2)
            # Skip external links and mailto
            if url.startswith(("http://", "https://", "mailto:", "#")):
                if url.startswith("#"):
                    links.append((url, i))
                continue
            links.append((url, i))
    return links


def check_file(file_path: Path, root_dir: Path) -> list[str]:
    """Check a single markdown file for broken links."""
    errors = []
    content = file_path.read_text(encoding="utf-8")
    links = extract_links(content)
    file_headings = extract_headings(content)

    for link, line_num in links:
        # Parse link into path and anchor
        if "#" in link:
            path_part, anchor = link.split("#", 1)
        else:
            path_part, anchor = link, None

        # Handle same-file anchor links
        if not path_part:
            if anchor and anchor not in file_headings:
                errors.append(f"{file_path}:{line_num}: broken anchor #{anchor}")
            continue

        # Resolve relative path
        if path_part.startswith("/"):
            target_path = root_dir / path_part.lstrip("/")
        else:
            target_path = (file_path.parent / path_part).resolve()

        # Check if target exists
        if not target_path.exists():
            errors.append(f"{file_path}:{line_num}: broken link to {path_part}")
            continue

        # Check anchor in target file if specified
        if anchor and target_path.suffix == ".md":
            try:
                target_content = target_path.read_text(encoding="utf-8")
                target_headings = extract_headings(target_content)
                if anchor not in target_headings:
                    errors.append(
                        f"{file_path}:{line_num}: broken anchor #{anchor} in {path_part}"
                    )
            except Exception as e:
                errors.append(f"{file_path}:{line_num}: error reading {path_part}: {e}")

    return errors


def main() -> int:
    """Check all markdown files for broken links."""
    # Find repo root (directory containing .git)
    root_dir = Path.cwd()
    while root_dir != root_dir.parent:
        if (root_dir / ".git").exists():
            break
        root_dir = root_dir.parent

    # Get files to check from args or find all markdown files
    if len(sys.argv) > 1:
        files = [Path(f) for f in sys.argv[1:] if f.endswith(".md")]
    else:
        files = list(root_dir.glob("**/*.md"))
        # Exclude common directories
        files = [
            f
            for f in files
            if not any(
                part.startswith(".")
                or part in ("node_modules", "__pycache__", ".venv", "venv")
                for part in f.parts
            )
        ]

    all_errors = []
    for file_path in files:
        errors = check_file(file_path, root_dir)
        all_errors.extend(errors)

    if all_errors:
        print("Broken markdown links found:\n")
        for error in sorted(all_errors):
            print(f"  {error}")
        print(f"\n{len(all_errors)} broken link(s) found")
        return 1

    if files:
        print(f"Checked {len(files)} markdown file(s), no broken links found")
    return 0


if __name__ == "__main__":
    sys.exit(main())
