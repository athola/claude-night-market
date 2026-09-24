"""Race condition detection for async code."""

from __future__ import annotations

import ast
import re
from typing import Any

from ._base import is_call_to, parse_code

__all__ = ["detect_race_conditions"]

#: Words ending in "lock" that do not name one. A substring test read
#: `blocklist`, `clock` and `unlock` as locks, and a false positive here
#: suppresses the unsynchronized access the detector exists to report.
#: A suffix test is still needed for run-together names like `rwlock`
#: and `dblock`, so the exceptions are listed as whole words.
_NOT_LOCKS = frozenset({"block", "clock", "unlock"})

#: Splits `writeLock` and also the acronym run in `RWLock`.
_CAMEL_BOUNDARY = re.compile(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])")


def _identifier_tokens(name: str) -> list[str]:
    """Split an identifier into lowercase words on underscores and camel case."""
    return [part for part in _CAMEL_BOUNDARY.sub("_", name).lower().split("_") if part]


def _names_a_lock(name: str) -> bool:
    """Return True when a word of *name* ends in `lock` and is not an exception."""
    for token in _identifier_tokens(name):
        stem = token[:-1] if token.endswith("locks") else token
        if stem.endswith("lock") and stem not in _NOT_LOCKS:
            return True
    return False


def _context_names_a_lock(ctx: ast.expr) -> bool:
    """Return True when the context expression is named as a lock."""
    if isinstance(ctx, ast.Subscript):
        key = ctx.slice
        if (
            isinstance(key, ast.Constant)
            and isinstance(key.value, str)
            and _names_a_lock(key.value)
        ):
            return True
        return _context_names_a_lock(ctx.value)
    if isinstance(ctx, ast.Attribute):
        return _names_a_lock(ctx.attr)
    if isinstance(ctx, ast.Name):
        return _names_a_lock(ctx.id)
    return False


def _detect_lock_usage(func_node: ast.AsyncFunctionDef) -> bool:
    """Detect if function uses a lock pattern."""
    for child in ast.walk(func_node):
        if isinstance(child, ast.AsyncWith):
            for with_item in child.items:
                if _context_names_a_lock(with_item.context_expr):
                    return True
    return False


def _check_async_function_locks(
    tree: ast.Module, safe_patterns: dict[str, Any]
) -> None:
    """Check async functions for lock usage patterns."""
    for node in ast.walk(tree):
        if isinstance(node, ast.AsyncFunctionDef):
            function_name = node.name
            if _detect_lock_usage(node):
                safe_patterns[function_name] = {"uses_lock": True}


def _collect_module_shared_state(tree: ast.Module) -> dict[str, int]:
    """Collect module-level shared state variables."""
    module_shared_state: dict[str, int] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    module_shared_state[target.id] = 0
    return module_shared_state


def _check_shared_state_access(
    tree: ast.Module,
    module_shared_state: dict[str, int],
    safe_patterns: dict[str, Any],
    unsynchronized: dict[str, Any],
    recommendations: list[str],
) -> None:
    """Check for unsynchronized access to shared state."""
    for node in ast.walk(tree):
        if isinstance(node, ast.AsyncFunctionDef):
            function_name = node.name
            accesses = 0

            for child in ast.walk(node):
                if (
                    isinstance(child, ast.Subscript)
                    and isinstance(child.value, ast.Name)
                    and child.value.id in module_shared_state
                ):
                    accesses += 1

            if accesses > 0 and function_name not in safe_patterns:
                unsynchronized[function_name] = {"accesses": accesses}
                recommendations.append(
                    f"Add asyncio.Lock to protect shared state in '{function_name}'"
                )


def _check_class_lock_usage(class_node: ast.ClassDef) -> bool:
    """Check if class uses lock in its async methods."""
    for body_item in class_node.body:
        if isinstance(body_item, ast.AsyncFunctionDef):
            for child in ast.walk(body_item):
                if isinstance(child, ast.Call) and (
                    is_call_to(child, "asyncio.Lock") or is_call_to(child, "Lock")
                ):
                    return True
    return False


def _check_class_shared_state(
    tree: ast.Module,
    safe_patterns: dict[str, Any],
    unsynchronized: dict[str, Any],
    recommendations: list[str],
) -> None:
    """Check classes for unsynchronized shared state."""
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            has_shared_state = any(isinstance(item, ast.Assign) for item in node.body)
            class_uses_lock = _check_class_lock_usage(node)

            if has_shared_state and not class_uses_lock:
                unsynchronized[node.name] = {
                    "warning": "Shared state without synchronization",
                }
                recommendations.append(f"Add asyncio.Lock to class '{node.name}'")
            elif has_shared_state and class_uses_lock:
                safe_patterns[node.name] = {"uses_lock": True}


async def detect_race_conditions(
    code: str, _tree: ast.Module | None = None
) -> dict[str, Any]:
    """Detect potential race conditions in async code.

    Args:
        code: Python code to analyze
        _tree: Pre-parsed AST (internal optimisation)

    Returns:
        Dictionary containing race condition analysis

    """
    if not code:
        return {
            "race_conditions": {
                "unsynchronized_shared_state": {},
                "safe_patterns": {},
                "recommendations": [],
            }
        }

    tree = _tree
    if tree is None:
        tree, err = parse_code(code)
        if tree is None:
            return {"race_conditions": {}, **(err or {})}

    unsynchronized: dict[str, Any] = {}
    safe_patterns: dict[str, Any] = {}
    recommendations: list[str] = []

    _check_async_function_locks(tree, safe_patterns)
    module_shared_state = _collect_module_shared_state(tree)
    _check_shared_state_access(
        tree, module_shared_state, safe_patterns, unsynchronized, recommendations
    )
    _check_class_shared_state(tree, safe_patterns, unsynchronized, recommendations)

    return {
        "race_conditions": {
            "unsynchronized_shared_state": unsynchronized,
            "safe_patterns": safe_patterns,
            "recommendations": recommendations,
        }
    }
