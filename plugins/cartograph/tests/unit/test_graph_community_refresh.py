"""Tests for PostToolUse community refresh hook."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

_HOOKS_DIR = Path(__file__).resolve().parents[2] / "hooks"
_GAUNTLET_SRC = Path(__file__).resolve().parents[3] / "gauntlet" / "src"
sys.path.insert(0, str(_HOOKS_DIR))
sys.path.insert(0, str(_GAUNTLET_SRC))

from gauntlet.graph import GraphStore  # noqa: E402 - sys.path modified above
from gauntlet.models import (  # noqa: E402 - sys.path modified above
    EdgeKind,
    GraphEdge,
    GraphNode,
    NodeKind,
)
from graph_community_refresh import main  # noqa: E402 - sys.path modified above


@pytest.fixture()
def gauntlet_dir(tmp_path: Path) -> Path:
    d = tmp_path / ".gauntlet"
    d.mkdir()
    return d


@pytest.fixture()
def graph_with_data(gauntlet_dir: Path) -> GraphStore:
    gs = GraphStore(str(gauntlet_dir / "graph.db"))
    for i in range(4):
        gs.upsert_node(
            GraphNode(
                kind=NodeKind.FUNCTION,
                qualified_name=f"mod{i}.py::fn{i}",
                file_path=f"mod{i}.py",
                line_start=0,
                line_end=10,
            )
        )
    gs.upsert_edge(
        GraphEdge(
            kind=EdgeKind.CALLS,
            source_qn="mod0.py::fn0",
            target_qn="mod1.py::fn1",
        )
    )
    yield gs
    gs.close()


class TestCommunityRefreshHook:
    """
    Feature: Auto-refresh communities after graph build

    As a developer
    I want communities to update when the graph rebuilds
    So that architecture analysis stays current
    """

    @pytest.mark.unit
    def test_ignores_non_graph_build_commands(self) -> None:
        """Non graph_build.py commands are ignored."""
        result = main(
            {
                "tool_name": "Bash",
                "tool_input": {"command": "git status"},
                "tool_result": {"exitCode": 0},
            }
        )
        assert result is None

    @pytest.mark.unit
    def test_ignores_failed_builds(self) -> None:
        """Failed graph_build.py runs are ignored."""
        result = main(
            {
                "tool_name": "Bash",
                "tool_input": {"command": "python3 scripts/graph_build.py ."},
                "tool_result": {"exitCode": 1},
            }
        )
        assert result is None

    @pytest.mark.unit
    def test_returns_context_on_success(
        self, gauntlet_dir: Path, graph_with_data: GraphStore
    ) -> None:
        """
        Scenario: graph_build.py succeeds and graph.db exists
        Given a populated graph
        When graph_build.py completes successfully
        Then community detection runs and returns context
        """
        with patch(
            "graph_community_refresh._find_graph_db",
            return_value=gauntlet_dir / "graph.db",
        ):
            result = main(
                {
                    "tool_name": "Bash",
                    "tool_input": {"command": "python3 scripts/graph_build.py ."},
                    "tool_result": {"exitCode": 0, "stdout": "{}"},
                }
            )
        assert result is not None
        assert "Communities refreshed" in result["additionalContext"]
        assert "clusters" in result["additionalContext"]

    @pytest.mark.unit
    def test_ignores_non_bash_tools(self) -> None:
        """Read, Write etc. are ignored."""
        result = main(
            {
                "tool_name": "Read",
                "tool_input": {},
            }
        )
        assert result is None
