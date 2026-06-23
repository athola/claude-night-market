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

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import ast

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


async def suggest_improvements(code: str) -> dict[str, Any]:
    """Suggest improvements for async code with default dependency injection."""
    return await _suggest_improvements_impl(
        code,
        detect_blocking_calls_fn=detect_blocking_calls,
        analyze_performance_fn=analyze_performance,
        detect_race_conditions_fn=detect_race_conditions,
        detect_missing_await_fn=detect_missing_await,
    )


async def validate_best_practices(code: str) -> dict[str, Any]:
    """Validate async code against best practices with default dependency injection."""
    return await _validate_best_practices_impl(
        code,
        analyze_error_handling_fn=analyze_error_handling,
        analyze_resource_management_fn=analyze_resource_management,
    )


__all__ = [
    "analyze_async_functions",
    "analyze_complex_scenarios",
    "analyze_concurrency_patterns",
    "analyze_context_managers",
    "analyze_error_handling",
    "analyze_event_loop_usage",
    "analyze_performance",
    "analyze_resource_management",
    "analyze_testing_patterns",
    "analyze_timeouts",
    "detect_blocking_calls",
    "detect_missing_await",
    "detect_race_conditions",
    "is_call_to",
    "parse_code",
    "suggest_improvements",
    "validate_best_practices",
]
