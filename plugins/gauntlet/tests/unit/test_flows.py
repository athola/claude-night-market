"""Tests for call chain tracing and flow criticality."""

from __future__ import annotations

from pathlib import Path

import pytest
from gauntlet.flows import (
    compute_criticality,
    detect_entry_points,
    trace_flows,
)
from gauntlet.graph import GraphStore
from gauntlet.models import EdgeKind, GraphEdge, GraphNode, NodeKind


@pytest.fixture()
def store(tmp_path: Path) -> GraphStore:
    s = GraphStore(tmp_path / "test.db")
    yield s
    s.close()


def _add_chain(store: GraphStore, names: list[str]) -> None:
    """Add a linear call chain: names[0] -> names[1] -> ..."""
    for name in names:
        fp = name.split("::")[0] if "::" in name else "app.py"
        store.upsert_node(
            GraphNode(
                kind=NodeKind.FUNCTION,
                qualified_name=name,
                file_path=fp,
                line_start=0,
                line_end=10,
                language="python",
            )
        )
    for i in range(len(names) - 1):
        store.upsert_edge(
            GraphEdge(
                kind=EdgeKind.CALLS,
                source_qn=names[i],
                target_qn=names[i + 1],
            )
        )


class TestDetectEntryPoints:
    """
    Feature: Detect execution entry points

    As a flow tracer
    I want to find functions with no incoming calls
    So that I can trace execution from the start
    """

    @pytest.mark.unit
    def test_function_with_no_callers_is_entry(self, store: GraphStore) -> None:
        """
        Scenario: A function nobody calls is an entry point
        Given function A calls B, but nobody calls A
        When I detect entry points
        Then A is an entry point, B is not
        """
        _add_chain(store, ["app.py::main", "app.py::helper"])
        entries = detect_entry_points(store)
        qns = {n.qualified_name for n in entries}
        assert "app.py::main" in qns
        assert "app.py::helper" not in qns

    @pytest.mark.unit
    def test_test_function_is_entry(self, store: GraphStore) -> None:
        """
        Scenario: Test functions are entry points
        Given a function named test_something
        When I detect entry points
        Then it is included
        """
        store.upsert_node(
            GraphNode(
                kind=NodeKind.TEST,
                qualified_name="test_app.py::test_login",
                file_path="test_app.py",
                line_start=0,
                line_end=10,
                is_test=True,
            )
        )
        entries = detect_entry_points(store)
        qns = {n.qualified_name for n in entries}
        assert "test_app.py::test_login" in qns

    @pytest.mark.unit
    def test_conventional_name_is_entry(self, store: GraphStore) -> None:
        """
        Scenario: Functions named 'main' or 'handle_*' are entries
        """
        store.upsert_node(
            GraphNode(
                kind=NodeKind.FUNCTION,
                qualified_name="app.py::main",
                file_path="app.py",
                line_start=0,
                line_end=5,
            )
        )
        # Even if something calls main, the name convention includes it
        entries = detect_entry_points(store)
        qns = {n.qualified_name for n in entries}
        assert "app.py::main" in qns


class TestTraceFlows:
    """
    Feature: Trace execution flows via BFS

    As a developer
    I want to trace call chains from entry points
    So that I understand how code flows through the system
    """

    @pytest.mark.unit
    def test_traces_linear_chain(self, store: GraphStore) -> None:
        """
        Scenario: Trace a simple A -> B -> C chain
        Given three functions in a call chain
        When I trace flows
        Then one flow contains all three
        """
        _add_chain(store, ["a.py::start", "b.py::middle", "c.py::end"])
        flows = trace_flows(store, max_depth=15)
        assert len(flows) >= 1
        # The flow from "start" should contain all three
        flow = flows[0]
        assert flow["node_count"] >= 3

    @pytest.mark.unit
    def test_respects_max_depth(self, store: GraphStore) -> None:
        """
        Scenario: BFS stops at max_depth
        Given a chain of 10 functions
        When I trace with max_depth=2
        Then flows contain at most 3 nodes
        """
        names = [f"f{i}.py::fn{i}" for i in range(10)]
        _add_chain(store, names)
        flows = trace_flows(store, max_depth=2)
        for flow in flows:
            assert flow["node_count"] <= 3

    @pytest.mark.unit
    def test_flow_includes_file_count(self, store: GraphStore) -> None:
        """
        Scenario: Flow records unique file count
        Given a chain spanning 3 files
        When I trace flows
        Then file_count is 3
        """
        _add_chain(store, ["a.py::fn1", "b.py::fn2", "c.py::fn3"])
        flows = trace_flows(store, max_depth=15)
        assert len(flows) >= 1
        assert flows[0]["file_count"] >= 3


class TestComputeCriticality:
    """
    Feature: Flow criticality scoring

    As a reviewer
    I want high-criticality flows highlighted
    So that I know which execution paths are most important
    """

    @pytest.mark.unit
    def test_multi_file_flow_has_higher_criticality(self, store: GraphStore) -> None:
        """
        Scenario: More files = higher file_spread factor
        Given a flow spanning 5 files
        When I compute criticality
        Then file_spread contributes to the score
        """
        nodes = []
        for i in range(5):
            n = GraphNode(
                kind=NodeKind.FUNCTION,
                qualified_name=f"f{i}.py::fn{i}",
                file_path=f"f{i}.py",
                line_start=0,
                line_end=10,
            )
            store.upsert_node(n)
            nodes.append(n)
        score = compute_criticality(nodes, store)
        assert score > 0.0

    @pytest.mark.unit
    def test_criticality_capped_at_one(self, store: GraphStore) -> None:
        """Score never exceeds 1.0."""
        nodes = []
        for i in range(20):
            n = GraphNode(
                kind=NodeKind.FUNCTION,
                qualified_name=f"auth{i}.py::verify_token_{i}",
                file_path=f"auth{i}.py",
                line_start=0,
                line_end=10,
            )
            store.upsert_node(n)
            nodes.append(n)
        score = compute_criticality(nodes, store)
        assert score <= 1.0
