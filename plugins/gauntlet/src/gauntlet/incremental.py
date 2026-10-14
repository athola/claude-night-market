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


class ChangedFilesUnavailableError(RuntimeError):
    """git failed, timed out or is missing, so the changed set is unknown."""


def get_changed_files(base_ref: str = "HEAD", strict: bool = False) -> list[str]:
    """Get files changed since base_ref using git diff.

    On git timeout or a missing binary, returns [] by default, and on a
    nonzero exit it falls back to the staged files. With ``strict=True``
    all three raise ChangedFilesUnavailableError instead, so the caller
    can tell "nothing changed" from "could not tell".
    """
    ref = _validate_ref(base_ref)
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", ref],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        if result.returncode != 0:
            if strict:
                msg = f"git diff {ref} exited with {result.returncode}"
                raise ChangedFilesUnavailableError(msg)
            _log.warning(
                "git diff failed (rc=%d); falling back to staged files"
                " -- incremental scope may differ from expected",
                result.returncode,
            )
            return _get_staged_files()
        return [f.strip() for f in result.stdout.splitlines() if f.strip()]
    except subprocess.TimeoutExpired as exc:
        if strict:
            msg = "git diff timed out"
            raise ChangedFilesUnavailableError(msg) from exc
        _log.warning(
            "git diff timed out; returning empty changeset"
            " -- full rebuild may be needed"
        )
        return []
    except FileNotFoundError as exc:
        if strict:
            msg = "git not found on PATH"
            raise ChangedFilesUnavailableError(msg) from exc
        _log.warning(
            "git not found on PATH; returning empty changeset"
            " -- full rebuild may be needed"
        )
        return []


def _get_staged_files() -> list[str]:
    """Fallback: get staged files."""
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        if result.returncode != 0:
            _log.warning(
                "git diff --cached failed (rc=%d); staged fallback returning empty",
                result.returncode,
            )
            return []
        return [f.strip() for f in result.stdout.splitlines() if f.strip()]
    except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
        _log.warning("staged file fallback failed: %s", exc)
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

    edges_resolved = graph.resolve_call_targets()
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
        "edges_resolved": edges_resolved,
        "duration_sec": duration,
    }


def _no_work_report(**reason: str) -> dict[str, Any]:
    return {
        "build_type": "incremental",
        "files_parsed": 0,
        "nodes_created": 0,
        "edges_created": 0,
        "edges_resolved": 0,
        "duration_sec": 0.0,
        **reason,
    }


def _changed_or_report(base_ref: str) -> tuple[list[str], dict[str, Any] | None]:
    """Return the changed files, or a finished report when there is no work."""
    try:
        changed = get_changed_files(base_ref, strict=True)
    except ChangedFilesUnavailableError as exc:
        return [], _no_work_report(error=f"{exc}; run a full build")
    if not changed:
        return [], _no_work_report(skipped="no changes detected")
    return changed, None


def incremental_update(
    root_dir: str,
    graph: GraphStore,
    base_ref: str = "HEAD",
) -> dict[str, Any]:
    """Update only changed files and their dependents."""
    start = time.monotonic()
    changed, early_report = _changed_or_report(base_ref)
    if early_report is not None:
        return early_report

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

    edges_resolved = graph.resolve_call_targets()
    graph.rebuild_fts()

    duration = round(time.monotonic() - start, 2)
    graph.set_metadata("last_build_type", "incremental")
    graph.set_metadata("last_build_duration", str(duration))

    return {
        "build_type": "incremental",
        "files_parsed": len(files_to_parse),
        "nodes_created": total_nodes,
        "edges_created": total_edges,
        "edges_resolved": edges_resolved,
        "duration_sec": duration,
    }
