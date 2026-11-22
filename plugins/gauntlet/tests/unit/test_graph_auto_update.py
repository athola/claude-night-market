"""Tests for PostToolUse graph auto-update hook."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

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
    def test_yaml_config_wins_over_json(self, gauntlet_dir: Path) -> None:
        """The gate preferred config.yaml and this hook config.json."""
        (gauntlet_dir / "config.yaml").write_text("auto_update: false\n")
        (gauntlet_dir / "config.json").write_text(json.dumps({"auto_update": True}))
        assert _is_auto_update_enabled(gauntlet_dir) is False

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

    @pytest.fixture(autouse=True)
    def _popen(self, monkeypatch: pytest.MonkeyPatch) -> MagicMock:
        # Every update is a detached graph_build.py run; nothing is spawned.
        popen = MagicMock()
        monkeypatch.setattr(graph_auto_update.shutil, "which", lambda name: "/bin/uv")
        monkeypatch.setattr("subprocess.Popen", popen)
        return popen

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
        self, gauntlet_dir: Path, monkeypatch: pytest.MonkeyPatch, _popen: MagicMock
    ) -> None:
        """Enabled auto-update without a built graph.db does nothing."""
        (gauntlet_dir / "config.json").write_text(json.dumps({"auto_update": True}))
        monkeypatch.chdir(gauntlet_dir.parent)
        assert main(_COMMIT_EVENT) is None
        _popen.assert_not_called()

    @pytest.mark.unit
    def test_returns_context_on_a_launched_update(
        self, gauntlet_dir: Path, monkeypatch: pytest.MonkeyPatch, _popen: MagicMock
    ) -> None:
        """Enabled auto-update with graph.db launches the build and says so."""
        (gauntlet_dir / "config.json").write_text(json.dumps({"auto_update": True}))
        GraphStore(str(gauntlet_dir / "graph.db")).close()
        monkeypatch.chdir(gauntlet_dir.parent)
        result = main(_COMMIT_EVENT)
        _popen.assert_called_once()
        context = result["hookSpecificOutput"]["additionalContext"]
        assert "Graph updating in the background" in context

    @pytest.mark.unit
    def test_a_chained_commit_also_refreshes_the_graph(
        self, gauntlet_dir: Path, monkeypatch: pytest.MonkeyPatch, _popen: MagicMock
    ) -> None:
        """`git add -A && git commit` is a commit, so the graph refreshes."""
        (gauntlet_dir / "config.json").write_text(json.dumps({"auto_update": True}))
        GraphStore(str(gauntlet_dir / "graph.db")).close()
        event = {
            **_COMMIT_EVENT,
            "tool_input": {"command": "git add -A && git commit -m 'test'"},
        }
        monkeypatch.chdir(gauntlet_dir.parent)
        assert main(event) is not None
        _popen.assert_called_once()

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


class TestBackgroundUpdate:
    """The detached update, the one path every commit takes.

    A failed update is reported from the exit status it wrote, on the next
    commit, which replaces reading an in-process report.
    """

    @staticmethod
    def _launch(gauntlet_dir: Path) -> tuple[dict[str, object] | None, list[str]]:
        popen = MagicMock()
        with (
            patch.object(graph_auto_update.shutil, "which", return_value="/bin/uv"),
            patch("subprocess.Popen", popen),
        ):
            output = graph_auto_update._update_in_plugin_env(gauntlet_dir)
        argv = popen.call_args.args[0] if popen.called else []
        return output, argv

    @pytest.mark.unit
    def test_background_update_diffs_from_the_last_build_not_head_parent(
        self, gauntlet_dir: Path
    ) -> None:
        """A diff of HEAD~1 skipped any commit the previous update missed."""
        _, argv = self._launch(gauntlet_dir)
        script = " ".join(argv)
        assert "--incremental" in script
        assert "--base-ref" not in script

    @pytest.mark.unit
    def test_background_update_records_its_exit_status(
        self, gauntlet_dir: Path
    ) -> None:
        _, argv = self._launch(gauntlet_dir)
        assert "update.status" in argv[-1]

    @pytest.mark.unit
    def test_failed_background_update_is_reported_on_the_next_commit(
        self, gauntlet_dir: Path
    ) -> None:
        """Every commit printed the same success-shaped line over a failure."""
        (gauntlet_dir / "update.status").write_text("2\n")
        output, argv = self._launch(gauntlet_dir)
        context = output["hookSpecificOutput"]["additionalContext"]
        assert context.startswith(
            "Graph not updated: the last background update failed"
        )
        assert str(gauntlet_dir / "update.log") in context
        assert argv, "the update is retried"

    @pytest.mark.unit
    def test_succeeded_background_update_reports_updating(
        self, gauntlet_dir: Path
    ) -> None:
        (gauntlet_dir / "update.status").write_text("0\n")
        output, _ = self._launch(gauntlet_dir)
        context = output["hookSpecificOutput"]["additionalContext"]
        assert context.startswith("Graph updating in the background")

    @pytest.mark.unit
    def test_failed_rebuild_holding_the_lock_is_reported(
        self, gauntlet_dir: Path
    ) -> None:
        """The auto-update skipped in silence behind a dead rebuild's lock."""
        (gauntlet_dir / "rebuild.lock").write_text("")
        (gauntlet_dir / "rebuild.status").write_text("1\n")
        output, argv = self._launch(gauntlet_dir)
        assert argv == []
        context = output["hookSpecificOutput"]["additionalContext"]
        assert str(gauntlet_dir / "rebuild.log") in context


@pytest.mark.unit
def test_commit_launches_the_stamped_build_even_where_a_parser_is_installed(
    gauntlet_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The in-process update diffed HEAD~1 and never stamped the build, so a
    commit an earlier update missed was never parsed.
    """
    (gauntlet_dir / "config.json").write_text(json.dumps({"auto_update": True}))
    GraphStore(str(gauntlet_dir / "graph.db")).close()
    monkeypatch.chdir(gauntlet_dir.parent)
    popen = MagicMock()
    with (
        patch("gauntlet.treesitter_parser.parser_available", return_value=True),
        patch("gauntlet.incremental.incremental_update") as in_process,
        patch.object(graph_auto_update.shutil, "which", return_value="/bin/uv"),
        patch("subprocess.Popen", popen),
    ):
        output = main(_COMMIT_EVENT)
    in_process.assert_not_called()
    script = popen.call_args.args[0][-1]
    assert "graph_build.py" in script
    assert "--incremental" in script
    assert "background" in output["hookSpecificOutput"]["additionalContext"]
