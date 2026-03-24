"""Async code analysis skill for parseltongue.

Provides detailed analysis of async Python code including:
- Async function detection and analysis
- Context manager pattern recognition
- Concurrency pattern detection
- Blocking call detection
- Missing await detection
- Error handling analysis
- Timeout pattern analysis
- Resource management analysis
- Performance analysis
- Race condition detection
- Event loop usage analysis
- Best practices validation
- Testing pattern analysis
- Complex scenario analysis
- Improvement suggestions
"""

from __future__ import annotations

import ast
from typing import Any

from ._base import is_call_to, parse_code
from .blocking_detection import detect_blocking_calls, detect_missing_await
from .complex_scenarios import analyze_complex_scenarios
from .complex_scenarios import suggest_improvements as _suggest_improvements_impl
from .error_timeout import analyze_error_handling, analyze_timeouts
from .function_analysis import (
    analyze_async_functions,
    analyze_concurrency_patterns,
    analyze_context_managers,
)
from .race_conditions import detect_race_conditions
from .resource_performance import analyze_performance, analyze_resource_management
from .testing_eventloop import (
    analyze_event_loop_usage,
    analyze_testing_patterns,
)
from .testing_eventloop import (
    validate_best_practices as _validate_best_practices_impl,
)


class AsyncAnalysisSkill:
    """Skill for analyzing async Python code patterns."""

    def __init__(self) -> None:
        """Initialize the async analysis skill."""
        pass

    def _parse_code(self, code: str) -> tuple[ast.Module | None, dict | None]:
        """Parse code into an AST, returning an error dict on failure."""
        return parse_code(code)

    def _is_call_to(self, node: ast.Call, target: str) -> bool:
        """Check if a call node is calling a specific function."""
        return is_call_to(node, target)

    async def analyze_async_functions(
        self, code: str, _tree: ast.Module | None = None
    ) -> dict[str, Any]:
        """Analyze async functions in the provided code."""
        return await analyze_async_functions(code, _tree=_tree)

    async def analyze_context_managers(
        self, code: str, _tree: ast.Module | None = None
    ) -> dict[str, Any]:
        """Analyze async context managers in the code."""
        return await analyze_context_managers(code, _tree=_tree)

    async def analyze_concurrency_patterns(
        self, code: str, _tree: ast.Module | None = None
    ) -> dict[str, Any]:
        """Detect concurrency patterns in async code."""
        return await analyze_concurrency_patterns(code, _tree=_tree)

    async def detect_blocking_calls(
        self, code: str, _tree: ast.Module | None = None
    ) -> dict[str, Any]:
        """Detect blocking calls in async code."""
        return await detect_blocking_calls(code, _tree=_tree)

    async def detect_missing_await(
        self, code: str, _tree: ast.Module | None = None
    ) -> dict[str, Any]:
        """Detect missing await keywords in async code."""
        return await detect_missing_await(code, _tree=_tree)

    async def analyze_error_handling(
        self, code: str, _tree: ast.Module | None = None
    ) -> dict[str, Any]:
        """Analyze async error handling patterns."""
        return await analyze_error_handling(code, _tree=_tree)

    async def analyze_timeouts(
        self, code: str, _tree: ast.Module | None = None
    ) -> dict[str, Any]:
        """Analyze timeout patterns in async code."""
        return await analyze_timeouts(code, _tree=_tree)

    async def analyze_resource_management(
        self, code: str, _tree: ast.Module | None = None
    ) -> dict[str, Any]:
        """Analyze async resource management patterns."""
        return await analyze_resource_management(code, _tree=_tree)

    async def analyze_performance(
        self, code: str, _tree: ast.Module | None = None
    ) -> dict[str, Any]:
        """Analyze async performance patterns."""
        return await analyze_performance(code, _tree=_tree)

    async def detect_race_conditions(
        self, code: str, _tree: ast.Module | None = None
    ) -> dict[str, Any]:
        """Detect potential race conditions in async code."""
        return await detect_race_conditions(code, _tree=_tree)

    async def analyze_testing_patterns(
        self, code: str, _tree: ast.Module | None = None
    ) -> dict[str, Any]:
        """Analyze async testing patterns."""
        return await analyze_testing_patterns(code, _tree=_tree)

    async def analyze_event_loop_usage(self, code: str) -> dict[str, Any]:
        """Analyze event loop usage patterns in async code."""
        return await analyze_event_loop_usage(code)

    async def validate_best_practices(self, code: str) -> dict[str, Any]:
        """Validate async code against best practices."""
        return await _validate_best_practices_impl(
            code,
            analyze_error_handling_fn=analyze_error_handling,
            analyze_resource_management_fn=analyze_resource_management,
        )

    async def analyze_complex_scenarios(self, code: str) -> dict[str, Any]:
        """Analyze complex async code scenarios."""
        return await analyze_complex_scenarios(code)

    async def suggest_improvements(self, code: str) -> dict[str, Any]:
        """Suggest improvements for async code."""
        return await _suggest_improvements_impl(
            code,
            detect_blocking_calls_fn=detect_blocking_calls,
            analyze_performance_fn=analyze_performance,
            detect_race_conditions_fn=detect_race_conditions,
            detect_missing_await_fn=detect_missing_await,
        )


__all__ = ["AsyncAnalysisSkill"]
