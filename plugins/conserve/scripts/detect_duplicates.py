#!/usr/bin/env python3
from __future__ import annotations

# ruff: noqa: S324, PLR0912, PLR2004
"""Duplicate code detection without external dependencies.

Detects repeated code blocks (Tab-completion bloat) using:
1. Line-based hashing for exact/near duplicates
2. Normalized comparison (ignoring whitespace/comments)
3. Function signature similarity detection

Usage:
    python detect_duplicates.py [path] [--min-lines N] [--format text|json]
    python detect_duplicates.py src/ --min-lines 5 --format json
"""

import argparse
import hashlib
import json
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class DuplicateBlock:
    """A block of code that appears multiple times."""

    content: str
    # (file, start, end)
    locations: list[tuple[str, int, int]] = field(default_factory=list)
    line_count: int = 0
    normalized_hash: str = ""

    @property
    def occurrence_count(self) -> int:
        """Number of times this block appears in the codebase."""
        return len(self.locations)


@dataclass
class DuplicateReport:
    """Summary of duplicate detection results."""

    duplicates: list[DuplicateBlock]
    files_scanned: int
    total_lines: int
    duplicate_lines: int

    @property
    def duplication_percentage(self) -> float:
        """Percentage of code that is duplicated."""
        if self.total_lines == 0:
            return 0.0
        return (self.duplicate_lines / self.total_lines) * 100


def normalize_line(line: str, lang: str = "python") -> str:
    """Normalize a line for comparison (remove comments, normalize whitespace)."""
    # Remove inline comments
    if lang == "python":
        # Remove # comments but not inside strings (simplified)
        if "#" in line and not ('"' in line or "'" in line):
            line = line.split("#")[0]
    elif lang in ("javascript", "typescript", "java", "c", "cpp", "go", "rust"):
        # Remove // comments
        if "//" in line:
            line = line.split("//")[0]

    # Normalize whitespace
    return " ".join(line.split()).strip()


def get_language(filepath: Path) -> str:
    """Determine language from file extension."""
    ext_map = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".jsx": "javascript",
        ".tsx": "typescript",
        ".java": "java",
        ".c": "c",
        ".cpp": "cpp",
        ".h": "c",
        ".hpp": "cpp",
        ".go": "go",
        ".rs": "rust",
        ".rb": "ruby",
        ".php": "php",
    }
    return ext_map.get(filepath.suffix.lower(), "unknown")


def hash_block(lines: list[str], lang: str) -> str:
    """Create a normalized hash for a block of code."""
    normalized = [normalize_line(line, lang) for line in lines]
    # Filter empty lines for hashing
    content = "\n".join(line for line in normalized if line)
    return hashlib.md5(content.encode(), usedforsecurity=False).hexdigest()


def extract_blocks(
    filepath: Path, min_lines: int = 5
) -> list[tuple[str, int, int, str]]:
    """Extract overlapping blocks from a file.

    Returns: list of (hash, start_line, end_line, content)
    """
    try:
        content = filepath.read_text(encoding="utf-8", errors="ignore")
    except (OSError, UnicodeDecodeError):
        return []

    lines = content.splitlines()
    if len(lines) < min_lines:
        return []

    lang = get_language(filepath)
    blocks = []

    # Sliding window of min_lines
    for start in range(len(lines) - min_lines + 1):
        end = start + min_lines
        block_lines = lines[start:end]

        # Skip blocks that are mostly empty/whitespace
        non_empty = [line for line in block_lines if line.strip()]
        if len(non_empty) < min_lines * 0.6:  # At least 60% non-empty
            continue

        block_hash = hash_block(block_lines, lang)
        block_content = "\n".join(block_lines)
        blocks.append((block_hash, start + 1, end, block_content))  # 1-indexed

    return blocks


def find_duplicates(
    paths: list[Path],
    min_lines: int = 5,
    extensions: set[str] | None = None,
) -> DuplicateReport:
    """Find duplicate code blocks across files.

    Args:
        paths: Files or directories to scan
        min_lines: Minimum block size to consider
        extensions: File extensions to include (None = all code files)

    """
    if extensions is None:
        extensions = {
            ".py",
            ".js",
            ".ts",
            ".jsx",
            ".tsx",
            ".java",
            ".c",
            ".cpp",
            ".h",
            ".go",
            ".rs",
            ".rb",
            ".php",
        }

    # Collect all files
    files: list[Path] = []
    for path in paths:
        if path.is_file():
            if path.suffix.lower() in extensions:
                files.append(path)
        elif path.is_dir():
            for ext in extensions:
                files.extend(path.rglob(f"*{ext}"))

    # Exclude common non-source directories
    exclude_patterns = {
        "__pycache__",
        "node_modules",
        ".git",
        ".venv",
        "venv",
        "dist",
        "build",
        ".tox",
        ".pytest_cache",
        ".mypy_cache",
    }
    files = [f for f in files if not any(excl in f.parts for excl in exclude_patterns)]

    # Hash all blocks
    hash_to_locations: dict[str, list[tuple[Path, int, int, str]]] = defaultdict(list)
    total_lines = 0

    for filepath in files:
        try:
            content = filepath.read_text(encoding="utf-8", errors="ignore")
            line_count = len(content.splitlines())
            total_lines += line_count
        except (OSError, UnicodeDecodeError):
            continue

        blocks = extract_blocks(filepath, min_lines)
        for block_hash, start, end, content in blocks:
            hash_to_locations[block_hash].append((filepath, start, end, content))

    # Find duplicates (blocks appearing in multiple locations)
    duplicates: list[DuplicateBlock] = []
    seen_ranges: set[tuple[str, int, int]] = set()  # Avoid overlapping reports

    for block_hash, locations in hash_to_locations.items():
        if len(locations) < 2:
            continue

        # Check for duplicates across different files OR distant in same file
        unique_locations: list[tuple[Path, int, int, str]] = []
        for filepath, start, end, content in locations:
            # Skip if overlaps with already-reported range in same file
            range_key = (str(filepath), start, end)
            overlaps = False
            for seen_file, seen_start, seen_end in seen_ranges:
                if seen_file == str(filepath):
                    # Check for overlap
                    if not (end < seen_start or start > seen_end):
                        overlaps = True
                        break
            if not overlaps:
                unique_locations.append((filepath, start, end, content))
                seen_ranges.add(range_key)

        if len(unique_locations) >= 2:
            dup = DuplicateBlock(
                content=unique_locations[0][3],
                locations=[(str(loc[0]), loc[1], loc[2]) for loc in unique_locations],
                line_count=min_lines,
                normalized_hash=block_hash,
            )
            duplicates.append(dup)

    # Calculate duplicate line count (approximate, avoids double-counting)
    duplicate_lines = sum(
        dup.line_count * (dup.occurrence_count - 1) for dup in duplicates
    )

    # Sort by occurrence count (most duplicated first)
    duplicates.sort(key=lambda d: d.occurrence_count, reverse=True)

    return DuplicateReport(
        duplicates=duplicates[:50],  # Limit to top 50
        files_scanned=len(files),
        total_lines=total_lines,
        duplicate_lines=duplicate_lines,
    )


def find_similar_functions(path: Path) -> list[tuple[str, list[str]]]:
    """Find functions with similar names (potential abstraction candidates).

    Returns: list of (base_name, [full_names])
    """
    # Extract function definitions
    func_pattern = re.compile(r"^\s*(?:def|function|fn|func)\s+(\w+)", re.MULTILINE)

    func_names: list[str] = []
    for filepath in path.rglob("*.py"):
        if any(excl in filepath.parts for excl in ("__pycache__", ".venv", "venv")):
            continue
        try:
            content = filepath.read_text(encoding="utf-8", errors="ignore")
            func_names.extend(func_pattern.findall(content))
        except (OSError, UnicodeDecodeError):
            continue

    # Group by common prefixes/suffixes
    # Find functions that differ only by a suffix like _1, _v2, _new, etc.
    similar_groups: dict[str, list[str]] = defaultdict(list)

    for name in func_names:
        # Strip common suffixes
        base = re.sub(r"(_\d+|_v\d+|_new|_old|_backup|_copy|_2)$", "", name)
        similar_groups[base].append(name)

    # Return groups with 2+ similar functions
    return [(base, names) for base, names in similar_groups.items() if len(names) >= 2]


def format_text(report: DuplicateReport, similar_funcs: list) -> str:
    """Format report as human-readable text."""
    lines = [
        "=" * 60,
        "DUPLICATE CODE DETECTION REPORT",
        "=" * 60,
        "",
        f"Files scanned: {report.files_scanned}",
        f"Total lines: {report.total_lines:,}",
        f"Duplicate lines: {report.duplicate_lines:,}",
        f"Duplication: {report.duplication_percentage:.1f}%",
        "",
    ]

    if report.duplicates:
        lines.append(f"DUPLICATE BLOCKS FOUND: {len(report.duplicates)}")
        lines.append("-" * 40)

        for i, dup in enumerate(report.duplicates[:10], 1):
            summary = (
                f"\n[{i}] {dup.occurrence_count} occurrences ({dup.line_count} lines)"
            )
            lines.append(summary)
            for filepath, start, end in dup.locations[:5]:
                lines.append(f"    {filepath}:{start}-{end}")
            if len(dup.locations) > 5:
                lines.append(f"    ... and {len(dup.locations) - 5} more")
            # Show first 3 lines of content
            preview = "\n".join(dup.content.splitlines()[:3])
            lines.append("    Content preview:")
            for line in preview.splitlines():
                lines.append(f"      {line[:70]}")
    else:
        lines.append("No significant duplicates found.")

    if similar_funcs:
        lines.append("")
        lines.append(f"SIMILAR FUNCTION NAMES: {len(similar_funcs)} groups")
        lines.append("-" * 40)
        for base, names in similar_funcs[:10]:
            lines.append(f"  {base}: {', '.join(names[:5])}")
            if len(names) > 5:
                lines.append(f"    ... and {len(names) - 5} more")

    # Recommendations
    lines.append("")
    lines.append("RECOMMENDATIONS")
    lines.append("-" * 40)
    if report.duplication_percentage > 15:
        lines.append(
            "HIGH duplication detected. Extract common patterns to shared utilities."
        )
    elif report.duplication_percentage > 5:
        lines.append(
            "MODERATE duplication. Review top blocks for refactoring opportunities."
        )
    else:
        lines.append("LOW duplication. Codebase appears well-factored.")

    return "\n".join(lines)


def format_json(report: DuplicateReport, similar_funcs: list) -> str:
    """Format report as JSON."""
    return json.dumps(
        {
            "summary": {
                "files_scanned": report.files_scanned,
                "total_lines": report.total_lines,
                "duplicate_lines": report.duplicate_lines,
                "duplication_percentage": round(report.duplication_percentage, 2),
            },
            "duplicates": [
                {
                    "occurrences": dup.occurrence_count,
                    "lines": dup.line_count,
                    "locations": [
                        {"file": f, "start": s, "end": e} for f, s, e in dup.locations
                    ],
                    "hash": dup.normalized_hash,
                }
                for dup in report.duplicates
            ],
            "similar_functions": [
                {"base_name": base, "variants": names} for base, names in similar_funcs
            ],
        },
        indent=2,
    )


def main() -> int:
    """CLI entry point for duplicate code detection."""
    parser = argparse.ArgumentParser(
        description="Detect duplicate code blocks (Tab-completion bloat)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    %(prog)s src/                    # Scan src/ directory
    %(prog)s . --min-lines 10        # Require 10+ line blocks
    %(prog)s . --format json         # JSON output for CI
    %(prog)s . --extensions .py .js  # Only Python and JavaScript
        """,
    )
    parser.add_argument(
        "paths",
        nargs="*",
        default=["."],
        help="Files or directories to scan (default: current directory)",
    )
    parser.add_argument(
        "--min-lines",
        type=int,
        default=5,
        help="Minimum lines for a duplicate block (default: 5)",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--extensions",
        nargs="+",
        help="File extensions to scan (default: common code files)",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=None,
        help="Exit with error if duplication exceeds threshold percentage",
    )

    args = parser.parse_args()

    paths = [Path(p) for p in args.paths]
    extensions = set(args.extensions) if args.extensions else None

    # Run detection
    report = find_duplicates(paths, args.min_lines, extensions)
    similar_funcs = []
    for path in paths:
        if path.is_dir():
            similar_funcs.extend(find_similar_functions(path))

    # Output
    if args.format == "json":
        print(format_json(report, similar_funcs))
    else:
        print(format_text(report, similar_funcs))

    # Exit code based on threshold
    if args.threshold is not None:
        if report.duplication_percentage > args.threshold:
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
