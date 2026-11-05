"""Regression tests for the bug-review sweep over pensive."""

from __future__ import annotations

import ast
import subprocess
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest
from pr_blast_radius import main as blast_radius_main

from gauntlet.graph import GraphStore
from pensive.harden import detectors_python
from pensive.harden.scanner import scan_directory
from pensive.skills.test_review import TestReviewSkill
from pensive.skills.tiered_audit import EscalationFlag, Tier1Results
from pensive.utils.severity_mapper import categorize


class TestEscalationTargets:
    """Commit-level flags name no area, so they are not escalation targets."""

    @pytest.mark.unit
    def test_commit_level_flags_add_no_blank_target(self) -> None:
        results = Tier1Results(
            fix_flags=[
                EscalationFlag(area="", reason="fix-on-fix", detail="abc1234: fix x")
            ],
            large_diff_flags=[
                EscalationFlag(area="", reason="large-diff", detail="def5678: big")
            ],
            new_cluster_flags=[
                EscalationFlag(area="pkg/mod", reason="new-file-cluster", detail="5")
            ],
        )

        assert results.escalation_targets() == ["pkg/mod"]


class TestBddStepGrouping:
    """A scenario missing one step keyword must not drop the others."""

    @pytest.mark.unit
    def test_unequal_step_counts_keep_every_given_and_then(self) -> None:
        content = (
            "@given('a cart')\n"
            "@when('it is priced')\n"
            "@then('total is 5')\n"
            "@given('an empty cart')\n"
            "@then('total is 0')\n"
        )
        context = Mock()
        context.get_file_content.return_value = content

        analysis = TestReviewSkill().analyze_bdd_patterns(context, "test_cart.py")

        steps = analysis["given_when_then"]
        assert [s["given"] for s in steps] == ["a cart", "an empty cart"]
        assert [s["then"] for s in steps] == ["total is 5", "total is 0"]


class TestSeverityNeverDowngrades:
    """A description keyword may raise a type's severity but never lower it."""

    @pytest.mark.unit
    def test_high_keyword_does_not_lower_a_critical_type(self) -> None:
        [issue] = categorize(
            [
                {
                    "type": "sql_injection",
                    "issue": "user input reaches a high-traffic query",
                }
            ]
        )

        assert issue["severity"] == "critical"


class TestHardenScanSurvivesNonUtf8Sources:
    """One Latin-1 file must not abort the scan of the whole tree."""

    @pytest.mark.unit
    def test_file_with_coding_cookie_is_scanned(self, tmp_path) -> None:
        (tmp_path / "legacy.py").write_bytes(
            "# -*- coding: latin-1 -*-\nname = 'caf\xe9'\n".encode("latin-1")
        )

        assert scan_directory(tmp_path) == []

    @pytest.mark.unit
    def test_undecodable_file_is_reported_not_raised(self, tmp_path) -> None:
        (tmp_path / "bad.py").write_bytes(b"name = 'caf\xe9'\n")
        (tmp_path / "ok.py").write_text("import os\nos.system('ls')\n")

        findings = scan_directory(tmp_path)

        assert any(f.id == "PYSX" and f.file.endswith("bad.py") for f in findings)

    @pytest.mark.unit
    def test_null_byte_file_is_reported_not_raised(self, tmp_path) -> None:
        (tmp_path / "nul.py").write_bytes(b"x = 1\x00\n")

        findings = scan_directory(tmp_path)

        assert [f.id for f in findings] == ["PYSX"]

    @pytest.mark.unit
    def test_parser_value_error_is_reported_not_raised(
        self, tmp_path, monkeypatch
    ) -> None:
        # Python 3.12+ raises SyntaxError for a null byte, so the file above
        # never reaches the ValueError branch there. Python 3.9 to 3.11 raise
        # ValueError, which this reproduces on any interpreter.
        def parse_rejecting_null_bytes(*_args, **_kwargs):
            raise ValueError("source code string cannot contain null bytes")

        # Patch the parser the detector module sees, not the global ast
        # module, which pytest itself uses to report failures.
        parser = SimpleNamespace(
            parse=parse_rejecting_null_bytes, walk=ast.walk, Call=ast.Call
        )
        monkeypatch.setattr(detectors_python, "ast", parser)
        (tmp_path / "nul.py").write_bytes(b"x = 1\x00\n")

        findings = scan_directory(tmp_path)

        assert [(f.id, f.line) for f in findings] == [("PYSX", 0)]
        assert "null bytes" in findings[0].detection_signal


class TestBlastRadiusContextShape:
    """PreToolUse context belongs under hookSpecificOutput."""

    @pytest.mark.unit
    def test_pr_create_context_is_nested(self, tmp_path, monkeypatch) -> None:
        # The hook diffs against the merge base with origin/HEAD, so the
        # project must be a repository whose clone refs name a default branch.
        for argv in (
            ["init", "-q", "-b", "master"],
            ["commit", "-q", "--allow-empty", "-m", "init"],
            ["update-ref", "refs/remotes/origin/master", "HEAD"],
            ["symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/master"],
        ):
            subprocess.run(
                [
                    "git",
                    "-c",
                    "user.email=t@example.com",
                    "-c",
                    "user.name=t",
                    "-c",
                    "commit.gpgsign=false",
                    *argv,
                ],
                cwd=tmp_path,
                check=True,
                capture_output=True,
            )
        monkeypatch.chdir(tmp_path)
        db_path = tmp_path / ".gauntlet" / "graph.db"
        db_path.parent.mkdir()
        GraphStore(str(db_path)).close()
        report = {
            "overall_risk": "medium",
            "total_affected": 8,
            "review_priorities": [],
            "risk_scores": {},
            "untested_functions": [],
        }

        with patch("gauntlet.blast_radius.analyze_changes", return_value=report):
            result = blast_radius_main(
                {"tool_input": {"command": "gh pr create --title t"}}
            )

        assert result is not None
        assert "additionalContext" not in result
        output = result["hookSpecificOutput"]
        assert output["hookEventName"] == "PreToolUse"
        assert "medium risk" in output["additionalContext"]
