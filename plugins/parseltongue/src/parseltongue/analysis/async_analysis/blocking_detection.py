"""Blocking call and missing await detection in async code."""

from __future__ import annotations

import ast
from typing import Any

from ._base import is_call_to, parse_code

__all__ = ["detect_blocking_calls", "detect_missing_await"]


def _is_blocking_sleep(call: ast.Call) -> bool:
    """Match time.sleep() and a bare sleep(); asyncio.sleep() is not blocking."""
    return is_call_to(call, "time.sleep") or (
        isinstance(call.func, ast.Name) and call.func.id == "sleep"
    )


def _collect_sync_function_info(
    tree: ast.Module,
    sync_func_names: set[str],
    sync_func_blocking: dict[str, list[str]],
) -> None:
    """Collect information about sync functions and their blocking calls."""
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and not isinstance(
            node, ast.AsyncFunctionDef
        ):
            sync_func_names.add(node.name)
            for child in ast.walk(node):
                if isinstance(child, ast.Call) and _is_blocking_sleep(child):
                    sync_func_blocking.setdefault(node.name, []).append("time_sleep")


def _check_time_sleep(
    call: ast.Call,
    blocking_patterns: dict[str, Any],
    recommendations: list[str],
) -> None:
    """Check for time.sleep() calls."""
    if _is_blocking_sleep(call):
        blocking_patterns["time_sleep"] = {"blocks_event_loop": True}
        recommendations.append("Replace time.sleep() with asyncio.sleep()")


def _check_requests(
    call: ast.Call,
    blocking_patterns: dict[str, Any],
    recommendations: list[str],
) -> None:
    """Check for requests library calls."""
    if is_call_to(call, "requests.get") or is_call_to(call, "requests.post"):
        blocking_patterns["requests"] = {"blocks_event_loop": True}
        recommendations.append("Replace requests with aiohttp")


def _check_file_io(
    call: ast.Call,
    blocking_patterns: dict[str, Any],
    recommendations: list[str],
) -> None:
    """Check for file I/O blocking calls."""
    if isinstance(call.func, ast.Name) and call.func.id == "open":
        blocking_patterns["file_io"] = {"blocks_event_loop": True}
        recommendations.append("Consider using aiofiles for async file I/O")


def _check_sync_function_call(
    call: ast.Call,
    sync_func_names: set[str],
    sync_func_blocking: dict[str, list[str]],
    blocking_patterns: dict[str, Any],
    recommendations: list[str],
) -> None:
    """Check for calls to sync functions from async context."""
    call_name = None
    if isinstance(call.func, ast.Name):
        call_name = call.func.id
    elif isinstance(call.func, ast.Attribute):
        call_name = call.func.attr

    if call_name and call_name in sync_func_names:
        blocking_patterns["sync_function_call"] = {
            "function_name": call_name,
            "blocks_event_loop": True,
        }
        recommendations.append(f"Consider making '{call_name}' async")
        for blocking in sync_func_blocking.get(call_name, []):
            if blocking == "time_sleep":
                blocking_patterns["time_sleep"] = {"blocks_event_loop": True}
                recommendations.append("Replace time.sleep() with asyncio.sleep()")


async def detect_blocking_calls(
    code: str, _tree: ast.Module | None = None
) -> dict[str, Any]:
    """Detect blocking calls in async code.

    Args:
        code: Python code to analyze
        _tree: Pre-parsed AST (internal optimisation)

    Returns:
        Dictionary containing blocking call analysis

    """
    if not code:
        return {"blocking_patterns": {}}

    tree = _tree
    if tree is None:
        tree, err = parse_code(code)
        if tree is None:
            return {"blocking_patterns": {}, **(err or {})}

    blocking_patterns: dict[str, Any] = {}
    recommendations: list[str] = []

    sync_func_names: set[str] = set()
    sync_func_blocking: dict[str, list[str]] = {}
    _collect_sync_function_info(tree, sync_func_names, sync_func_blocking)

    for node in ast.walk(tree):
        if isinstance(node, ast.AsyncFunctionDef):
            for child in ast.walk(node):
                if isinstance(child, ast.Call):
                    _check_time_sleep(child, blocking_patterns, recommendations)
                    _check_requests(child, blocking_patterns, recommendations)
                    _check_file_io(child, blocking_patterns, recommendations)
                    _check_sync_function_call(
                        child,
                        sync_func_names,
                        sync_func_blocking,
                        blocking_patterns,
                        recommendations,
                    )

    blocking_patterns["recommendations"] = list(set(recommendations))
    return {"blocking_patterns": blocking_patterns}


async def detect_missing_await(
    code: str, _tree: ast.Module | None = None
) -> dict[str, Any]:
    """Detect missing await keywords in async code.

    Args:
        code: Python code to analyze
        _tree: Pre-parsed AST (internal optimisation)

    Returns:
        Dictionary containing missing await analysis

    """
    if not code:
        return {"missing_awaits": {}}

    tree = _tree
    if tree is None:
        tree, err = parse_code(code)
        if tree is None:
            return {"missing_awaits": {}, **(err or {})}

    missing_awaits: dict[str, Any] = {}
    coroutine_names = {
        node.name for node in ast.walk(tree) if isinstance(node, ast.AsyncFunctionDef)
    }

    for node in ast.walk(tree):
        if not isinstance(node, ast.AsyncFunctionDef):
            continue
        # A name awaited or handed to a call (gather, create_task, ...) later
        # is not a dropped coroutine. Returning it unawaited still is.
        consumed = {
            name.id
            for use in ast.walk(node)
            if isinstance(use, (ast.Await, ast.Call))
            for name in ast.walk(use)
            if isinstance(name, ast.Name) and isinstance(name.ctx, ast.Load)
        }
        lines = [
            call.lineno
            for call in _unawaited_calls(node.body, consumed)
            if _callee_name(call) in coroutine_names
        ]
        if lines:
            missing_awaits[node.name] = {
                "line_number": lines[0],
                "line_numbers": lines,
                "suggestion": "Add await before the coroutine call",
            }

    return {"missing_awaits": missing_awaits}


def _callee_name(call: ast.Call) -> str | None:
    """Name a call targets: ``f()`` and ``self.f()`` / ``cls.f()`` give ``f``."""
    func = call.func
    if isinstance(func, ast.Name):
        return func.id
    if (
        isinstance(func, ast.Attribute)
        and isinstance(func.value, ast.Name)
        and func.value.id in ("self", "cls")
    ):
        return func.attr
    return None


def _unawaited_calls(body: list[ast.stmt], consumed: set[str]) -> list[ast.Call]:
    """Collect calls used as a statement or assigned to a name never read.

    Nested function and class bodies are skipped: they get their own pass.
    """
    calls: list[ast.Call] = []
    for stmt in body:
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        if isinstance(stmt, (ast.Expr, ast.Assign, ast.AnnAssign)) and isinstance(
            stmt.value, ast.Call
        ):
            targets = (
                [stmt.target]
                if isinstance(stmt, ast.AnnAssign)
                else getattr(stmt, "targets", [])
            )
            names = {t.id for t in targets if isinstance(t, ast.Name)}
            if not names & consumed:
                calls.append(stmt.value)
        for field in ("body", "orelse", "finalbody"):
            nested = getattr(stmt, field, None)
            if isinstance(nested, list):
                calls.extend(_unawaited_calls(nested, consumed))
        for handler in getattr(stmt, "handlers", []):
            calls.extend(_unawaited_calls(handler.body, consumed))
    return calls
