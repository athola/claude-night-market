"""TDD tests for SML-001: remove AsyncAnalysisSkill delegation class.

AsyncAnalysisSkill was a stateless wrapper (bare __init__ pass) whose 13 async
methods did nothing but forward to the module-level functions already imported
in the same __init__.py. The class added an indirection layer with no value.

After the fix:
- Module-level functions are in __all__
- AsyncAnalysisSkill is gone from __all__
- cli.py calls analyze_async_functions() directly
"""

from __future__ import annotations

import pytest

from parseltongue.analysis.async_analysis import (
    __all__ as exports,
)
from parseltongue.analysis.async_analysis import (
    analyze_async_functions,
    analyze_concurrency_patterns,
    analyze_context_managers,
    analyze_error_handling,
    analyze_event_loop_usage,
    analyze_performance,
    analyze_resource_management,
    analyze_testing_patterns,
    analyze_timeouts,
    detect_blocking_calls,
    detect_missing_await,
    detect_race_conditions,
    suggest_improvements,
)


class TestSml001DelegationRemoval:
    """Verify AsyncAnalysisSkill class removed, module-level functions exported."""

    def test_analyze_async_functions_in_module_all(self) -> None:
        """analyze_async_functions must be in __all__ after SML-001."""
        assert "analyze_async_functions" in exports

    def test_async_analysis_skill_not_in_module_all(self) -> None:
        """AsyncAnalysisSkill must not be in __all__ after SML-001."""
        assert "AsyncAnalysisSkill" not in exports

    def test_module_level_functions_directly_callable(self) -> None:
        """All formerly-delegated functions are importable and callable at module level."""
        for fn in [
            analyze_async_functions,
            analyze_context_managers,
            analyze_concurrency_patterns,
            detect_blocking_calls,
            detect_missing_await,
            analyze_error_handling,
            analyze_timeouts,
            analyze_resource_management,
            analyze_performance,
            detect_race_conditions,
            analyze_testing_patterns,
            analyze_event_loop_usage,
            suggest_improvements,
        ]:
            assert callable(fn)

    @pytest.mark.asyncio
    async def test_analyze_async_functions_callable_directly(self) -> None:
        """analyze_async_functions works when called directly, not through class."""
        result = await analyze_async_functions("async def f(): pass")
        assert "async_functions" in result
