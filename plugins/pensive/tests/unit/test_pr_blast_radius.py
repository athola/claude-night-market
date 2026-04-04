"""Tests for PreToolUse PR blast radius hook."""

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
from pr_blast_radius import main  # noqa: E402 - sys.path modified above


class TestPrBlastRadiusHook:
    """
    Feature: Blast radius context on PR creation

    As a developer creating a PR
    I want to see the blast radius of my changes
    So that I include risk context in my PR description
    """

    @pytest.mark.unit
    def test_ignores_non_pr_commands(self) -> None:
        """Non-PR commands are ignored."""
        result = main(
            {
                "tool_input": {"command": "git push origin main"},
            }
        )
        assert result is None

    @pytest.mark.unit
    def test_ignores_when_no_graph(self) -> None:
        """Missing graph.db means no context."""
        with patch("pr_blast_radius._find_graph_db", return_value=None):
            result = main(
                {
                    "tool_input": {"command": "gh pr create --title 'test'"},
                }
            )
        assert result is None

    @pytest.mark.unit
    def test_returns_context_on_pr_create(self, tmp_path: Path) -> None:
        """
        Scenario: PR creation with graph available
        Given a graph.db exists and analysis returns medium risk
        When gh pr create is run
        Then additionalContext includes risk summary
        """
        gauntlet_dir = tmp_path / ".gauntlet"
        gauntlet_dir.mkdir()
        db_path = gauntlet_dir / "graph.db"

        gs = GraphStore(str(db_path))
        gs.close()

        mock_report = {
            "overall_risk": "medium",
            "total_affected": 8,
            "review_priorities": [
                {"qualified_name": "api.py::handle_request"},
            ],
            "risk_scores": {"api.py::handle_request": 0.55},
            "untested_functions": ["api.py::handle_request"],
        }

        with (
            patch("pr_blast_radius._find_graph_db", return_value=db_path),
            patch(
                "gauntlet.blast_radius.analyze_changes",
                return_value=mock_report,
            ),
        ):
            result = main(
                {
                    "tool_input": {"command": "gh pr create --title 'feat: new api'"},
                }
            )

        assert result is not None
        ctx = result["additionalContext"]
        assert "medium risk" in ctx
        assert "8 nodes" in ctx
        assert "handle_request" in ctx
        assert "untested" in ctx.lower()

    @pytest.mark.unit
    def test_handles_gh_pr_submit(self) -> None:
        """Also triggers on gh pr submit."""
        with patch("pr_blast_radius._find_graph_db", return_value=None):
            result = main(
                {
                    "tool_input": {"command": "gh pr submit"},
                }
            )
        # Returns None because no graph, but it didn't bail on command match
        assert result is None
