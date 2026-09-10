"""Tests for PostToolUse graph auto-update hook."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from graph_auto_update import (
    _is_auto_update_enabled,
    main,
)

from gauntlet.graph import GraphStore


@pytest.fixture()
def gauntlet_dir(tmp_path: Path) -> Path:
    d = tmp_path / ".gauntlet"
    d.mkdir()
    return d


def _bash_response(stdout: str) -> dict[str, object]:
    """Build a realistic PostToolUse tool_response for the Bash tool.

    The payload key is ``tool_response``, not ``tool_result``, and the Bash
    entry carries ``stdout``, ``stderr``, ``interrupted`` and ``isImage``.
    There is no ``exitCode``: PostToolUse fires only after a tool completes
    successfully, and failures route to PostToolUseFailure instead. Tests
    that invented an ``exitCode`` passed against a payload shape the harness
    has never sent.
    """
    return {
        "stdout": stdout,
        "stderr": "",
        "interrupted": False,
        "isImage": False,
    }


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
    def test_ignores_a_commit_that_recorded_nothing(self) -> None:
        """A commit reporting "nothing to commit" leaves the graph alone.

        This replaces a test that fed ``{"exitCode": 1}`` and asserted None.
        It passed for the wrong reason: the hook read ``tool_result``, which
        the payload never carries, so every input produced None. A failed
        commit never reaches PostToolUse at all, so "nothing to commit" in
        stdout is the only no-op this hook can actually observe.
        """
        result = main(
            {
                "tool_name": "Bash",
                "tool_input": {"command": "git commit -m 'test'"},
                "tool_response": _bash_response(
                    "nothing to commit, working tree clean"
                ),
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
                    "tool_response": _bash_response(
                        "[main abc123] test\n 1 file changed"
                    ),
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
                    "tool_response": _bash_response(
                        "[main abc123] test\n 1 file changed"
                    ),
                }
            )
        assert result is None

    @pytest.mark.unit
    def test_returns_context_on_successful_update(self, gauntlet_dir: Path) -> None:
        """Enabled auto-update with graph.db returns context."""
        # Enable auto-update
        (gauntlet_dir / "config.json").write_text(json.dumps({"auto_update": True}))
        # Create a dummy graph.db
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
                    "tool_response": _bash_response(
                        "[main abc123] test\n 1 file changed"
                    ),
                }
            )
        assert result is not None
        assert "Graph updated" in result["additionalContext"]
        assert "3 files" in result["additionalContext"]
