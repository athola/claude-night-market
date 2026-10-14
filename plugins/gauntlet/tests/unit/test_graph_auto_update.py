"""Tests for PostToolUse graph auto-update hook."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

import graph_auto_update
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


_COMMIT_EVENT: dict[str, object] = {
    "tool_name": "Bash",
    "tool_input": {"command": "git commit -m 'test'"},
    "tool_response": _bash_response("[main abc123] test\n 1 file changed"),
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

    @pytest.mark.unit
    def test_enabled_via_yaml(self, gauntlet_dir: Path) -> None:
        """config.yaml with auto_update: true enables it."""
        (gauntlet_dir / "config.yaml").write_text("auto_update: true\n")
        assert _is_auto_update_enabled(gauntlet_dir) is True

    @pytest.mark.unit
    def test_yaml_config_is_skipped_without_pyyaml(self, gauntlet_dir: Path) -> None:
        """Without pyyaml (system Python 3.9) a YAML config reads as disabled."""
        (gauntlet_dir / "config.yaml").write_text("auto_update: true\n")
        with patch.dict(sys.modules, {"yaml": None}):
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
    def test_ignores_when_no_gauntlet_dir(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """No .gauntlet directory in the working directory means no update."""
        monkeypatch.chdir(tmp_path)
        result = main(_COMMIT_EVENT)
        assert result is None

    @pytest.mark.unit
    def test_a_gauntlet_file_is_not_a_gauntlet_dir(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A regular file named .gauntlet is ignored, not opened as a dir."""
        (tmp_path / ".gauntlet").write_text("not a directory")
        monkeypatch.chdir(tmp_path)
        assert main(_COMMIT_EVENT) is None

    @pytest.mark.unit
    def test_ignores_when_auto_update_disabled(
        self, gauntlet_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Auto-update disabled in config means no update."""
        monkeypatch.chdir(gauntlet_dir.parent)
        result = main(_COMMIT_EVENT)
        assert result is None

    @pytest.mark.unit
    def test_ignores_when_graph_db_missing(
        self, gauntlet_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Enabled auto-update without a built graph.db does nothing."""
        (gauntlet_dir / "config.json").write_text(json.dumps({"auto_update": True}))
        monkeypatch.chdir(gauntlet_dir.parent)
        with patch("gauntlet.incremental.incremental_update") as update:
            assert main(_COMMIT_EVENT) is None
        update.assert_not_called()

    @pytest.mark.unit
    def test_update_failure_logs_and_returns_none(
        self,
        gauntlet_dir: Path,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """A failing update is logged and the hook still exits quietly."""
        (gauntlet_dir / "config.json").write_text(json.dumps({"auto_update": True}))
        GraphStore(str(gauntlet_dir / "graph.db")).close()
        monkeypatch.chdir(gauntlet_dir.parent)
        with patch(
            "gauntlet.incremental.incremental_update",
            side_effect=RuntimeError("git diff failed"),
        ):
            assert main(_COMMIT_EVENT) is None
        assert "RuntimeError: git diff failed" in caplog.text

    @pytest.mark.unit
    def test_returns_context_on_successful_update(
        self, gauntlet_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
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
        monkeypatch.chdir(gauntlet_dir.parent)
        with patch(
            "gauntlet.incremental.incremental_update",
            return_value=mock_report,
        ):
            result = main(_COMMIT_EVENT)
        assert result is not None
        context = result["hookSpecificOutput"]["additionalContext"]
        assert "Graph updated" in context
        assert "3 files" in context

    @pytest.mark.unit
    @pytest.mark.parametrize(
        ("layout", "found"),
        [("dir", True), ("file", False), ("absent", False)],
    )
    def test_gauntlet_dir_lookup_accepts_only_a_directory(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        layout: str,
        found: bool,
    ) -> None:
        """Only a .gauntlet directory in cwd counts; a file or nothing is None."""
        target = tmp_path / ".gauntlet"
        if layout == "dir":
            target.mkdir()
        elif layout == "file":
            target.write_text("not a directory")
        monkeypatch.chdir(tmp_path)
        expected = target if found else None
        assert graph_auto_update._get_gauntlet_dir() == expected
