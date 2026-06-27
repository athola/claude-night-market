"""Superpower wrapper infrastructure for translating between commands and superpowers.

This module provides base classes and utilities for creating plugin command wrappers
that delegate to superpowers with parameter translation and error handling.
"""

from __future__ import annotations

import ast
import subprocess  # nosec B404
from pathlib import Path
from typing import Any


def _detect_breaking_changes(files: list[str]) -> list[dict[str, Any]]:
    """Detect breaking changes in a list of files.

    Compares the working-tree version of each file against the
    git HEAD version and reports:

    - Removed public functions/classes
    - Modified function signatures
    - Removed/renamed parameters
    - Changed return types (in type hints)

    Args:
        files: List of file paths to analyze for breaking changes

    Returns:
        List of detected breaking changes with details about each change.
        Empty list if no files or no breaking changes detected.

    """
    if not files:
        return []

    changes: list[dict[str, Any]] = []

    for file_path in files:
        path = Path(file_path)

        # Skip non-Python files
        if path.suffix != ".py":
            continue

        # Parse the current version
        try:
            current_source = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        try:
            current_tree = ast.parse(current_source)
        except SyntaxError:
            continue

        # Get the HEAD version via git
        try:
            cmd = ["git", "show", "HEAD:" + file_path]
            result = subprocess.run(  # nosec B603
                cmd,
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
        except (subprocess.TimeoutExpired, FileNotFoundError):
            continue

        if result.returncode != 0:
            # File is new (no git history) -- no breaking changes
            continue

        try:
            old_tree = ast.parse(result.stdout)
        except SyntaxError:
            continue

        old_public = _extract_public_symbols(old_tree)
        new_public = _extract_public_symbols(current_tree)
        _compare_symbols(file_path, old_public, new_public, changes)

    return changes


def _compare_symbols(
    file_path: str,
    old_public: dict[str, dict[str, Any]],
    new_public: dict[str, dict[str, Any]],
    changes: list[dict[str, Any]],
) -> None:
    """Compare old and new public symbols, appending breaking changes."""
    for name in sorted(old_public):
        if name not in new_public:
            kind = old_public[name]["kind"]
            changes.append(
                {
                    "file": file_path,
                    "type": "removed",
                    "name": name,
                    "details": f"public {kind} '{name}' was removed",
                }
            )
            continue

        old_sym = old_public[name]
        new_sym = new_public[name]

        if old_sym["kind"] != "function" or new_sym["kind"] != "function":
            continue

        _compare_function_sigs(file_path, name, old_sym, new_sym, changes)


def _compare_function_sigs(
    file_path: str,
    name: str,
    old_sym: dict[str, Any],
    new_sym: dict[str, Any],
    changes: list[dict[str, Any]],
) -> None:
    """Compare function signatures and record parameter/return type changes."""
    old_params = old_sym["params"]
    new_params = new_sym["params"]

    for p in old_params:
        if p not in new_params:
            changes.append(
                {
                    "file": file_path,
                    "type": "parameter_removed",
                    "name": name,
                    "details": f"parameter '{p}' was removed from '{name}'",
                }
            )

    common = [p for p in old_params if p in new_params]
    new_order = [p for p in new_params if p in old_params]
    if common != new_order:
        changes.append(
            {
                "file": file_path,
                "type": "parameters_reordered",
                "name": name,
                "details": (
                    f"parameters of '{name}' were reordered: {common} -> {new_order}"
                ),
            }
        )

    old_ret = old_sym["return_type"]
    new_ret = new_sym["return_type"]
    if old_ret is not None and old_ret != new_ret:
        changes.append(
            {
                "file": file_path,
                "type": "return_type_changed",
                "name": name,
                "details": (
                    f"return type of '{name}' changed: '{old_ret}' -> '{new_ret}'"
                ),
            }
        )


def _extract_public_symbols(
    tree: ast.Module,
) -> dict[str, dict[str, Any]]:
    """Extract public functions and classes from an AST module.

    Args:
        tree: Parsed AST module

    Returns:
        Dict mapping symbol name to metadata (kind, params,
        return_type).

    """
    symbols: dict[str, dict[str, Any]] = {}

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.FunctionDef):
            name = node.name
            if name.startswith("_"):
                continue
            params = _extract_param_names(node)
            ret = _unparse_annotation(node.returns)
            symbols[name] = {
                "kind": "function",
                "params": params,
                "return_type": ret,
            }
        elif isinstance(node, ast.ClassDef):
            name = node.name
            if name.startswith("_"):
                continue
            symbols[name] = {
                "kind": "class",
                "params": [],
                "return_type": None,
            }

    return symbols


def _extract_param_names(func_node: ast.FunctionDef) -> list[str]:
    """Return the parameter names of a function (excluding 'self'/'cls').

    Args:
        func_node: An AST FunctionDef node

    Returns:
        Ordered list of parameter names.

    """
    names: list[str] = []
    for arg in func_node.args.args:
        if arg.arg in ("self", "cls"):
            continue
        names.append(arg.arg)
    for arg in func_node.args.kwonlyargs:
        names.append(arg.arg)
    if func_node.args.vararg:
        names.append("*" + func_node.args.vararg.arg)
    if func_node.args.kwarg:
        names.append("**" + func_node.args.kwarg.arg)
    return names


def _unparse_annotation(node: Any) -> str | None:
    """Convert an AST annotation node to a string representation.

    Uses ast.unparse on Python 3.9+.

    Args:
        node: An AST expression node (or None)

    Returns:
        String representation of the annotation, or None.

    """
    if node is None:
        return None
    try:
        return ast.unparse(node)
    except (ValueError, TypeError):
        return None
