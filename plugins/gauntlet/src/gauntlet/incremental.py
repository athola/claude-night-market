"""Git-diff-based incremental graph updates."""

from __future__ import annotations

import hashlib
import logging
import re
import subprocess
import time
from pathlib import Path
from typing import Any

from gauntlet.graph import GraphStore
from gauntlet.models import EdgeKind
from gauntlet.treesitter_parser import detect_language, parse_file

_log = logging.getLogger(__name__)

_UNSAFE_REF_PATTERN = re.compile(r"[`$;|&]|\.\.|\@\{")

# Extensions we can parse
_SUPPORTED_EXTENSIONS = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".go",
    ".rs",
    ".java",
    ".c",
    ".h",
    ".cpp",
    ".cc",
    ".hpp",
    ".cs",
    ".rb",
    ".php",
    ".kt",
    ".swift",
    ".scala",
    ".lua",
    ".r",
    ".R",
}

_SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    ".tox",
    ".mypy_cache",
    ".ruff_cache",
    "dist",
    "build",
    ".egg-info",
    ".eggs",
}


def _validate_ref(ref: str) -> str:
    """Validate a git ref to prevent injection."""
    if _UNSAFE_REF_PATTERN.search(ref):
        msg = f"unsafe git ref: {ref}"
        raise ValueError(msg)
    return ref


def get_changed_files(base_ref: str = "HEAD") -> list[str]:
    """Get files changed since base_ref using git diff."""
    ref = _validate_ref(base_ref)
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", ref],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            _log.info(
                "git diff failed (rc=%d), falling back to staged files",
                result.returncode,
            )
            return _get_staged_files()
        return [f.strip() for f in result.stdout.splitlines() if f.strip()]
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return []


def _get_staged_files() -> list[str]:
    """Fallback: get staged files."""
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return [f.strip() for f in result.stdout.splitlines() if f.strip()]
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return []


def find_dependents(graph: GraphStore, file_path: str) -> list[str]:
    """Find files that import from or depend on the given file."""
    nodes = graph.get_nodes_in_file(file_path)
    dependent_files: set[str] = set()

    for node in nodes:
        # Find incoming IMPORTS_FROM, CALLS, INHERITS edges
        for edge in graph.get_edges_by_target(node.qualified_name):
            if edge.kind in (
                EdgeKind.IMPORTS_FROM,
                EdgeKind.CALLS,
                EdgeKind.INHERITS,
                EdgeKind.IMPLEMENTS,
            ):
                source_node = graph.get_node(edge.source_qn)
                if source_node and source_node.file_path != file_path:
                    dependent_files.add(source_node.file_path)

    return list(dependent_files)


def collect_files(root_dir: str) -> list[str]:
    """Walk directory tree and collect parseable source files."""
    root = Path(root_dir)
    files: list[str] = []

    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix not in _SUPPORTED_EXTENSIONS:
            continue
        # Skip hidden dirs and common exclusions
        parts = path.relative_to(root).parts
        if any(p.startswith(".") or p in _SKIP_DIRS for p in parts[:-1]):
            continue
        # Skip binary files (check first 512 bytes)
        try:
            with open(path, "rb") as f:
                chunk = f.read(512)
            if b"\x00" in chunk:
                continue
        except OSError:
            continue
        files.append(str(path))

    return sorted(files)


def full_build(root_dir: str, graph: GraphStore) -> dict[str, Any]:
    """Parse all source files and build the graph from scratch."""
    start = time.monotonic()
    files = collect_files(root_dir)

    total_nodes = 0
    total_edges = 0

    for fp in files:
        nodes, edges = parse_file(fp)
        if nodes:
            graph.store_file(fp, nodes, edges)
            total_nodes += len(nodes)
            total_edges += len(edges)

    graph.rebuild_fts()

    # Store build metadata
    duration = round(time.monotonic() - start, 2)
    graph.set_metadata("last_build_type", "full")
    graph.set_metadata("last_build_duration", str(duration))
    graph.set_metadata("last_build_files", str(len(files)))

    return {
        "build_type": "full",
        "files_parsed": len(files),
        "nodes_created": total_nodes,
        "edges_created": total_edges,
        "duration_sec": duration,
    }


def incremental_update(
    root_dir: str,
    graph: GraphStore,
    base_ref: str = "HEAD",
) -> dict[str, Any]:
    """Update only changed files and their dependents."""
    start = time.monotonic()
    changed = get_changed_files(base_ref)

    if not changed:
        return {
            "build_type": "incremental",
            "files_parsed": 0,
            "nodes_created": 0,
            "edges_created": 0,
            "duration_sec": 0.0,
            "skipped": "no changes detected",
        }

    # Collect dependents
    to_reparse: set[str] = set()
    for fp in changed:
        abs_path = str(Path(root_dir) / fp) if not Path(fp).is_absolute() else fp
        if Path(abs_path).exists() and detect_language(abs_path):
            to_reparse.add(abs_path)
            for dep in find_dependents(graph, abs_path):
                if Path(dep).exists():
                    to_reparse.add(dep)

    # Hash-based skip: don't re-parse if content unchanged
    files_to_parse: list[str] = []
    for fp in to_reparse:
        try:
            content = Path(fp).read_bytes()
            current_hash = hashlib.sha256(content).hexdigest()
        except OSError:
            continue

        existing_nodes = graph.get_nodes_in_file(fp)
        if existing_nodes and existing_nodes[0].file_hash == current_hash:
            continue
        files_to_parse.append(fp)

    # Handle deleted files
    for fp in changed:
        abs_path = str(Path(root_dir) / fp) if not Path(fp).is_absolute() else fp
        if not Path(abs_path).exists():
            graph.delete_nodes_in_file(abs_path)
            graph.delete_edges_in_file(abs_path)

    total_nodes = 0
    total_edges = 0

    for fp in files_to_parse:
        nodes, edges = parse_file(fp)
        if nodes:
            graph.store_file(fp, nodes, edges)
            total_nodes += len(nodes)
            total_edges += len(edges)

    graph.rebuild_fts()

    duration = round(time.monotonic() - start, 2)
    graph.set_metadata("last_build_type", "incremental")
    graph.set_metadata("last_build_duration", str(duration))

    return {
        "build_type": "incremental",
        "files_parsed": len(files_to_parse),
        "nodes_created": total_nodes,
        "edges_created": total_edges,
        "duration_sec": duration,
    }
