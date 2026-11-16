"""A build without a parser must say so, and every build records its version."""

from __future__ import annotations

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
    def test_incremental_build_records_gauntlet_version(
        self, tmp_path: Path, store: GraphStore
    ) -> None:
        pytest.importorskip("tree_sitter")
        src = tmp_path / "a.py"
        src.write_text("def a():\n    pass\n")
        with patch("gauntlet.incremental.get_changed_files", return_value=[str(src)]):
            incremental_update(str(tmp_path), store)
        assert store.get_metadata("gauntlet_version") == gauntlet.__version__
