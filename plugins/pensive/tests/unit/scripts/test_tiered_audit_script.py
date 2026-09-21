"""Tests for scripts/tiered_audit.py, the Tier 1 git-history runner.

The checks in ``pensive.skills.tiered_audit`` had thresholds nobody
could apply, because the skill told the model to eyeball raw git output.
The script is the seam that feeds real git history into them.
"""

from __future__ import annotations

import json
import subprocess
from typing import TYPE_CHECKING

import pytest
from scripts.tiered_audit import _parse_numstat, collect, main

if TYPE_CHECKING:
    from pathlib import Path


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, text=True, check=True
    ).stdout.strip()


def _commit(repo: Path, message: str) -> str:
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", message)
    return _git(repo, "rev-parse", "HEAD")


@pytest.fixture
def noisy_repo(tmp_path: Path) -> tuple[Path, str]:
    """A repository whose history trips all four Tier 1 signals.

    Returns the repo and the base commit to audit from.
    """
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "audit@example.invalid")
    _git(repo, "config", "user.name", "Audit")
    (repo / "README.md").write_text("# demo\n")
    base = _commit(repo, "chore: seed")

    module = repo / "pkg" / "mod"
    module.mkdir(parents=True)
    for index in range(6):
        (module / f"f{index}.py").write_text(f"VALUE = {index}\n")
    _commit(repo, "feat: add pkg")

    for round_number in range(3):
        (module / "f0.py").write_text(f"VALUE = {round_number + 10}\n")
        (module / f"f{round_number + 1}.py").write_text("VALUE = 99\n")
        _commit(repo, f"fix: patch f0 again ({round_number})")

    (module / "f5.py").write_text(
        "\n".join(f"LINE_{i} = {i}" for i in range(250)) + "\n"
    )
    _commit(repo, "refactor: rewrite f5")
    return repo, base


class TestCollect:
    """Feature: git history becomes typed flags."""

    def test_every_signal_fires_on_the_noisy_history(
        self, noisy_repo: tuple[Path, str]
    ) -> None:
        """Churn, fix-on-fix, large diff, and new-file cluster all flag."""
        repo, base = noisy_repo
        results, evidence = collect(base, repo)
        reasons = {flag.reason for flag in results.all_flags()}
        assert reasons == {"churn", "fix-on-fix", "large-diff", "new-file-cluster"}
        assert results.escalation_targets()[0] == "pkg/mod"
        assert evidence["churn"].startswith("git log --format= --name-only")

    def test_a_quiet_history_has_no_flags(self, tmp_path: Path) -> None:
        """One small commit above base produces nothing to escalate."""
        repo = tmp_path / "quiet"
        repo.mkdir()
        _git(repo, "init", "-q", "-b", "main")
        _git(repo, "config", "user.email", "audit@example.invalid")
        _git(repo, "config", "user.name", "Audit")
        (repo / "a.py").write_text("x = 1\n")
        base = _commit(repo, "chore: seed")
        (repo / "a.py").write_text("x = 2\n")
        _commit(repo, "feat: bump")
        results, _ = collect(base, repo)
        assert results.all_flags() == []


class TestNumstatParsing:
    """Feature: per-commit insertion and deletion totals."""

    def test_binary_rows_are_skipped_and_commits_are_summed(self) -> None:
        """A commit with two text files and one binary sums the text rows."""
        raw = "abc\x00feat: two files\n10\t2\ta.py\n-\t-\timg.png\n5\t5\tb.py\n"
        assert _parse_numstat(raw) == [("abc", "feat: two files", 15, 7)]


class TestCommandLine:
    """Feature: the skill runs one command and cites its output."""

    def test_json_mode_reports_escalation(
        self, noisy_repo: tuple[Path, str], capsys: pytest.CaptureFixture[str]
    ) -> None:
        """--json carries the flags, the targets, and the escalate verdict."""
        repo, base = noisy_repo
        assert main(["--base", base, "--cwd", str(repo), "--json"]) == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload["escalate"] is True
        assert "pkg/mod" in payload["escalation_targets"]
        assert len(payload["flags"]) >= 4

    def test_markdown_mode_matches_the_findings_sections(
        self, noisy_repo: tuple[Path, str], capsys: pytest.CaptureFixture[str]
    ) -> None:
        """The default output uses the section names the findings file expects."""
        repo, base = noisy_repo
        assert main(["--base", base, "--cwd", str(repo)]) == 0
        out = capsys.readouterr().out
        for heading in (
            "## Churn Hotspots",
            "## Fix-on-Fix Patterns",
            "## New File Clusters",
            "## Large Diffs",
        ):
            assert heading in out
        assert "[E1] Command: git log" in out
        assert "Escalate to Tier 2: yes" in out

    def test_a_bad_base_fails_with_git_error(
        self, noisy_repo: tuple[Path, str], capsys: pytest.CaptureFixture[str]
    ) -> None:
        """An unknown ref is reported, not swallowed."""
        repo, _ = noisy_repo
        assert main(["--base", "no-such-ref", "--cwd", str(repo)]) == 1
        assert "git failed" in capsys.readouterr().err
