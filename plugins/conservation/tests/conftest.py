"""Shared fixtures and configuration for conservation plugin testing.

This module provides common test fixtures, mocks, and utilities for testing
the conservation plugin's skills, commands, and agents following TDD/BDD principles.
"""

import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest

# Add the scripts directory to Python path for importing conservation scripts
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

try:
    from scripts.conservation_validator import ConservationValidator
except ImportError:
    ConservationValidator = None

# Constants for PLR2004 magic values
FIVE = 5

# Constants for test thresholds and limits
CPU_USAGE_THRESHOLD = 80
TOKEN_USAGE_THRESHOLD = 10000
MECW_THRESHOLD = 0.5  # 50% rule
LOW_UTILIZATION_THRESHOLD = 0.3
OPTIMAL_UTILIZATION_THRESHOLD = 0.5
HIGH_UTILIZATION_THRESHOLD = 0.7


@pytest.fixture
def conservation_plugin_root():
    """Return the conservation plugin root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def sample_skill_content() -> str:
    """Sample valid skill file content with frontmatter for conservation."""
    return """---
name: token-conservation-test
description: Test skill for token conservation workflow methodology
category: conservation
token_budget: 150
progressive_loading: true
dependencies:
  hub: []
  modules: []
tools:
  - Read
  - Glob
  - Grep
  - Bash
  - TodoWrite
tags:
  - conservation
  - tokens
  - optimization
---

# Token Conservation Test Skill

Test skill for validating token conservation workflow patterns.

## TodoWrite Items

- `token-conservation-test:quota-check`
- `token-conservation-test:context-plan`
- `token-conservation-test:delegation-check`
- `token-conservation-test:compression-review`
- `token-conservation-test:logging`

## Usage

Use this skill to test token conservation patterns.
"""


@pytest.fixture
def sample_context_optimization_skill() -> str:
    """Sample context optimization skill content."""
    return """---
name: context-optimization-test
description: Test skill for MECW principles and context optimization
category: conservation
token_budget: 200
progressive_loading: true
dependencies:
  hub: []
  modules: []
tools:
  - Read
  - Glob
  - Grep
  - Bash
  - TodoWrite
tags:
  - conservation
  - context
  - MECW
  - optimization
---

# Context Optimization Test Skill

Test skill for validating context optimization and MECW principles.

## TodoWrite Items

- `context-optimization-test:mecw-assessment`
- `context-optimization-test:context-classification`
- `context-optimization-test:module-coordination`
- `context-optimization-test:synthesis`
- `context-optimization-test:validation`

## Usage

Use this skill to test context optimization patterns.
"""


@pytest.fixture
def sample_plugin_json():
    """Sample valid conservation plugin.json configuration."""
    return {
        "name": "conservation",
        "version": "2.0.0",
        "description": (
            "Resource optimization and performance monitoring toolkit for "
            "efficient Claude Code workflows"
        ),
        "skills": [
            {
                "name": "context-optimization",
                "description": "Optimize context usage by implementing MECW principles",
                "file": "skills/context-optimization/SKILL.md",
            },
            {
                "name": "token-conservation",
                "description": "Minimize token usage through conservative prompting",
                "file": "skills/resource-management/token-conservation/SKILL.md",
            },
            {
                "name": "mcp-code-execution",
                "description": "Optimize code execution using MCP patterns",
                "file": "skills/mcp-code-execution/SKILL.md",
            },
            {
                "name": "performance-monitoring",
                "description": "Monitor CPU/GPU performance and resource usage",
                "file": "skills/performance-monitoring/cpu-gpu-performance/SKILL.md",
            },
            {
                "name": "optimizing-large-skills",
                "description": "Optimize large skills for better performance",
                "file": "skills/optimizing-large-skills/SKILL.md",
            },
        ],
        "commands": [
            {
                "name": "optimize-context",
                "description": "Optimize context usage and apply MECW principles",
                "usage": "/optimize-context [target]",
                "file": "commands/optimize-context.md",
            },
            {
                "name": "analyze-growth",
                "description": "Analyze resource usage and growth patterns",
                "usage": "/analyze-growth [timeframe]",
                "file": "commands/analyze-growth.md",
            },
        ],
        "agents": [
            {
                "name": "context-optimizer",
                "description": "Autonomous agent for context optimization",
                "file": "agents/context-optimizer.md",
                "tools": ["Read", "Glob", "Grep", "Bash", "TodoWrite"],
            },
        ],
    }


@pytest.fixture
def sample_token_quota():
    """Sample token quota configuration."""
    return {
        "session_duration_hours": 2.5,
        "weekly_usage_tokens": 45000,
        "weekly_limit_tokens": 100000,
        "remaining_budget_tokens": 55000,
        "rolling_cap_hours": 5,
        "task_max_tokens": 5000,
    }


@pytest.fixture
def sample_context_analysis():
    """Sample context analysis results."""
    return {
        "total_context_tokens": 8500,
        "context_window_size": 200000,
        "utilization_percentage": 4.25,
        "status": "LOW",
        "mecw_compliance": True,
        "risk_factors": [],
        "recommendations": [
            "Context usage is within optimal range",
            "Continue with current approach",
        ],
    }


@pytest.fixture
def sample_performance_metrics():
    """Sample performance monitoring metrics."""
    return {
        "timestamp": datetime.now(UTC).isoformat(),
        "cpu_usage_percent": 15.2,
        "memory_usage_mb": 512,
        "gpu_usage_percent": 0.0,
        "token_generation_rate": 45.5,
        "response_time_seconds": 1.2,
        "context_compression_ratio": 0.85,
        "tool_calls_per_minute": 3.2,
    }


@pytest.fixture
def sample_growth_analysis():
    """Sample resource growth analysis results."""
    return {
        "analysis_period": "7_days",
        "baseline_tokens": 1000,
        "current_tokens": 2500,
        "growth_percentage": 150.0,
        "growth_trend": "increasing",
        "peak_usage_hour": "14:00",
        "efficiency_score": 0.75,
        "recommendations": [
            "Consider context optimization techniques",
            "Monitor token usage during peak hours",
        ],
    }


@pytest.fixture
def temp_skill_file(tmp_path, sample_skill_content):
    """Create a temporary skill file."""
    skill_dir = tmp_path / "test-skill"
    skill_dir.mkdir()
    skill_file = skill_dir / "SKILL.md"
    skill_file.write_text(sample_skill_content)
    return skill_file


@pytest.fixture
def temp_skill_dir(tmp_path):
    """Create a temporary skill directory structure."""
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()

    # Create multiple skill directories for conservation plugin
    skill_configs = [
        ("context-optimization", "MECW principles and context management"),
        ("token-conservation", "Token optimization and quota management"),
        ("performance-monitoring", "Resource usage and performance tracking"),
        ("mcp-code-execution", "MCP pattern optimization"),
        ("optimizing-large-skills", "Large skill optimization patterns"),
    ]

    for skill_name, description in skill_configs:
        skill_dir = skills_dir / skill_name
        skill_dir.mkdir()
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text(f"""---
name: {skill_name}
description: {description}
category: conservation
token_budget: 200
progressive_loading: true
---""")

    return skills_dir


@pytest.fixture
def mock_todo_write():
    """Mock TodoWrite tool for testing."""
    mock = Mock()
    mock.return_value = None
    # Configure mock to track calls
    return mock


@pytest.fixture
def mock_claude_tools():
    """Mock Claude Code tools."""
    tools = {
        "Read": Mock(),
        "Glob": Mock(),
        "Grep": Mock(),
        "Bash": Mock(),
        "Write": Mock(),
        "Edit": Mock(),
        "TodoWrite": Mock(),
        "AskUserQuestion": Mock(),
    }

    # Configure default return values
    tools["Read"].return_value = "Mock file content"
    tools["Glob"].return_value = []
    tools["Grep"].return_value = []
    tools["Bash"].return_value = "Mock bash output"

    return tools


@pytest.fixture
def mock_performance_monitor():
    """Mock performance monitoring functionality."""

    class MockPerformanceMonitor:
        def __init__(self) -> None:
            self.metrics_history = []
            self.alerts = []

        def collect_metrics(self):
            return {
                "cpu_usage": 20.5,
                "memory_usage": 1024,
                "token_usage": 5000,
                "context_efficiency": 0.85,
            }

        def check_thresholds(self, metrics):
            alerts = []
            if metrics["cpu_usage"] > CPU_USAGE_THRESHOLD:
                alerts.append("High CPU usage detected")
            if metrics["token_usage"] > TOKEN_USAGE_THRESHOLD:
                alerts.append("High token usage detected")
            return alerts

        def generate_report(self):
            return {
                "average_cpu": 25.3,
                "peak_memory": 2048,
                "total_tokens": 50000,
                "efficiency_score": 0.88,
            }

    return MockPerformanceMonitor()


@pytest.fixture
def mock_mecw_analyzer():
    """Mock MECW (Maximum Effective Context Window) analyzer."""

    class MockMECWAnalyzer:
        def __init__(self) -> None:
            self.context_window = 200000
            self.mecw_threshold = MECW_THRESHOLD  # 50% rule

        def analyze_context_usage(self, context_tokens):
            utilization = context_tokens / self.context_window
            return {
                "utilization_percentage": utilization * 100,
                "status": self._classify_status(utilization),
                "mecw_compliant": utilization <= self.mecw_threshold,
                "recommended_actions": self._get_recommendations(utilization),
            }

        def _classify_status(self, utilization) -> str:
            if utilization < LOW_UTILIZATION_THRESHOLD:
                return "LOW"
            if utilization < OPTIMAL_UTILIZATION_THRESHOLD:
                return "OPTIMAL"
            if utilization < HIGH_UTILIZATION_THRESHOLD:
                return "HIGH"
            return "CRITICAL"

        def _get_recommendations(self, utilization):
            if utilization < LOW_UTILIZATION_THRESHOLD:
                return ["Context usage is low, optimization not required"]
            if utilization < OPTIMAL_UTILIZATION_THRESHOLD:
                return ["Continue current approach, monitor usage"]
            if utilization < HIGH_UTILIZATION_THRESHOLD:
                return ["Consider context compression", "Evaluate token efficiency"]
            return [
                "Immediate context optimization required",
                "Use subagent delegation",
            ]

    return MockMECWAnalyzer()


@pytest.fixture
def mock_token_quota_tracker():
    """Mock token quota tracking functionality."""

    class MockTokenQuotaTracker:
        def __init__(self) -> None:
            self.session_start = datetime.now(UTC)
            self.weekly_usage = 45000
            self.weekly_limit = 100000

        def check_quota(self):
            session_duration = (
                datetime.now(UTC) - self.session_start
            ).total_seconds() / 3600
            remaining = self.weekly_limit - self.weekly_usage
            return {
                "session_duration_hours": session_duration,
                "weekly_usage": self.weekly_usage,
                "weekly_limit": self.weekly_limit,
                "remaining_budget": remaining,
                "within_limits": session_duration < FIVE and remaining > 0,
            }

        def track_usage(self, tokens_used):
            self.weekly_usage += tokens_used
            return self.check_quota()

    return MockTokenQuotaTracker()


@pytest.fixture
def mock_conservation_validator(conservation_plugin_root):
    """Create ConservationValidator instance with mocked dependencies."""
    if ConservationValidator is not None:
        # Initialize with real plugin root but mock file operations
        return ConservationValidator(str(conservation_plugin_root))
    else:
        # If the module doesn't exist yet, create a mock
        mock_validator = Mock()
        mock_validator.plugin_root = str(conservation_plugin_root)
        mock_validator.scan_conservation_workflows = Mock(return_value=[])
        mock_validator.validate_conservation_workflows = Mock(return_value=[])
        mock_validator.generate_report = Mock(return_value="Mock report")
        return mock_validator


# Test markers for pytest configuration
def pytest_configure(config) -> None:
    """Configure custom pytest markers."""
    config.addinivalue_line("markers", "unit: Unit tests for individual components")
    config.addinivalue_line(
        "markers",
        "integration: Integration tests for workflow orchestration",
    )
    config.addinivalue_line("markers", "performance: Performance and scalability tests")
    config.addinivalue_line("markers", "slow: Tests that take longer to execute")
    config.addinivalue_line("markers", "bdd: Behavior-driven development style tests")


def pytest_collection_modifyitems(config, items) -> None:
    """Add custom markers to items based on their content."""
    for item in items:
        # Add performance marker to performance tests
        if "performance" in item.nodeid or any(
            keyword in item.nodeid
            for keyword in ["performance", "scalability", "benchmark"]
        ):
            item.add_marker(pytest.mark.performance)

        # Add bdd marker to BDD-style tests
        if "bdd" in item.nodeid or any(
            keyword in item.nodeid
            for keyword in ["bdd", "behavior", "feature", "scenario"]
        ):
            item.add_marker(pytest.mark.bdd)


# Helper functions for test data generation
def create_mock_conservation_skill(
    name: str,
    category: str = "conservation",
) -> dict[str, Any]:
    """Create a mock conservation skill configuration."""
    return {
        "name": name,
        "description": f"Test skill for {name}",
        "file": f"skills/{name}/SKILL.md",
        "category": category,
        "token_budget": 200,
        "progressive_loading": True,
    }


def create_mock_token_log_entry(
    session_id: str,
    tokens_used: int,
    operation: str,
) -> dict[str, Any]:
    """Create a mock token usage log entry."""
    return {
        "session_id": session_id,
        "timestamp": datetime.now(UTC).isoformat(),
        "tokens_used": tokens_used,
        "operation": operation,
        "efficiency_score": 0.85,
    }


def create_mock_performance_metric(
    metric_name: str,
    value: float,
    unit: str,
) -> dict[str, Any]:
    """Create a mock performance metric."""
    return {
        "name": metric_name,
        "value": value,
        "unit": unit,
        "timestamp": datetime.now(UTC).isoformat(),
        "threshold_exceeded": False,
    }


def create_mock_context_analysis(
    context_tokens: int,
    window_size: int = 200000,
) -> dict[str, Any]:
    """Create a mock context analysis result."""
    utilization = context_tokens / window_size
    return {
        "context_tokens": context_tokens,
        "window_size": window_size,
        "utilization_percentage": utilization * 100,
        "status": "OPTIMAL"
        if utilization < OPTIMAL_UTILIZATION_THRESHOLD
        else "HIGH"
        if utilization < HIGH_UTILIZATION_THRESHOLD
        else "CRITICAL",
        "mecw_compliant": utilization <= OPTIMAL_UTILIZATION_THRESHOLD,
    }
