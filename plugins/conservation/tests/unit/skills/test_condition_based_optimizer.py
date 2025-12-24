"""Tests for condition-based optimizer with intelligent waiting.

Tests the ConditionBasedOptimizer which implements condition-based waiting
to eliminate flaky optimization behavior caused by arbitrary timeouts.
"""

import importlib.util
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Constants for tests
COMPRESSION_RATIO_THRESHOLD = 0.3
TOKEN_REDUCTION_THRESHOLD = 100
SEMANTIC_COHERENCE_THRESHOLD = 0.7
WARNING_THRESHOLD = 0.40
CRITICAL_THRESHOLD = 0.50
HIGH_PRESSURE_THRESHOLD = 0.9

# Test timing constants
TIMEOUT_SHORT_MS = 100
TIMEOUT_MEDIUM_MS = 500
POLL_INTERVAL_MS = 10


# Create mock service registry with required method
class MockServiceRegistry:
    """Mock service registry for testing."""

    def __init__(self):
        self.services = {}

    def register_service(self, name, service):
        """Register a service."""
        self.services[name] = service


@pytest.fixture(scope="module")
def optimizer_module():
    """Import the condition_based_optimizer module with mocked dependencies.

    We need to mock before import because the module creates a global instance.
    """
    # Remove from cache if already imported
    if "condition_based_optimizer" in sys.modules:
        del sys.modules["condition_based_optimizer"]

    # Create mock module for context_optimization_service
    mock_service_module = type(sys)("context_optimization_service")
    mock_service_module.ConservationContextOptimizer = MagicMock
    mock_service_module.ConservationServiceRegistry = MockServiceRegistry
    mock_service_module.ContentBlock = MagicMock
    sys.modules["context_optimization_service"] = mock_service_module

    skill_path = Path(__file__).resolve().parents[3] / "skills" / "context-optimization"
    module_path = skill_path / "condition_based_optimizer.py"

    spec = importlib.util.spec_from_file_location(
        "condition_based_optimizer", module_path
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["condition_based_optimizer"] = module
    spec.loader.exec_module(module)

    yield module

    # Cleanup
    if "context_optimization_service" in sys.modules:
        del sys.modules["context_optimization_service"]
    if "condition_based_optimizer" in sys.modules:
        del sys.modules["condition_based_optimizer"]


class TestOptimizationRequest:
    """Test OptimizationRequest dataclass."""

    def test_create_request_with_defaults(self, optimizer_module) -> None:
        """Should create request with sensible defaults."""
        OptimizationRequest = optimizer_module.OptimizationRequest

        request = OptimizationRequest(
            plugin_name="test_plugin",
            content_blocks=[],
            max_tokens=1000,
        )

        assert request.plugin_name == "test_plugin"
        assert request.max_tokens == 1000
        assert request.strategy == "balanced"
        assert request.priority == 0.5
        assert request.timeout_ms == 30000

    def test_create_request_with_custom_values(self, optimizer_module) -> None:
        """Should accept custom configuration."""
        OptimizationRequest = optimizer_module.OptimizationRequest

        def custom_condition(r):
            return r.get("done", False)

        def custom_callback(r):
            return None

        request = OptimizationRequest(
            plugin_name="custom_plugin",
            content_blocks=[],
            max_tokens=500,
            strategy="aggressive",
            priority=0.9,
            timeout_ms=10000,
            completion_condition=custom_condition,
            callback=custom_callback,
        )

        assert request.strategy == "aggressive"
        assert request.priority == 0.9
        assert request.timeout_ms == 10000
        assert request.completion_condition is not None
        assert request.callback is not None


class TestOptimizationResult:
    """Test OptimizationResult dataclass."""

    def test_create_result_with_defaults(self, optimizer_module) -> None:
        """Should create result with default values."""
        OptimizationResult = optimizer_module.OptimizationResult

        result = OptimizationResult(
            optimization_id="test_123",
            plugin_name="test_plugin",
            status="pending",
        )

        assert result.optimization_id == "test_123"
        assert result.plugin_name == "test_plugin"
        assert result.status == "pending"
        assert result.optimized_content == ""
        assert result.metrics == {}
        assert result.error_message == ""
        assert result.start_time is not None
        assert result.end_time is None

    def test_result_status_values(self, optimizer_module) -> None:
        """Should support all expected status values."""
        OptimizationResult = optimizer_module.OptimizationResult

        for status in ["pending", "completed", "failed", "timeout"]:
            result = OptimizationResult(
                optimization_id="test",
                plugin_name="test",
                status=status,
            )
            assert result.status == status


class TestModuleConstants:
    """Test module-level constants."""

    def test_compression_threshold(self, optimizer_module) -> None:
        """Compression ratio threshold should be 0.3."""
        assert (
            optimizer_module.COMPRESSION_RATIO_THRESHOLD == COMPRESSION_RATIO_THRESHOLD
        )

    def test_token_reduction_threshold(self, optimizer_module) -> None:
        """Token reduction threshold should be 100."""
        assert optimizer_module.TOKEN_REDUCTION_THRESHOLD == TOKEN_REDUCTION_THRESHOLD

    def test_warning_threshold(self, optimizer_module) -> None:
        """MECW warning threshold should be 0.40 (40%)."""
        assert optimizer_module.WARNING_THRESHOLD == WARNING_THRESHOLD

    def test_critical_threshold(self, optimizer_module) -> None:
        """MECW critical threshold should be 0.50 (50%)."""
        assert optimizer_module.CRITICAL_THRESHOLD == CRITICAL_THRESHOLD

    def test_threshold_ordering(self, optimizer_module) -> None:
        """Critical threshold should be higher than warning threshold."""
        assert optimizer_module.CRITICAL_THRESHOLD > optimizer_module.WARNING_THRESHOLD


class TestConditionBasedOptimizer:
    """Test ConditionBasedOptimizer main class."""

    @pytest.fixture
    def mock_optimizer(self, optimizer_module):
        """Create optimizer instance (deps already mocked at module level)."""
        return optimizer_module.ConditionBasedOptimizer()

    def test_init_creates_optimizer(self, mock_optimizer) -> None:
        """Should initialize with empty tracking structures."""
        assert mock_optimizer.active_optimizations == {}
        assert mock_optimizer.optimization_queue == []
        assert mock_optimizer.is_processing is False

    def test_init_registers_condition_checkers(self, mock_optimizer) -> None:
        """Should register built-in condition checkers."""
        checkers = mock_optimizer.condition_checkers

        assert "compression_ratio" in checkers
        assert "token_reduction" in checkers
        assert "priority_preserved" in checkers
        assert "structure_intact" in checkers
        assert "semantic_coherence" in checkers

    def test_condition_checker_compression_ratio(self, mock_optimizer) -> None:
        """Compression ratio checker should use 0.3 threshold."""
        checker = mock_optimizer.condition_checkers["compression_ratio"]

        assert checker({"compression_ratio": 0.4}) is True
        assert checker({"compression_ratio": 0.2}) is False
        assert checker({"compression_ratio": 0.3}) is False  # Not > threshold
        assert checker({}) is False  # Missing key

    def test_condition_checker_token_reduction(self, mock_optimizer) -> None:
        """Token reduction checker should use 100 threshold."""
        checker = mock_optimizer.condition_checkers["token_reduction"]

        assert checker({"tokens_saved": 150}) is True
        assert checker({"tokens_saved": 50}) is False
        assert checker({"tokens_saved": 100}) is False  # Not > threshold

    def test_condition_checker_structure_intact(self, mock_optimizer) -> None:
        """Structure intact checker should check boolean."""
        checker = mock_optimizer.condition_checkers["structure_intact"]

        assert checker({"structure_preserved": True}) is True
        assert checker({"structure_preserved": False}) is False
        assert checker({}) is False


class TestWaitForCondition:
    """Test the core wait_for_condition method."""

    @pytest.fixture
    def mock_optimizer(self, optimizer_module):
        """Create optimizer instance (deps already mocked at module level)."""
        return optimizer_module.ConditionBasedOptimizer()

    def test_wait_for_condition_immediate_success(self, mock_optimizer) -> None:
        """Should return immediately when condition is already met."""
        call_count = 0

        def condition():
            nonlocal call_count
            call_count += 1
            return "success_value"

        start = time.time()
        result = mock_optimizer.wait_for_condition(
            condition=condition,
            description="immediate success",
            timeout_ms=1000,
        )
        elapsed = time.time() - start

        assert result == "success_value"
        assert call_count == 1
        assert elapsed < 0.1  # Should be very fast

    def test_wait_for_condition_eventual_success(self, mock_optimizer) -> None:
        """Should poll until condition becomes true."""
        call_count = 0

        def condition():
            nonlocal call_count
            call_count += 1
            return call_count >= 3

        result = mock_optimizer.wait_for_condition(
            condition=condition,
            description="eventual success",
            timeout_ms=1000,
            poll_interval_ms=10,
        )

        assert result is True
        assert call_count == 3

    def test_wait_for_condition_timeout(self, mock_optimizer) -> None:
        """Should raise TimeoutError when condition never met."""

        def never_true():
            return False

        with pytest.raises(TimeoutError) as exc_info:
            mock_optimizer.wait_for_condition(
                condition=never_true,
                description="never met",
                timeout_ms=TIMEOUT_SHORT_MS,
                poll_interval_ms=POLL_INTERVAL_MS,
            )

        assert "never met" in str(exc_info.value)
        assert f"{TIMEOUT_SHORT_MS}ms" in str(exc_info.value)

    def test_wait_for_condition_handles_exceptions(self, mock_optimizer) -> None:
        """Should continue polling if condition raises exception."""
        call_count = 0

        def flaky_condition():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary error")
            return True

        result = mock_optimizer.wait_for_condition(
            condition=flaky_condition,
            description="flaky condition",
            timeout_ms=1000,
            poll_interval_ms=10,
        )

        assert result is True
        assert call_count == 3


class TestValidateOptimizationResult:
    """Test optimization result validation."""

    @pytest.fixture
    def mock_optimizer(self, optimizer_module):
        """Create optimizer instance (deps already mocked at module level)."""
        return optimizer_module.ConditionBasedOptimizer()

    @pytest.fixture
    def mock_request(self, optimizer_module):
        """Create a mock optimization request."""
        return optimizer_module.OptimizationRequest(
            plugin_name="test",
            content_blocks=[],
            max_tokens=1000,
        )

    def test_validate_valid_result(self, mock_optimizer, mock_request) -> None:
        """Should validate result with good metrics."""
        result = {
            "optimized_tokens": 500,  # Under max_tokens
            "blocks_kept": 5,
            "compression_ratio": 0.5,  # Above minimum
        }

        assert (
            mock_optimizer._validate_optimization_result(result, mock_request) is True
        )

    def test_validate_fails_tokens_exceeded(self, mock_optimizer, mock_request) -> None:
        """Should fail if optimized tokens >= max_tokens."""
        result = {
            "optimized_tokens": 1000,  # Equal to max
            "blocks_kept": 5,
            "compression_ratio": 0.5,
        }

        assert (
            mock_optimizer._validate_optimization_result(result, mock_request) is False
        )

    def test_validate_fails_no_blocks_kept(self, mock_optimizer, mock_request) -> None:
        """Should fail if no blocks were kept."""
        result = {
            "optimized_tokens": 500,
            "blocks_kept": 0,  # No blocks
            "compression_ratio": 0.5,
        }

        assert (
            mock_optimizer._validate_optimization_result(result, mock_request) is False
        )

    def test_validate_fails_low_compression(self, mock_optimizer, mock_request) -> None:
        """Should fail if compression ratio too low."""
        result = {
            "optimized_tokens": 500,
            "blocks_kept": 5,
            "compression_ratio": 0.05,  # Below 0.1 minimum
        }

        assert (
            mock_optimizer._validate_optimization_result(result, mock_request) is False
        )


class TestContextPressureMonitoring:
    """Test context pressure monitoring with MECW thresholds."""

    @pytest.fixture
    def mock_optimizer(self, optimizer_module):
        """Create optimizer instance (deps already mocked at module level)."""
        return optimizer_module.ConditionBasedOptimizer()

    def test_monitor_returns_when_threshold_reached(self, mock_optimizer) -> None:
        """Should return when usage exceeds threshold."""
        mock_optimizer._get_current_context_usage = MagicMock(return_value=0.85)

        result = mock_optimizer.monitor_context_pressure(
            threshold=0.8,
            check_interval_ms=10,
            timeout_ms=1000,
        )

        assert result is not None
        assert result["usage"] == 0.85
        assert result["threshold"] == 0.8
        assert "timestamp" in result

    def test_monitor_warning_level(self, mock_optimizer) -> None:
        """Should return warning level for usage >= 40%."""
        mock_optimizer._get_current_context_usage = MagicMock(return_value=0.45)

        result = mock_optimizer.monitor_context_pressure(
            threshold=0.4,
            timeout_ms=1000,
        )

        assert result["alert_level"] == "warning"
        assert len(result["recommendations"]) > 0
        assert any("optimize-context" in r for r in result["recommendations"])

    def test_monitor_critical_level(self, mock_optimizer) -> None:
        """Should return critical level for usage >= 50%."""
        mock_optimizer._get_current_context_usage = MagicMock(return_value=0.55)

        result = mock_optimizer.monitor_context_pressure(
            threshold=0.5,
            timeout_ms=1000,
        )

        assert result["alert_level"] == "critical"
        assert len(result["recommendations"]) >= 2
        assert any("subagent" in r.lower() for r in result["recommendations"])

    def test_monitor_high_pressure_detection(self, mock_optimizer) -> None:
        """Should detect high pressure above 90%."""
        mock_optimizer._get_current_context_usage = MagicMock(return_value=0.95)

        result = mock_optimizer.monitor_context_pressure(
            threshold=0.9,
            timeout_ms=1000,
        )

        assert result["pressure_level"] == "high"

    def test_monitor_moderate_pressure_detection(self, mock_optimizer) -> None:
        """Should detect moderate pressure below 90%."""
        mock_optimizer._get_current_context_usage = MagicMock(return_value=0.85)

        result = mock_optimizer.monitor_context_pressure(
            threshold=0.8,
            timeout_ms=1000,
        )

        assert result["pressure_level"] == "moderate"


class TestPluginCoordination:
    """Test multi-plugin coordination."""

    @pytest.fixture
    def mock_optimizer(self, optimizer_module):
        """Create optimizer instance (deps already mocked at module level)."""
        return optimizer_module.ConditionBasedOptimizer()

    def test_coordination_returns_ready_status(self, mock_optimizer) -> None:
        """Should return ready status for all plugins."""
        plugins = ["abstract", "sanctum", "imbue"]

        result = mock_optimizer.wait_for_plugin_coordination(
            plugins=plugins,
            coordination_type="optimization",
            timeout_ms=5000,
        )

        assert result is not None
        for plugin in plugins:
            assert plugin in result
            assert result[plugin] is True


class TestModuleExports:
    """Test module-level export functions."""

    def test_optimize_content_with_conditions_exists(self, optimizer_module) -> None:
        """Should export optimize_content_with_conditions function."""
        assert hasattr(optimizer_module, "optimize_content_with_conditions")
        assert callable(optimizer_module.optimize_content_with_conditions)

    def test_wait_for_optimal_conditions_exists(self, optimizer_module) -> None:
        """Should export wait_for_optimal_conditions function."""
        assert hasattr(optimizer_module, "wait_for_optimal_conditions")
        assert callable(optimizer_module.wait_for_optimal_conditions)

    def test_wait_for_optimal_conditions_invalid_type(self, optimizer_module) -> None:
        """Should raise ValueError for unknown optimization type."""
        with pytest.raises(ValueError) as exc_info:
            optimizer_module.wait_for_optimal_conditions(
                optimization_type="invalid_type"
            )

        assert "Unknown optimization type" in str(exc_info.value)

    def test_condition_optimizer_global_instance(self, optimizer_module) -> None:
        """Should create global condition_optimizer instance."""
        assert hasattr(optimizer_module, "condition_optimizer")
        assert optimizer_module.condition_optimizer is not None
