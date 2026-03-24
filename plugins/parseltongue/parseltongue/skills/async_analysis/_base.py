"""Base utilities for async analysis: AST parsing and call detection."""

from __future__ import annotations

import ast

__all__ = ["parse_code", "is_call_to"]


def parse_code(code: str) -> tuple[ast.Module | None, dict | None]:
    """Parse code into an AST, returning an error dict on failure."""
    try:
        return ast.parse(code), None
    except SyntaxError:
        return None, {"error": "Invalid Python syntax"}


def is_call_to(node: ast.Call, target: str) -> bool:
    """Check if a call node is calling a specific function.

    Args:
        node: AST Call node
        target: Target function name (e.g., "asyncio.gather")

    Returns:
        True if the call matches the target

    """
    if isinstance(node.func, ast.Name):
        return node.func.id == target or node.func.id == target.split(".")[-1]

    if isinstance(node.func, ast.Attribute):
        if "." in target:
            module, func = target.rsplit(".", 1)
            if isinstance(node.func.value, ast.Name):
                return node.func.value.id == module and node.func.attr == func
        return node.func.attr == target.split(".")[-1]

    return False
