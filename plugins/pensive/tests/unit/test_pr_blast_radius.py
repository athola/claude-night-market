"""Tests for PreToolUse PR blast radius hook."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from pr_blast_radius import main

from gauntlet.graph import GraphStore
from gauntlet.incremental import full_build

_HOOK_SCRIPT = Path(__file__).resolve().parents[2] / "hooks" / "pr_blast_radius.py"

_MEDIUM_REPORT = {
    "overall_risk": "medium",
    "total_affected": 8,
    "review_priorities": [
        {"qualified_name": "api.py::handle_request"},
    ],
    "risk_scores": {"api.py::handle_request": 0.55},
    "untested_functions": ["api.py::handle_request"],
}


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
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
        text=True,
    ).stdout.strip()


def _init_repo_with_origin(repo: Path) -> None:
    """A git repo on branch ``feature`` whose origin/HEAD names origin/master.

    No remote is contacted: the remote-tracking refs are written directly,
    which is the state a clone leaves behind.
    """
    _git(repo, "init", "-q", "-b", "master")
    (repo / ".gitignore").write_text(".gauntlet/\n")
    _git(repo, "add", ".gitignore")
    _git(repo, "commit", "-q", "-m", "init")
    _git(repo, "update-ref", "refs/remotes/origin/master", "HEAD")
    _git(
        repo,
        "symbolic-ref",
        "refs/remotes/origin/HEAD",
        "refs/remotes/origin/master",
    )
    _git(repo, "checkout", "-q", "-b", "feature")


@pytest.fixture()
def project_with_graph(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A git project holding an empty .gauntlet/graph.db, used as cwd.

    The hook locates graph.db by walking up from the working directory, so
    the tests set the directory rather than patching the lookup. It is a
    git repository with an origin/HEAD because the hook diffs the branch
    against its merge base with the PR base.
    """
    _init_repo_with_origin(tmp_path)
    gauntlet_dir = tmp_path / ".gauntlet"
    gauntlet_dir.mkdir()
    GraphStore(str(gauntlet_dir / "graph.db")).close()
    monkeypatch.chdir(tmp_path)
    return tmp_path


class TestPrBlastRadiusHook:
    """
    Feature: Blast radius context on PR creation

    As a developer creating a PR
    I want to see the blast radius of my changes
    So that I include risk context in my PR description
    """

    @pytest.mark.unit
    def test_ignores_non_pr_commands(self, project_with_graph: Path) -> None:
        """Non-PR commands are ignored even when a graph exists."""
        with patch(
            "gauntlet.blast_radius.analyze_changes", return_value=_MEDIUM_REPORT
        ) as analyze:
            result = main(
                {
                    "tool_input": {"command": "git push origin main"},
                }
            )
        assert result is None
        analyze.assert_not_called()

    @pytest.mark.unit
    def test_ignores_when_no_graph(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Missing graph.db means no context."""
        monkeypatch.chdir(tmp_path)
        with patch("gauntlet.blast_radius.analyze_changes") as analyze:
            result = main(
                {
                    "tool_input": {"command": "gh pr create --title 'test'"},
                }
            )
        assert result is None
        analyze.assert_not_called()

    @pytest.mark.unit
    def test_finds_graph_db_from_a_subdirectory(
        self, project_with_graph: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        nested = project_with_graph / "src" / "pkg"
        nested.mkdir(parents=True)
        monkeypatch.chdir(nested)
        with patch(
            "gauntlet.blast_radius.analyze_changes", return_value=_MEDIUM_REPORT
        ):
            result = main({"tool_input": {"command": "gh pr create"}})
        assert result is not None

    @pytest.mark.unit
    def test_returns_context_on_pr_create(self, project_with_graph: Path) -> None:
        """
        Scenario: PR creation with graph available
        Given a graph.db exists and analysis returns medium risk
        When gh pr create is run
        Then additionalContext includes risk summary
        """
        with patch(
            "gauntlet.blast_radius.analyze_changes",
            return_value=_MEDIUM_REPORT,
        ):
            result = main(
                {
                    "tool_input": {"command": "gh pr create --title 'feat: new api'"},
                }
            )

        assert result is not None
        ctx = result["hookSpecificOutput"]["additionalContext"]
        assert "medium risk" in ctx
        assert "8 nodes" in ctx
        assert "0.55 handle_request" in ctx
        assert "1 untested function(s)" in ctx

    @pytest.mark.unit
    def test_skips_context_when_git_diff_failed(
        self, project_with_graph: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """A report carrying ``error`` (git failed) adds no risk context."""
        failed_report = {
            "overall_risk": "unknown",
            "total_affected": 0,
            "review_priorities": [],
            "risk_scores": {},
            "untested_functions": [],
            "error": "git diff HEAD exited with 128",
        }

        with patch(
            "gauntlet.blast_radius.analyze_changes",
            return_value=failed_report,
        ):
            result = main({"tool_input": {"command": "gh pr create"}})

        assert result is None
        assert "exited with 128" in capsys.readouterr().err

    @pytest.mark.unit
    def test_handles_gh_pr_submit(self, project_with_graph: Path) -> None:
        """``gh pr submit`` triggers the same analysis as ``gh pr create``."""
        with patch(
            "gauntlet.blast_radius.analyze_changes", return_value=_MEDIUM_REPORT
        ):
            result = main(
                {
                    "tool_input": {"command": "gh pr submit"},
                }
            )
        assert result is not None
        assert "medium risk" in result["hookSpecificOutput"]["additionalContext"]

    @pytest.mark.unit
    @pytest.mark.parametrize("exc", [OSError("disk gone"), ValueError("bad weights")])
    def test_analysis_failure_is_logged_and_adds_no_context(
        self,
        project_with_graph: Path,
        capsys: pytest.CaptureFixture[str],
        exc: Exception,
    ) -> None:
        with patch("gauntlet.blast_radius.analyze_changes", side_effect=exc):
            result = main({"tool_input": {"command": "gh pr create"}})
        assert result is None
        assert f"analysis failed: {exc}" in capsys.readouterr().err

    @pytest.mark.unit
    def test_missing_gauntlet_package_adds_no_context(
        self, project_with_graph: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Gauntlet is an optional sibling; without it the hook stays silent."""
        monkeypatch.setitem(sys.modules, "gauntlet.blast_radius", None)
        result = main({"tool_input": {"command": "gh pr create"}})
        assert result is None


class TestPrBaseRef:
    """
    Feature: the PR's changes are the branch's commits, not the work tree

    At ``gh pr create`` the branch is committed and the tree is usually
    clean, so diffing against HEAD reported no change for every PR.
    """

    @pytest.mark.unit
    def test_diffs_against_the_merge_base_with_the_default_branch(
        self, project_with_graph: Path
    ) -> None:
        (project_with_graph / "m.py").write_text("def foo():\n    return 1\n")
        _git(project_with_graph, "add", "m.py")
        _git(project_with_graph, "commit", "-q", "-m", "feature")
        merge_base = _git(project_with_graph, "merge-base", "HEAD", "origin/master")

        with patch(
            "gauntlet.blast_radius.analyze_changes", return_value=_MEDIUM_REPORT
        ) as analyze:
            main({"tool_input": {"command": "gh pr create --title t"}})

        assert analyze.call_args.kwargs["base_ref"] == merge_base

    @pytest.mark.unit
    @pytest.mark.parametrize("flag", ["--base develop", "-B develop", "--base=develop"])
    def test_explicit_base_branch_selects_its_merge_base(
        self, project_with_graph: Path, flag: str
    ) -> None:
        _git(project_with_graph, "update-ref", "refs/remotes/origin/develop", "HEAD")
        (project_with_graph / "m.py").write_text("x = 1\n")
        _git(project_with_graph, "add", "m.py")
        _git(project_with_graph, "commit", "-q", "-m", "feature")
        develop = _git(project_with_graph, "rev-parse", "origin/develop")
        _git(project_with_graph, "update-ref", "refs/remotes/origin/master", "HEAD")

        with patch(
            "gauntlet.blast_radius.analyze_changes", return_value=_MEDIUM_REPORT
        ) as analyze:
            main({"tool_input": {"command": f"gh pr create {flag} --title t"}})

        assert analyze.call_args.kwargs["base_ref"] == develop

    @pytest.mark.unit
    def test_unknown_merge_base_adds_no_context(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Outside a repo with an origin/HEAD the hook says why and stays out."""
        (tmp_path / ".gauntlet").mkdir()
        GraphStore(str(tmp_path / ".gauntlet" / "graph.db")).close()
        monkeypatch.chdir(tmp_path)
        with patch("gauntlet.blast_radius.analyze_changes") as analyze:
            result = main({"tool_input": {"command": "gh pr create"}})
        assert result is None
        analyze.assert_not_called()
        assert "no merge base" in capsys.readouterr().err

    @pytest.mark.unit
    def test_unparseable_command_adds_no_context(
        self, project_with_graph: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """An unbalanced quote leaves the PR base unknown, so no report."""
        with patch("gauntlet.blast_radius.analyze_changes") as analyze:
            result = main({"tool_input": {"command": 'gh pr create --title "x'}})
        assert result is None
        analyze.assert_not_called()
        assert "no merge base" in capsys.readouterr().err

    @pytest.mark.unit
    def test_committed_branch_change_reaches_the_report_from_a_clean_tree(
        self, project_with_graph: Path
    ) -> None:
        """End to end: real graph, real git, committed edit, clean tree."""
        module = project_with_graph / "m.py"
        module.write_text("def foo():\n    return 1\n")
        _git(project_with_graph, "add", "m.py")
        _git(project_with_graph, "commit", "-q", "-m", "add foo")
        db = project_with_graph / ".gauntlet" / "graph.db"
        with GraphStore(str(db)) as graph:
            full_build(str(project_with_graph.resolve()), graph)
        assert _git(project_with_graph, "status", "--porcelain") == ""

        result = main({"tool_input": {"command": "gh pr create"}})

        assert result is not None
        context = result["hookSpecificOutput"]["additionalContext"]
        assert "0 nodes affected" not in context
        assert "foo" in context


class TestScriptEntryPoint:
    """Run as the harness runs it: JSON on stdin, JSON or nothing on stdout."""

    @staticmethod
    def _run(stdin: str, cwd: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(_HOOK_SCRIPT)],
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
    def test_non_pr_command_prints_nothing(self, tmp_path: Path) -> None:
        proc = self._run(json.dumps({"tool_input": {"command": "ls"}}), tmp_path)
        assert proc.returncode == 0
        assert proc.stdout == ""
