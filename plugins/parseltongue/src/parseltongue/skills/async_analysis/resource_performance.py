"""Resource management and performance analysis for async code."""

from __future__ import annotations

import ast
from typing import Any

from ._base import is_call_to, parse_code

__all__ = ["analyze_resource_management", "analyze_performance"]


def _check_context_manager_methods(
    class_node: ast.ClassDef,
) -> tuple[bool, bool]:
    """Check if class has context manager methods."""
    uses_context_manager = False
    cleanup_in_finally = False

    for item in class_node.body:
        if isinstance(item, ast.AsyncFunctionDef):
            if item.name == "__aexit__":
                uses_context_manager = True
                for child in ast.walk(item):
                    if (
                        isinstance(child, ast.Call)
                        and isinstance(child.func, ast.Attribute)
                        and child.func.attr == "close"
                    ):
                        cleanup_in_finally = True
            elif item.name == "__aenter__":
                uses_context_manager = True

    return uses_context_manager, cleanup_in_finally


def _check_session_creation(class_node: ast.ClassDef) -> bool:
    """Check if class creates a session."""
    for item in ast.walk(class_node):
        if isinstance(item, ast.Assign):
            for target in item.targets:
                if (
                    isinstance(target, ast.Attribute)
                    and "session" in target.attr.lower()
                ):
                    return True
    return False


def _check_session_closure(class_node: ast.ClassDef) -> bool:
    """Check if class closes a session."""
    for item in ast.walk(class_node):
        if (
            isinstance(item, ast.Call)
            and isinstance(item.func, ast.Attribute)
            and item.func.attr == "close"
        ):
            return True
    return False


async def analyze_resource_management(
    code: str, _tree: ast.Module | None = None
) -> dict[str, Any]:
    """Analyze async resource management patterns.

    Args:
        code: Python code to analyze
        _tree: Pre-parsed AST (internal optimisation)

    Returns:
        Dictionary containing resource management analysis

    """
    if not code:
        return {"resource_management": {"services": {}}}

    tree = _tree
    if tree is None:
        tree, err = parse_code(code)
        if tree is None:
            return {"resource_management": {}, **(err or {})}

    services: dict[str, Any] = {}
    has_session_management = False

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            class_name = node.name
            uses_context_manager, cleanup_in_finally = _check_context_manager_methods(
                node
            )
            creates_session = _check_session_creation(node)
            closes_session = _check_session_closure(node)

            if creates_session or closes_session:
                has_session_management = True
                services[class_name] = {
                    "creates_session": creates_session,
                    "closes_session": closes_session,
                    "uses_context_manager": uses_context_manager,
                    "cleanup_in_finally": cleanup_in_finally,
                }

    result: dict[str, Any] = {"services": services}
    if has_session_management:
        result["session_management"] = True

    return {"resource_management": result}


async def analyze_performance(
    code: str, _tree: ast.Module | None = None
) -> dict[str, Any]:
    """Analyze async performance patterns.

    Args:
        code: Python code to analyze
        _tree: Pre-parsed AST (internal optimisation)

    Returns:
        Dictionary containing performance analysis

    """
    if not code:
        return {"performance_analysis": {"issues": {}}}

    tree = _tree
    if tree is None:
        tree, err = parse_code(code)
        if tree is None:
            return {"performance_analysis": {}, **(err or {})}

    issues: dict[str, Any] = {}
    concurrent_alternative: dict[str, Any] = {}
    improvement_potential: dict[str, Any] = {}

    async_func_names: list[str] = []
    sequential_funcs: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.AsyncFunctionDef):
            function_name = node.name
            async_func_names.append(function_name)

            for child in ast.walk(node):
                if isinstance(child, ast.For):
                    has_await = any(
                        isinstance(item, ast.Await) for item in ast.walk(child)
                    )

                    if has_await:
                        sequential_funcs.append(function_name)
                        if "sequential_processing" not in issues:
                            issues["sequential_processing"] = {}
                        issues["sequential_processing"][function_name] = {
                            "issue": "Sequential await in loop",
                            "problem": "sequential_async_calls",
                            "suggestion": "Consider using asyncio.gather()",
                        }

            for child in ast.walk(node):
                if isinstance(child, ast.Call) and (
                    is_call_to(child, "asyncio.gather") or is_call_to(child, "gather")
                ):
                    concurrent_alternative[function_name] = {
                        "pattern": "asyncio.gather",
                    }

    if sequential_funcs:
        improvement_potential = {
            "speedup": float(max(2.0, len(sequential_funcs) * 2.0)),
        }

    return {
        "performance_analysis": {
            "issues": issues,
            "concurrent_alternative": concurrent_alternative,
            "improvement_potential": improvement_potential,
        }
    }
