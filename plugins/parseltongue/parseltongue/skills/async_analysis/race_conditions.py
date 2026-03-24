"""Race condition detection for async code."""

from __future__ import annotations

import ast
from typing import Any

from ._base import is_call_to, parse_code

__all__ = ["detect_race_conditions"]


def _detect_lock_usage(func_node: ast.AsyncFunctionDef) -> bool:
    """Detect if function uses a lock pattern."""
    for child in ast.walk(func_node):
        if isinstance(child, ast.AsyncWith):
            for with_item in child.items:
                ctx = with_item.context_expr
                if (
                    isinstance(ctx, ast.Subscript)
                    and isinstance(ctx.slice, ast.Constant)
                    and ctx.slice.value == "lock"
                ):
                    return True
                if isinstance(ctx, ast.Attribute) and "lock" in ctx.attr.lower():
                    return True
                if isinstance(ctx, ast.Name) and "lock" in ctx.id.lower():
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
