"""Root pytest configuration for claude-night-market ecosystem.

This conftest.py resolves test infrastructure conflicts when running pytest from
the repository root. Each plugin has its own test suite with isolated fixtures
and configuration.

Usage:
    # Run tests for a specific plugin (recommended)
    cd plugins/attune && uv run pytest

    # Run tests from root with specific plugin
    uv run pytest plugins/attune/tests/ --ignore=plugins/*/tests/conftest.py

    # Run all plugin tests (requires --ignore to avoid conflicts)
    uv run pytest plugins/*/tests/ --ignore-glob='**/conftest.py'

The conflict arises because:
1. Each plugin has its own conftest.py with unique fixtures
2. Running `pytest plugins/` collects all conftest.py files
3. Duplicate fixtures and hooks cause ImportPathMismatchError

Solution:
- Run plugin tests individually from plugin directories
- Use --ignore flags when running from root
- This conftest provides root-level configuration without conflicting fixtures
"""
from __future__ import annotations

from pathlib import Path

import pytest


def pytest_configure(config) -> None:
    """Configure pytest for root-level execution.

    Adds custom markers and configures collection to avoid conflicts.
    """
    # Register ecosystem-wide markers
    config.addinivalue_line(
        "markers", "plugin(name): Mark test as belonging to a specific plugin"
    )
    config.addinivalue_line(
        "markers", "ecosystem: Mark test as ecosystem-level integration test"
    )


def pytest_collection_modifyitems(config, items) -> None:
    """Modify collected test items.

    Adds plugin markers based on test location for filtering.
    """
    for item in items:
        # Extract plugin name from path
        path_parts = Path(item.fspath).parts
        if "plugins" in path_parts:
            try:
                plugin_idx = path_parts.index("plugins")
                if plugin_idx + 1 < len(path_parts):
                    plugin_name = path_parts[plugin_idx + 1]
                    item.add_marker(pytest.mark.plugin(plugin_name))
            except (ValueError, IndexError):
                pass


# Ignore patterns for plugin-specific conftest files when running from root
collect_ignore_glob = [
    # Ignore virtual environment test files
    "**/.*venv/**",
    "**/.venv/**",
    # Ignore cache directories
    "**/.uv-cache/**",
    "**/__pycache__/**",
    # Ignore worktrees (separate git worktree directories)
    ".worktrees/**",
]


def pytest_ignore_collect(collection_path: Path, config) -> bool | None:
    """Ignore certain paths during collection.

    Returns True to ignore, None to let pytest decide.
    """
    path_str = str(collection_path)

    # Always ignore virtual environments and caches
    ignore_patterns = [".venv", ".uv-cache", "__pycache__", ".worktrees"]
    if any(pattern in path_str for pattern in ignore_patterns):
        return True

    return None
