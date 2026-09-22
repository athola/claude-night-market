"""Tests for scripts/tiered_audit.py, the Tier 1 git-history runner.

The checks in ``pensive.skills.tiered_audit`` had thresholds nobody
could apply, because the skill told the model to eyeball raw git output.
The script is the seam that feeds real git history into them.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest
from scripts.tiered_audit import _parse_numstat, collect, main

from pensive.skills.tiered_audit import Tier1Results


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


class TestOneModuleIdentity:
    """The checks used to be loaded by file path, registering the module
    twice: a Tier1Results built by the script was not an instance of the
    class a typed caller imported from the package.
    """

    def test_results_are_instances_of_the_package_class(self, noisy_repo) -> None:
        repo, base = noisy_repo
        results, _ = collect(base, cwd=repo)
        assert isinstance(results, Tier1Results)
        assert type(results).__module__ == "pensive.skills.tiered_audit"

    def test_the_checks_import_without_psutil_under_system_python(self) -> None:
        """The script runs under whatever python3 the skill has, which on
        macOS is 3.9 with no psutil. Importing the thresholds through the
        package must not pull in pensive.workflows.
        """
        interpreter = Path("/usr/bin/python3")
        if not interpreter.exists():
            pytest.skip("no system python")
        src = Path(__file__).resolve().parents[3] / "src"
        probe = (
            f"import sys; sys.path.insert(0, {str(src)!r}); "
            "import pensive.skills.tiered_audit; "
            "assert 'psutil' not in sys.modules, 'psutil imported'; "
            "assert 'pensive.workflows' not in sys.modules, 'workflows imported'"
        )
        run = subprocess.run(
            [str(interpreter), "-c", probe], capture_output=True, text=True, check=False
        )
        assert run.returncode == 0, run.stderr
        assert sys.version_info >= (3, 9)


class TestNewFileClusterSpan:
    """git diff with two dots compares endpoints, so a file added on the
    base branch after the fork point looked like a file this branch added.
    """

    def test_files_added_on_base_after_the_fork_are_not_counted(
        self, tmp_path: Path
    ) -> None:
        repo = tmp_path / "repo"
        repo.mkdir()
        _git(repo, "init", "-q", "-b", "main")
        _git(repo, "config", "user.email", "audit@example.invalid")
        _git(repo, "config", "user.name", "Audit")
        (repo / "README.md").write_text("# demo\n")
        _commit(repo, "chore: seed")
        _git(repo, "checkout", "-q", "-b", "feature")
        (repo / "feature.py").write_text("X = 1\n")
        _commit(repo, "feat: one file on the branch")
        _git(repo, "checkout", "-q", "main")
        cluster = repo / "pkg" / "mod"
        cluster.mkdir(parents=True)
        for index in range(6):
            (cluster / f"f{index}.py").write_text(f"VALUE = {index}\n")
        _commit(repo, "feat: six files on main after the fork")
        _git(repo, "checkout", "-q", "feature")

        results, _ = collect("main", cwd=repo)

        assert results.new_cluster_flags == []


class TestEscalationModuleMatchesTheScript:
    """The skill points readers at modules/escalation-criteria.md while the
    script prints its own verdict. Every criterion heading in the module
    is either a signal the script computes or is marked as a manual check.
    """

    def test_every_tier1_criterion_is_computed_or_marked_manual(self) -> None:

        module = (
            Path(__file__).resolve().parents[3]
            / "skills"
            / "tiered-audit"
            / "modules"
            / "escalation-criteria.md"
        )
        text = module.read_text(encoding="utf-8")
        tier1 = text.split("## Tier 2")[0]
        headings = re.findall(r"^### (.+)$", tier1, re.MULTILINE)
        computed = {
            "Churn Hotspots",
            "Fix-on-Fix Patterns",
            "Large Diffs",
            "New File Clusters",
        }
        for heading in headings:
            assert heading in computed or "(manual check)" in heading, heading
