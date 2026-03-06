"""Tests for plugin health dimensions.

Feature: Plugin Health Measurement

    As an ecosystem maintainer
    I want to see health dimensions per plugin
    So that I can identify areas needing stewardship attention
"""

from __future__ import annotations

from pathlib import Path

import pytest


class TestDocFreshness:
    """Test documentation freshness dimension."""

    @pytest.mark.unit
    def test_reports_freshness_for_plugin_with_docs(self, tmp_path: Path) -> None:
        """
        Scenario: Plugin has markdown documentation
        Given a plugin directory with .md files
        When measuring documentation freshness
        Then it reports the age of the most recent .md file
        """
        from plugin_health import measure_doc_freshness

        plugin_dir = tmp_path / "plugins" / "test-plugin"
        plugin_dir.mkdir(parents=True)
        readme = plugin_dir / "README.md"
        readme.write_text("# Test")

        result = measure_doc_freshness(plugin_dir)
        assert result == "docs updated today"

    @pytest.mark.unit
    def test_reports_not_measured_when_no_docs(self, tmp_path: Path) -> None:
        """
        Scenario: Plugin has no documentation
        Given an empty plugin directory
        When measuring documentation freshness
        Then it reports "not measured"
        """
        from plugin_health import measure_doc_freshness

        plugin_dir = tmp_path / "plugins" / "empty-plugin"
        plugin_dir.mkdir(parents=True)

        result = measure_doc_freshness(plugin_dir)
        assert result == "not measured"


class TestImprovementVelocity:
    """Test improvement velocity dimension."""

    @pytest.mark.unit
    def test_reports_action_count(self, tmp_path: Path) -> None:
        """
        Scenario: Plugin has stewardship actions
        Given a stewardship tracker with actions for a plugin
        When measuring improvement velocity
        Then it reports the count of recent actions
        """
        from plugin_health import measure_improvement_velocity

        actions_dir = tmp_path / "stewardship"
        actions_dir.mkdir(parents=True)
        actions_file = actions_dir / "actions.jsonl"
        actions_file.write_text(
            '{"plugin":"sanctum","action_type":"fix","file":"x","description":"d","timestamp":"2026-03-01T00:00:00Z"}\n'
            '{"plugin":"sanctum","action_type":"doc","file":"y","description":"d","timestamp":"2026-03-02T00:00:00Z"}\n'
            '{"plugin":"imbue","action_type":"fix","file":"z","description":"d","timestamp":"2026-03-03T00:00:00Z"}\n'
        )

        result = measure_improvement_velocity(actions_dir, "sanctum")
        assert result == "2 stewardship actions recorded"

    @pytest.mark.unit
    def test_reports_not_measured_when_no_tracker(self, tmp_path: Path) -> None:
        """
        Scenario: No stewardship tracker exists
        Given an empty directory with no actions file
        When measuring improvement velocity
        Then it reports "not measured"
        """
        from plugin_health import measure_improvement_velocity

        actions_dir = tmp_path / "empty"
        result = measure_improvement_velocity(actions_dir, "sanctum")
        assert result == "not measured"


class TestGetPluginHealth:
    """Test the full health report for a plugin."""

    @pytest.mark.unit
    def test_returns_all_five_dimensions(self, tmp_path: Path) -> None:
        """
        Scenario: Full health report
        Given a plugin directory exists
        When getting the full health report
        Then it contains all 5 dimension keys
        """
        from plugin_health import get_plugin_health

        plugin_dir = tmp_path / "plugins" / "test-plugin"
        plugin_dir.mkdir(parents=True)
        (plugin_dir / "README.md").write_text("# Test")

        actions_dir = tmp_path / "stewardship"

        health = get_plugin_health(
            plugin_dir=plugin_dir,
            actions_dir=actions_dir,
            plugin_name="test-plugin",
        )

        assert "doc_freshness" in health
        assert "test_coverage" in health
        assert "code_quality" in health
        assert "contributor_friendliness" in health
        assert "improvement_velocity" in health

    @pytest.mark.unit
    def test_handles_missing_plugin_gracefully(self, tmp_path: Path) -> None:
        """
        Scenario: Plugin directory does not exist
        Given a non-existent plugin path
        When getting the health report
        Then all dimensions report "not measured"
        """
        from plugin_health import get_plugin_health

        health = get_plugin_health(
            plugin_dir=tmp_path / "nonexistent",
            actions_dir=tmp_path / "stewardship",
            plugin_name="ghost",
        )

        for key, value in health.items():
            assert value == "not measured"


class TestIndividualDimensions:
    """Test individual health dimensions with positive-path data."""

    @pytest.mark.unit
    def test_coverage_reports_available_when_coverage_file_exists(
        self, tmp_path: Path
    ) -> None:
        """Given a plugin with .coverage file, reports coverage available."""
        from plugin_health import measure_test_coverage

        plugin_dir = tmp_path / "plugins" / "test-plugin"
        plugin_dir.mkdir(parents=True)
        (plugin_dir / ".coverage").write_text("")

        result = measure_test_coverage(plugin_dir)
        assert "coverage data available" in result

    @pytest.mark.unit
    def test_code_quality_reports_indicators(self, tmp_path: Path) -> None:
        """Given a plugin with pyproject.toml and tests, reports quality indicators."""
        from plugin_health import measure_code_quality

        plugin_dir = tmp_path / "plugins" / "test-plugin"
        plugin_dir.mkdir(parents=True)
        (plugin_dir / "pyproject.toml").write_text("[tool.pytest]")
        test_dir = plugin_dir / "tests"
        test_dir.mkdir()
        (test_dir / "test_example.py").write_text("def test_x(): pass")
        (plugin_dir / "Makefile").write_text("test:\n\tpytest")

        result = measure_code_quality(plugin_dir)
        assert "pyproject.toml configured" in result
        assert "tests present" in result
        assert "Makefile targets available" in result

    @pytest.mark.unit
    def test_contributor_friendliness_reports_indicators(self, tmp_path: Path) -> None:
        """Given a plugin with README containing stewardship and examples, reports all."""
        from plugin_health import measure_contributor_friendliness

        plugin_dir = tmp_path / "plugins" / "test-plugin"
        plugin_dir.mkdir(parents=True)
        (plugin_dir / "README.md").write_text(
            "# Plugin\n\n## Stewardship\n\nCare.\n\n```python\nprint()\n```\n"
        )

        result = measure_contributor_friendliness(plugin_dir)
        assert "README present" in result
        assert "stewardship section" in result
        assert "code examples" in result

    @pytest.mark.unit
    def test_doc_freshness_singular_day(self, tmp_path: Path) -> None:
        """Given a plugin with docs updated exactly 1 day ago, reports singular."""
        import os
        import time

        from plugin_health import measure_doc_freshness

        plugin_dir = tmp_path / "plugins" / "test-plugin"
        plugin_dir.mkdir(parents=True)
        readme = plugin_dir / "README.md"
        readme.write_text("# Test")
        # Set mtime to 1 day ago
        one_day_ago = time.time() - 86400
        os.utime(readme, (one_day_ago, one_day_ago))

        result = measure_doc_freshness(plugin_dir)
        assert result == "docs updated 1 day ago"
