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

from graph_community_refresh import main  # noqa: E402 - sys.path modified above

from gauntlet.graph import GraphStore  # noqa: E402 - sys.path modified above
from gauntlet.models import (  # noqa: E402 - sys.path modified above
    EdgeKind,
    GraphEdge,
    GraphNode,
    NodeKind,
)


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
                "tool_response": _bash_response(""),
            }
        )
        assert result is None

    @pytest.mark.unit
    def test_a_realistic_success_payload_is_not_discarded(
        self, gauntlet_dir: Path, graph_with_data: GraphStore
    ) -> None:
        """A payload in the harness's real shape must reach the refresh.

        This replaces a test that fed ``{"exitCode": 1}`` and asserted None.
        It passed for the wrong reason: the hook read ``tool_result``, a key
        the payload never carries, so ``exitCode`` always defaulted to 1 and
        the hook returned None on every invocation. Asserting the positive
        case is what discriminates, because the negative case held whether
        the hook worked or not.
        """
        with patch(
            "graph_community_refresh._find_graph_db",
            return_value=gauntlet_dir / "graph.db",
        ):
            result = main(
                {
                    "tool_name": "Bash",
                    "tool_input": {"command": "python3 scripts/graph_build.py ."},
                    "tool_response": _bash_response(""),
                }
            )
        assert result is not None

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
                    "tool_response": _bash_response("{}"),
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

    @pytest.mark.unit
    def test_exception_returns_none_and_logs(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """
        Scenario: Community detection raises an exception
        Given graph_build.py succeeds but graph.db is missing
        When community detection fails
        Then None is returned and error is logged to stderr
        """
        with patch(
            "graph_community_refresh._find_graph_db",
            return_value=Path("/nonexistent/graph.db"),
        ):
            result = main(
                {
                    "tool_name": "Bash",
                    "tool_input": {"command": "python3 scripts/graph_build.py ."},
                    "tool_response": _bash_response("{}"),
                }
            )
        assert result is None
        captured = capsys.readouterr()
        assert "community detection failed" in captured.err
