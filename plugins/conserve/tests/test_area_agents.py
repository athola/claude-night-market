"""Tests for the area-agent registry and lookup.

Tests config format parsing, path-to-area matching,
and fallback behavior.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest
from scripts.area_agent_registry import (
    load_area_config,
)

# --------------- config loading ---------------


class TestAreaAgentConfigLoading:
    """Feature: Load area-agent configuration files.

    As a dispatcher
    I want to load area-specific agent configs
    So that agents get relevant context automatically.
    """

    @pytest.mark.unit
    def test_load_valid_config(self, tmp_path: Path) -> None:
        """Given a well-formed area-agent config, parse all fields."""
        config_file = tmp_path / "plugins-imbue.md"
        config_file.write_text(
            textwrap.dedent("""\
            ---
            area_name: plugins/imbue
            ownership_globs:
              - "plugins/imbue/**"
            tags:
              - review-workflow
              - evidence-management
            ---

            # plugins/imbue Area Guide

            ## Patterns

            Uses proof-of-work evidence pattern.

            ## Pitfalls

            Coverage threshold is strict (85%).

            ## Testing

            Run: cd plugins/imbue && uv run pytest tests/ -v
        """)
        )
        config = load_area_config(config_file)
        assert config.area_name == "plugins/imbue"
        assert "plugins/imbue/**" in config.ownership_globs
        assert "review-workflow" in config.tags
        assert "proof-of-work" in config.body

    @pytest.mark.unit
    def test_load_config_missing_optional_fields(self, tmp_path: Path) -> None:
        """Given a config with only required fields, use defaults."""
        config_file = tmp_path / "hooks.md"
        config_file.write_text(
            textwrap.dedent("""\
            ---
            area_name: hooks
            ownership_globs:
              - "hooks/**"
            ---

            Hook conventions here.
        """)
        )
        config = load_area_config(config_file)
        assert config.area_name == "hooks"
        assert config.tags == []


# --------------- path matching ---------------


# --------------- config edge cases ---------------


class TestAreaAgentConfigEdgeCases:
    """Feature: Handle unusual config files gracefully.

    As a dispatcher
    I want resilient config loading
    So that malformed files don't crash the system.
    """

    @pytest.mark.unit
    def test_config_without_frontmatter(self, tmp_path: Path) -> None:
        """Given a config with no frontmatter, use filename as area_name."""
        config_file = tmp_path / "plain-config.md"
        config_file.write_text("# Just a heading\n\nNo frontmatter here.\n")
        config = load_area_config(config_file)
        assert config.area_name == "plain-config"
        assert config.ownership_globs == ()
        assert config.tags == []

    @pytest.mark.unit
    def test_config_with_empty_globs(self, tmp_path: Path) -> None:
        """Given a config with ownership_globs but no list items, globs are empty."""
        config_file = tmp_path / "empty-globs.md"
        config_file.write_text(
            textwrap.dedent("""\
            ---
            area_name: test-area
            ---

            Body content.
        """)
        )
        config = load_area_config(config_file)
        assert config.area_name == "test-area"
        assert config.ownership_globs == ()
        assert not config.matches_path("any/path/here.py")
