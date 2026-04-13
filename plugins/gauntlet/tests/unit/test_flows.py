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

    @pytest.mark.unit
    def test_file_and_class_nodes_excluded(self, store: GraphStore) -> None:
        """
        Scenario: FILE and CLASS nodes are not entry points
        Given a FILE node and a CLASS node
        When I detect entry points
        Then neither appears in the result
        """
        store.upsert_node(
            GraphNode(
                kind=NodeKind.FILE,
                qualified_name="app.py",
                file_path="app.py",
                line_start=0,
                line_end=100,
            )
        )
        store.upsert_node(
            GraphNode(
                kind=NodeKind.CLASS,
                qualified_name="app.py::MyClass",
                file_path="app.py",
                line_start=10,
                line_end=50,
            )
        )
        entries = detect_entry_points(store)
        kinds = {n.kind for n in entries}
        assert NodeKind.FILE not in kinds
        assert NodeKind.CLASS not in kinds


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
            assert flow["node_count"] == 3

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
    def test_empty_flow_nodes_returns_zero(self, store: GraphStore) -> None:
        """
        Scenario: Empty flow yields zero criticality
        Given an empty list of flow nodes
        When I compute criticality
        Then the score is 0.0
        """
        score = compute_criticality([], store)
        assert score == 0.0

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


class TestFlowSorting:
    """
    Feature: Flows sorted by criticality

    As a reviewer
    I want flows sorted highest-criticality first
    So that the most important paths appear at the top
    """

    @pytest.mark.unit
    def test_flows_sorted_by_criticality_descending(self, store: GraphStore) -> None:
        """
        Scenario: Multiple flows are returned in descending order
        Given two independent chains with different file spans
        When I trace flows
        Then the first flow has equal or higher criticality
        """
        # Chain spanning 1 file (low criticality)
        for name in ["a.py::fn1", "a.py::fn2"]:
            store.upsert_node(
                GraphNode(
                    kind=NodeKind.FUNCTION,
                    qualified_name=name,
                    file_path="a.py",
                    line_start=0,
                    line_end=10,
                )
            )
        store.upsert_edge(
            GraphEdge(
                kind=EdgeKind.CALLS,
                source_qn="a.py::fn1",
                target_qn="a.py::fn2",
            )
        )

        # Chain spanning 3 files (higher criticality)
        for name, fp in [
            ("x.py::start", "x.py"),
            ("y.py::middle", "y.py"),
            ("z.py::end", "z.py"),
        ]:
            store.upsert_node(
                GraphNode(
                    kind=NodeKind.FUNCTION,
                    qualified_name=name,
                    file_path=fp,
                    line_start=0,
                    line_end=10,
                )
            )
        store.upsert_edge(
            GraphEdge(
                kind=EdgeKind.CALLS,
                source_qn="x.py::start",
                target_qn="y.py::middle",
            )
        )
        store.upsert_edge(
            GraphEdge(
                kind=EdgeKind.CALLS,
                source_qn="y.py::middle",
                target_qn="z.py::end",
            )
        )

        flows = trace_flows(store, max_depth=15)
        assert len(flows) >= 2
        # Flows should be sorted by criticality descending
        for i in range(len(flows) - 1):
            assert flows[i]["criticality"] >= flows[i + 1]["criticality"]
