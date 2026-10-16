"""Tests for PostToolUse community refresh hook."""

from __future__ import annotations

import json
import subprocess
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
        self,
        gauntlet_dir: Path,
        graph_with_data: GraphStore,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """A payload in the harness's real shape must reach the refresh.

        This replaces a test that fed ``{"exitCode": 1}`` and asserted None.
        It passed for the wrong reason: the hook read ``tool_result``, a key
        the payload never carries, so ``exitCode`` always defaulted to 1 and
        the hook returned None on every invocation. Asserting the positive
        case is what discriminates, because the negative case held whether
        the hook worked or not.
        """
        monkeypatch.chdir(gauntlet_dir.parent)
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
        self,
        gauntlet_dir: Path,
        graph_with_data: GraphStore,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """
        Scenario: graph_build.py succeeds and graph.db exists
        Given a populated graph
        When graph_build.py completes successfully
        Then community detection runs and returns context
        """
        monkeypatch.chdir(gauntlet_dir.parent)
        result = main(
            {
                "tool_name": "Bash",
                "tool_input": {"command": "python3 scripts/graph_build.py ."},
                "tool_response": _bash_response("{}"),
            }
        )
        assert result is not None
        hook_output = result["hookSpecificOutput"]
        assert hook_output["hookEventName"] == "PostToolUse"
        assert "Communities refreshed" in hook_output["additionalContext"]
        assert "clusters" in hook_output["additionalContext"]

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
        self,
        gauntlet_dir: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """
        Scenario: Community detection raises an exception
        Given graph_build.py succeeds but graph.db cannot be opened
        When community detection fails
        Then None is returned and error is logged to stderr
        """
        # A directory named graph.db passes the exists() walk but sqlite
        # cannot open it, which is the real failure the handler guards.
        (gauntlet_dir / "graph.db").mkdir()
        monkeypatch.chdir(gauntlet_dir.parent)
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


class TestGraphDiscovery:
    """The hook finds graph.db by walking up from the working directory."""

    @pytest.mark.unit
    def test_returns_none_when_no_graph_db_above_cwd(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        result = main(
            {
                "tool_name": "Bash",
                "tool_input": {"command": "python3 scripts/graph_build.py ."},
                "tool_response": _bash_response(""),
            }
        )
        assert result is None

    @pytest.mark.unit
    def test_finds_graph_db_in_an_ancestor_directory(
        self,
        gauntlet_dir: Path,
        graph_with_data: GraphStore,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        nested = gauntlet_dir.parent / "pkg" / "sub"
        nested.mkdir(parents=True)
        monkeypatch.chdir(nested)
        result = main(
            {
                "tool_name": "Bash",
                "tool_input": {"command": "python3 scripts/graph_build.py ."},
                "tool_response": _bash_response(""),
            }
        )
        assert result is not None
        hook_output = result["hookSpecificOutput"]
        assert hook_output["hookEventName"] == "PostToolUse"
        assert "Communities refreshed" in hook_output["additionalContext"]

    @pytest.mark.unit
    def test_prefers_gauntlet_src_beside_the_graph_db(
        self,
        gauntlet_dir: Path,
        graph_with_data: GraphStore,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """A project that vendors gauntlet in ./src is put on sys.path first."""
        local_src = gauntlet_dir.parent / "src"
        (local_src / "gauntlet").mkdir(parents=True)
        monkeypatch.setattr(sys, "path", list(sys.path))
        monkeypatch.chdir(gauntlet_dir.parent)
        main(
            {
                "tool_name": "Bash",
                "tool_input": {"command": "python3 scripts/graph_build.py ."},
                "tool_response": _bash_response(""),
            }
        )
        assert sys.path[0] == str(local_src)


class TestScriptEntryPoint:
    """Run as the harness runs it: JSON on stdin, JSON or nothing on stdout."""

    _SCRIPT = _HOOKS_DIR / "graph_community_refresh.py"

    def _run(self, stdin: str, cwd: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(self._SCRIPT)],
            input=stdin,
            capture_output=True,
            text=True,
            cwd=cwd,
            check=False,
            timeout=30,
        )

    @pytest.mark.unit
    def test_malformed_stdin_exits_zero_with_no_output(self, tmp_path: Path) -> None:
        proc = self._run("not json", tmp_path)
        assert proc.returncode == 0
        assert proc.stdout == ""

    @pytest.mark.unit
    def test_non_object_payload_is_logged_and_not_raised(self, tmp_path: Path) -> None:
        """A JSON list makes main() raise; the entry point logs it and exits 0."""
        proc = self._run("[]", tmp_path)
        assert proc.returncode == 0
        assert proc.stdout == ""
        assert proc.stderr.startswith("graph_community_refresh: ")

    @pytest.mark.unit
    def test_context_is_printed_as_json(
        self, gauntlet_dir: Path, graph_with_data: GraphStore
    ) -> None:
        payload = json.dumps(
            {
                "tool_name": "Bash",
                "tool_input": {"command": "python3 scripts/graph_build.py ."},
                "tool_response": _bash_response(""),
            }
        )
        proc = self._run(payload, gauntlet_dir.parent)
        assert proc.returncode == 0
        hook_output = json.loads(proc.stdout)["hookSpecificOutput"]
        assert hook_output["hookEventName"] == "PostToolUse"
        assert "Communities refreshed" in hook_output["additionalContext"]


class TestGraphStoreIsAlwaysClosed:
    """A failing detector must not leak the open sqlite connection."""

    @pytest.mark.unit
    def test_store_is_closed_when_community_detection_raises(
        self,
        gauntlet_dir: Path,
        graph_with_data: GraphStore,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        closed: list[bool] = []
        real_close = GraphStore.close

        def recording_close(self: GraphStore) -> None:
            closed.append(True)
            real_close(self)

        monkeypatch.chdir(gauntlet_dir.parent)
        with (
            patch(
                "gauntlet.communities.detect_communities",
                side_effect=RuntimeError("boom"),
            ),
            patch.object(GraphStore, "close", recording_close),
        ):
            result = main(
                {
                    "tool_name": "Bash",
                    "tool_input": {"command": "python3 scripts/graph_build.py ."},
                    "tool_response": _bash_response(""),
                }
            )

        assert result is None
        assert closed == [True]
