"""Import analysis, hot file detection, and blast radius graph."""

from __future__ import annotations

import re
from collections import deque
from pathlib import Path

from .models import (
    BlastResult,
    ImportGraph,
    _walk_limited,
)

# ---------------------------------------------------------------------------
# T008: Import Graph + Hot File Detection
# ---------------------------------------------------------------------------

# Language-specific import patterns (compiled once)
_PY_IMPORT_RE = re.compile(
    r"^\s*(?:from\s+([\w.]+)\s+import|import\s+([\w.]+))", re.MULTILINE
)
_JS_IMPORT_RE = re.compile(
    r"""(?:import\s+.*?\s+from\s+['"]([^'"]+)['"]|"""
    r"""import\s+['"]([^'"]+)['"]|"""
    r"""require\s*\(\s*['"]([^'"]+)['"]\s*\))""",
    re.MULTILINE,
)
_GO_IMPORT_RE = re.compile(r'^\s*"([^"]+)"', re.MULTILINE)
_RUST_USE_RE = re.compile(r"^\s*(?:use|mod)\s+([\w:]+)", re.MULTILINE)

_SOURCE_EXTS: set[str] = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".go",
    ".rs",
    ".java",
    ".kt",
    ".rb",
    ".php",
}


def _extract_imports_from_file(filepath: Path, root: Path) -> list[str]:
    """Extract import targets from a single source file.

    Returns relative module names (not resolved to disk paths).
    """
    ext = filepath.suffix.lower()
    try:
        text = filepath.read_text(errors="replace")
    except OSError:
        return []

    raw: list[str] = []

    if ext in (".py", ".pyi"):
        for m in _PY_IMPORT_RE.finditer(text):
            raw.append(m.group(1) or m.group(2))
    elif ext in (".js", ".jsx", ".ts", ".tsx"):
        for m in _JS_IMPORT_RE.finditer(text):
            raw.append(m.group(1) or m.group(2) or m.group(3))
    elif ext == ".go":
        for m in _GO_IMPORT_RE.finditer(text):
            raw.append(m.group(1))
    elif ext == ".rs":
        for m in _RUST_USE_RE.finditer(text):
            raw.append(m.group(1))

    return raw


def _resolve_import(
    raw_import: str,
    source_file: Path,
    root: Path,
    file_index: dict[str, str],
) -> str | None:
    """Resolve an import string to a project-relative file path.

    Uses a filename index for fast lookup. Returns None for
    external/stdlib imports.
    """
    # Skip stdlib and external packages (match top-level module exactly)
    _top = raw_import.split(".")[0]
    if _top in {
        "os",
        "sys",
        "re",
        "json",
        "typing",
        "collections",
        "pathlib",
        "datetime",
        "dataclasses",
        "abc",
        "functools",
        "itertools",
        "logging",
        "unittest",
        "io",
        "math",
        "hashlib",
        "http",
        "urllib",
        "socket",
        "subprocess",
    }:
        return None

    # For relative imports (Python . prefix), resolve against source dir
    clean = raw_import.lstrip(".")

    # JS/TS relative imports start with ./  or ../
    if raw_import.startswith(("./", "../")):
        source_dir = source_file.parent
        candidate = (source_dir / raw_import).resolve()
        # Try with and without extensions
        for ext in ("", ".js", ".ts", ".tsx", ".jsx"):
            test_path = candidate.parent / (candidate.name + ext)
            if test_path.exists() and test_path.is_file():
                try:
                    rel = str(test_path.relative_to(root))
                    return rel
                except ValueError:
                    continue
        # Try index file in directory
        if candidate.is_dir():
            for idx in ("index.js", "index.ts"):
                idx_path = candidate / idx
                if idx_path.exists():
                    return str(idx_path.relative_to(root))
        return None

    # Module name -> filename heuristic
    parts = clean.rsplit(".", 1)
    stem = parts[-1] if parts else clean
    # Also try the first part (top-level module)
    top_module = clean.split(".")[0] if "." in clean else clean

    for candidate_stem in (stem, top_module):
        for ext in (".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs"):
            key = candidate_stem + ext
            if key in file_index:
                return file_index[key]

    return None


def build_import_graph(root: Path) -> ImportGraph:
    """Build an import graph from source files in the project."""
    root = root.resolve()
    graph = ImportGraph()

    # First pass: index all source files by name for resolution
    file_index: dict[str, str] = {}  # filename -> relative path
    source_files: list[Path] = []

    for dirpath, _dirs, files in _walk_limited(root, max_depth=8):
        for fname in files:
            fpath = Path(dirpath) / fname
            if fpath.suffix.lower() in _SOURCE_EXTS:
                rel = str(fpath.relative_to(root))
                file_index.setdefault(fname, rel)
                source_files.append(fpath)

    # Second pass: extract imports and resolve to project files
    for fpath in source_files:
        source_rel = str(fpath.relative_to(root))
        raw_imports = _extract_imports_from_file(fpath, root)
        for raw in raw_imports:
            target = _resolve_import(raw, fpath, root, file_index)
            if target and target != source_rel:
                graph.add_edge(source_rel, target)

    return graph


def detect_hot_files(graph: ImportGraph, threshold: int = 3) -> list[str]:
    """Identify files imported by threshold or more other files.

    Returns paths sorted by import count (descending).
    """
    hot = [
        (path, len(importers))
        for path, importers in graph.imported_by.items()
        if len(importers) >= threshold
    ]
    hot.sort(key=lambda x: x[1], reverse=True)
    return [path for path, _count in hot]


def blast_radius(graph: ImportGraph, target: str) -> BlastResult:
    """BFS over imported_by to find all files affected by changing target.

    Returns direct dependents (depth 1) and transitive dependents
    (depth 2+) with the intermediate file they're reached through.
    """
    result = BlastResult(target=target)

    if target not in graph.imported_by:
        return result

    # BFS (deque for O(1) popleft)
    visited: set[str] = {target}
    # queue entries: (file, depth, via_file)
    queue: deque[tuple[str, int, str]] = deque(
        (dep, 1, target) for dep in sorted(graph.imported_by.get(target, set()))
    )

    while queue:
        current, depth, via = queue.popleft()
        if current in visited:
            continue
        visited.add(current)

        if depth == 1:
            result.direct.append(current)
        else:
            result.transitive.append((current, via))

        for next_dep in sorted(graph.imported_by.get(current, set())):
            if next_dep not in visited:
                queue.append((next_dep, depth + 1, current))

    result.direct.sort()
    result.transitive.sort()
    return result
