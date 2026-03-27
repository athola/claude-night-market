"""Error handling and timeout pattern analysis for async code."""

from __future__ import annotations

import ast
from typing import Any

from ._base import is_call_to, parse_code

__all__ = ["analyze_error_handling", "analyze_timeouts"]


async def analyze_error_handling(
    code: str, _tree: ast.Module | None = None
) -> dict[str, Any]:
    """Analyze async error handling patterns.

    Args:
        code: Python code to analyze
        _tree: Pre-parsed AST (internal optimisation)

    Returns:
        Dictionary containing error handling analysis

    """
    if not code:
        return {"error_handling": {"try_catch_blocks": [], "functions": {}}}

    tree = _tree
    if tree is None:
        tree, err = parse_code(code)
        if tree is None:
            return {"error_handling": {}, **(err or {})}

    try_catch_blocks: list[dict[str, Any]] = []
    functions: dict[str, Any] = {}

    for node in ast.walk(tree):
        if isinstance(node, ast.AsyncFunctionDef):
            function_name = node.name
            has_error_handling = False
            exception_types: list[str] = []
            graceful_degradation = False

            for child in ast.walk(node):
                if isinstance(child, ast.Try):
                    has_error_handling = True
                    try_catch_blocks.append(
                        {
                            "line_number": child.lineno,
                            "function": function_name,
                        }
                    )

                    for handler in child.handlers:
                        if handler.type:
                            if isinstance(handler.type, ast.Name):
                                exception_types.append(handler.type.id)
                            elif isinstance(handler.type, ast.Attribute):
                                exception_types.append(
                                    f"{handler.type.value.id}.{handler.type.attr}"
                                    if isinstance(handler.type.value, ast.Name)
                                    else handler.type.attr
                                )

                        for stmt in handler.body:
                            if isinstance(stmt, ast.Return):
                                graceful_degradation = True

            functions[function_name] = {
                "has_error_handling": has_error_handling,
                "exception_types": list(set(exception_types)),
                "graceful_degradation": graceful_degradation,
            }

    return {
        "error_handling": {
            "try_catch_blocks": try_catch_blocks,
            "functions": functions,
        }
    }


def _extract_timeout_parameter(node: ast.AsyncFunctionDef) -> Any:
    """Extract timeout parameter from function defaults."""
    for i, arg in enumerate(node.args.args):
        if arg.arg == "timeout" and node.args.defaults:
            defaults_offset = len(node.args.args) - len(node.args.defaults)
            default_index = i - defaults_offset
            if 0 <= default_index < len(node.args.defaults):
                default = node.args.defaults[default_index]
                if isinstance(default, ast.Constant):
                    return default.value
    return None


def _check_wait_for_calls(
    node: ast.AsyncFunctionDef,
    wait_for_functions: list[str],
    timeout_value: Any,
    timeout_arg_index: int,
) -> tuple[bool, Any]:
    """Check for asyncio.wait_for() calls and extract timeout values."""
    has_timeout = False
    for child in ast.walk(node):
        if isinstance(child, ast.Call) and (
            is_call_to(child, "asyncio.wait_for") or is_call_to(child, "wait_for")
        ):
            has_timeout = True
            wait_for_functions.append(node.name)
            for keyword in child.keywords:
                if keyword.arg == "timeout" and isinstance(keyword.value, ast.Constant):
                    timeout_value = keyword.value.value
            pos_arg = (
                child.args[timeout_arg_index - 1]
                if len(child.args) >= timeout_arg_index
                else None
            )
            if pos_arg is not None and isinstance(pos_arg, ast.Constant):
                timeout_value = pos_arg.value
    return has_timeout, timeout_value


def _check_timeout_error_handling(node: ast.AsyncFunctionDef) -> bool:
    """Check if function handles TimeoutError."""
    for child in ast.walk(node):
        if isinstance(child, ast.Try):
            for handler in child.handlers:
                if handler.type:
                    type_name = ""
                    if isinstance(handler.type, ast.Name):
                        type_name = handler.type.id
                    elif isinstance(handler.type, ast.Attribute):
                        type_name = handler.type.attr
                    if "TimeoutError" in type_name:
                        return True
    return False


async def analyze_timeouts(
    code: str, _tree: ast.Module | None = None
) -> dict[str, Any]:
    """Analyze timeout patterns in async code.

    Args:
        code: Python code to analyze
        _tree: Pre-parsed AST (internal optimisation)

    Returns:
        Dictionary containing timeout analysis

    """
    if not code:
        return {"timeout_analysis": {"wait_for_usage": {}, "functions": {}}}

    tree = _tree
    if tree is None:
        tree, err = parse_code(code)
        if tree is None:
            return {"timeout_analysis": {}, **(err or {})}

    wait_for_functions: list[str] = []
    functions: dict[str, Any] = {}
    timeout_arg_index = 2

    for node in ast.walk(tree):
        if isinstance(node, ast.AsyncFunctionDef):
            function_name = node.name
            timeout_value = _extract_timeout_parameter(node)
            has_timeout, timeout_value = _check_wait_for_calls(
                node, wait_for_functions, timeout_value, timeout_arg_index
            )
            handles_timeout_error = _check_timeout_error_handling(node)

            if has_timeout:
                functions[function_name] = {
                    "has_timeout": True,
                    "timeout_value": timeout_value,
                    "handles_timeout_error": handles_timeout_error,
                }

    return {
        "timeout_analysis": {
            "wait_for_usage": {
                "functions": list(set(wait_for_functions)),
            },
            "functions": functions,
        }
    }
