"""Base utilities for async analysis: AST parsing and call detection."""

from __future__ import annotations

import ast

__all__ = ["is_call_to", "parse_code"]


def parse_code(code: str) -> tuple[ast.Module | None, dict | None]:
    """Parse code into an AST, returning an error dict on failure."""
    try:
        return ast.parse(code), None
    except SyntaxError:
        return None, {"error": "Invalid Python syntax"}


def _dotted_name(node: ast.expr) -> str | None:
    """Return "a.b.c" for a chain of names and attributes, else None."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        receiver = _dotted_name(node.value)
        return f"{receiver}.{node.attr}" if receiver else None
    return None


def is_call_to(node: ast.Call, target: str) -> bool:
    """Check if a call node is calling a specific function.

    A dotted target (``requests.get``) matches only that exact chain, so
    ``os.environ.get`` and a bare ``get`` do not match. An undotted target
    (``gather``) matches a bare call or any attribute call of that name.

    Args:
        node: AST Call node
        target: Target function name (e.g., "asyncio.gather")

    Returns:
        True if the call matches the target

    """
    if "." in target:
        return _dotted_name(node.func) == target

    if isinstance(node.func, ast.Name):
        return node.func.id == target
    if isinstance(node.func, ast.Attribute):
        return node.func.attr == target
    return False
