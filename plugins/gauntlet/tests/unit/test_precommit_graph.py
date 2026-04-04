"""Tests for graph-aware blast radius in precommit hook."""

from __future__ import annotations

# Import the hook's internal function directly
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

_HOOKS_DIR = Path(__file__).resolve().parents[2] / "hooks"
sys.path.insert(0, str(_HOOKS_DIR))

from gauntlet.graph import GraphStore  # noqa: E402 - sys.path modified above
from gauntlet.models import GraphNode, NodeKind  # noqa: E402 - sys.path modified above
from precommit_gate import _graph_risk_context  # noqa: E402 - sys.path modified above


@pytest.fixture()
def gauntlet_dir(tmp_path: Path) -> Path:
    d = tmp_path / ".gauntlet"
    d.mkdir()
    return d


@pytest.fixture()
def graph_with_nodes(gauntlet_dir: Path) -> GraphStore:
    db = gauntlet_dir / "graph.db"
    store = GraphStore(str(db))
    store.upsert_node(
        GraphNode(
            kind=NodeKind.FUNCTION,
            qualified_name="app.py::handler",
            file_path="app.py",
            line_start=1,
            line_end=20,
        )
    )
    store.rebuild_fts()
    yield store
    store.close()


class TestGraphRiskContext:
    """
    Feature: Graph-aware risk context in precommit

    As a developer committing code
    I want to see blast radius warnings
    So that I know about high-risk changes before commit
    """

    @pytest.mark.unit
    def test_returns_none_when_no_graph_db(self, gauntlet_dir: Path) -> None:
        """
        Scenario: No graph.db exists
        Given .gauntlet/ has no graph.db
        When precommit checks for risk
        Then None is returned (no warning)
        """
        result = _graph_risk_context(gauntlet_dir)
        assert result is None

    @pytest.mark.unit
    def test_returns_none_when_low_risk(
        self, gauntlet_dir: Path, graph_with_nodes: GraphStore
    ) -> None:
        """
        Scenario: Changes are low risk
        Given a graph exists but git diff shows no changes
        When precommit checks for risk
        Then None is returned
        """
        with patch(
            "gauntlet.blast_radius.subprocess.run",
            side_effect=FileNotFoundError,
        ):
            result = _graph_risk_context(gauntlet_dir)
        # No git = no diff = "none" risk = None
        assert result is None

    @pytest.mark.unit
    def test_returns_warning_when_high_risk(
        self, gauntlet_dir: Path, graph_with_nodes: GraphStore
    ) -> None:
        """
        Scenario: High-risk changes detected
        Given a graph with analyze_changes returning high risk
        When precommit checks for risk
        Then a warning string is returned
        """
        mock_report = {
            "overall_risk": "high",
            "review_priorities": [
                {"qualified_name": "app.py::handler", "kind": "Function"},
            ],
            "risk_scores": {"app.py::handler": 0.85},
            "untested_functions": ["app.py::handler"],
        }
        with patch(
            "precommit_gate.gauntlet.blast_radius.analyze_changes",
            return_value=mock_report,
        ):
            result = _graph_risk_context(gauntlet_dir)
        assert result is not None
        assert "high risk" in result
        assert "handler" in result
        assert "untested" in result.lower()
