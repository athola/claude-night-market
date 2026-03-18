"""Tests for the area-agent registry and lookup.

Tests config format parsing, path-to-area matching,
and fallback behavior.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest
from scripts.area_agent_registry import (
    find_area_config,
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


class TestAreaAgentLookup:
    """Feature: Match file paths to area-agent configs.

    As a dispatcher
    I want to find the right config for a given file
    So that the agent gets area-specific context.
    """

    @pytest.mark.unit
    def test_match_file_to_area(self, tmp_path: Path) -> None:
        """Given configs and a file path, return matching config."""
        configs_dir = tmp_path / "area-agents"
        configs_dir.mkdir()
        (configs_dir / "plugins-imbue.md").write_text(
            textwrap.dedent("""\
            ---
            area_name: plugins/imbue
            ownership_globs:
              - "plugins/imbue/**"
            ---
            Imbue guide.
        """)
        )
        (configs_dir / "plugins-conserve.md").write_text(
            textwrap.dedent("""\
            ---
            area_name: plugins/conserve
            ownership_globs:
              - "plugins/conserve/**"
            ---
            Conserve guide.
        """)
        )

        result = find_area_config(
            "plugins/imbue/scripts/validator.py",
            configs_dir,
        )
        assert result is not None
        assert result.area_name == "plugins/imbue"

    @pytest.mark.unit
    def test_no_match_returns_none(self, tmp_path: Path) -> None:
        """Given a path with no matching config, return None."""
        configs_dir = tmp_path / "area-agents"
        configs_dir.mkdir()
        (configs_dir / "plugins-imbue.md").write_text(
            textwrap.dedent("""\
            ---
            area_name: plugins/imbue
            ownership_globs:
              - "plugins/imbue/**"
            ---
            Imbue guide.
        """)
        )

        result = find_area_config(
            "plugins/unknown/foo.py",
            configs_dir,
        )
        assert result is None

    @pytest.mark.unit
    def test_multiple_files_multiple_configs(self, tmp_path: Path) -> None:
        """Given files spanning 2 areas, find both configs."""
        configs_dir = tmp_path / "area-agents"
        configs_dir.mkdir()
        (configs_dir / "plugins-imbue.md").write_text(
            textwrap.dedent("""\
            ---
            area_name: plugins/imbue
            ownership_globs:
              - "plugins/imbue/**"
            ---
            Imbue guide.
        """)
        )
        (configs_dir / "plugins-conserve.md").write_text(
            textwrap.dedent("""\
            ---
            area_name: plugins/conserve
            ownership_globs:
              - "plugins/conserve/**"
            ---
            Conserve guide.
        """)
        )

        files = [
            "plugins/imbue/foo.py",
            "plugins/conserve/bar.py",
        ]
        configs = [find_area_config(f, configs_dir) for f in files]
        valid = [c for c in configs if c is not None]
        area_names = {c.area_name for c in valid}
        assert area_names == {"plugins/imbue", "plugins/conserve"}

    @pytest.mark.unit
    def test_missing_configs_dir_returns_none(self, tmp_path: Path) -> None:
        """Given a nonexistent configs directory, return None."""
        result = find_area_config(
            "plugins/imbue/foo.py",
            tmp_path / "does-not-exist",
        )
        assert result is None


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
