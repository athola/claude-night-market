"""Shared test fixtures and configuration for leyline tests.

This conftest.py follows the project's mocking standards:
- Use MagicMock over Mock for enhanced functionality
- All mocks have meaningful name parameters
- Factory fixtures for common mock patterns
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Setup path for importing script modules
_script_path = Path(__file__).parent.parent / "scripts"
if str(_script_path) not in sys.path:
    sys.path.insert(0, str(_script_path))


@pytest.fixture
def subprocess_result_factory():
    """Factory for creating mock subprocess.CompletedProcess objects.

    Usage:
        result = subprocess_result_factory(0, stdout="success")
    """

    def _create(returncode: int, stdout: str = "", stderr: str = "") -> MagicMock:
        result = MagicMock(name="CompletedProcess")
        result.returncode = returncode
        result.stdout = stdout
        result.stderr = stderr
        return result

    return _create


@pytest.fixture
def sample_plugins_single() -> dict[str, list[dict[str, str]]]:
    """Sample plugin configuration with single plugin."""
    return {"test@marketplace": [{"version": "1.0.0"}]}


@pytest.fixture
def sample_plugins_multiple() -> dict[str, list[dict[str, str]]]:
    """Sample plugin configuration with multiple plugins."""
    return {
        "plugin1@marketplace1": [{"version": "1.0.0"}],
        "plugin2@marketplace2": [{"version": "2.0.0"}],
    }


@pytest.fixture
def sample_plugins_with_versions() -> dict[str, list[dict[str, str]]]:
    """Sample plugin configuration with multiple version entries."""
    return {
        "plugin1@marketplace1": [
            {"version": "1.0.0"},
            {"version": "1.1.0"},
        ]
    }


@pytest.fixture
def mock_claude_tools() -> dict[str, MagicMock]:
    """Mock Claude Code tools for testing update workflows."""
    return {
        "subprocess_run": MagicMock(name="subprocess.run"),
        "path_exists": MagicMock(name="Path.exists"),
        "file_open": MagicMock(name="builtins.open"),
        "sys_exit": MagicMock(name="sys.exit"),
        "print": MagicMock(name="builtins.print"),
    }


@pytest.fixture
def valid_plugins_json() -> str:
    """Valid JSON content for plugins configuration file."""
    return '{"plugins": {"test@marketplace": [{"version": "1.0.0"}]}}'


@pytest.fixture
def empty_plugins_json() -> str:
    """JSON content for empty plugins configuration."""
    return '{"plugins": {}}'
