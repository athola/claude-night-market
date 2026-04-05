"""Tests for PostToolUse graph auto-update hook."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

_HOOKS_DIR = Path(__file__).resolve().parents[2] / "hooks"
sys.path.insert(0, str(_HOOKS_DIR))

from graph_auto_update import (  # noqa: E402 - sys.path modified above
    _is_auto_update_enabled,
    main,
)


@pytest.fixture()
def gauntlet_dir(tmp_path: Path) -> Path:
    d = tmp_path / ".gauntlet"
    d.mkdir()
    return d


class TestIsAutoUpdateEnabled:
    """
    Feature: Auto-update config toggle

    As a project owner
    I want to opt-in to auto graph updates
    So that the graph stays fresh without manual effort
    """

    @pytest.mark.unit
    def test_disabled_by_default(self, gauntlet_dir: Path) -> None:
        """No config file means disabled."""
        assert _is_auto_update_enabled(gauntlet_dir) is False

    @pytest.mark.unit
    def test_enabled_via_json(self, gauntlet_dir: Path) -> None:
        """config.json with auto_update: true enables it."""
        (gauntlet_dir / "config.json").write_text(json.dumps({"auto_update": True}))
        assert _is_auto_update_enabled(gauntlet_dir) is True

    @pytest.mark.unit
    def test_disabled_via_json(self, gauntlet_dir: Path) -> None:
        """config.json with auto_update: false keeps it off."""
        (gauntlet_dir / "config.json").write_text(json.dumps({"auto_update": False}))
        assert _is_auto_update_enabled(gauntlet_dir) is False

    @pytest.mark.unit
    def test_survives_malformed_json(self, gauntlet_dir: Path) -> None:
        """Bad config falls back to disabled."""
        (gauntlet_dir / "config.json").write_text("not json {{{")
        assert _is_auto_update_enabled(gauntlet_dir) is False


class TestMainHook:
    """
    Feature: Post-commit graph auto-update

    As a developer
    I want the graph to update after commits
    So that blast radius analysis uses fresh data
    """

    @pytest.mark.unit
    def test_ignores_non_bash_tools(self) -> None:
        """Non-Bash tool events are ignored."""
        result = main({"tool_name": "Read", "tool_input": {}})
        assert result is None

    @pytest.mark.unit
    def test_ignores_non_commit_commands(self) -> None:
        """Bash commands that aren't git commit are ignored."""
        result = main(
            {
                "tool_name": "Bash",
                "tool_input": {"command": "git status"},
            }
        )
        assert result is None

    @pytest.mark.unit
    def test_ignores_failed_commits(self) -> None:
        """Failed commits (exit code != 0) are ignored."""
        result = main(
            {
                "tool_name": "Bash",
                "tool_input": {"command": "git commit -m 'test'"},
                "tool_result": {"exitCode": 1, "stdout": "error"},
            }
        )
        assert result is None

    @pytest.mark.unit
    def test_ignores_when_no_gauntlet_dir(self) -> None:
        """No .gauntlet directory means no update."""
        with patch("graph_auto_update._get_gauntlet_dir", return_value=None):
            result = main(
                {
                    "tool_name": "Bash",
                    "tool_input": {"command": "git commit -m 'test'"},
                    "tool_result": {"exitCode": 0, "stdout": "[main abc123]"},
                }
            )
        assert result is None

    @pytest.mark.unit
    def test_ignores_when_auto_update_disabled(self, gauntlet_dir: Path) -> None:
        """Auto-update disabled in config means no update."""
        with patch(
            "graph_auto_update._get_gauntlet_dir",
            return_value=gauntlet_dir,
        ):
            result = main(
                {
                    "tool_name": "Bash",
                    "tool_input": {"command": "git commit -m 'test'"},
                    "tool_result": {"exitCode": 0, "stdout": "[main abc123]"},
                }
            )
        assert result is None

    @pytest.mark.unit
    def test_returns_context_on_successful_update(self, gauntlet_dir: Path) -> None:
        """Enabled auto-update with graph.db returns context."""
        # Enable auto-update
        (gauntlet_dir / "config.json").write_text(json.dumps({"auto_update": True}))
        # Create a dummy graph.db
        from gauntlet.graph import GraphStore

        gs = GraphStore(str(gauntlet_dir / "graph.db"))
        gs.close()

        mock_report = {
            "files_parsed": 3,
            "nodes_created": 12,
            "edges_created": 8,
        }
        with (
            patch(
                "graph_auto_update._get_gauntlet_dir",
                return_value=gauntlet_dir,
            ),
            patch(
                "gauntlet.incremental.incremental_update",
                return_value=mock_report,
            ),
        ):
            result = main(
                {
                    "tool_name": "Bash",
                    "tool_input": {"command": "git commit -m 'test'"},
                    "tool_result": {"exitCode": 0, "stdout": "[main abc123]"},
                }
            )
        assert result is not None
        assert "Graph updated" in result["additionalContext"]
        assert "3 files" in result["additionalContext"]
