"""Complex scenario analysis and improvement suggestions for async code."""

from __future__ import annotations

import ast
from typing import Any

from ._base import parse_code

__all__ = ["analyze_complex_scenarios", "suggest_improvements"]


def _analyze_cache_patterns(code: str, complex_analysis: dict[str, Any]) -> None:
    """Analyze cache stampede prevention patterns."""
    if "cache" in code.lower():
        prevents_stampede = "create_task" in code or "future" in code.lower()
        uses_futures = "create_task" in code or "future" in code.lower()
        complex_analysis["cache_anti_pattern"] = {
            "prevents_cache_stampede": prevents_stampede,
            "uses_futures": uses_futures,
        }


def _analyze_rate_limiting(code: str, complex_analysis: dict[str, Any]) -> None:
    """Analyze rate limiting patterns."""
    if "rate_limit" in code.lower() or "rate_limiter" in code.lower():
        complex_analysis["rate_limiting"] = True


def _analyze_custom_context_managers(
    code: str, complex_analysis: dict[str, Any]
) -> None:
    """Analyze custom async context manager patterns."""
    if "@asynccontextmanager" in code or "__aenter__" in code:
        complex_analysis["custom_context_manager"] = True


def _analyze_resource_cleanup(
    code: str,
    complex_analysis: dict[str, Any],
    _tree: ast.Module | None = None,
) -> None:
    """Analyze resource cleanup in try/except blocks."""
    tree = _tree
    if tree is None:
        tree, _ = parse_code(code)
        if tree is None:
            complex_analysis["resource_cleanup"] = {
                "error_cleanup": False,
                "finally_blocks": 0,
            }
            return

    finally_blocks = 0
    error_cleanup = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Try):
            if node.finalbody:
                finally_blocks += 1
            for handler in node.handlers:
                for stmt in ast.walk(handler):
                    if (
                        isinstance(stmt, ast.Call)
                        and isinstance(stmt.func, ast.Attribute)
                        and stmt.func.attr in ("pop", "remove", "close")
                    ):
                        error_cleanup = True

    complex_analysis["resource_cleanup"] = {
        "error_cleanup": error_cleanup,
        "finally_blocks": finally_blocks,
    }


async def analyze_complex_scenarios(code: str) -> dict[str, Any]:
    """Analyze complex async code scenarios.

    Args:
        code: Python code to analyze

    Returns:
        Dictionary containing complex analysis results

    """
    if not code:
        return {"complex_analysis": {}}

    complex_analysis: dict[str, Any] = {}
    _analyze_cache_patterns(code, complex_analysis)
    _analyze_rate_limiting(code, complex_analysis)
    _analyze_custom_context_managers(code, complex_analysis)
    _analyze_resource_cleanup(code, complex_analysis)

    return {"complex_analysis": complex_analysis}


async def suggest_improvements(
    code: str,
    detect_blocking_calls_fn: Any,
    analyze_performance_fn: Any,
    detect_race_conditions_fn: Any,
    detect_missing_await_fn: Any,
) -> dict[str, Any]:
    """Suggest improvements for async code.

    Args:
        code: Python code to analyze
        detect_blocking_calls_fn: Coroutine function for blocking call detection
        analyze_performance_fn: Coroutine function for performance analysis
        detect_race_conditions_fn: Coroutine function for race condition detection
        detect_missing_await_fn: Coroutine function for missing await detection

    Returns:
        Dictionary containing improvement suggestions

    """
    if not code:
        return {"improvements": []}

    tree, err = parse_code(code)
    if tree is None:
        return {"improvements": [], **(err or {})}

    improvements: list[dict[str, str]] = []

    blocking = await detect_blocking_calls_fn(code, _tree=tree)
    performance = await analyze_performance_fn(code, _tree=tree)
    race_conditions = await detect_race_conditions_fn(code, _tree=tree)
    missing_await = await detect_missing_await_fn(code, _tree=tree)

    if blocking.get("blocking_patterns"):
        bp = blocking["blocking_patterns"]
        if "time_sleep" in bp:
            improvements.append(
                {
                    "category": "blocking_call",
                    "issue": "Blocking time.sleep() in async context",
                    "recommendation": "Use asyncio.sleep() instead",
                    "code_before": "time.sleep(1)",
                    "code_after": "await asyncio.sleep(1)",
                    "explanation": "Use asyncio.sleep() instead of "
                    "time.sleep() to avoid blocking the event loop",
                }
            )
        if "sync_function_call" in bp:
            func_name = bp["sync_function_call"].get("function_name", "sync_func")
            improvements.append(
                {
                    "category": "blocking_call",
                    "issue": f"Sync function '{func_name}' called in async",
                    "recommendation": f"Make '{func_name}' async",
                    "code_before": f"result = {func_name}()",
                    "code_after": f"result = await {func_name}()",
                    "explanation": f"Convert '{func_name}' to an async "
                    f"function to avoid blocking",
                }
            )

    if missing_await.get("missing_awaits"):
        for func_name in missing_await["missing_awaits"]:
            improvements.append(
                {
                    "category": "missing_await",
                    "issue": f"Missing await in '{func_name}'",
                    "recommendation": "Add await keyword",
                    "code_before": "data = api_call()",
                    "code_after": "data = await api_call()",
                    "explanation": "Add await keyword before async "
                    "function calls to properly wait for the result",
                }
            )

    if performance.get("performance_analysis", {}).get("issues"):
        improvements.append(
            {
                "category": "performance",
                "issue": "Sequential async processing in loop",
                "recommendation": "Use asyncio.gather()",
                "code_before": "for item in items:\n"
                "    result = await process_item(item)",
                "code_after": "results = await asyncio.gather("
                "*[process_item(item) for item in items])",
                "explanation": "Use asyncio.gather() to process items "
                "concurrently instead of sequentially",
            }
        )

    if race_conditions.get("race_conditions", {}).get("unsynchronized_shared_state"):
        improvements.append(
            {
                "category": "race_condition",
                "issue": "Shared state without synchronization",
                "recommendation": "Use asyncio.Lock",
                "code_before": "self.counter += 1",
                "code_after": "async with self.lock:\n    self.counter += 1",
                "explanation": "Protect shared state with asyncio.Lock "
                "to prevent race conditions",
            }
        )

    return {"improvements": improvements}
