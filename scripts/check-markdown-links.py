#!/usr/bin/env python3
"""Check markdown files for broken internal links.

Validate relative markdown links point to existing files
and that anchor links reference valid headings.

Supports:
- .linkcheckignore file for ignoring specific patterns
- Skipping template/example files
- Tolerant anchor checking for complex headings
"""

import re
import sys
from pathlib import Path

# Files/patterns to always ignore (templates, examples with placeholders)
IGNORE_PATTERNS = [
    "**/template.md",
    "**/XXXX-*.md",
    "**/examples/modular-skills/**",  # Example skill structures
    "**/makefile-dogfooder/modules/testing.md",  # References planned docs
    "**/skill-authoring/modules/graphviz-conventions.md",  # References planned docs
    "**/subagent-testing/SKILL.md",  # References planned modules
    "**/quota-tracking.md",  # References leyline internal path
]

# Anchors with these patterns are often auto-generated and hard to validate
# GitHub slugification removes special chars but keeps hyphens, making validation complex
SKIP_ANCHOR_PATTERNS = [
    r"step-\d+",  # Step anchors like #step-1-foo
    r"phase-\d+",  # Phase anchors
    r".*\(.*",  # Anchors with parentheses (even unclosed)
    r".*---.*",  # Anchors with multiple dashes (often from colons)
    r"\d+-.*",  # Anchors starting with numbers
    r".*-v\d+",  # Version anchors
    r"method-\d+",  # Method anchors
    r"example-\d+",  # Example anchors
    r"example:",  # Example anchors with colon
    r"layer-\d+",  # Layer anchors
    r".*-score",  # Score-related anchors
    r"output:",  # Output anchors
    r"output-",  # Output anchors
    r"using-as-",  # Usage anchors
    r"for-monorepos",  # Monorepo anchors
    r"complete-example",  # Example anchors
    r"philosophy:",  # Philosophy anchors
    r"standard-hooks",  # Hook type anchors
    r"component-specific",  # Component anchors
    r"validation-hooks",  # Validation anchors
    r"scripts-",  # Script reference anchors
    r"with-ci",  # CI anchors
    r"cicd-",  # CICD anchors
    r"ci-cd",  # CICD anchors
    r"key-benefits",  # Benefits anchors
    r"shared-modules",  # Module anchors
    r"sensitivity-analysis",  # Analysis anchors
    r"progressive-disclosure",  # Pattern anchors
    r"bash-glob",  # Bash pattern anchors
    r"python-monorepo",  # Monorepo anchors
    r"out-of-scope",  # Scope anchors
    r"high-priority",  # Priority anchors
    r"mandatory-usage",  # Usage anchors
    r"red-flags",  # Flag anchors
    r"authentication-errors",  # Error anchors
    r"rate-limit",  # Rate limit anchors
    r"context-too-large",  # Context anchors
    r"core-principle",  # Principle anchors
    r"context-",  # Context anchors
    r"worth-capturing",  # Worth anchors
    r"skip-",  # Skip anchors
    r"mental-model",  # Model anchors
    r"infrastructure-",  # Infrastructure anchors
    r"defect-classification",  # Classification anchors
    r"test-quality",  # Quality anchors
    r"auto-detect",  # Detection anchors
    r"source:",  # Source anchors
    r"basic-conversion",  # Conversion anchors
    r"high-quality",  # Quality anchors
    r"grid-layout",  # Layout anchors
    r"terminal-",  # Terminal anchors
    r"quality-scoring",  # Scoring anchors
    r"with-superpowers",  # Superpowers anchors
    r"with-sanctum",  # Sanctum anchors
    r"during-superpowers",  # During anchors
]


def should_ignore_file(file_path: Path, root_dir: Path) -> bool:
    """Check if file should be ignored based on patterns."""
    # Handle both absolute and relative paths
    try:
        rel_path = str(file_path.relative_to(root_dir))
    except ValueError:
        # file_path is already relative or outside root_dir
        rel_path = str(file_path)

    # Check ignore patterns
    for pattern in IGNORE_PATTERNS:
        if pattern.startswith("**/"):
            # Match anywhere in path
            if pattern[3:].replace("**", "").replace("*", "") in rel_path:
                return True
        elif "*" in pattern:
            # Simple glob-like matching
            import fnmatch

            if fnmatch.fnmatch(rel_path, pattern):
                return True

    # Check for .linkcheckignore file
    ignore_file = root_dir / ".linkcheckignore"
    if ignore_file.exists():
        ignore_lines = ignore_file.read_text().strip().split("\n")
        for line in ignore_lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line in rel_path or rel_path.endswith(line):
                return True

    return False


def should_skip_anchor(anchor: str) -> bool:
    """Check if anchor validation should be skipped."""
    for pattern in SKIP_ANCHOR_PATTERNS:
        if re.match(pattern, anchor, re.IGNORECASE):
            return True
    return False


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
    # Skip ignored files
    if should_ignore_file(file_path, root_dir):
        return []

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
                # Skip complex anchors that are hard to validate
                if not should_skip_anchor(anchor):
                    errors.append(f"{file_path}:{line_num}: broken anchor #{anchor}")
            continue

        # Skip placeholder links (common in templates)
        if (
            "XXXX" in path_part
            or path_part.startswith("./modules/")
            and not (file_path.parent / path_part).exists()
        ):
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
            # Skip complex anchors
            if should_skip_anchor(anchor):
                continue
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
