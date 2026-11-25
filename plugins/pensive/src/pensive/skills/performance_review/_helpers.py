"""Helper functions and constants for performance_review.

Module-level utilities used by _PerfVisitor. Split out so
_visitor.py can import them without a circular dependency. Receiver
classification for the membership check is in ``_receivers``.
"""

from __future__ import annotations

import ast

_MEMOIZATION_DECORATORS: frozenset[str] = frozenset(
    {
        "lru_cache",
        "cache",
        "functools.lru_cache",
        "functools.cache",
        "memoize",
    }
)

_REDUCER_FUNCTIONS: frozenset[str] = frozenset(
    {"sum", "max", "min", "any", "all", "sorted", "set", "frozenset"}
)


def _decorator_name(decorator: ast.expr) -> str:
    """Return a string form of a decorator expression for matching."""
    if isinstance(decorator, ast.Name):
        return decorator.id
    if isinstance(decorator, ast.Attribute):
        parts: list[str] = []
        node: ast.expr = decorator
        while isinstance(node, ast.Attribute):
            parts.append(node.attr)
            node = node.value
        if isinstance(node, ast.Name):
            parts.append(node.id)
        return ".".join(reversed(parts))
    if isinstance(decorator, ast.Call):
        return _decorator_name(decorator.func)
    return ""


def _is_memoized(func: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """True if the function carries a known memoization decorator."""
    for dec in func.decorator_list:
        name = _decorator_name(dec)
        if name in _MEMOIZATION_DECORATORS:
            return True
    return False


def _has_self_call(func: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """True if the function body contains a Call to its own name."""
    target = func.name
    for node in ast.walk(func):
        if isinstance(node, ast.Call):
            callee = node.func
            if isinstance(callee, ast.Name) and callee.id == target:
                return True
    return False


def _iter_name(for_node: ast.For) -> str | None:
    """Return the iterable's Name id when `for x in <Name>:`, else None."""
    if isinstance(for_node.iter, ast.Name):
        return for_node.iter.id
    return None


def _is_empty_list_value(value: ast.expr | None) -> bool:
    """True for ``[]`` and a bare ``list()``: an accumulator's start."""
    if value is None:
        return False
    if isinstance(value, ast.List) and not value.elts:
        return True
    return bool(
        isinstance(value, ast.Call)
        and isinstance(value.func, ast.Name)
        and value.func.id == "list"
        and not value.args
        and not value.keywords
    )
