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


@pytest.fixture()
def project_with_graph(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A project root holding an empty .gauntlet/graph.db, used as cwd.

    The hook locates graph.db by walking up from the working directory, so
    the tests set the directory rather than patching the lookup.
    """
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
