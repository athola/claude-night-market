"""Tests for blast radius analysis and risk scoring."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from gauntlet.blast_radius import (
    _DEFAULT_WEIGHTS,
    SECURITY_KEYWORDS,
    GitDiffError,
    analyze_changes,
    compute_risk_score,
    load_weights,
    map_changes_to_nodes,
    parse_git_diff_ranges,
)
from gauntlet.graph import GraphStore
from gauntlet.incremental import full_build
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
        assert len(result["app.py"]) == 1
        assert result["app.py"][0] == (10, 14)

    @pytest.mark.unit
    def test_skips_deletion_only_hunks(self) -> None:
        """
        Scenario: Deletion-only hunks (count=0) are skipped
        Given a diff with a pure deletion hunk
        When I parse it
        Then the deletion hunk is excluded from ranges
        """
        diff_output = (
            "diff --git a/app.py b/app.py\n"
            "--- a/app.py\n"
            "+++ b/app.py\n"
            "@@ -5,3 +5,0 @@ def foo():\n"
            "-removed line 1\n"
            "-removed line 2\n"
            "-removed line 3\n"
        )
        with patch("gauntlet.blast_radius.subprocess.run") as mock_run:
            mock_run.return_value = type(
                "R", (), {"returncode": 0, "stdout": diff_output}
            )()
            result = parse_git_diff_ranges("HEAD")
        assert result.get("app.py", []) == []

    @pytest.mark.unit
    def test_raises_when_git_is_missing(self) -> None:
        """
        Scenario: git not available
        Given subprocess fails
        When I parse
        Then GitDiffError is raised, so a failure is not read as no changes
        """
        with patch(
            "gauntlet.blast_radius.subprocess.run",
            side_effect=FileNotFoundError,
        ):
            with pytest.raises(GitDiffError):
                parse_git_diff_ranges()

    @pytest.mark.unit
    def test_raises_when_git_diff_exits_nonzero(self) -> None:
        with patch("gauntlet.blast_radius.subprocess.run") as mock_run:
            mock_run.return_value = type("R", (), {"returncode": 128, "stdout": ""})()
            with pytest.raises(GitDiffError, match="128"):
                parse_git_diff_ranges("HEAD")


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
        config = tmp_path / "config.json"
        config.write_text(
            json.dumps({"risk_weights": {"test_gap": 0.50, "security": 0.10}})
        )
        weights = load_weights(tmp_path)
        assert weights["test_gap"] == 0.50
        assert weights["security"] == 0.10
        assert weights["flow_participation"] == 0.25  # default kept

    @pytest.mark.unit
    @pytest.mark.parametrize("body", ["[]", '"text"', "7", '{"risk_weights": [1]}'])
    def test_config_that_is_not_an_object_falls_back_to_defaults(
        self, tmp_path: Path, body: str, caplog: pytest.LogCaptureFixture
    ) -> None:
        """A list or scalar config.json is reported and the defaults apply."""
        (tmp_path / "config.json").write_text(body)
        with caplog.at_level("WARNING", logger="gauntlet.blast_radius"):
            weights = load_weights(tmp_path)
        assert weights == _DEFAULT_WEIGHTS
        assert "config.json" in caplog.text

    @pytest.mark.unit
    def test_survives_malformed_json(self, tmp_path: Path) -> None:
        """Bad JSON returns defaults without crashing."""
        config = tmp_path / "config.json"
        config.write_text("not json {{{")
        weights = load_weights(tmp_path)
        assert weights == _DEFAULT_WEIGHTS


class TestImpactRadiusBatchQuery:
    """GAT-001: impact_radius resolves nodes via batch SELECT IN, not N get_node calls."""

    @pytest.mark.unit
    def test_impact_radius_does_not_call_get_node(self, store: GraphStore) -> None:
        """
        Scenario: Batch resolution replaces per-node get_node calls
        Given 3 nodes connected by CALLS edges
        When impact_radius is called
        Then get_node is never invoked (batch SELECT IN used instead)
        """
        for i in range(3):
            store.upsert_node(
                GraphNode(
                    kind=NodeKind.FUNCTION,
                    qualified_name=f"a.py::fn_{i}",
                    file_path="a.py",
                    line_start=i * 10 + 1,
                    line_end=i * 10 + 5,
                )
            )
        store.upsert_edge(
            GraphEdge(
                kind=EdgeKind.CALLS, source_qn="a.py::fn_0", target_qn="a.py::fn_1"
            )
        )
        store.upsert_edge(
            GraphEdge(
                kind=EdgeKind.CALLS, source_qn="a.py::fn_1", target_qn="a.py::fn_2"
            )
        )
        get_node_calls: list[str] = []
        _original = store.get_node

        def _counting(qn: str) -> object:
            get_node_calls.append(qn)
            return _original(qn)

        store.get_node = _counting  # type: ignore[method-assign]  # call-tracking spy: instance attr shadows class method
        result = store.impact_radius(["a.py"], depth=3)
        assert get_node_calls == [], f"Expected 0 calls; got {get_node_calls}"
        assert {n.qualified_name for n in result} == {
            "a.py::fn_0",
            "a.py::fn_1",
            "a.py::fn_2",
        }

    @pytest.mark.unit
    def test_impact_radius_batch_handles_large_visited_set(
        self, store: GraphStore
    ) -> None:
        """
        Scenario: 500 visited nodes don't crash (chunked IN query required)
        Given 500 isolated nodes in big.py
        When impact_radius is called
        Then all 500 are returned
        """
        for i in range(500):
            store.upsert_node(
                GraphNode(
                    kind=NodeKind.FUNCTION,
                    qualified_name=f"big.py::fn_{i}",
                    file_path="big.py",
                    line_start=i * 10 + 1,
                    line_end=i * 10 + 5,
                )
            )
        result = store.impact_radius(["big.py"], depth=1)
        assert len(result) == 500


class TestLoadWeightsReportsMalformedConfig:
    """A typo in .gauntlet/config.json must be distinguishable from no config."""

    def test_malformed_weights_warn_and_fall_back(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """The operator's typo is named in a warning; defaults still apply."""
        (tmp_path / "config.json").write_text('{"risk_weights": {"security": "lots"}}')
        with caplog.at_level("WARNING"):
            weights = load_weights(tmp_path)
        assert weights == load_weights(None)
        assert any("config.json" in rec.message for rec in caplog.records)


#: Repository top level the analyze_changes tests report from rev-parse.
#: The graph stores absolute paths under it, as graph_build does.
_TOP = "/repo"


class TestAnalyzeChangesPipeline:
    """
    Feature: End-to-end blast radius analysis

    As the precommit gate
    I want one call that turns a diff into a risk verdict
    So that a commit can be held on what it actually touched.
    """

    @staticmethod
    def _diff(path: str, start: int, count: int) -> str:
        """Build a unified diff naming one changed hunk."""
        return (
            f"diff --git a/{path} b/{path}\n"
            f"--- a/{path}\n"
            f"+++ b/{path}\n"
            f"@@ -{start},{count} +{start},{count} @@\n"
            "+changed\n"
        )

    @staticmethod
    def _git(diff: str):
        """Answer git diff with ``diff`` and rev-parse with ``_TOP``."""

        def run(argv: list[str], **_kwargs: object) -> object:
            stdout = _TOP + "\n" if argv[1] == "rev-parse" else diff
            return type("R", (), {"returncode": 0, "stdout": stdout})()

        return run

    @pytest.mark.unit
    def test_an_empty_diff_reports_no_risk_without_touching_the_graph(
        self, store: GraphStore
    ) -> None:
        """
        Scenario: nothing changed
        Given a diff that names no file
        When changes are analyzed
        Then the verdict is 'none' with empty collections

        The gate branches on this verdict, so a commit touching nothing
        must not be scored against whatever the graph last held.
        """
        with patch("gauntlet.blast_radius.subprocess.run") as mock_run:
            mock_run.return_value = type("R", (), {"returncode": 0, "stdout": ""})()
            result = analyze_changes(store)

        assert result["overall_risk"] == "none"
        assert result["affected_nodes"] == []
        assert result["risk_scores"] == {}
        assert result["review_priorities"] == []

    @pytest.mark.unit
    def test_unknown_repository_root_reports_an_error_not_a_verdict(
        self, store: GraphStore
    ) -> None:
        """
        Scenario: git diff succeeds but rev-parse --show-toplevel fails
        Then the verdict is 'unknown' with the git error attached

        Without the root the diff paths cannot be matched to the graph's
        absolute paths, and an empty match would read as 'low' risk.
        """
        diff = self._diff("app.py", 10, 5)

        def run(argv: list[str], **_kwargs: object) -> object:
            failed = argv[1] == "rev-parse"
            return type("R", (), {"returncode": 128 if failed else 0, "stdout": diff})()

        with patch("gauntlet.blast_radius.subprocess.run", side_effect=run):
            result = analyze_changes(store)

        assert result["overall_risk"] == "unknown"
        assert "rev-parse" in result["error"]

    @staticmethod
    def _timed_git(diff_seconds: float, clock: list[float], timeouts: dict):
        """Answer git like ``_git``; the diff call advances ``clock``.

        A zero or negative budget raises TimeoutExpired, as subprocess.run
        does once its deadline has passed.
        """

        def run(argv: list[str], *, timeout: float, **_kwargs: object) -> object:
            timeouts[argv[1]] = timeout
            if timeout <= 0:
                raise subprocess.TimeoutExpired(argv, timeout)
            if argv[1] == "diff":
                clock[0] += diff_seconds
                stdout = TestAnalyzeChangesPipeline._diff("app.py", 10, 5)
            else:
                stdout = _TOP + "\n"
            return type("R", (), {"returncode": 0, "stdout": stdout})()

        return run

    @pytest.mark.unit
    def test_rev_parse_gets_only_the_budget_the_diff_left(
        self, store: GraphStore
    ) -> None:
        """The two git calls share one deadline, not one each."""
        clock = [100.0]
        timeouts: dict[str, float] = {}
        run = self._timed_git(3.2, clock, timeouts)
        with (
            patch("gauntlet.blast_radius.time.monotonic", lambda: clock[0]),
            patch("gauntlet.blast_radius.subprocess.run", side_effect=run),
        ):
            analyze_changes(store, timeout=4.0)

        assert timeouts["diff"] == 4.0
        assert timeouts["rev-parse"] == pytest.approx(0.8)

    @pytest.mark.unit
    def test_a_spent_budget_reports_an_error_without_running_rev_parse_long(
        self, store: GraphStore
    ) -> None:
        """A diff that used the whole budget leaves rev-parse 0.0, not a hang."""
        clock = [100.0]
        timeouts: dict[str, float] = {}
        run = self._timed_git(5.0, clock, timeouts)
        with (
            patch("gauntlet.blast_radius.time.monotonic", lambda: clock[0]),
            patch("gauntlet.blast_radius.subprocess.run", side_effect=run),
        ):
            result = analyze_changes(store, timeout=4.0)

        assert timeouts["rev-parse"] == 0.0
        assert result["overall_risk"] == "unknown"
        assert "rev-parse" in result["error"]

    @pytest.mark.unit
    def test_an_untested_changed_function_is_reported_and_scored(
        self, store: GraphStore
    ) -> None:
        """
        Scenario: a changed function that no test covers
        Given a function at lines 10-20 with no TESTED_BY edge
        When changes overlapping it are analyzed
        Then it appears in untested_functions and carries a risk score

        untested_functions is the list the gate shows a developer, and
        an entry missing from it is a change nobody is asked about.
        """
        store.upsert_node(
            GraphNode(
                kind=NodeKind.FUNCTION,
                qualified_name="app.py::process",
                file_path=f"{_TOP}/app.py",
                line_start=10,
                line_end=20,
            )
        )

        with patch("gauntlet.blast_radius.subprocess.run") as mock_run:
            mock_run.side_effect = self._git(self._diff("app.py", 10, 5))
            result = analyze_changes(store)

        assert result["untested_functions"] == ["app.py::process"]
        assert result["risk_scores"]["app.py::process"] > 0
        assert result["direct_changes"] == 1
        assert result["total_affected"] >= 1

    @pytest.mark.unit
    def test_configured_risk_weights_reach_the_scores(self, store: GraphStore) -> None:
        """
        Scenario: a user overrides risk weights in .gauntlet/config.json
        Given an untested function, scored once with defaults and once with
          test_gap raised to 0.9
        Then the configured weight changes its score

        load_weights promised per-key overrides, but analyze_changes never
        called it, so every run scored with the defaults.
        """
        store.upsert_node(
            GraphNode(
                kind=NodeKind.FUNCTION,
                qualified_name="app.py::process",
                file_path=f"{_TOP}/app.py",
                line_start=10,
                line_end=20,
            )
        )
        diff = self._diff("app.py", 10, 5)
        with patch("gauntlet.blast_radius.subprocess.run") as mock_run:
            mock_run.side_effect = self._git(diff)
            default = analyze_changes(store)["risk_scores"]["app.py::process"]
            heavy = analyze_changes(
                store, weights={**load_weights(None), "test_gap": 0.9}
            )
        assert heavy["risk_scores"]["app.py::process"] > default

    @pytest.mark.unit
    def test_a_tested_function_is_left_out_of_the_untested_list(
        self, store: GraphStore
    ) -> None:
        """
        Scenario: a changed function a test covers
        Given the same function with a TESTED_BY edge
        When changes overlapping it are analyzed
        Then it is absent from untested_functions

        Reporting a covered function as untested trains the reader to
        ignore the list, which costs more than the list gains. The BFS
        still pulls the test function itself into the affected set, and
        that node has no TESTED_BY edge of its own, so the list is not
        empty: the assertion names the changed function rather than the
        length.
        """
        store.upsert_node(
            GraphNode(
                kind=NodeKind.FUNCTION,
                qualified_name="app.py::process",
                file_path=f"{_TOP}/app.py",
                line_start=10,
                line_end=20,
            )
        )
        store.upsert_node(
            GraphNode(
                kind=NodeKind.FUNCTION,
                qualified_name="test_app.py::test_process",
                file_path=f"{_TOP}/test_app.py",
                line_start=1,
                line_end=5,
            )
        )
        store.upsert_edge(
            GraphEdge(
                kind=EdgeKind.TESTED_BY,
                source_qn="app.py::process",
                target_qn="test_app.py::test_process",
            )
        )

        with patch("gauntlet.blast_radius.subprocess.run") as mock_run:
            mock_run.side_effect = self._git(self._diff("app.py", 10, 5))
            result = analyze_changes(store)

        assert "app.py::process" not in result["untested_functions"]

    @pytest.mark.unit
    def test_review_priorities_are_ordered_by_risk_and_capped_at_ten(
        self, store: GraphStore
    ) -> None:
        """
        Scenario: a change touching more nodes than the report shows
        Given twelve changed functions in one file
        When changes are analyzed
        Then ten entries come back, highest risk first

        The cap keeps the gate's output readable; the ordering is what
        makes the truncation safe to do at all.
        """
        for i in range(12):
            store.upsert_node(
                GraphNode(
                    kind=NodeKind.FUNCTION,
                    qualified_name=f"app.py::fn_{i}",
                    file_path=f"{_TOP}/app.py",
                    line_start=10 * (i + 1),
                    line_end=10 * (i + 1) + 5,
                )
            )

        with patch("gauntlet.blast_radius.subprocess.run") as mock_run:
            mock_run.side_effect = self._git(self._diff("app.py", 1, 200))
            result = analyze_changes(store)

        priorities = result["review_priorities"]
        scores = [result["risk_scores"][n["qualified_name"]] for n in priorities]
        assert len(priorities) == 10
        assert scores == sorted(scores, reverse=True)


class TestAnalyzeChangesOnABuiltGraph:
    """
    Feature: blast radius over a graph built the way production builds it

    graph_build.py resolves the root and stores absolute file paths, while
    git diff names files relative to the repository top level. Every test
    above stores relative paths, the one form production never writes.
    """

    @staticmethod
    def _git(repo: Path, *args: str) -> None:
        subprocess.run(
            [
                "git",
                "-c",
                "user.email=t@example.com",
                "-c",
                "user.name=t",
                "-c",
                "commit.gpgsign=false",
                *args,
            ],
            cwd=repo,
            check=True,
            capture_output=True,
        )

    @pytest.mark.unit
    def test_edited_function_is_a_direct_change_in_a_full_build_graph(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Scenario: edit a function after a full build
        Given a git repo whose graph came from full_build on the resolved root
        When foo() is edited and analyze_changes runs against HEAD
        Then foo is a direct change and appears among the affected nodes
        """
        repo = (tmp_path / "repo").resolve()
        repo.mkdir()
        module = repo / "m.py"
        module.write_text("def foo():\n    return 1\n\n\ndef bar():\n    return 2\n")
        self._git(repo, "init", "-q")
        self._git(repo, "add", "m.py")
        self._git(repo, "commit", "-q", "-m", "init")

        graph = GraphStore(tmp_path / "graph.db")
        try:
            full_build(str(repo), graph)
            module.write_text(
                "def foo():\n    return 42\n\n\ndef bar():\n    return 2\n"
            )
            monkeypatch.chdir(repo)
            report = analyze_changes(graph, "HEAD")
        finally:
            graph.close()

        affected = {n["qualified_name"] for n in report["affected_nodes"]}
        assert report["direct_changes"] == 1
        assert any(qn.endswith("::foo") for qn in affected)
