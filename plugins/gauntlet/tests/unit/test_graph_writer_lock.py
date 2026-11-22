"""One writer at a time on .gauntlet/graph.db.

Only the SessionStart launcher took a lock, and only for itself. The
post-commit update checked that a lock file existed, and a manual build
took nothing, so two builds could write graph.db together and fail with
"database is locked". The lock now lives in graph_build.py itself, for
full and incremental builds alike, and the hooks only check it.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from gauntlet.build_lock import BUSY_EXIT_CODE, writer_busy, writer_lock

_SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "graph_build.py"


def _build(root: Path, *extra: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(_SCRIPT), str(root), *extra],
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.mark.unit
class TestWriterLock:
    """The lock is held for the life of a build and released when it ends."""

    def test_a_second_writer_in_another_open_is_refused(self, tmp_path: Path) -> None:
        with writer_lock(tmp_path) as first:
            assert first is True
            with writer_lock(tmp_path) as second:
                assert second is False
            assert writer_busy(tmp_path) is True
        assert writer_busy(tmp_path) is False

    def test_no_lock_file_reads_as_free(self, tmp_path: Path) -> None:
        assert writer_busy(tmp_path) is False


@pytest.mark.unit
class TestOverlappingBuilds:
    """A build that finds another writer exits busy and leaves the graph alone."""

    @pytest.mark.parametrize("mode", [(), ("--incremental",)])
    def test_build_exits_busy_while_another_writer_holds_the_lock(
        self, tmp_path: Path, mode: tuple[str, ...]
    ) -> None:
        (tmp_path / "mod.py").write_text("def f():\n    return 1\n")
        gauntlet_dir = tmp_path / ".gauntlet"
        gauntlet_dir.mkdir()
        with writer_lock(gauntlet_dir):
            completed = _build(tmp_path, *mode)
        assert completed.returncode == BUSY_EXIT_CODE, completed.stderr
        assert "another gauntlet graph build" in json.loads(completed.stdout)["error"]
        assert not (gauntlet_dir / "graph.db").exists()

    def test_build_runs_once_the_other_writer_ends(self, tmp_path: Path) -> None:
        pytest.importorskip("tree_sitter")
        (tmp_path / "mod.py").write_text("def f():\n    return 1\n")
        gauntlet_dir = tmp_path / ".gauntlet"
        gauntlet_dir.mkdir()
        with writer_lock(gauntlet_dir):
            assert _build(tmp_path).returncode == BUSY_EXIT_CODE
        completed = _build(tmp_path)
        assert completed.returncode == 0, completed.stdout + completed.stderr
        assert json.loads(completed.stdout)["nodes_created"] > 0
