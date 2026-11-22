"""SessionStart hook: rebuild a graph that an older gauntlet built."""

from __future__ import annotations

import fcntl
import json
import os
import re
import sqlite3
import subprocess
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import graph_version_rebuild as hook
import pytest


def _graph(root: Path, version: str | None) -> Path:
    """Write a .gauntlet/graph.db whose metadata names ``version``."""
    gdir = root / ".gauntlet"
    gdir.mkdir()
    conn = sqlite3.connect(gdir / "graph.db")
    conn.execute("CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT)")
    if version is not None:
        conn.execute("INSERT INTO metadata VALUES ('gauntlet_version', ?)", (version,))
    conn.commit()
    conn.close()
    return gdir


@pytest.fixture()
def project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(hook, "_installed_version", lambda: "2.0.0")
    return tmp_path


def _run(which: dict[str, str | None] | None = None) -> tuple[dict | None, MagicMock]:
    tools = {"uv": "/usr/bin/uv", "nice": "/usr/bin/nice"}
    tools.update(which or {})
    with patch.object(hook.shutil, "which", side_effect=tools.get):
        with patch.object(subprocess, "Popen") as popen:
            output = hook.main({"hook_event_name": "SessionStart"})
    return output, popen


@pytest.mark.unit
class TestGraphVersionRebuild:
    """A graph older than the installed plugin is rebuilt once, in the background."""

    def test_matching_version_starts_nothing(self, project: Path) -> None:
        _graph(project, "2.0.0")
        output, popen = _run()
        assert output is None
        popen.assert_not_called()

    def test_older_graph_starts_one_background_full_build(self, project: Path) -> None:
        gdir = _graph(project, "1.0.0")
        output, popen = _run()
        popen.assert_called_once()
        argv = popen.call_args.args[0]
        script = " ".join(argv)
        assert "uv run --project" in script
        assert "graph_build.py" in script
        assert "--incremental" not in script
        assert popen.call_args.kwargs["start_new_session"] is True
        assert (gdir / "rebuild.lock").exists()
        assert "1.0.0" in output["hookSpecificOutput"]["additionalContext"]

    def test_newer_graph_is_left_alone(self, project: Path) -> None:
        # The release runbook builds with the bumped version before the
        # installed plugin is updated; an older plugin must not rebuild it.
        _graph(project, "2.1.0")
        output, popen = _run()
        assert output is None
        popen.assert_not_called()

    def test_failed_build_keeps_the_lock_so_sessions_do_not_relaunch(
        self, project: Path
    ) -> None:
        _graph(project, "1.0.0")
        _, popen = _run()
        script = popen.call_args.args[0][-1]
        assert "&& rm -f" in script

    def test_graph_without_a_recorded_version_is_rebuilt(self, project: Path) -> None:
        _graph(project, None)
        _, popen = _run()
        popen.assert_called_once()

    def test_live_lock_blocks_a_second_build(self, project: Path) -> None:
        gdir = _graph(project, "1.0.0")
        (gdir / "rebuild.lock").write_text(str(time.time()))
        output, popen = _run()
        popen.assert_not_called()
        assert output is None

    def test_stale_lock_is_replaced(self, project: Path) -> None:
        gdir = _graph(project, "1.0.0")
        lock = gdir / "rebuild.lock"
        lock.write_text("0")
        old = time.time() - hook._LOCK_TTL_SECONDS - 60
        os.utime(lock, (old, old))
        _, popen = _run()
        popen.assert_called_once()

    def test_opt_out_in_config_is_respected(self, project: Path) -> None:
        gdir = _graph(project, "1.0.0")
        (gdir / "config.json").write_text(json.dumps({"rebuild_on_upgrade": False}))
        output, popen = _run()
        popen.assert_not_called()
        assert output is None

    def test_opt_out_in_config_yaml_is_respected(self, project: Path) -> None:
        """Only config.json was read, so a YAML opt-out still rebuilt."""
        gdir = _graph(project, "1.0.0")
        (gdir / "config.yaml").write_text("rebuild_on_upgrade: false\n")
        output, popen = _run()
        popen.assert_not_called()
        assert output is None

    def test_yaml_opt_out_unreadable_without_pyyaml_starts_nothing(
        self, project: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A config the hook cannot read is not consent to a rebuild."""
        gdir = _graph(project, "1.0.0")
        (gdir / "config.yaml").write_text("rebuild_on_upgrade: false\n")
        monkeypatch.setitem(sys.modules, "yaml", None)
        output, popen = _run()
        popen.assert_not_called()
        assert output is None

    def test_no_graph_starts_nothing(self, project: Path) -> None:
        output, popen = _run()
        assert output is None
        popen.assert_not_called()

    def test_missing_uv_gives_a_hint_and_no_build(self, project: Path) -> None:
        gdir = _graph(project, "1.0.0")
        output, popen = _run({"uv": None})
        popen.assert_not_called()
        assert (
            "/gauntlet-graph build" in output["hookSpecificOutput"]["additionalContext"]
        )
        assert not (gdir / "rebuild.lock").exists()

    def test_plugin_json_and_package_versions_agree(self) -> None:
        # A drift would make every session see a version mismatch.
        init = (
            Path(hook.__file__).resolve().parents[1]
            / "src"
            / "gauntlet"
            / "__init__.py"
        )
        package = re.search(r'__version__ = "([^"]+)"', init.read_text()).group(1)
        assert hook._installed_version() == package

    def test_installed_version_comes_from_plugin_json(self) -> None:
        manifest = (
            Path(hook.__file__).resolve().parents[1] / ".claude-plugin" / "plugin.json"
        )
        expected = json.loads(manifest.read_text())["version"]
        assert hook._installed_version() == expected


@pytest.mark.unit
class TestRebuildFailsSafe:
    """A wrong guess here starts a multi-minute rebuild, so doubt means wait."""

    def test_locked_graph_starts_no_second_build(self, project: Path) -> None:
        _graph(project, "1.0.0")
        conn = MagicMock()
        conn.execute.side_effect = sqlite3.OperationalError("database is locked")
        with patch.object(hook.sqlite3, "connect", return_value=conn):
            output, popen = _run()
        popen.assert_not_called()
        assert output is None

    def test_corrupt_graph_returns_a_hint_not_a_traceback(self, project: Path) -> None:
        """A raised DatabaseError printed a traceback at SessionStart (GAU-5)."""
        gdir = _graph(project, "1.0.0")
        (gdir / "graph.db").write_bytes(b"not a sqlite database" * 100)
        output, popen = _run()
        popen.assert_not_called()
        assert "/gauntlet-graph build" in json.dumps(output)

    def test_unreadable_opt_out_config_starts_nothing(self, project: Path) -> None:
        gdir = _graph(project, "1.0.0")
        (gdir / "config.json").write_text("{not json")
        output, popen = _run()
        popen.assert_not_called()
        assert output is None


def test_stale_lock_takeover_waits_for_a_concurrent_taker(tmp_path: Path) -> None:
    """Two takers could both unlink a stale lock and both build (GAU-9)."""
    lock = tmp_path / "rebuild.lock"
    lock.write_text("old")
    old = time.time() - hook._LOCK_TTL_SECONDS - 60
    os.utime(lock, (old, old))
    with open(hook._guard_path(lock), "a") as guard:
        fcntl.flock(guard, fcntl.LOCK_EX)
        assert hook._take_lock(lock) is False
    assert hook._take_lock(lock) is True


def test_a_failed_launch_releases_the_lock(project: Path) -> None:
    """Popen raising left the lock, blocking rebuilds for two hours (GAU-5)."""
    gdir = _graph(project, "1.0.0")
    tools = {"uv": "/usr/bin/uv", "nice": "/usr/bin/nice"}
    with (
        patch.object(hook.shutil, "which", side_effect=tools.get),
        patch.object(subprocess, "Popen", side_effect=OSError("exec format")),
        pytest.raises(OSError),
    ):
        hook.main({"hook_event_name": "SessionStart"})
    assert not (gdir / "rebuild.lock").exists()


class TestAFailedRebuildIsReported:
    """A failed build keeps the lock, and later sessions printed nothing."""

    @pytest.mark.unit
    def test_rebuild_records_its_exit_status(self, project: Path) -> None:
        _graph(project, "1.0.0")
        _, popen = _run()
        assert "rebuild.status" in popen.call_args.args[0][-1]

    @pytest.mark.unit
    def test_held_lock_after_a_failed_rebuild_names_the_log(
        self, project: Path
    ) -> None:
        gdir = _graph(project, "1.0.0")
        (gdir / "rebuild.lock").write_text(str(time.time()))
        (gdir / "rebuild.status").write_text("1\n")
        output, popen = _run()
        popen.assert_not_called()
        context = output["hookSpecificOutput"]["additionalContext"]
        assert "failed" in context
        assert str(gdir / "rebuild.log") in context

    @pytest.mark.unit
    def test_held_lock_while_a_rebuild_runs_stays_silent(self, project: Path) -> None:
        gdir = _graph(project, "1.0.0")
        (gdir / "rebuild.lock").write_text(str(time.time()))
        output, _ = _run()
        assert output is None

    @pytest.mark.unit
    def test_a_new_rebuild_clears_the_last_status(self, project: Path) -> None:
        gdir = _graph(project, "1.0.0")
        (gdir / "rebuild.status").write_text("1\n")
        _run()
        assert not (gdir / "rebuild.status").exists()


@pytest.mark.unit
class TestVersionsThatDoNotParse:
    """A version such as 1.10.4rc1 or dev raised ValueError at SessionStart."""

    @pytest.mark.parametrize("built", ["1.10.4rc1", "dev", ""])
    def test_unparseable_built_version_counts_as_older(self, built: str) -> None:
        assert hook._older(built, "1.10.4") is True

    @pytest.mark.parametrize("installed", ["1.10.5rc1", "dev"])
    def test_unparseable_installed_version_is_not_newer(self, installed: str) -> None:
        assert hook._older("1.10.4", installed) is False

    def test_session_start_survives_a_prerelease_graph_stamp(
        self, project: Path
    ) -> None:
        _graph(project, "1.10.4rc1")
        _, popen = _run()
        popen.assert_called_once()
