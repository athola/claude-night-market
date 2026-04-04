"""Tests for blast radius analysis and risk scoring."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from gauntlet.blast_radius import (
    _DEFAULT_WEIGHTS,
    SECURITY_KEYWORDS,
    compute_risk_score,
    load_weights,
    map_changes_to_nodes,
    parse_git_diff_ranges,
)
from gauntlet.graph import GraphStore
from gauntlet.models import EdgeKind, GraphEdge, GraphNode, NodeKind


@pytest.fixture()
def store(tmp_path: Path) -> GraphStore:
    s = GraphStore(tmp_path / "test.db")
    yield s
    s.close()


class TestParseGitDiffRanges:
    """
    Feature: Parse git diff for changed line ranges

    As a blast radius analyzer
    I want to know which lines changed in which files
    So that I can map changes to graph nodes
    """

    @pytest.mark.unit
    def test_parses_unified_diff(self) -> None:
        """
        Scenario: Parse a standard unified diff
        Given git diff output with hunk headers
        When I parse it
        Then file paths map to changed line ranges
        """
        diff_output = (
            "diff --git a/app.py b/app.py\n"
            "--- a/app.py\n"
            "+++ b/app.py\n"
            "@@ -10,3 +10,5 @@ def foo():\n"
            " context\n"
            "+added line 1\n"
            "+added line 2\n"
        )
        with patch("gauntlet.blast_radius.subprocess.run") as mock_run:
            mock_run.return_value = type(
                "R",
                (),
                {
                    "returncode": 0,
                    "stdout": diff_output,
                },
            )()
            result = parse_git_diff_ranges("HEAD")
        assert "app.py" in result
        assert len(result["app.py"]) >= 1

    @pytest.mark.unit
    def test_returns_empty_on_failure(self) -> None:
        """
        Scenario: git not available
        Given subprocess fails
        When I parse
        Then empty dict returned
        """
        with patch(
            "gauntlet.blast_radius.subprocess.run",
            side_effect=FileNotFoundError,
        ):
            result = parse_git_diff_ranges()
            assert result == {}


class TestMapChangesToNodes:
    """
    Feature: Map changed line ranges to graph nodes

    As a blast radius analyzer
    I want to find which code entities overlap with changes
    So that I know what was actually modified
    """

    @pytest.mark.unit
    def test_maps_overlapping_lines(self, store: GraphStore) -> None:
        """
        Scenario: Changed lines overlap a function's range
        Given a function at lines 10-20
        When lines 12-15 changed
        Then the function is in the result
        """
        store.upsert_node(
            GraphNode(
                kind=NodeKind.FUNCTION,
                qualified_name="app.py::process",
                file_path="app.py",
                line_start=10,
                line_end=20,
            )
        )
        ranges = {"app.py": [(12, 15)]}
        result = map_changes_to_nodes(store, ranges)
        qns = {n.qualified_name for n in result}
        assert "app.py::process" in qns

    @pytest.mark.unit
    def test_skips_non_overlapping(self, store: GraphStore) -> None:
        """
        Scenario: Changed lines don't overlap any node
        Given a function at lines 10-20
        When lines 1-5 changed
        Then the function is not in the result
        """
        store.upsert_node(
            GraphNode(
                kind=NodeKind.FUNCTION,
                qualified_name="app.py::process",
                file_path="app.py",
                line_start=10,
                line_end=20,
            )
        )
        ranges = {"app.py": [(1, 5)]}
        result = map_changes_to_nodes(store, ranges)
        assert len(result) == 0


class TestComputeRiskScore:
    """
    Feature: Risk scoring for changed nodes

    As a code reviewer
    I want high-risk changes flagged
    So that I focus review effort on risky areas
    """

    @pytest.mark.unit
    def test_untested_code_gets_high_score(self, store: GraphStore) -> None:
        """
        Scenario: Untested function has high risk
        Given a function with no TESTED_BY edge
        When I compute risk
        Then score >= 0.30 (test gap weight)
        """
        node = GraphNode(
            kind=NodeKind.FUNCTION,
            qualified_name="app.py::handler",
            file_path="app.py",
            line_start=1,
            line_end=10,
        )
        store.upsert_node(node)
        score = compute_risk_score(node, store)
        assert score >= 0.30

    @pytest.mark.unit
    def test_security_keyword_increases_score(self, store: GraphStore) -> None:
        """
        Scenario: Function with 'auth' in name gets security boost
        Given a function named authenticate_user
        When I compute risk
        Then score includes 0.20 security weight
        """
        node = GraphNode(
            kind=NodeKind.FUNCTION,
            qualified_name="app.py::authenticate_user",
            file_path="app.py",
            line_start=1,
            line_end=10,
        )
        store.upsert_node(node)
        score = compute_risk_score(node, store)
        # Untested (0.30) + security (0.20) = at least 0.50
        assert score >= 0.50

    @pytest.mark.unit
    def test_tested_code_has_lower_score(self, store: GraphStore) -> None:
        """
        Scenario: Tested function has lower risk
        Given a function with a TESTED_BY edge
        When I compute risk
        Then score is lower than untested equivalent
        """
        node = GraphNode(
            kind=NodeKind.FUNCTION,
            qualified_name="app.py::safe_fn",
            file_path="app.py",
            line_start=1,
            line_end=10,
        )
        store.upsert_node(node)
        store.upsert_edge(
            GraphEdge(
                kind=EdgeKind.TESTED_BY,
                source_qn="app.py::safe_fn",
                target_qn="test_app.py::test_safe_fn",
            )
        )
        score = compute_risk_score(node, store)
        assert score < 0.30  # Below untested weight

    @pytest.mark.unit
    def test_score_capped_at_one(self, store: GraphStore) -> None:
        """
        Scenario: Risk score never exceeds 1.0
        Given a worst-case node (untested, security, many callers)
        When I compute risk
        Then score <= 1.0
        """
        node = GraphNode(
            kind=NodeKind.FUNCTION,
            qualified_name="app.py::admin_login",
            file_path="app.py",
            line_start=1,
            line_end=50,
        )
        store.upsert_node(node)
        # Add many callers
        for i in range(30):
            store.upsert_edge(
                GraphEdge(
                    kind=EdgeKind.CALLS,
                    source_qn=f"x.py::caller_{i}",
                    target_qn="app.py::admin_login",
                )
            )
        score = compute_risk_score(node, store)
        assert score <= 1.0

    @pytest.mark.unit
    def test_custom_weights_applied(self, store: GraphStore) -> None:
        """
        Scenario: Custom weights change the score
        Given custom weights with test_gap=0.50
        When I compute risk for untested code
        Then score reflects the custom weight
        """
        node = GraphNode(
            kind=NodeKind.FUNCTION,
            qualified_name="app.py::plain_fn",
            file_path="app.py",
            line_start=1,
            line_end=10,
        )
        store.upsert_node(node)
        custom = dict(_DEFAULT_WEIGHTS)
        custom["test_gap"] = 0.50
        score = compute_risk_score(node, store, weights=custom)
        assert score >= 0.50

    @pytest.mark.unit
    def test_security_keywords_present(self) -> None:
        """Verify expected keywords exist in the set."""
        assert "auth" in SECURITY_KEYWORDS
        assert "password" in SECURITY_KEYWORDS
        assert "sql" in SECURITY_KEYWORDS


class TestLoadWeights:
    """
    Feature: Configurable risk weights

    As a project lead
    I want to tune risk scoring per project
    So that scoring reflects my team's priorities
    """

    @pytest.mark.unit
    def test_defaults_when_no_config(self, tmp_path: Path) -> None:
        """No config file returns defaults."""
        weights = load_weights(tmp_path)
        assert weights == _DEFAULT_WEIGHTS

    @pytest.mark.unit
    def test_defaults_when_none(self) -> None:
        """None gauntlet_dir returns defaults."""
        weights = load_weights(None)
        assert weights == _DEFAULT_WEIGHTS

    @pytest.mark.unit
    def test_reads_custom_weights(self, tmp_path: Path) -> None:
        """Custom weights override defaults."""
        import json

        config = tmp_path / "config.json"
        config.write_text(
            json.dumps({"risk_weights": {"test_gap": 0.50, "security": 0.10}})
        )
        weights = load_weights(tmp_path)
        assert weights["test_gap"] == 0.50
        assert weights["security"] == 0.10
        assert weights["flow_participation"] == 0.25  # default kept

    @pytest.mark.unit
    def test_survives_malformed_json(self, tmp_path: Path) -> None:
        """Bad JSON returns defaults without crashing."""
        config = tmp_path / "config.json"
        config.write_text("not json {{{")
        weights = load_weights(tmp_path)
        assert weights == _DEFAULT_WEIGHTS
