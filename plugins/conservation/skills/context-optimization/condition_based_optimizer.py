"""Enhanced Context Optimizer with Condition-Based Waiting Integration.

This module provides intelligent context optimization that waits for actual conditions
rather than using arbitrary timeouts, eliminating flaky optimization behavior.
"""

import asyncio
import logging
import random
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

# Constants
COMPRESSION_RATIO_THRESHOLD = 0.3
TOKEN_REDUCTION_THRESHOLD = 100
PRIORITY_THRESHOLD = 0
SEMANTIC_COHERENCE_THRESHOLD = 0.7
COMPRESSION_RATIO_MIN = 0.1
HIGH_PRESSURE_THRESHOLD = 0.9
LOW_USAGE_SIMULATION = 0.3
HIGH_USAGE_SIMULATION = 0.95

# Import the base optimizer
try:
    from context_optimization_service import (
        ConservationContextOptimizer,
        ConservationServiceRegistry,
        ContentBlock,
    )
except ImportError:
    # Fallback for standalone use
    class ConservationContextOptimizer:
        """Fallback optimizer when imports are not available."""

        pass

    class ContentBlock:
        """Fallback content block when imports are not available."""

        pass

    class ConservationServiceRegistry:
        """Fallback service registry when imports are not available."""

        pass


@dataclass
class OptimizationRequest:
    """Represents a request for optimization with condition-based monitoring."""

    plugin_name: str
    content_blocks: list[ContentBlock]
    max_tokens: int
    strategy: str = "balanced"
    priority: float = 0.5
    timeout_ms: int = 30000
    completion_condition: Callable[[dict], bool] | None = None
    callback: Callable[[dict], None] | None = None


@dataclass
class OptimizationResult:
    """Result of an optimization with detailed metrics."""

    optimization_id: str
    plugin_name: str
    status: str  # "pending", "completed", "failed", "timeout"
    optimized_content: str = ""
    metrics: dict[str, Any] = field(default_factory=dict)
    error_message: str = ""
    start_time: float = field(default_factory=time.time)
    end_time: float | None = None


class ConditionBasedOptimizer:
    """Enhanced optimizer using condition-based waiting instead of arbitrary timeouts.

    Eliminates flaky optimization behavior by waiting for actual completion signals.
    """

    def __init__(self) -> None:
        """Initialize the condition-based optimizer with default services."""
        self.optimizer = ConservationContextOptimizer()
        self.active_optimizations: dict[str, OptimizationResult] = {}
        self.optimization_queue: list[OptimizationRequest] = []
        self.is_processing = False
        self.condition_checkers = {}
        self._register_condition_checkers()

        # Register as enhanced service
        registry = ConservationServiceRegistry()
        registry.register_service("condition_based_optimizer", self)
        registry.register_service(
            "optimize_with_conditions",
            self.optimize_with_conditions,
        )

        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def _register_condition_checkers(self) -> None:
        """Register built-in condition checkers."""
        self.condition_checkers.update(
            {
                "compression_ratio": lambda r: r.get("compression_ratio", 0)
                > COMPRESSION_RATIO_THRESHOLD,  # noqa: E501
                "token_reduction": lambda r: r.get("tokens_saved", 0)
                > TOKEN_REDUCTION_THRESHOLD,  # noqa: E501
                "priority_preserved": lambda r: r.get("high_priority_kept", 0)
                > PRIORITY_THRESHOLD,  # noqa: E501
                "structure_intact": lambda r: r.get("structure_preserved", False),
                "semantic_coherence": lambda r: r.get("coherence_score", 0)
                > SEMANTIC_COHERENCE_THRESHOLD,  # noqa: E501
            },
        )

    def wait_for_condition(
        self,
        condition: Callable[[], Any],
        description: str,
        timeout_ms: int = 5000,
        poll_interval_ms: int = 10,
    ) -> Any:
        """Wait for a condition to be met with proper error handling.

        This is the core condition-based waiting function that replaces
        arbitrary sleep() calls with intelligent polling.
        """
        start_time = time.time()
        timeout_seconds = timeout_ms / 1000
        poll_interval = poll_interval_ms / 1000

        self.logger.info(f"Waiting for condition: {description}")

        while True:
            try:
                result = condition()
                if result:
                    elapsed_ms = (time.time() - start_time) * 1000
                    self.logger.info(
                        f"Condition met: {description} (elapsed: {elapsed_ms:.0f}ms)",
                    )
                    return result
            except Exception as e:
                self.logger.warning(f"Condition check failed: {e}")

            if time.time() - start_time > timeout_seconds:
                msg = f"Timeout waiting for {description} after {timeout_ms}ms"
                raise TimeoutError(
                    msg,
                )

            time.sleep(poll_interval)

    def optimize_with_conditions(
        self,
        request: OptimizationRequest,
    ) -> OptimizationResult:
        """Perform optimization with condition-based completion monitoring.

        This method eliminates flaky optimization behavior by waiting for
        actual completion signals rather than using arbitrary timeouts.
        """
        optimization_id = f"{request.plugin_name}_{int(time.time() * 1000)}"

        result = OptimizationResult(
            optimization_id=optimization_id,
            plugin_name=request.plugin_name,
            status="pending",
        )

        self.active_optimizations[optimization_id] = result

        try:
            self.logger.info(
                f"Starting optimization {optimization_id} "
                f"for plugin {request.plugin_name}",
            )

            # Step 1: Perform optimization
            optimization_result = self.optimizer.optimize_content(
                content_blocks=request.content_blocks,
                max_tokens=request.max_tokens,
                strategy=request.strategy,
                preserve_structure=True,
            )

            # Step 2: Wait for optimization to complete successfully
            # Instead of: time.sleep(2)  # Arbitrary wait
            # We wait for actual completion conditions

            completion_condition = request.completion_condition
            if not completion_condition:
                # Default condition: good compression ratio
                completion_condition = self.condition_checkers["compression_ratio"]

            # Wait for condition to be met
            self.wait_for_condition(
                condition=lambda: completion_condition(optimization_result),
                description=f"optimization {optimization_id} completion",
                timeout_ms=request.timeout_ms,
            )

            # Step 3: Validate result meets requirements
            self.wait_for_condition(
                condition=lambda: self._validate_optimization_result(
                    optimization_result,
                    request,
                ),
                description=f"optimization {optimization_id} validation",
                timeout_ms=5000,
            )

            # Step 4: Finalize result
            result.status = "completed"
            result.optimized_content = optimization_result["optimized_content"]
            result.metrics = optimization_result
            result.end_time = time.time()

            # Step 5: Notify callback if provided
            if request.callback:
                request.callback(result)

            self.logger.info(
                f"Optimization {optimization_id} completed successfully "
                f"in {result.end_time - result.start_time:.2f}s",
            )

        except TimeoutError as e:
            result.status = "timeout"
            result.error_message = str(e)
            result.end_time = time.time()
            self.logger.exception(f"Optimization {optimization_id} timed out: {e}")

        except Exception as e:
            result.status = "failed"
            result.error_message = str(e)
            result.end_time = time.time()
            self.logger.exception(f"Optimization {optimization_id} failed: {e}")

        return result

    def _validate_optimization_result(
        self,
        result: dict[str, Any],
        request: OptimizationRequest,
    ) -> bool:
        """Validate that optimization meets minimum requirements."""
        # Check we actually reduced token usage
        if result.get("optimized_tokens", 0) >= request.max_tokens:
            return False

        # Check we preserved some content
        if result.get("blocks_kept", 0) == 0:
            return False

        # Check compression ratio is reasonable
        return not result.get("compression_ratio", 0) <= COMPRESSION_RATIO_MIN

    async def optimize_batch_async(
        self,
        requests: list[OptimizationRequest],
        max_concurrent: int = 3,
    ) -> list[OptimizationResult]:
        """Optimize multiple requests concurrently with condition-based waiting.

        This coordinates multiple optimizations without arbitrary delays,
        waiting for each to complete based on actual conditions.
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        results = []

        async def optimize_single(request: OptimizationRequest):
            async with semaphore:
                # Run synchronous optimization in thread pool
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(
                    None,
                    self.optimize_with_conditions,
                    request,
                )

        # Create tasks
        tasks = [optimize_single(req) for req in requests]

        # Wait for all to complete using condition-based coordination
        self.logger.info(f"Starting batch optimization of {len(requests)} requests")

        # Instead of: await asyncio.gather(*tasks) with arbitrary timeout
        # We monitor completion and wait for actual conditions

        completed_count = 0
        total_count = len(tasks)

        def completion_condition():
            nonlocal completed_count
            completed_tasks = sum(1 for task in tasks if task.done())
            completed_count = completed_tasks
            return completed_tasks >= total_count

        # Start tasks
        task_results = asyncio.gather(*tasks, return_exceptions=True)

        # Wait for completion condition
        await asyncio.get_event_loop().run_in_executor(
            None,
            self.wait_for_condition,
            completion_condition,
            f"batch completion ({total_count} optimizations)",
            60000,  # 60 second timeout for batch
        )

        # Collect results
        for i, task_result in enumerate(await task_results):
            if isinstance(task_result, Exception):
                # Create failed result
                failed_result = OptimizationResult(
                    optimization_id=f"batch_{i}_{int(time.time())}",
                    plugin_name=requests[i].plugin_name,
                    status="failed",
                    error_message=str(task_result),
                )
                results.append(failed_result)
            else:
                results.append(task_result)

        self.logger.info(
            f"Batch optimization completed: "
            f"{sum(1 for r in results if r.status == 'completed')}/{
                total_count
            } successful",
        )

        return results

    def wait_for_plugin_coordination(
        self,
        plugins: list[str],
        coordination_type: str = "optimization",
        timeout_ms: int = 20000,
    ) -> dict[str, bool]:
        """Wait for multiple plugins to be ready for coordinated optimization.

        Replaces arbitrary coordination delays with condition-based waiting.
        """
        self.logger.info(f"Coordinating {coordination_type} across {plugins}")

        def check_plugin_readiness(plugin: str) -> bool:
            """Check if a specific plugin is ready for coordination."""
            # In real implementation, this would check plugin state
            # For now, simulate varied readiness times
            time.sleep(0.1)  # Simulate check time
            return True  # Assume ready for demo

        def coordination_condition():
            ready_plugins = {
                plugin: check_plugin_readiness(plugin) for plugin in plugins
            }
            all_ready = all(ready_plugins.values())
            return ready_plugins if all_ready else None

        return self.wait_for_condition(
            coordination_condition,
            f"{coordination_type} coordination for {plugins}",
            timeout_ms,
        )

    def monitor_context_pressure(
        self,
        threshold: float = 0.8,
        check_interval_ms: int = 100,
        timeout_ms: int = 30000,
    ) -> dict[str, Any]:
        """Monitor context usage and wait for threshold breach.

        Proactively monitors instead of using fixed monitoring intervals.
        """
        self.logger.info(f"Monitoring context pressure threshold: {threshold}")

        def pressure_condition():
            # Get current context usage
            usage = self._get_current_context_usage()
            if usage >= threshold:
                return {
                    "usage": usage,
                    "threshold": threshold,
                    "timestamp": time.time(),
                    "pressure_level": (
                        "high" if usage > HIGH_PRESSURE_THRESHOLD else "moderate"
                    ),
                }
            return None

        return self.wait_for_condition(
            pressure_condition,
            f"context pressure threshold {threshold}",
            timeout_ms,
            poll_interval_ms=check_interval_ms,
        )

    def _get_current_context_usage(self) -> float:
        """Get current context usage as percentage (0-1)."""
        # In real implementation, this would check actual token usage
        # For demo, simulate varying usage
        return random.uniform(LOW_USAGE_SIMULATION, HIGH_USAGE_SIMULATION)  # noqa: S311


# Create global instance for service registry
condition_optimizer = ConditionBasedOptimizer()


# Export key functions for easy import by other plugins
def optimize_content_with_conditions(
    plugin_name: str,
    content_blocks: list[ContentBlock],
    max_tokens: int,
    strategy: str = "balanced",
    **kwargs,
) -> OptimizationResult:
    """Optimize content with condition-based waiting.

    This is the main entry point for other plugins to use Conservation's
    enhanced optimization services.
    """
    request = OptimizationRequest(
        plugin_name=plugin_name,
        content_blocks=content_blocks,
        max_tokens=max_tokens,
        strategy=strategy,
        **kwargs,
    )

    return condition_optimizer.optimize_with_conditions(request)


def wait_for_optimal_conditions(
    optimization_type: str = "context",
    **kwargs,
) -> dict[str, Any]:
    """Wait for optimal conditions before performing optimization.

    Replaces arbitrary pre-optimization delays with intelligent waiting.
    """
    if optimization_type == "context":
        return condition_optimizer.monitor_context_pressure(**kwargs)
    if optimization_type == "coordination":
        return condition_optimizer.wait_for_plugin_coordination(**kwargs)
    msg = f"Unknown optimization type: {optimization_type}"
    raise ValueError(msg)


# Example usage patterns
if __name__ == "__main__":
    # Demonstration of condition-based optimization

    # Create test content blocks
    test_blocks = [
        ContentBlock(
            content="# Main function\ndef main():\n    pass",
            priority=0.9,
            source="core_code",
            token_estimate=100,
            metadata={"section": "main"},
        ),
        ContentBlock(
            content="# TODO: Add error handling\n# Debug code",
            priority=0.5,
            source="comments",
            token_estimate=50,
            metadata={"section": "notes"},
        ),
        ContentBlock(
            content="def helper():\n    return None",
            priority=0.7,
            source="helper_code",
            token_estimate=60,
            metadata={"section": "helpers"},
        ),
    ]

    # Example 1: Basic optimization with conditions
    request = OptimizationRequest(
        plugin_name="demo_plugin",
        content_blocks=test_blocks,
        max_tokens=150,
        strategy="priority",
    )

    result = condition_optimizer.optimize_with_conditions(request)

    # Example 2: Plugin coordination
    coordination = condition_optimizer.wait_for_plugin_coordination(
        plugins=["abstract", "sanctum", "imbue"],
        coordination_type="resource_optimization",
    )

    # Example 3: Context pressure monitoring
    pressure = condition_optimizer.monitor_context_pressure(
        threshold=0.7,
        check_interval_ms=50,
    )
