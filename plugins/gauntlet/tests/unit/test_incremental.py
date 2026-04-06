"""Tests for git-diff-based incremental graph updates."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

pytest.importorskip("tree_sitter")

from gauntlet.graph import GraphStore  # noqa: E402 - must follow importorskip
from gauntlet.incremental import (  # noqa: E402 - must follow importorskip
    _validate_ref,
    collect_files,
    find_dependents,
    full_build,
    get_changed_files,
    incremental_update,
)
from gauntlet.models import (  # noqa: E402 - must follow importorskip
    EdgeKind,
    GraphEdge,
    GraphNode,
    NodeKind,
)


@pytest.fixture()
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "test.db"


@pytest.fixture()
def store(db_path: Path) -> GraphStore:
    s = GraphStore(db_path)
    yield s
    s.close()


class TestValidateRef:
    """
    Feature: Git ref validation

    As a security-conscious tool
    I want to reject dangerous git ref strings
    So that command injection is prevented
    """

    @pytest.mark.unit
    def test_valid_ref_passes(self) -> None:
        assert _validate_ref("HEAD") == "HEAD"
        assert _validate_ref("main") == "main"
        assert _validate_ref("abc123") == "abc123"

    @pytest.mark.unit
    def test_rejects_double_dot(self) -> None:
        with pytest.raises(ValueError, match="unsafe"):
            _validate_ref("HEAD..main")

    @pytest.mark.unit
    def test_rejects_backtick(self) -> None:
        with pytest.raises(ValueError, match="unsafe"):
            _validate_ref("`rm -rf /`")

    @pytest.mark.unit
    def test_rejects_semicolon(self) -> None:
        with pytest.raises(ValueError, match="unsafe"):
            _validate_ref("HEAD; rm -rf /")

    @pytest.mark.unit
    def test_rejects_at_brace(self) -> None:
        with pytest.raises(ValueError, match="unsafe"):
            _validate_ref("HEAD@{0}")

    @pytest.mark.unit
    def test_rejects_pipe(self) -> None:
        """
        Scenario: Pipe character is rejected
        Given a ref containing '|'
        When I validate
        Then a ValueError is raised
        """
        with pytest.raises(ValueError, match="unsafe"):
            _validate_ref("HEAD|cat /etc/passwd")

    @pytest.mark.unit
    def test_rejects_ampersand(self) -> None:
        """
        Scenario: Ampersand character is rejected
        Given a ref containing '&'
        When I validate
        Then a ValueError is raised
        """
        with pytest.raises(ValueError, match="unsafe"):
            _validate_ref("HEAD&rm -rf /")


class TestGetChangedFiles:
    """
    Feature: Detect changed files via git diff

    As a graph updater
    I want to know which files changed since a ref
    So that I only re-parse those files
    """

    @pytest.mark.unit
    def test_returns_changed_files(self) -> None:
        """
        Scenario: git diff returns changed file paths
        Given git diff outputs two file paths
        When I call get_changed_files
        Then both paths are returned
        """
        mock_result = type(
            "R",
            (),
            {
                "returncode": 0,
                "stdout": "src/app.py\nsrc/lib.py\n",
            },
        )()
        with patch("gauntlet.incremental.subprocess.run", return_value=mock_result):
            result = get_changed_files("HEAD")
        assert result == ["src/app.py", "src/lib.py"]

    @pytest.mark.unit
    def test_returns_empty_on_git_failure(self) -> None:
        """
        Scenario: git is not available
        Given subprocess raises FileNotFoundError
        When I call get_changed_files
        Then an empty list is returned
        """
        with patch(
            "gauntlet.incremental.subprocess.run",
            side_effect=FileNotFoundError,
        ):
            result = get_changed_files()
        assert result == []


class TestFindDependents:
    """
    Feature: Find files that depend on a changed file

    As a graph updater
    I want to find importers of a changed file
    So that I re-parse them too
    """

    @pytest.mark.unit
    def test_finds_importers(self, store: GraphStore) -> None:
        """
        Scenario: File B imports from file A
        Given B has an IMPORTS_FROM edge targeting A
        When I call find_dependents for A
        Then B's file path is returned
        """
        store.upsert_node(
            GraphNode(
                kind=NodeKind.FILE,
                qualified_name="a.py",
                file_path="a.py",
                line_start=0,
                line_end=10,
            )
        )
        store.upsert_node(
            GraphNode(
                kind=NodeKind.FILE,
                qualified_name="b.py",
                file_path="b.py",
                line_start=0,
                line_end=10,
            )
        )
        store.upsert_edge(
            GraphEdge(
                kind=EdgeKind.IMPORTS_FROM,
                source_qn="b.py",
                target_qn="a.py",
                file_path="b.py",
            )
        )
        deps = find_dependents(store, "a.py")
        assert "b.py" in deps

    @pytest.mark.unit
    def test_no_self_dependency(self, store: GraphStore) -> None:
        """
        Scenario: A file should not list itself as a dependent
        Given a file with internal edges
        When I call find_dependents
        Then the file itself is not in the result
        """
        store.upsert_node(
            GraphNode(
                kind=NodeKind.FUNCTION,
                qualified_name="a.py::foo",
                file_path="a.py",
                line_start=0,
                line_end=5,
            )
        )
        store.upsert_node(
            GraphNode(
                kind=NodeKind.FUNCTION,
                qualified_name="a.py::bar",
                file_path="a.py",
                line_start=6,
                line_end=10,
            )
        )
        store.upsert_edge(
            GraphEdge(
                kind=EdgeKind.CALLS,
                source_qn="a.py::bar",
                target_qn="a.py::foo",
                file_path="a.py",
            )
        )
        deps = find_dependents(store, "a.py")
        assert "a.py" not in deps


class TestCollectFiles:
    """
    Feature: Collect parseable source files from a directory

    As a graph builder
    I want to find all supported source files
    So that I can parse them into the graph
    """

    @pytest.mark.unit
    def test_finds_python_files(self, tmp_path: Path) -> None:
        (tmp_path / "app.py").write_text("x = 1")
        (tmp_path / "data.json").write_text("{}")
        result = collect_files(str(tmp_path))
        assert any(f.endswith("app.py") for f in result)
        assert not any(f.endswith("data.json") for f in result)

    @pytest.mark.unit
    def test_skips_hidden_dirs(self, tmp_path: Path) -> None:
        hidden = tmp_path / ".hidden"
        hidden.mkdir()
        (hidden / "secret.py").write_text("x = 1")
        result = collect_files(str(tmp_path))
        assert not any(".hidden" in f for f in result)

    @pytest.mark.unit
    def test_skips_node_modules(self, tmp_path: Path) -> None:
        nm = tmp_path / "node_modules"
        nm.mkdir()
        (nm / "dep.js").write_text("var x = 1;")
        result = collect_files(str(tmp_path))
        assert not any("node_modules" in f for f in result)


class TestFullBuild:
    """
    Feature: Full graph build from directory

    As a developer
    I want to build a complete graph of my codebase
    So that I can query structural relationships
    """

    @pytest.mark.unit
    def test_builds_graph_from_directory(
        self, tmp_path: Path, store: GraphStore
    ) -> None:
        """
        Scenario: Parse all files in a directory
        Given a directory with two Python files
        When I run full_build
        Then nodes are created for both files
        """
        (tmp_path / "a.py").write_text("def hello():\n    pass\n")
        (tmp_path / "b.py").write_text("class Foo:\n    pass\n")
        report = full_build(str(tmp_path), store)
        assert report["build_type"] == "full"
        assert report["files_parsed"] == 2
        assert report["nodes_created"] > 0
        assert store.node_count() > 0


class TestIncrementalUpdate:
    """
    Feature: Incremental graph updates

    As a developer who just committed
    I want only changed files to be re-parsed
    So that updates are fast
    """

    @pytest.mark.unit
    def test_no_changes_returns_early(self, tmp_path: Path, store: GraphStore) -> None:
        """
        Scenario: No files changed
        Given git diff returns nothing
        When I run incremental_update
        Then zero files are parsed
        """
        with patch("gauntlet.incremental.get_changed_files", return_value=[]):
            report = incremental_update(str(tmp_path), store)
        assert report["files_parsed"] == 0
        assert "skipped" in report
