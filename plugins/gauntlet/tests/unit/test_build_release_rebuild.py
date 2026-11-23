"""A build without a parser must say so, and every build records its version."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

import gauntlet
from gauntlet.graph import GraphStore
from gauntlet.incremental import full_build, incremental_update

_SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "graph_build.py"


@pytest.fixture()
def store(tmp_path: Path) -> GraphStore:
    s = GraphStore(tmp_path / "graph.db")
    yield s
    s.close()


class TestIncrementalWithoutParser:
    """A system python3 without tree-sitter once reported 1123 files parsed
    and wrote nothing, so a stale graph looked fresh.
    """

    @pytest.mark.unit
    def test_changed_file_without_parser_reports_an_error(
        self, tmp_path: Path, store: GraphStore
    ) -> None:
        src = tmp_path / "a.py"
        src.write_text("def a():\n    pass\n")
        with patch("gauntlet.incremental.get_changed_files", return_value=[str(src)]):
            with patch("gauntlet.incremental.parser_available", return_value=False):
                report = incremental_update(str(tmp_path), store)
        assert "tree-sitter" in report["error"]
        assert store.node_count() == 0
        assert store.get_metadata("last_build_type") is None

    @pytest.mark.unit
    def test_no_changes_without_parser_is_still_a_skip(
        self, tmp_path: Path, store: GraphStore
    ) -> None:
        with patch("gauntlet.incremental.get_changed_files", return_value=[]):
            with patch("gauntlet.incremental.parser_available", return_value=False):
                report = incremental_update(str(tmp_path), store)
        assert "skipped" in report
        assert "error" not in report

    @pytest.mark.unit
    def test_script_exits_nonzero_on_an_incremental_error(self, tmp_path: Path) -> None:
        # Not a git repository: the diff cannot be read and the report has an error
        result = subprocess.run(
            [sys.executable, str(_SCRIPT), str(tmp_path), "--incremental"],
            capture_output=True,
            text=True,
            check=False,
        )
        assert "error" in json.loads(result.stdout)
        assert result.returncode == 2


class TestBuildRecordsVersion:
    """The rebuild-on-release hook compares this key with the installed version."""

    @pytest.mark.unit
    def test_full_build_records_gauntlet_version(
        self, tmp_path: Path, store: GraphStore
    ) -> None:
        pytest.importorskip("tree_sitter")
        (tmp_path / "a.py").write_text("def a():\n    pass\n")
        full_build(str(tmp_path), store)
        assert store.get_metadata("gauntlet_version") == gauntlet.__version__

    @pytest.mark.unit
    def test_incremental_build_leaves_the_version_alone(
        self, tmp_path: Path, store: GraphStore
    ) -> None:
        # It re-parses only changed files; the rest still have the old shape.
        pytest.importorskip("tree_sitter")
        src = tmp_path / "a.py"
        src.write_text("def a():\n    pass\n")
        with patch("gauntlet.incremental.get_changed_files", return_value=[str(src)]):
            incremental_update(str(tmp_path), store)
        assert store.get_metadata("gauntlet_version") is None

    @pytest.mark.unit
    def test_full_build_that_created_nothing_records_no_version(
        self, tmp_path: Path, store: GraphStore
    ) -> None:
        full_build(str(tmp_path), store)
        assert store.get_metadata("gauntlet_version") is None


def _git(root: Path, *args: str) -> None:
    base = ["git", "-C", str(root), "-c", "user.email=t@t", "-c", "user.name=t"]
    subprocess.run([*base, *args], capture_output=True, check=True)


class TestIncrementalDiffsFromTheLastBuild:
    """On a clean tree an incremental diff against HEAD is empty, so a graph
    220 hours stale reported "no changes detected".
    """

    @pytest.mark.unit
    def test_incremental_after_a_commit_picks_up_the_committed_file(
        self, tmp_path: Path
    ) -> None:
        pytest.importorskip("tree_sitter")
        (tmp_path / "a.py").write_text("def a():\n    pass\n")
        _git(tmp_path, "init", "-q")
        _git(tmp_path, "add", "a.py")
        _git(tmp_path, "commit", "-qm", "one")
        build = [sys.executable, str(_SCRIPT), str(tmp_path)]
        subprocess.run(build, capture_output=True, check=True)

        (tmp_path / "b.py").write_text("def added_later():\n    pass\n")
        _git(tmp_path, "add", "b.py")
        _git(tmp_path, "commit", "-qm", "two")
        result = subprocess.run(
            [*build, "--incremental"], capture_output=True, text=True, check=False
        )

        assert result.returncode == 0, result.stdout
        graph = GraphStore(tmp_path / ".gauntlet" / "graph.db")
        try:
            nodes = graph.get_nodes_in_file(str(tmp_path / "b.py"))
            names = {n.qualified_name.rsplit("::", 1)[-1] for n in nodes}
        finally:
            graph.close()
        assert "added_later" in names

    @pytest.mark.unit
    def test_incremental_build_with_base_ref_does_not_stamp_past_unbuilt_commits(
        self, tmp_path: Path
    ) -> None:
        """A diff of HEAD~1 alone stamped HEAD, so the commit before it was
        never parsed and the next plain incremental reported no changes.
        """
        pytest.importorskip("tree_sitter")
        (tmp_path / "a.py").write_text("def a():\n    pass\n")
        _git(tmp_path, "init", "-q")
        _git(tmp_path, "add", "a.py")
        _git(tmp_path, "commit", "-qm", "c0")
        build = [sys.executable, str(_SCRIPT), str(tmp_path)]
        subprocess.run(build, capture_output=True, check=True)

        (tmp_path / "a.py").write_text(
            "def a():\n    pass\n\n\ndef gamma():\n    pass\n"
        )
        _git(tmp_path, "commit", "-qam", "c1")
        (tmp_path / "b.py").write_text("def delta():\n    pass\n")
        _git(tmp_path, "add", "b.py")
        _git(tmp_path, "commit", "-qm", "c2")
        subprocess.run(
            [*build, "--incremental", "--base-ref", "HEAD~1"],
            capture_output=True,
            check=True,
        )
        result = subprocess.run(
            [*build, "--incremental"], capture_output=True, text=True, check=False
        )

        assert result.returncode == 0, result.stdout
        graph = GraphStore(tmp_path / ".gauntlet" / "graph.db")
        try:
            nodes = graph.get_nodes_in_file(str(tmp_path / "a.py"))
            names = {n.qualified_name.rsplit("::", 1)[-1] for n in nodes}
        finally:
            graph.close()
        assert "gamma" in names


def _load_graph_build():

    spec = importlib.util.spec_from_file_location("graph_build_under_test", _SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestBuildBookkeeping:
    """GAU-6, GAU-7."""

    @pytest.mark.unit
    def test_hook_artifacts_are_gitignored(self, tmp_path: Path) -> None:
        """A legacy .gitignore left rebuild.lock and rebuild.log untracked."""
        gdir = tmp_path / ".gauntlet"
        gdir.mkdir()
        (gdir / ".gitignore").write_text("graph.db\n*.db-wal\n*.db-shm\n")
        (tmp_path / "a.py").write_text("def a():\n    pass\n")
        subprocess.run([sys.executable, str(_SCRIPT), str(tmp_path)], check=False)
        lines = (gdir / ".gitignore").read_text().splitlines()
        assert "rebuild.*" in lines
        assert "update.*" in lines
        assert lines.count("graph.db") == 1

    @pytest.mark.unit
    def test_head_recorded_is_the_one_seen_before_the_build(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A commit made during a long build was stamped as built, and its
        changes were never re-parsed.
        """
        module = _load_graph_build()
        built: list[bool] = []
        real_full_build = module.full_build

        def full_build(*args, **kwargs):
            report = real_full_build(*args, **kwargs)
            built.append(True)
            return report

        monkeypatch.setattr(module, "full_build", full_build)
        monkeypatch.setattr(
            module, "_head_commit", lambda _root: "after" if built else "before"
        )
        (tmp_path / "a.py").write_text("def a():\n    pass\n")
        monkeypatch.setattr(sys, "argv", ["graph_build.py", str(tmp_path)])
        module.main()
        db = GraphStore(tmp_path / ".gauntlet" / "graph.db")
        try:
            assert db.get_metadata("last_build_commit") == "before"
        finally:
            db.close()
