"""Tests for shared constants module."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))


class TestCacheExcludes:
    """
    Feature: Shared CACHE_EXCLUDES constant

    As a script developer
    I want a single source of truth for directory exclusions
    So that all scanning scripts skip the same directories consistently.
    """

    @pytest.mark.unit
    def test_cache_excludes_is_frozenset(self):
        """Scenario: CACHE_EXCLUDES is immutable."""
        from update_plugins_modules.constants import CACHE_EXCLUDES

        assert isinstance(CACHE_EXCLUDES, frozenset)

    @pytest.mark.unit
    def test_cache_excludes_contains_python_caches(self):
        """Scenario: Python cache directories are excluded."""
        from update_plugins_modules.constants import CACHE_EXCLUDES

        for name in ("__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"):
            assert name in CACHE_EXCLUDES, f"{name} missing from CACHE_EXCLUDES"

    @pytest.mark.unit
    def test_cache_excludes_contains_venvs(self):
        """Scenario: Virtual environment directories are excluded."""
        from update_plugins_modules.constants import CACHE_EXCLUDES

        for name in (".venv", "venv"):
            assert name in CACHE_EXCLUDES

    @pytest.mark.unit
    def test_cache_excludes_contains_node_modules(self):
        """Scenario: Node.js directories are excluded."""
        from update_plugins_modules.constants import CACHE_EXCLUDES

        assert "node_modules" in CACHE_EXCLUDES

    @pytest.mark.unit
    def test_cache_excludes_contains_vcs_dirs(self):
        """Scenario: Version control directories are excluded."""
        from update_plugins_modules.constants import CACHE_EXCLUDES

        assert ".git" in CACHE_EXCLUDES
