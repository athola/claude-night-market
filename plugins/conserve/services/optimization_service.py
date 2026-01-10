"""Conservation Plugin Optimization Service Interface.

Provides a clean, discoverable interface for other plugins to use
Conservation's context optimization capabilities with condition-based waiting.
"""

import contextlib
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

# Import Conservation components
# Import skill helpers (mypy: no stubs available)
try:
    from ..skills.context_optimization.condition_based_optimizer import (  # type: ignore[import-not-found]
        ConditionBasedOptimizer,
        OptimizationRequest,
        OptimizationResult,
    )
    from ..skills.context_optimization.context_optimization_service import (  # type: ignore[import-not-found]
        ConservationServiceRegistry,
        ContentBlock,
    )
except ImportError:
    # Handle relative imports for different usage contexts
    import sys
    from pathlib import Path

    sys.path.append(str(Path(__file__).parent.parent))

    from skills.context_optimization.condition_based_optimizer import (  # type: ignore[import-not-found]
        ConditionBasedOptimizer,
        OptimizationRequest,
        OptimizationResult,
    )
    from skills.context_optimization.context_optimization_service import (  # type: ignore[import-not-found]
        ConservationServiceRegistry,
        ContentBlock,
    )


@dataclass
class OptimizationServiceInfo:
    """Information about available optimization services."""

    service_name: str
    description: str
    capabilities: list[str]
    version: str = "2.0.0"
    supported_strategies: list[str] | None = None

    def __post_init__(self) -> None:
        """Initialize default values after dataclass creation."""
        if self.supported_strategies is None:
            self.supported_strategies = [
                "priority",
                "recency",
                "importance",
                "semantic",
                "balanced",
            ]


class OptimizationServiceInterface:
    """High-level service interface for plugins to use Conservation's.

    optimization capabilities without needing to know implementation details.
    """

    def __init__(self) -> None:
        """Initialize the optimization service interface."""
        self.optimizer = ConditionBasedOptimizer()
        self.registry = ConservationServiceRegistry()
        self._register_services()

    def _register_services(self) -> None:
        """Register optimization services in the global registry."""
        self.registry.register_service("conservation.optimize", self.optimize_content)
        self.registry.register_service(
            "conservation.optimize_async",
            self.optimize_content_async,
        )
        self.registry.register_service(
            "conservation.monitor_context",
            self.monitor_context_pressure,
        )
        self.registry.register_service(
            "conservation.coordinate_plugins",
            self.coordinate_plugin_optimization,
        )
        self.registry.register_service(
            "conservation.get_service_info",
            self.get_service_info,
        )

    def optimize_content(
        self,
        plugin_name: str,
        content: str | list[dict[str, Any]],
        max_tokens: int,
        strategy: str = "balanced",
        priority: float = 0.5,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Optimize content to fit within token limits.

        This is the main entry point for other plugins to optimize their content.
        Uses condition-based waiting to validate reliable optimization.

        Args:
            plugin_name: Name of the plugin requesting optimization
            content: Content to optimize (string or list of content blocks)
            max_tokens: Maximum tokens to keep
            strategy: Optimization strategy to use
            priority: Content priority (0.0 to 1.0)
            **kwargs: Additional optimization parameters

        Returns:
            Dictionary with optimization results and metadata

        """
        # Convert content to ContentBlock objects
        content_blocks = self._prepare_content_blocks(content, priority)

        # Create optimization request
        request = OptimizationRequest(
            plugin_name=plugin_name,
            content_blocks=content_blocks,
            max_tokens=max_tokens,
            strategy=strategy,
            priority=priority,
            **kwargs,
        )

        # Perform optimization with condition-based waiting
        result = self.optimizer.optimize_with_conditions(request)

        # Convert to serializable format
        return self._serialize_result(result)

    def optimize_content_async(
        self,
        plugin_name: str,
        content: str | list[dict[str, Any]],
        max_tokens: int,
        strategy: str = "balanced",
        **kwargs: Any,
    ) -> str:
        """Start asynchronous optimization and return optimization ID.

        Returns immediately with an optimization ID that can be used
        to check status later.
        """
        content_blocks = self._prepare_content_blocks(content)

        request = OptimizationRequest(
            plugin_name=plugin_name,
            content_blocks=content_blocks,
            max_tokens=max_tokens,
            strategy=strategy,
            **kwargs,
        )

        # Start optimization (in real implementation, this would be async)
        result = self.optimizer.optimize_with_conditions(request)

        return str(result.optimization_id)

    def monitor_context_pressure(
        self,
        threshold: float = 0.8,
        timeout_ms: int = 30000,
        plugin_name: str | None = None,
    ) -> dict[str, Any]:
        """Monitor context usage and wait for threshold breach.

        Args:
            threshold: Context usage threshold (0.0 to 1.0)
            timeout_ms: Maximum time to wait in milliseconds
            plugin_name: Optional plugin name for coordinated monitoring

        Returns:
            Dictionary with pressure information and recommendations

        """
        pressure_info = self.optimizer.monitor_context_pressure(
            threshold=threshold,
            timeout_ms=timeout_ms,
        )

        # Add optimization recommendations
        recommendations: list[str] = []
        if pressure_info["pressure_level"] == "high":
            recommendations.extend(
                [
                    "Consider using 'priority' strategy to keep essential content",
                    "Enable structure preservation for better coherence",
                    "Increase monitoring frequency during peak usage",
                ],
            )
        elif pressure_info["pressure_level"] == "moderate":
            recommendations.extend(
                [
                    "Use 'balanced' strategy for general optimization",
                    "Monitor for additional context pressure",
                ],
            )

        return {
            **pressure_info,
            "recommendations": recommendations,
            "plugin_context": plugin_name,
            "optimization_service": "conservation",
        }

    def coordinate_plugin_optimization(
        self,
        plugins: list[str],
        optimization_type: str = "context",
        timeout_ms: int = 20000,
    ) -> dict[str, Any]:
        """Coordinate optimization across multiple plugins.

        Uses condition-based waiting to validate all plugins are ready
        before proceeding with coordinated optimization.
        """
        coordination_result = self.optimizer.wait_for_plugin_coordination(
            plugins=plugins,
            coordination_type=optimization_type,
            timeout_ms=timeout_ms,
        )

        # Add coordination metadata
        return {
            "coordination_successful": all(coordination_result.values()),
            "plugin_readiness": coordination_result,
            "optimization_type": optimization_type,
            "coordinated_plugins": plugins,
            "timestamp": time.time(),
        }

    def get_service_info(self) -> dict[str, Any]:
        """Get information about available optimization services."""
        services = [
            OptimizationServiceInfo(
                service_name="content_optimization",
                description="Optimize content to fit within token limits",
                capabilities=[
                    "Condition-based waiting",
                    "Multiple optimization strategies",
                    "Async optimization support",
                    "MECW compliance",
                ],
            ),
            OptimizationServiceInfo(
                service_name="context_monitoring",
                description="Monitor context usage and pressure",
                capabilities=[
                    "Real-time monitoring",
                    "Threshold-based alerts",
                    "Pressure level detection",
                    "Optimization recommendations",
                ],
            ),
            OptimizationServiceInfo(
                service_name="plugin_coordination",
                description="Coordinate optimization across plugins",
                capabilities=[
                    "Multi-plugin synchronization",
                    "Condition-based coordination",
                    "Resource sharing",
                    "Conflict resolution",
                ],
            ),
        ]

        return {
            "conservation_services": [asdict(service) for service in services],
            "version": "2.0.0",
            "features": [
                "Condition-based waiting (no arbitrary timeouts)",
                "MECW compliance (50% context rule)",
                "Plugin coordination",
                "Async optimization",
                "Real-time monitoring",
            ],
            "supported_strategies": [
                "priority",
                "recency",
                "importance",
                "semantic",
                "balanced",
            ],
        }

    def _prepare_content_blocks(
        self,
        content: str | list[dict[str, Any]],
        default_priority: float = 0.5,
    ) -> list[ContentBlock]:
        """Convert content input to ContentBlock objects."""
        if isinstance(content, str):
            # Split content into logical blocks
            return [
                ContentBlock(
                    content=content,
                    priority=default_priority,
                    source="plugin_content",
                    token_estimate=len(content.split()) * 1.3,
                    metadata={"section": "main", "timestamp": time.time()},
                ),
            ]
        if isinstance(content, list):
            # Assume list of dictionaries with content info
            blocks = []
            for item in content:
                if isinstance(item, dict):
                    blocks.append(
                        ContentBlock(
                            content=item.get("content", ""),
                            priority=item.get("priority", default_priority),
                            source=item.get("source", "plugin"),
                            token_estimate=item.get("token_estimate", 0)
                            or len(str(item.get("content", "")).split()) * 1.3,
                            metadata=item.get("metadata", {}),
                        ),
                    )
            return blocks
        msg = f"Unsupported content type: {type(content)}"
        raise ValueError(msg)

    def _serialize_result(self, result: OptimizationResult) -> dict[str, Any]:
        """Convert OptimizationResult to serializable dictionary."""
        return {
            "optimization_id": result.optimization_id,
            "plugin_name": result.plugin_name,
            "status": result.status,
            "optimized_content": result.optimized_content,
            "metrics": result.metrics,
            "error_message": result.error_message,
            "duration_seconds": (
                result.end_time - result.start_time if result.end_time else None
            ),
            "service": "conservation_optimization",
            "condition_based": True,
        }


# Create global service instance
optimization_service = OptimizationServiceInterface()


# Convenience functions for easy import
def optimize_content(
    plugin_name: str,
    content: str | list[dict[str, Any]],
    max_tokens: int,
    strategy: str = "balanced",
    **kwargs: Any,
) -> dict[str, Any]:
    """Quick optimization function for other plugins to use.

    Example:
        from conservation.services.optimization_service import optimize_content

        result = optimize_content(
            plugin_name="my_plugin",
            content=my_long_content,
            max_tokens=2000,
            strategy="priority"
        )

        optimized = result["optimized_content"]

    """
    return optimization_service.optimize_content(
        plugin_name=plugin_name,
        content=content,
        max_tokens=max_tokens,
        strategy=strategy,
        **kwargs,
    )


def monitor_context(
    threshold: float = 0.8,
    plugin_name: str | None = None,
) -> dict[str, Any]:
    """Quick context monitoring function.

    Example:
        from conservation.services.optimization_service import monitor_context

        pressure = monitor_context(threshold=0.7)
        if pressure["usage"] > 0.7:
            # Trigger optimization
            pass

    """
    return optimization_service.monitor_context_pressure(
        threshold=threshold,
        plugin_name=plugin_name,
    )


def coordinate_plugins(
    plugins: list[str],
    optimization_type: str = "context",
) -> dict[str, Any]:
    """Quick plugin coordination function.

    Example:
        from conservation.services.optimization_service import coordinate_plugins

        coordination = coordinate_plugins(
            plugins=["abstract", "sanctum"],
            optimization_type="resource"
        )

        if coordination["coordination_successful"]:
            # Proceed with coordinated optimization
            pass

    """
    return optimization_service.coordinate_plugin_optimization(
        plugins=plugins,
        optimization_type=optimization_type,
    )


# Service discovery helper
def get_conservation_services() -> dict[str, Any]:
    """Get information about all available Conservation services.

    Other plugins can call this to discover what services are available.
    """
    return optimization_service.get_service_info()


# Auto-register with global service registry
def register_services() -> None:
    """Register all services with the global registry."""
    registry = ConservationServiceRegistry()

    # Register main optimization service
    registry.register_service("conservation.optimize", optimize_content)

    # Register monitoring service
    registry.register_service("conservation.monitor", monitor_context)

    # Register coordination service
    registry.register_service("conservation.coordinate", coordinate_plugins)

    # Register discovery service
    registry.register_service("conservation.discover", get_conservation_services)


# Auto-register on import
register_services()


# Example usage for documentation
if __name__ == "__main__":
    # Demonstrate service interface

    # 1. Discover services
    services = get_conservation_services()

    # 2. Basic optimization
    test_content = """
    # This is a long document with many sections
    def function_one():
        # Important function
        return "important"

    def helper_function():
        # Less important helper
        return "helper"

    # Additional documentation goes here
    """

    result = optimize_content(
        plugin_name="demo_plugin",
        content=test_content,
        max_tokens=100,
        strategy="importance",
    )

    # 3. Context monitoring
    with contextlib.suppress(TimeoutError):
        pressure = monitor_context(threshold=0.5)

    # 4. Plugin coordination
    coordination = coordinate_plugins(
        plugins=["abstract", "sanctum", "imbue"],
        optimization_type="context",
    )
