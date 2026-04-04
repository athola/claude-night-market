"""Tests for graph_build.py and graph_query.py CLI scripts."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

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
            ["python3", str(_SCRIPTS_DIR / "graph_build.py"), str(tmp_path)],
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
            ["python3", str(_SCRIPTS_DIR / "graph_build.py"), "/nonexistent"],
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
            ["python3", str(_SCRIPTS_DIR / "graph_build.py"), str(tmp_path)],
            capture_output=True,
            timeout=30,
        )
        db = str(tmp_path / ".gauntlet" / "graph.db")
        result = subprocess.run(
            [
                "python3",
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
            ["python3", str(_SCRIPTS_DIR / "graph_build.py"), str(tmp_path)],
            capture_output=True,
            timeout=30,
        )
        db = str(tmp_path / ".gauntlet" / "graph.db")
        result = subprocess.run(
            [
                "python3",
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
                "python3",
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
