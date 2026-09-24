"""Tests for scripts/pr_prep_analyze.py, the git front end to PRPrepAnalyzer.

PRPrepAnalyzer's methods took dictionaries no caller ever built, so the
pr-prep skill re-derived the same facts by hand. The script builds the
dictionaries from git and the tests prove the analyzer's answers reach
the shell.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from pr_prep_analyze import analyze, classify, collect, main

from sanctum.pr_prep import _is_test_path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "pr_prep_analyze.py"


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, text=True, check=True
    ).stdout.strip()


@pytest.fixture
def branch_repo(tmp_path: Path) -> tuple[Path, str]:
    """A repo with a base commit and one breaking feature commit above it."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "prep@example.invalid")
    _git(repo, "config", "user.name", "Prep")
    (repo / "src").mkdir()
    (repo / "src" / "api.py").write_text("def legacy():\n    return 1\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "chore: seed")
    base = _git(repo, "rev-parse", "HEAD")

    (repo / "src" / "api.py").write_text("def modern():\n    return 2\n")
    (repo / "tests").mkdir()
    (repo / "tests" / "test_api.py").write_text("def test_modern():\n    pass\n")
    (repo / "docs").mkdir()
    (repo / "docs" / "api.md").write_text("# API\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "feat!: replace legacy with modern")
    return repo, base


class TestClassify:
    """Feature: paths land in the bucket the analyzer expects."""

    @pytest.mark.parametrize(
        "path,bucket",
        [
            ("tests/test_x.py", "test"),
            ("plugins/a/tests/unit/test_y.py", "test"),
            ("src/test_helpers.py", "test"),
            ("docs/guide.md", "docs"),
            ("src/api.py", "feature"),
        ],
    )
    def test_buckets(self, path: str, bucket: str) -> None:
        """Test paths, doc suffixes, and everything else."""
        assert classify(path) == bucket

    @pytest.mark.parametrize(
        "path",
        [
            "src/api.py",
            "tests/test_x.py",
            "docs/guide.md",
            "Makefile",
            "plugins/a/x.json",
        ],
    )
    def test_the_bucket_vocabulary_is_closed(self, path: str) -> None:
        """classify never says "breaking", which is why no report line can.

        ``PRPrepAnalyzer.detect_breaking_changes`` populates
        ``affected_apis`` from files typed ``breaking``. This script is
        the only caller that builds those dicts, and it cannot emit that
        type, so the markdown carries no line for it.
        """
        assert classify(path) in {"test", "docs", "feature"}


class TestCollectAndAnalyze:
    """Feature: git history becomes the analyzer's context."""

    def test_the_breaking_feature_commit_is_fully_described(
        self, branch_repo: tuple[Path, str]
    ) -> None:
        """Categories, the `!` marker, gates and strategy all come from git."""
        repo, base = branch_repo
        context = collect(base, repo)
        assert {f["path"] for f in context["changed_files"]} == {
            "src/api.py",
            "tests/test_api.py",
            "docs/api.md",
        }
        assert context["commits"][0]["message"].startswith("feat!")

        report = analyze(context)
        assert report["categories"]["feature"] == ["src/api.py"]
        assert report["categories"]["test"] == ["tests/test_api.py"]
        assert report["categories"]["docs"] == ["docs/api.md"]
        assert report["breaking"]["has_breaking_changes"] is True
        assert report["quality_gates"]["has_tests"] is True
        assert report["quality_gates"]["has_documentation"] is True
        assert report["merge_strategy"]["strategy"] == "squash"

    def test_gates_the_script_cannot_check_stay_unevaluated(
        self, branch_repo: tuple[Path, str]
    ) -> None:
        """No test, lint or type run happened, so those gates are None."""
        repo, base = branch_repo
        report = analyze(collect(base, repo))
        assert report["quality_gates"]["passes_checks"] is None
        assert report["quality_gates"]["includes_breaking_changes"] is None

    def test_collected_files_never_populate_affected_apis(
        self, branch_repo: tuple[Path, str]
    ) -> None:
        """classify() emits no "breaking" type, so the list stays empty."""
        repo, base = branch_repo
        report = analyze(collect(base, repo))
        assert report["breaking"]["affected_apis"] == []

    def test_reviewers_come_from_the_map(self, branch_repo: tuple[Path, str]) -> None:
        """A prefix map turns changed paths into reviewer names."""
        repo, base = branch_repo
        report = analyze(collect(base, repo), {"src/": ["alex"], "docs/": ["sam"]})
        assert report["reviewers"] == ["alex", "sam"]


class TestCommandLine:
    """Feature: the skill runs one command and pastes from it."""

    def test_json_mode(
        self, branch_repo: tuple[Path, str], capsys: pytest.CaptureFixture[str]
    ) -> None:
        """--json prints the full report."""
        repo, base = branch_repo
        assert main(["--base", base, "--cwd", str(repo), "--json"]) == 0
        report = json.loads(capsys.readouterr().out)
        assert report["breaking"]["has_breaking_changes"] is True

    def test_markdown_mode_has_the_sections_the_skill_pastes(
        self, branch_repo: tuple[Path, str], capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Default output carries categories, gates, strategy and scaffold."""
        repo, base = branch_repo
        reviewer_map = repo / "reviewers.json"
        reviewer_map.write_text(json.dumps({"src/": ["alex"]}))
        assert (
            main(
                [
                    "--base",
                    base,
                    "--cwd",
                    str(repo),
                    "--reviewer-map",
                    str(reviewer_map),
                ]
            )
            == 0
        )
        out = capsys.readouterr().out
        for heading in (
            "## File categories",
            "## Breaking changes",
            "## Quality gates",
            "## Merge strategy",
            "## Suggested reviewers",
            "## Description scaffold",
        ):
            assert heading in out
        assert "carries a `!` marker" in out
        assert "- alex" in out

    def test_render_marks_unevaluated_gates_unknown(
        self, branch_repo: tuple[Path, str], capsys: pytest.CaptureFixture[str]
    ) -> None:
        """A gate nothing evaluated renders as unknown, never as pass."""
        repo, base = branch_repo
        assert main(["--base", base, "--cwd", str(repo)]) == 0
        out = capsys.readouterr().out
        assert "- passes_checks: unknown" in out
        assert "- includes_breaking_changes: unknown" in out
        assert "- has_tests: pass" in out

    def test_a_bad_base_is_reported(
        self, branch_repo: tuple[Path, str], capsys: pytest.CaptureFixture[str]
    ) -> None:
        """An unknown ref returns 1 with git's complaint on stderr."""
        repo, _ = branch_repo
        assert main(["--base", "no-such-ref", "--cwd", str(repo)]) == 1
        assert "git failed" in capsys.readouterr().err


class TestClassifyAgreesWithTheAnalyzer:
    """classify and PRPrepAnalyzer must not disagree about what a test is."""

    @pytest.mark.parametrize(
        "path",
        [
            "pkg/foo_test.py",
            "pkg/handler_test.go",
            "web/src/__tests__/App.jsx",
            "src/app.spec.ts",
            "tests/test_x.py",
            "src/test_helpers.py",
            "src/latest_config.py",
            "docs/guide.md",
        ],
    )
    def test_classify_says_test_exactly_when_is_test_path_does(self, path: str) -> None:
        assert (classify(path) == "test") == _is_test_path(path)


class TestRunsWithoutPyYAML:
    """The skill runs this script with the operator's python3."""

    def test_script_runs_when_pyyaml_is_not_importable(
        self, branch_repo: tuple[Path, str], tmp_path: Path
    ) -> None:
        """GIVEN an interpreter that cannot import yaml.

        WHEN the documented command runs against a repository
        THEN it exits 0, because pr_prep needs nothing outside stdlib
        """
        repo, base = branch_repo
        blocker = tmp_path / "blocker"
        blocker.mkdir()
        (blocker / "sitecustomize.py").write_text(
            'import sys\n\nsys.modules["yaml"] = None\n'
        )
        env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        env["PYTHONPATH"] = str(blocker)
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--base", base],
            cwd=repo,
            capture_output=True,
            text=True,
            env=env,
            timeout=60,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        assert "PR prep analysis" in result.stdout
