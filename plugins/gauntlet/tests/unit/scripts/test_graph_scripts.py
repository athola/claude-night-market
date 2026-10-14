"""Tests for graph_build.py and graph_query.py CLI scripts."""

from __future__ import annotations

import argparse
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

pytest.importorskip("tree_sitter")

import graph_query  # noqa: E402 - after the tree_sitter skip guard

from gauntlet.graph import GraphStore  # noqa: E402 - after the tree_sitter skip guard

_SCRIPTS_DIR = Path(__file__).resolve().parents[3] / "scripts"


class TestGraphBuildScript:
    """
    Feature: Graph build CLI

    As a developer
    I want a CLI to build the code graph
    So that skills and agents can query it
    """

    @pytest.mark.unit
    def test_build_creates_graph_db(self, tmp_path: Path) -> None:
        """
        Scenario: Full build creates graph.db
        Given a directory with a Python file
        When I run graph_build.py
        Then .gauntlet/graph.db is created and report is valid JSON
        """
        (tmp_path / "hello.py").write_text("def greet():\n    pass\n")
        result = subprocess.run(
            [sys.executable, str(_SCRIPTS_DIR / "graph_build.py"), str(tmp_path)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, result.stderr
        report = json.loads(result.stdout)
        assert report["build_type"] == "full"
        assert report["files_parsed"] >= 1
        assert (tmp_path / ".gauntlet" / "graph.db").exists()

    @pytest.mark.unit
    def test_build_invalid_dir_fails(self, tmp_path: Path) -> None:
        """
        Scenario: Non-existent directory fails gracefully
        Given a path that doesn't exist
        When I run graph_build.py
        Then exit code is 1 and error JSON is returned
        """
        result = subprocess.run(
            [sys.executable, str(_SCRIPTS_DIR / "graph_build.py"), "/nonexistent"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 1
        output = json.loads(result.stdout)
        assert "error" in output


class TestGraphQueryScript:
    """
    Feature: Graph query CLI

    As a skill or agent
    I want a CLI to query the graph
    So that I can get structured JSON results
    """

    @pytest.mark.unit
    def test_status_action(self, tmp_path: Path) -> None:
        """
        Scenario: Status action returns graph metadata
        Given a built graph
        When I query with --action status
        Then node and edge counts are returned
        """
        # Build first
        (tmp_path / "app.py").write_text("def main():\n    pass\n")
        subprocess.run(
            [sys.executable, str(_SCRIPTS_DIR / "graph_build.py"), str(tmp_path)],
            capture_output=True,
            timeout=30,
        )
        db = str(tmp_path / ".gauntlet" / "graph.db")
        result = subprocess.run(
            [
                sys.executable,
                str(_SCRIPTS_DIR / "graph_query.py"),
                "--action",
                "status",
                "--db",
                db,
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0, result.stderr
        status = json.loads(result.stdout)
        assert "node_count" in status
        assert status["node_count"] > 0

    @pytest.mark.unit
    def test_search_action(self, tmp_path: Path) -> None:
        """
        Scenario: Search finds matching nodes
        Given a graph with a function named 'main'
        When I search for 'main'
        Then results include it
        """
        (tmp_path / "app.py").write_text("def main():\n    pass\n")
        subprocess.run(
            [sys.executable, str(_SCRIPTS_DIR / "graph_build.py"), str(tmp_path)],
            capture_output=True,
            timeout=30,
        )
        db = str(tmp_path / ".gauntlet" / "graph.db")
        result = subprocess.run(
            [
                sys.executable,
                str(_SCRIPTS_DIR / "graph_query.py"),
                "--action",
                "search",
                "--query",
                "main",
                "--db",
                db,
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout)
        assert data["count"] >= 1

    @pytest.mark.unit
    def test_missing_db_fails(self) -> None:
        """
        Scenario: Query without graph.db fails gracefully
        Given no graph.db exists
        When I query
        Then error JSON is returned
        """
        result = subprocess.run(
            [
                sys.executable,
                str(_SCRIPTS_DIR / "graph_query.py"),
                "--action",
                "status",
                "--db",
                "/nonexistent/graph.db",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 1
        assert "graph.db not found" in json.loads(result.stdout)["error"]


class TestGraphQueryInProcess:
    """
    Feature: graph_query argument routing and database discovery

    The subprocess tests above prove the happy paths end to end but are
    invisible to coverage. These run the same functions in process.
    """

    @pytest.mark.unit
    def test_search_without_query_returns_error(self, tmp_path: Path) -> None:
        graph = GraphStore(tmp_path / "graph.db")
        try:
            args = argparse.Namespace(action="search", query=None)
            assert graph_query._dispatch(args, graph) == {
                "error": "--query required for search action"
            }
        finally:
            graph.close()

    @pytest.mark.unit
    def test_unknown_action_returns_error(self, tmp_path: Path) -> None:
        graph = GraphStore(tmp_path / "graph.db")
        try:
            args = argparse.Namespace(action="bogus")
            assert graph_query._dispatch(args, graph) == {
                "error": "unknown action: bogus"
            }
        finally:
            graph.close()

    @pytest.mark.unit
    def test_find_db_walks_up_to_an_ancestor_gauntlet_dir(self, tmp_path: Path) -> None:
        db = tmp_path / ".gauntlet" / "graph.db"
        db.parent.mkdir()
        db.touch()
        nested = tmp_path / "a" / "b"
        nested.mkdir(parents=True)
        assert graph_query._find_db(str(nested)) == db

    @pytest.mark.unit
    def test_find_db_returns_none_without_a_gauntlet_dir(self, tmp_path: Path) -> None:
        assert graph_query._find_db(str(tmp_path)) is None


class TestABuildOfNothingIsNotAGreenBuild:
    """Feature: an empty graph is an error, not a report.

    A missing tree-sitter parser or a tree with no parseable sources
    produced a full report with ``nodes_created: 0`` and exit 0, and
    every downstream search then read ``count: 0`` as "not in the
    codebase". The Exit Criterion in graph-build's SKILL.md ("values are
    non-zero for non-empty codebases") had nothing enforcing it.
    """

    @pytest.mark.unit
    def test_full_build_with_no_sources_exits_nonzero(self, tmp_path: Path) -> None:
        (tmp_path / "notes.txt").write_text("nothing parseable here\n")
        result = subprocess.run(
            [sys.executable, str(_SCRIPTS_DIR / "graph_build.py"), str(tmp_path)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode != 0
        report = json.loads(result.stdout)
        assert "error" in report
        assert report["nodes_created"] == 0

    @pytest.mark.unit
    def test_a_known_symbol_is_indexed_and_found(self, tmp_path: Path) -> None:
        """
        Given one file with a distinctively named class and function
        When the graph is built
        Then nodes were created, which is the control a search may cite
        """
        (tmp_path / "known_symbol.py").write_text(
            "class PlantedCanaryRecord:\n    pass\n\n\ndef planted_canary_probe():\n    return PlantedCanaryRecord()\n"
        )
        result = subprocess.run(
            [sys.executable, str(_SCRIPTS_DIR / "graph_build.py"), str(tmp_path)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, result.stderr
        assert json.loads(result.stdout)["nodes_created"] >= 2


class TestGraphBuildStoresFlows:
    """
    Feature: A build persists the execution flows it traces

    blast_radius scores a node partly by the stored flows it appears in.
    A build that never stored any left that term at zero for every node.
    """

    @pytest.mark.unit
    def test_full_build_reports_and_stores_flows(self, tmp_path: Path) -> None:
        """
        Given a module whose entry point calls two levels deep
        When I run graph_build.py
        Then the report counts at least one stored flow
        And the flows table holds that many rows
        """
        (tmp_path / "chain.py").write_text(
            "def leaf():\n    return 1\n\n\n"
            "def middle():\n    return leaf()\n\n\n"
            "def entry():\n    return middle()\n"
        )
        result = subprocess.run(
            [sys.executable, str(_SCRIPTS_DIR / "graph_build.py"), str(tmp_path)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, result.stderr
        report = json.loads(result.stdout)
        assert report["flows_stored"] >= 1

        conn = sqlite3.connect(tmp_path / ".gauntlet" / "graph.db")
        try:
            stored = conn.execute("SELECT COUNT(*) FROM flows").fetchone()[0]
        finally:
            conn.close()
        assert stored == report["flows_stored"]

    @pytest.mark.unit
    def test_incremental_build_refreshes_flows(self, tmp_path: Path) -> None:
        """
        Given a built graph
        When I run an incremental update
        Then the report still carries a flows_stored count
        """
        (tmp_path / "chain.py").write_text(
            "def leaf():\n    return 1\n\n\ndef entry():\n    return leaf()\n"
        )
        subprocess.run(
            ["git", "init", "-q", str(tmp_path)], capture_output=True, check=True
        )
        subprocess.run(
            [sys.executable, str(_SCRIPTS_DIR / "graph_build.py"), str(tmp_path)],
            capture_output=True,
            text=True,
            timeout=30,
            check=True,
        )
        result = subprocess.run(
            [
                sys.executable,
                str(_SCRIPTS_DIR / "graph_build.py"),
                str(tmp_path),
                "--incremental",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, result.stderr
        assert "flows_stored" in json.loads(result.stdout)
