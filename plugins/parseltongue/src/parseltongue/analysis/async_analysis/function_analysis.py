"""Async function and context manager analysis."""

from __future__ import annotations

import ast
from typing import Any

from ._base import is_call_to, parse_code

__all__ = [
    "analyze_async_functions",
    "analyze_concurrency_patterns",
    "analyze_context_managers",
]


async def analyze_async_functions(
    code: str, _tree: ast.Module | None = None
) -> dict[str, Any]:
    """Analyze async functions in the provided code.

    Args:
        code: Python code to analyze
        _tree: Pre-parsed AST (internal optimisation)

    Returns:
        Dictionary containing async function analysis

    """
    if not code:
        return {"async_functions": []}

    tree = _tree
    if tree is None:
        tree, err = parse_code(code)
        if tree is None:
            return {"async_functions": [], **(err or {})}

    async_functions = []

    for node in ast.walk(tree):
        if isinstance(node, ast.AsyncFunctionDef):
            await_count = sum(
                1 for child in ast.walk(node) if isinstance(child, ast.Await)
            )
            params = [arg.arg for arg in node.args.args]
            async_functions.append(
                {
                    "name": node.name,
                    "line_number": node.lineno,
                    "parameters": params,
                    "await_calls": await_count,
                }
            )

    return {"async_functions": async_functions}


async def analyze_context_managers(
    code: str, _tree: ast.Module | None = None
) -> dict[str, Any]:
    """Analyze async context managers in the code.

    Args:
        code: Python code to analyze
        _tree: Pre-parsed AST (internal optimisation)

    Returns:
        Dictionary containing context manager analysis

    """
    if not code:
        return {"context_managers": {}}

    tree = _tree
    if tree is None:
        tree, err = parse_code(code)
        if tree is None:
            return {"context_managers": {}, **(err or {})}

    context_managers = {}

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            methods = [
                item.name
                for item in node.body
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
            ]

            has_aenter = "__aenter__" in methods
            has_aexit = "__aexit__" in methods

            if has_aenter or has_aexit:
                context_managers[node.name] = {
                    "has_async_context_manager": has_aenter and has_aexit,
                    "methods": [m for m in methods if m in ("__aenter__", "__aexit__")],
                }

    return {"context_managers": context_managers}


def _analyze_gather_pattern(
    node: ast.AsyncFunctionDef, gather_functions: list[str]
) -> tuple[list[str], str]:
    """Analyze asyncio.gather() usage pattern."""
    concurrent_calls: list[str] = []
    error_handling = "none"
    for child in ast.walk(node):
        if isinstance(child, ast.Call) and (
            is_call_to(child, "asyncio.gather") or is_call_to(child, "gather")
        ):
            gather_functions.append(node.name)
            for kw in child.keywords:
                if kw.arg == "return_exceptions":
                    error_handling = "return_exceptions"
            concurrent_calls.extend(_extract_gather_args(child, node))
    return concurrent_calls, error_handling


def _extract_gather_args(
    call_node: ast.Call, func_node: ast.AsyncFunctionDef
) -> list[str]:
    """Extract function names from gather() arguments."""
    calls: list[str] = []
    for arg in call_node.args:
        if isinstance(arg, ast.Starred):
            calls.extend(_extract_starred_arg(arg, func_node))
        elif isinstance(arg, ast.Call):
            calls.extend(_extract_call_name(arg))
    return calls


def _extract_starred_arg(
    arg: ast.Starred, func_node: ast.AsyncFunctionDef
) -> list[str]:
    """Extract call names from starred arguments."""
    calls: list[str] = []
    list_comp = None

    if isinstance(arg.value, ast.ListComp):
        list_comp = arg.value
    elif isinstance(arg.value, ast.Name):
        var_name = arg.value.id
        for stmt in ast.walk(func_node):
            if isinstance(stmt, ast.Assign) and isinstance(stmt.value, ast.ListComp):
                for t in stmt.targets:
                    if isinstance(t, ast.Name) and t.id == var_name:
                        list_comp = stmt.value

    if list_comp and isinstance(list_comp.elt, ast.Call):
        calls.extend(_extract_call_name(list_comp.elt))

    return calls


def _extract_call_name(call_node: ast.Call) -> list[str]:
    """Extract function name from a call node."""
    if isinstance(call_node.func, ast.Name):
        return [call_node.func.id]
    if isinstance(call_node.func, ast.Attribute):
        return [call_node.func.attr]
    return []


def _check_create_task_pattern(
    node: ast.AsyncFunctionDef, create_task_functions: list[str]
) -> None:
    """Check for asyncio.create_task() usage."""
    for child in ast.walk(node):
        if isinstance(child, ast.Call) and (
            is_call_to(child, "asyncio.create_task") or is_call_to(child, "create_task")
        ):
            create_task_functions.append(node.name)


def _check_task_group_pattern(
    node: ast.AsyncFunctionDef, task_group_functions: list[str]
) -> None:
    """Check for TaskGroup usage."""
    for child in ast.walk(node):
        if isinstance(child, ast.Call) and is_call_to(child, "TaskGroup"):
            task_group_functions.append(node.name)


async def analyze_concurrency_patterns(
    code: str, _tree: ast.Module | None = None
) -> dict[str, Any]:
    """Detect concurrency patterns in async code.

    Args:
        code: Python code to analyze
        _tree: Pre-parsed AST (internal optimisation)

    Returns:
        Dictionary containing concurrency pattern analysis

    """
    if not code:
        return {"concurrency_patterns": {}}

    tree = _tree
    if tree is None:
        tree, err = parse_code(code)
        if tree is None:
            return {"concurrency_patterns": {}, **(err or {})}

    patterns: dict[str, Any] = {}
    gather_functions: list[str] = []
    create_task_functions: list[str] = []
    task_group_functions: list[str] = []

    gather_error_handling = "none"

    for node in ast.walk(tree):
        if isinstance(node, ast.AsyncFunctionDef):
            function_name = node.name
            concurrent_calls, err_handling = _analyze_gather_pattern(
                node, gather_functions
            )
            if err_handling != "none":
                gather_error_handling = err_handling
            _check_create_task_pattern(node, create_task_functions)
            _check_task_group_pattern(node, task_group_functions)

            if concurrent_calls:
                patterns[function_name] = {
                    "concurrent_operations": concurrent_calls[0]
                    if len(concurrent_calls) == 1
                    else concurrent_calls,
                }

    if gather_functions:
        patterns["gather_usage"] = {
            "functions": list(set(gather_functions)),
            "error_handling": gather_error_handling,
        }

    if create_task_functions:
        patterns["create_task_usage"] = {"functions": list(set(create_task_functions))}

    if task_group_functions:
        patterns["task_group_usage"] = {"functions": list(set(task_group_functions))}

    return {"concurrency_patterns": patterns}
