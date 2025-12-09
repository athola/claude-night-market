"""Unit tests for async code analysis and optimization.

Tests async pattern recognition, performance analysis,
and optimization recommendations.
"""

from __future__ import annotations

import pytest

# Import the skills we're testing
from parseltongue.skills.async_analyzer import AsyncAnalysisSkill


class TestAsyncAnalysisSkill:
    """Test suite for AsyncAnalysisSkill."""

    def setup_method(self) -> None:
        """Set up test fixtures before each test."""
        self.skill = AsyncAnalysisSkill()

    @pytest.mark.asyncio
    async def test_detects_async_functions(self, sample_async_code) -> None:
        """Given async code, when skill analyzes, then identifies all async functions."""
        # Arrange
        code = sample_async_code

        # Act
        result = await self.skill.analyze_async_functions(code)

        # Assert
        async_functions = result["async_functions"]

        # Should detect multiple async functions
        assert len(async_functions) >= 3
        assert "fetch_user" in [func["name"] for func in async_functions]
        assert "fetch_multiple_users" in [func["name"] for func in async_functions]
        assert "process_with_timeout" in [func["name"] for func in async_functions]

        # Should provide function details
        for func in async_functions:
            assert "name" in func
            assert "line_number" in func
            assert "parameters" in func
            assert "await_calls" in func

    @pytest.mark.asyncio
    async def test_identifies_async_context_managers(self, sample_async_code) -> None:
        """Given async code, when skill analyzes, then identifies async context managers."""
        # Arrange
        code = sample_async_code

        # Act
        result = await self.skill.analyze_context_managers(code)

        # Assert
        context_managers = result["context_managers"]

        # Should detect async context manager class
        assert "AsyncDataService" in context_managers
        assert context_managers["AsyncDataService"]["has_async_context_manager"] is True

        # Should detect __aenter__ and __aexit__ methods
        async_service = context_managers["AsyncDataService"]
        assert "__aenter__" in async_service["methods"]
        assert "__aexit__" in async_service["methods"]

    @pytest.mark.asyncio
    async def test_analyzes_concurrency_patterns(self, sample_async_code) -> None:
        """Given async code, when skill analyzes, then identifies concurrency patterns."""
        # Arrange
        code = sample_async_code

        # Act
        result = await self.skill.analyze_concurrency_patterns(code)

        # Assert
        concurrency = result["concurrency_patterns"]

        # Should detect asyncio.gather usage
        assert "gather_usage" in concurrency
        assert "fetch_multiple_users" in concurrency["gather_usage"]["functions"]

        # Should analyze concurrency potential
        assert (
            concurrency["fetch_multiple_users"]["concurrent_operations"] == "fetch_user"
        )

        # Should detect return_exceptions usage
        assert concurrency["gather_usage"]["error_handling"] == "return_exceptions"

    @pytest.mark.asyncio
    async def test_detects_blocking_calls(self, async_issues) -> None:
        """Given async code with blocking calls, when skill analyzes, then identifies blocking patterns."""
        # Arrange
        blocking_code = async_issues["blocking_io"]

        # Act
        result = await self.skill.detect_blocking_calls(blocking_code)

        # Assert
        blocking_patterns = result["blocking_patterns"]

        # Should detect time.sleep blocking call
        assert "time_sleep" in blocking_patterns
        assert blocking_patterns["time_sleep"]["blocks_event_loop"] is True

        # Should detect sync_operation call in async context
        assert "sync_function_call" in blocking_patterns
        assert (
            blocking_patterns["sync_function_call"]["function_name"] == "sync_operation"
        )

        # Should provide recommendations
        assert len(blocking_patterns["recommendations"]) >= 1

    @pytest.mark.asyncio
    async def test_identifies_missing_await(self, async_issues) -> None:
        """Given async code with missing await, when skill analyzes, then detect missing awaits."""
        # Arrange
        missing_await_code = async_issues["missing_await"]

        # Act
        result = await self.skill.detect_missing_await(missing_await_code)

        # Assert
        missing_awaits = result["missing_awaits"]

        # Should detect missing await on api_call
        assert "fetch_data" in missing_awaits
        assert missing_awaits["fetch_data"]["line_number"] is not None

        # Should suggest adding await
        assert "suggestion" in missing_awaits["fetch_data"]
        assert "await" in missing_awaits["fetch_data"]["suggestion"]

    @pytest.mark.asyncio
    async def test_analyzes_error_handling(self, sample_async_code) -> None:
        """Given async code, when skill analyzes, then evaluates error handling patterns."""
        # Arrange
        code = sample_async_code

        # Act
        result = await self.skill.analyze_error_handling(code)

        # Assert
        error_handling = result["error_handling"]

        # Should detect try-catch blocks in async functions
        assert "try_catch_blocks" in error_handling
        assert len(error_handling["try_catch_blocks"]) >= 1

        # Should analyze fetch_user error handling
        fetch_user_errors = error_handling["functions"]["fetch_user"]
        assert fetch_user_errors["has_error_handling"] is True
        assert fetch_user_errors["exception_types"] == ["aiohttp.ClientError"]

        # Should detect graceful degradation
        assert fetch_user_errors["graceful_degradation"] is True

    @pytest.mark.asyncio
    async def test_analyzes_timeout_handling(self, sample_async_code) -> None:
        """Given async code with timeouts, when skill analyzes, then evaluates timeout patterns."""
        # Arrange
        code = sample_async_code

        # Act
        result = await self.skill.analyze_timeouts(code)

        # Assert
        timeouts = result["timeout_analysis"]

        # Should detect asyncio.wait_for usage
        assert "wait_for_usage" in timeouts
        assert "process_with_timeout" in timeouts["wait_for_usage"]["functions"]

        # Should analyze timeout handling
        process_timeout = timeouts["functions"]["process_with_timeout"]
        assert process_timeout["has_timeout"] is True
        assert process_timeout["timeout_value"] == 5.0

        # Should detect TimeoutError handling
        assert process_timeout["handles_timeout_error"] is True

    @pytest.mark.asyncio
    async def test_identifies_resource_management(self, sample_async_code) -> None:
        """Given async code, when skill analyzes, then identifies resource management patterns."""
        # Arrange
        code = sample_async_code

        # Act
        result = await self.skill.analyze_resource_management(code)

        # Assert
        resource_mgmt = result["resource_management"]

        # Should detect session management
        assert "session_management" in resource_mgmt
        async_service = resource_mgmt["services"]["AsyncDataService"]

        # Should track session lifecycle
        assert async_service["creates_session"] is True
        assert async_service["closes_session"] is True
        assert async_service["uses_context_manager"] is True

        # Should detect proper resource cleanup
        assert async_service["cleanup_in_finally"] is True

    @pytest.mark.asyncio
    async def test_analyzes_performance_issues(self, sample_async_code) -> None:
        """Given async code, when skill analyzes, then identifies performance opportunities."""
        # Arrange
        code_with_issues = '''
import asyncio
import aiohttp

async def process_items_sequential(items):
    """Sequential processing - performance issue."""
    results = []
    for item in items:
        result = await fetch_item(item)  # Sequential
        results.append(result)
    return results

async def process_items_concurrent(items):
    """Concurrent processing - better performance."""
    tasks = [fetch_item(item) for item in items]
    results = await asyncio.gather(*tasks)
    return results

async def fetch_item(item):
    """Simulate network call."""
    await asyncio.sleep(0.1)
    return {"item": item, "processed": True}
        '''

        # Act
        result = await self.skill.analyze_performance(code_with_issues)

        # Assert
        performance = result["performance_analysis"]

        # Should identify sequential processing issue
        assert "sequential_processing" in performance["issues"]
        sequential_func = performance["issues"]["sequential_processing"][
            "process_items_sequential"
        ]
        assert sequential_func["problem"] == "sequential_async_calls"

        # Should identify better alternative
        assert "concurrent_alternative" in performance
        assert "process_items_concurrent" in performance["concurrent_alternative"]

        # Should calculate performance improvement
        assert performance["improvement_potential"]["speedup"] > 1.0

    @pytest.mark.asyncio
    async def test_detects_race_conditions(self) -> None:
        """Given async code, when skill analyzes, then identifies potential race conditions."""
        # Arrange
        race_condition_code = '''
import asyncio

shared_state = {"counter": 0}

async def increment_counter():
    """Potential race condition - shared state without synchronization."""
    current = shared_state["counter"]
    await asyncio.sleep(0.001)  # Simulate async operation
    shared_state["counter"] = current + 1

async def safe_increment(counter):
    """Thread-safe increment using asyncio.Lock."""
    async with counter["lock"]:
        current = counter["value"]
        await asyncio.sleep(0.001)
        counter["value"] = current + 1

async def main():
    # Race condition scenario
    tasks = [increment_counter() for _ in range(100)]
    await asyncio.gather(*tasks)

    # Safe scenario
    safe_counter = {"value": 0, "lock": asyncio.Lock()}
    tasks = [safe_increment(safe_counter) for _ in range(100)]
    await asyncio.gather(*tasks)
        '''

        # Act
        result = await self.skill.detect_race_conditions(race_condition_code)

        # Assert
        race_conditions = result["race_conditions"]

        # Should detect shared state access without synchronization
        assert "unsynchronized_shared_state" in race_conditions
        assert (
            race_conditions["unsynchronized_shared_state"]["increment_counter"][
                "accesses"
            ]
            == 2
        )

        # Should identify safe patterns
        assert "safe_patterns" in race_conditions
        assert race_conditions["safe_patterns"]["safe_increment"]["uses_lock"] is True

        # Should provide recommendations
        assert len(race_conditions["recommendations"]) >= 1

    @pytest.mark.asyncio
    async def test_analyzes_event_loop_usage(self) -> None:
        """Given async code, when skill analyzes, then evaluates event loop patterns."""
        # Arrange
        event_loop_code = '''
import asyncio

async def custom_loop_example():
    """Custom event loop usage."""
    loop = asyncio.get_event_loop()
    loop.call_soon(some_callback)
    await asyncio.sleep(1)

def run_with_custom_loop():
    """Running with custom loop configuration."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()

async def background_task():
    """Background task pattern."""
    loop = asyncio.get_running_loop()
    loop.create_background_task(long_running_operation())

async def callback_example():
    """Callback registration pattern."""
    loop = asyncio.get_running_loop()
    loop.set_debug(True)
    # Schedule callbacks
        '''

        # Act
        result = await self.skill.analyze_event_loop_usage(event_loop_code)

        # Assert
        event_loop_analysis = result["event_loop_analysis"]

        # Should detect loop management patterns
        assert "loop_management" in event_loop_analysis
        assert event_loop_analysis["loop_management"]["get_event_loop_usage"] >= 1
        assert event_loop_analysis["loop_management"]["new_event_loop_usage"] >= 1

        # Should detect callback usage
        assert "callback_usage" in event_loop_analysis
        assert "call_soon" in str(event_loop_analysis)

        # Should check proper loop cleanup
        cleanup_analysis = event_loop_analysis["cleanup_patterns"]
        assert cleanup_analysis["proper_loop_close"] is True

    @pytest.mark.asyncio
    async def test_suggests_async_improvements(self, async_issues) -> None:
        """Given async code with issues, when skill analyzes, then suggests improvements."""
        # Arrange
        problematic_code = (
            async_issues["missing_await"] + "\n\n" + async_issues["blocking_io"]
        )

        # Act
        result = await self.skill.suggest_improvements(problematic_code)

        # Assert
        suggestions = result["improvements"]

        # Should provide multiple suggestions
        assert len(suggestions) >= 2

        # Should categorize suggestions
        categories = [s["category"] for s in suggestions]
        assert "missing_await" in categories
        assert "blocking_call" in categories

        # Should provide before/after examples
        for suggestion in suggestions:
            assert "issue" in suggestion
            assert "recommendation" in suggestion
            assert "code_before" in suggestion
            assert "code_after" in suggestion
            assert "explanation" in suggestion

    @pytest.mark.asyncio
    async def test_validates_async_best_practices(self, sample_async_code) -> None:
        """Given well-structured async code, when skill analyzes, then validates best practices."""
        # Arrange
        good_async_code = sample_async_code

        # Act
        result = await self.skill.validate_best_practices(good_async_code)

        # Assert
        validation = result["validation"]

        # Should identify good practices
        good_practices = validation["good_practices"]

        assert "context_manager_usage" in good_practices
        assert "error_handling" in good_practices
        assert "resource_cleanup" in good_practices
        assert "concurrent_processing" in good_practices

        # Should calculate compliance score
        assert validation["compliance_score"] > 0.8

        # Should provide areas for improvement (if any)
        assert "recommendations" in validation

    @pytest.mark.asyncio
    async def test_analyzes_async_testing_patterns(self) -> None:
        """Given async test code, when skill analyzes, then evaluates testing patterns."""
        # Arrange
        async_test_code = '''
import pytest
import asyncio
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_async_function():
    """Test async function directly."""
    result = await my_async_function()
    assert result.success is True

@pytest.mark.asyncio
async def test_with_mock():
    """Test with async mock."""
    mock_api = AsyncMock()
    mock_api.get.return_value = {"data": "test"}

    result = await fetch_data(mock_api)
    assert result["data"] == "test"

@pytest.mark.asyncio
async def test_timeout_handling():
    """Test timeout handling."""
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(
            slow_operation(),
            timeout=0.1
        )

@pytest.mark.asyncio
async def test_concurrent_operations():
    """Test concurrent async operations."""
    tasks = [
        fetch_user(1),
        fetch_user(2),
        fetch_user(3)
    ]
    users = await asyncio.gather(*tasks)
    assert len(users) == 3
        '''

        # Act
        result = await self.skill.analyze_testing_patterns(async_test_code)

        # Assert
        testing_analysis = result["testing_analysis"]

        # Should detect pytest.mark.asyncio usage
        assert testing_analysis["uses_pytest_asyncio"] is True
        assert testing_analysis["async_test_count"] >= 4

        # Should detect AsyncMock usage
        assert "mocking_patterns" in testing_analysis
        assert testing_analysis["mocking_patterns"]["uses_asyncmock"] is True

        # Should detect timeout testing
        assert testing_analysis["timeout_testing"] is True

        # Should detect concurrency testing
        assert testing_analysis["concurrency_testing"] is True

    @pytest.mark.asyncio
    async def test_handles_complex_async_scenarios(self) -> None:
        """Given complex async scenarios, when skill analyzes, then handles correctly."""
        # Arrange
        complex_async_code = '''
import asyncio
from contextlib import asynccontextmanager

@asynccontextmanager
async def database_connection():
    conn = await create_database_connection()
    try:
        yield conn
    finally:
        await conn.close()

class AsyncCache:
    def __init__(self):
        self.cache = {}
        self.lock = asyncio.Lock()

    async def get_or_fetch(self, key):
        async with self.lock:
            if key in self.cache:
                return self.cache[key]

            # Avoid cache stampede
            future = asyncio.create_task(self.fetch_and_cache(key))
            self.cache[key] = future
            return await future

    async def fetch_and_cache(self, key):
        try:
            data = await fetch_from_database(key)
            self.cache[key] = data
            return data
        except Exception:
            # Clean up on error
            self.cache.pop(key, None)
            raise

async def process_with_rate_limit(items, rate_limiter):
    """Process items with rate limiting."""
    async with rate_limiter:
        for item in items:
            async with rate_limiter.acquire():
                result = await process_item(item)
                yield result
        '''

        # Act
        result = await self.skill.analyze_complex_scenarios(complex_async_code)

        # Assert
        complex_analysis = result["complex_analysis"]

        # Should detect advanced patterns
        assert "cache_anti_pattern" in complex_analysis
        assert "rate_limiting" in complex_analysis
        assert "custom_context_manager" in complex_analysis

        # Should analyze cache stampede prevention
        cache_analysis = complex_analysis["cache_anti_pattern"]
        assert cache_analysis["prevents_cache_stampede"] is True
        assert cache_analysis["uses_futures"] is True

        # Should detect proper cleanup
        cleanup_analysis = complex_analysis["resource_cleanup"]
        assert cleanup_analysis["error_cleanup"] is True
        assert cleanup_analysis["finally_blocks"] >= 1
