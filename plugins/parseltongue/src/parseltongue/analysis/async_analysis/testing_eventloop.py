"""Async testing patterns and event loop usage analysis."""

from __future__ import annotations

import ast
import asyncio
from typing import Any

from ._base import is_call_to, parse_code

__all__ = [
    "analyze_event_loop_usage",
    "analyze_testing_patterns",
    "validate_best_practices",
]


async def analyze_testing_patterns(
    code: str, _tree: ast.Module | None = None
) -> dict[str, Any]:
    """Analyze async testing patterns.

    Args:
        code: Python code to analyze
        _tree: Pre-parsed AST (internal optimisation)

    Returns:
        Dictionary containing testing pattern analysis

    """
    if not code:
        return {"testing_analysis": {}}

    tree = _tree
    if tree is None:
        tree, err = parse_code(code)
        if tree is None:
            return {"testing_analysis": {}, **(err or {})}

    uses_pytest_asyncio = False
    async_test_count = 0
    uses_asyncmock = False
    timeout_testing = False
    concurrency_testing = False

    for node in ast.walk(tree):
        if isinstance(node, ast.AsyncFunctionDef):
            if node.name.startswith("test_"):
                async_test_count += 1

            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Attribute) and decorator.attr == "asyncio":
                    uses_pytest_asyncio = True

        if isinstance(node, ast.Call) and is_call_to(node, "AsyncMock"):
            uses_asyncmock = True

    if "TimeoutError" in code or "wait_for" in code:
        timeout_testing = True

    if "asyncio.gather" in code or "create_task" in code:
        concurrency_testing = True

    return {
        "testing_analysis": {
            "uses_pytest_asyncio": uses_pytest_asyncio,
            "async_test_count": async_test_count,
            "mocking_patterns": {
                "uses_asyncmock": uses_asyncmock,
            },
            "timeout_testing": timeout_testing,
            "concurrency_testing": concurrency_testing,
        }
    }


async def analyze_event_loop_usage(code: str) -> dict[str, Any]:
    """Analyze event loop usage patterns in async code.

    Args:
        code: Python code to analyze

    Returns:
        Dictionary containing event loop analysis

    """
    if not code:
        return {"event_loop_analysis": {}}

    loop_management: dict[str, int] = {
        "get_event_loop_usage": 0,
        "new_event_loop_usage": 0,
        "get_running_loop_usage": 0,
    }
    callback_usage: list[str] = []
    proper_loop_close = False

    if "get_event_loop" in code:
        loop_management["get_event_loop_usage"] = code.count("get_event_loop")
    if "new_event_loop" in code:
        loop_management["new_event_loop_usage"] = code.count("new_event_loop")
    if "get_running_loop" in code:
        loop_management["get_running_loop_usage"] = code.count("get_running_loop")

    for pattern in ["call_soon", "call_later", "call_at"]:
        if pattern in code:
            callback_usage.append(pattern)

    if "loop.close()" in code or ".close()" in code:
        proper_loop_close = True

    return {
        "event_loop_analysis": {
            "loop_management": loop_management,
            "callback_usage": callback_usage,
            "cleanup_patterns": {
                "proper_loop_close": proper_loop_close,
            },
        }
    }


async def validate_best_practices(
    code: str,
    analyze_error_handling_fn: Any,
    analyze_resource_management_fn: Any,
) -> dict[str, Any]:
    """Validate async code against best practices.

    Args:
        code: Python code to analyze
        analyze_error_handling_fn: Coroutine function for error handling analysis
        analyze_resource_management_fn: Coroutine function for resource management

    Returns:
        Dictionary containing validation results

    """
    if not code:
        return {"validation": {"good_practices": {}, "compliance_score": 0.0}}

    tree, err = parse_code(code)
    if tree is None:
        return {
            "validation": {
                "good_practices": {},
                "compliance_score": 0.0,
                **(err or {}),
            }
        }

    good_practices: dict[str, bool] = {}
    recommendations: list[str] = []
    score = 0.0
    total_checks = 4

    if "__aenter__" in code or "async with" in code:
        good_practices["context_manager_usage"] = True
        score += 1
    else:
        recommendations.append("Use async context managers for resources")

    error_result, resource_result = await asyncio.gather(
        analyze_error_handling_fn(code, _tree=tree),
        analyze_resource_management_fn(code, _tree=tree),
    )

    if error_result["error_handling"].get("try_catch_blocks"):
        good_practices["error_handling"] = True
        score += 1
    else:
        recommendations.append("Add try/except blocks for error handling")

    services = resource_result["resource_management"].get("services", {})
    if (
        any(s.get("closes_session", False) for s in services.values())
        or "__aexit__" in code
    ):
        good_practices["resource_cleanup"] = True
        score += 1
    else:
        recommendations.append("Ensure resources are properly cleaned up")

    if "asyncio.gather" in code or "create_task" in code:
        good_practices["concurrent_processing"] = True
        score += 1
    else:
        recommendations.append("Consider concurrent processing with asyncio.gather")

    compliance_score = score / total_checks if total_checks > 0 else 0.0

    return {
        "validation": {
            "good_practices": good_practices,
            "compliance_score": compliance_score,
            "recommendations": recommendations,
        }
    }
