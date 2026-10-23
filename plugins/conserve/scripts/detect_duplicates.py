#!/usr/bin/env python3
"""Duplicate code detection without external dependencies.

Detects repeated code blocks (Tab-completion bloat) using:
1. Line-based hashing for exact/near duplicates
2. Normalized comparison (ignoring whitespace/comments)
3. Function signature similarity detection
4. Competing implementations: one name, different bodies, several files

Usage:
    python detect_duplicates.py [path] [--min-lines N] [--format text|json]
    python detect_duplicates.py src/ --min-lines 5 --format json
"""

from __future__ import annotations

# ruff: noqa: S324, PLR0912, PLR2004
import argparse
import ast
import bisect
import hashlib
import json
import os
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
class CompetingImplementation:
    """One module-level function name defined with different bodies.

    Each variant is one distinct body, listed as the (file, line) sites
    that define it. Two or more variants are two models of one concern.
    """

    name: str
    variants: list[list[tuple[str, int]]] = field(default_factory=list)

    @property
    def body_count(self) -> int:
        """Number of distinct bodies defined under this name."""
        return len(self.variants)

    @property
    def file_count(self) -> int:
        """Number of files that define this name."""
        return len({f for body in self.variants for f, _ in body})


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
            line = line.split("#", maxsplit=1)[0]
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


def _report_unreadable(filepath: Path, exc: OSError) -> None:
    """Name a file the scan skipped, so "no duplicates" is not read as clean."""
    print(f"detect_duplicates: skipped unreadable {filepath}: {exc}", file=sys.stderr)


def extract_blocks(
    filepath: Path, min_lines: int = 5, content: str | None = None
) -> list[tuple[str, int, int, str]]:
    """Extract overlapping blocks from a file.

    Args:
        filepath: Path to the source file.
        min_lines: Minimum block size to consider.
        content: Pre-read file content. If None, reads from filepath.

    Returns: list of (hash, start_line, end_line, content)

    """
    if content is None:
        try:
            content = filepath.read_text(encoding="utf-8", errors="ignore")
        except OSError as exc:
            _report_unreadable(filepath, exc)
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


CODE_EXTENSIONS = frozenset(
    {
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
)

# Directories that hold build output, caches or vendored packages.
EXCLUDED_DIRS = frozenset(
    {
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
        ".uv-cache",
    }
)


def _collect_files(
    paths: list[Path], extensions: set[str] | frozenset[str]
) -> list[Path]:
    """Source files under ``paths`` with a wanted suffix, caches excluded."""
    files: list[Path] = []
    for path in paths:
        if path.is_file():
            if path.suffix.lower() in extensions:
                files.append(path)
        elif path.is_dir():
            # Prune excluded dirs during the walk: rglob descends into
            # node_modules and .git before the filter below drops them.
            for dirpath, dirnames, filenames in os.walk(path):
                dirnames[:] = [d for d in dirnames if d not in EXCLUDED_DIRS]
                files.extend(
                    f
                    for f in (Path(dirpath, name) for name in filenames)
                    if f.suffix.lower() in extensions and f.is_file()
                )
    return [f for f in files if not any(excl in f.parts for excl in EXCLUDED_DIRS)]


def _drop_overlaps(
    locations: list[tuple[Path, int, int, str]],
    seen_by_file: dict[str, list[tuple[int, int]]],
) -> list[tuple[Path, int, int, str]]:
    """Keep locations that overlap no range already reported in their file.

    ``seen_by_file`` holds each file's reported ranges sorted by start and
    is updated with every location kept.
    """
    unique: list[tuple[Path, int, int, str]] = []
    for filepath, start, end, content in locations:
        seen = seen_by_file[str(filepath)]
        idx = bisect.bisect_right(seen, (start,))
        overlaps = any(
            start <= seen[i][1] and end >= seen[i][0]
            for i in range(max(0, idx - 1), min(len(seen), idx + 2))
        )
        if not overlaps:
            unique.append((filepath, start, end, content))
            bisect.insort(seen, (start, end))
    return unique


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
    files = _collect_files(paths, CODE_EXTENSIONS if extensions is None else extensions)

    hash_to_locations: dict[str, list[tuple[Path, int, int, str]]] = defaultdict(list)
    total_lines = 0
    for filepath in files:
        try:
            file_content = filepath.read_text(encoding="utf-8", errors="ignore")
        except OSError as exc:
            _report_unreadable(filepath, exc)
            continue
        total_lines += len(file_content.splitlines())
        for block_hash, start, end, content in extract_blocks(
            filepath, min_lines, content=file_content
        ):
            hash_to_locations[block_hash].append((filepath, start, end, content))

    # A block counts once per location that does not overlap one already
    # reported, so a sliding window over one long run is not a duplicate.
    duplicates: list[DuplicateBlock] = []
    seen_by_file: dict[str, list[tuple[int, int]]] = defaultdict(list)
    for block_hash, locations in hash_to_locations.items():
        if len(locations) < 2:
            continue
        unique_locations = _drop_overlaps(locations, seen_by_file)
        if len(unique_locations) >= 2:
            duplicates.append(
                DuplicateBlock(
                    content=unique_locations[0][3],
                    locations=[
                        (str(loc[0]), loc[1], loc[2]) for loc in unique_locations
                    ],
                    line_count=min_lines,
                    normalized_hash=block_hash,
                )
            )

    # Approximate, avoids double-counting.
    duplicate_lines = sum(
        dup.line_count * (dup.occurrence_count - 1) for dup in duplicates
    )
    duplicates.sort(key=lambda d: d.occurrence_count, reverse=True)

    return DuplicateReport(
        duplicates=duplicates[:50],
        files_scanned=len(files),
        total_lines=total_lines,
        duplicate_lines=duplicate_lines,
    )


def _is_test_module(filepath: Path) -> bool:
    """Test modules keep local helpers and numbered cases by convention."""
    return (
        "tests" in filepath.parts
        or filepath.name.startswith("test_")
        or filepath.name == "conftest.py"
    )


def find_similar_functions(
    path: Path,
    extensions: list[str] | None = None,
) -> list[tuple[str, list[str]]]:
    """Find functions that differ only by a suffix such as ``_v2`` or ``_new``.

    A name repeated with no suffix variant is left to
    ``find_competing_implementations``, which compares bodies.

    Returns: list of (base_name, [full_names])
    """
    if extensions is None:
        extensions = [".py"]
    # Extract function definitions
    func_pattern = re.compile(r"^\s*(?:def|function|fn|func)\s+(\w+)", re.MULTILINE)

    func_names: list[str] = []
    for ext in extensions:
        glob_pattern = f"*{ext}" if ext.startswith(".") else f"*.{ext}"
        for filepath in path.rglob(glob_pattern):
            if any(excl in filepath.parts for excl in ("__pycache__", ".venv", "venv")):
                continue
            if _is_test_module(filepath):
                continue
            try:
                content = filepath.read_text(encoding="utf-8", errors="ignore")
                func_names.extend(func_pattern.findall(content))
            except OSError as exc:
                _report_unreadable(filepath, exc)
                continue

    # Group by common prefixes/suffixes
    # Find functions that differ only by a suffix like _1, _v2, _new, etc.
    similar_groups: dict[str, list[str]] = defaultdict(list)

    for name in func_names:
        # Strip common suffixes
        base = re.sub(r"(_\d+|_v\d+|_new|_old|_backup|_copy|_2)$", "", name)
        similar_groups[base].append(name)

    # Return groups with 2+ names, at least one of them a suffixed variant
    return [
        (base, names)
        for base, names in similar_groups.items()
        if len(names) >= 2 and any(name != base for name in names)
    ]


def _body_fingerprint(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    """Hash a function's arguments and body, ignoring its docstring."""
    body = node.body
    if (
        body
        and isinstance(body[0], ast.Expr)
        and isinstance(body[0].value, ast.Constant)
        and isinstance(body[0].value.value, str)
    ):
        body = body[1:]
    dumped = ast.dump(node.args) + ast.dump(ast.Module(body=body, type_ignores=[]))
    return hashlib.md5(dumped.encode(), usedforsecurity=False).hexdigest()


def find_competing_implementations(
    paths: list[Path],
) -> list[CompetingImplementation]:
    """Find module-level Python functions that share a name but not a body.

    Python only, through ``ast``, unlike the regex scan in
    ``find_similar_functions``. ``main`` and dunder names are skipped
    because they share a name by protocol, and test modules because they
    keep local helpers by convention. Results are ranked by the number
    of distinct bodies, then by the number of files.
    """
    sites: dict[str, dict[str, list[tuple[str, int]]]] = defaultdict(dict)
    for filepath in _collect_files(paths, frozenset({".py"})):
        if _is_test_module(filepath):
            continue
        try:
            source = filepath.read_text(encoding="utf-8", errors="ignore")
        except OSError as exc:
            _report_unreadable(filepath, exc)
            continue
        try:
            tree = ast.parse(source)
        except (SyntaxError, ValueError) as exc:
            print(
                f"detect_duplicates: skipped unparsable {filepath}: {exc}",
                file=sys.stderr,
            )
            continue
        for node in tree.body:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if node.name == "main" or (
                node.name.startswith("__") and node.name.endswith("__")
            ):
                continue
            by_body = sites[node.name]
            by_body.setdefault(_body_fingerprint(node), []).append(
                (str(filepath), node.lineno)
            )

    competing = [
        CompetingImplementation(name=name, variants=list(by_body.values()))
        for name, by_body in sites.items()
        if len(by_body) >= 2
    ]
    competing = [c for c in competing if c.file_count >= 2]
    competing.sort(key=lambda c: (-c.body_count, -c.file_count, c.name))
    return competing


def _format_location(file_path: str, start_line: int, end_line: int) -> str:
    """Format a location tuple as a human-readable string."""
    return f"{file_path}:{start_line}-{end_line}"


def format_text(
    report: DuplicateReport,
    similar_funcs: list,
    competing: list[CompetingImplementation] | None = None,
) -> str:
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
                lines.append(f"    {_format_location(filepath, start, end)}")
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

    if competing:
        lines.append("")
        lines.append(f"COMPETING IMPLEMENTATIONS: {len(competing)} names")
        lines.append("-" * 40)
        for impl in competing[:10]:
            lines.append(
                f"  {impl.name}: {impl.body_count} bodies in {impl.file_count} files"
            )
            first_sites = [f"{f}:{line}" for f, line in (b[0] for b in impl.variants)]
            lines.append(f"    {', '.join(first_sites[:5])}")
        if len(competing) > 10:
            lines.append(f"  ... and {len(competing) - 10} more")

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


def format_json(
    report: DuplicateReport,
    similar_funcs: list,
    competing: list[CompetingImplementation] | None = None,
) -> str:
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
            "competing_implementations": [
                {
                    "name": impl.name,
                    "bodies": impl.body_count,
                    "variants": [
                        [{"file": f, "line": line} for f, line in body]
                        for body in impl.variants
                    ],
                }
                for impl in competing or []
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

    competing = find_competing_implementations(paths)

    # Output
    if args.format == "json":
        print(format_json(report, similar_funcs, competing))
    else:
        print(format_text(report, similar_funcs, competing))

    # A scan of nothing is not a clean scan. The filters above can zero
    # out the file list silently, and tier 1 of the bloat stack gates on
    # this report, so an empty scan must fail rather than pass.
    if report.files_scanned == 0:
        print(
            "detect_duplicates: nothing was scanned (files scanned: 0)", file=sys.stderr
        )
        return 2

    # Exit code based on threshold
    if args.threshold is not None:
        if report.duplication_percentage > args.threshold:
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
