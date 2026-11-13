"""Tests for scripts/description_paths.py, the description-to-diff check.

A PR description that claims changes the diff does not contain merges
far less often (arXiv 2601.04886: 28.3% against 80.0%). The check reads
the paths a description names in backticks and compares them with the
diff, so a draft that names a file it never touched is caught before a
reviewer finds it.
"""

from __future__ import annotations

import io
import subprocess
from pathlib import Path

import pytest
from description_paths import check, main, named_paths


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, text=True, check=True
    ).stdout.strip()


class TestNamedPaths:
    def test_extracts_backticked_paths_and_strips_line_numbers(self) -> None:
        """GIVEN a description naming `file:line` and a plain path
        WHEN its paths are read
        THEN both come back without the line number.
        """
        text = "Fixes `src/api.py:42` and `docs/guide.md`."
        assert named_paths(text) == ["src/api.py", "docs/guide.md"]

    def test_keeps_bare_file_names_with_an_extension(self) -> None:
        """GIVEN a bare file name in backticks
        WHEN its paths are read
        THEN the name is kept for suffix matching.
        """
        assert named_paths("Edits `pr-template.md`.") == ["pr-template.md"]

    def test_ignores_commands_identifiers_and_urls(self) -> None:
        """GIVEN commands, class names, URLs, and flags in backticks
        WHEN its paths are read
        THEN none is taken for a file.
        """
        text = (
            "Run `make test`, call `PRPrepAnalyzer`, see "
            "`https://example.invalid/a/b.md`, and `--base`."
        )
        assert named_paths(text) == []

    def test_ignores_home_absolute_and_elided_paths(self) -> None:
        """GIVEN home, absolute, and `...`-elided paths
        WHEN its paths are read
        THEN none is checked, since none is repo-relative.
        """
        text = (
            "See `~/.claude/CLAUDE.md`, `/etc/hosts`, `.../modules/a.md`, "
            "and `app/.../Service.kt`."
        )
        assert named_paths(text) == []

    def test_ignores_branches_addresses_globs_and_directories(self) -> None:
        """GIVEN branches, IPs, counts, versions, globs, and directories
        WHEN its paths are read
        THEN none is taken for a file.
        """
        text = (
            "Port of `feature/rc5` on `origin/main`, `127.0.0.1/tcp/44337`, "
            "`142/142`, `v1.2.4-rc.8`, `manager/src-tauri/**/*`, "
            "`[mobile/*.kt]`, and `swarm/tests/`."
        )
        assert named_paths(text) == []

    def test_strips_a_rust_symbol_suffix(self) -> None:
        """GIVEN a `file.rs::function` reference
        WHEN its paths are read
        THEN the file is kept and the symbol dropped.
        """
        text = "See `catalog/follow.rs::pull_known_catalogs`."
        assert named_paths(text) == ["catalog/follow.rs"]

    def test_ignores_paths_inside_fenced_code(self) -> None:
        """GIVEN a backticked path inside a fenced block
        WHEN its paths are read
        THEN the code block is not treated as a claim.
        """
        text = "```bash\ncat `src/api.py`\n```\nNothing else."
        assert named_paths(text) == []


class TestCheck:
    TRACKED = ["src/api.py", "src/other.py", "swarm/event/mod.rs"]

    def test_path_in_the_diff_passes(self) -> None:
        """GIVEN a named path the diff changed
        WHEN it is checked
        THEN nothing is reported.
        """
        report = check("`src/api.py`", ["src/api.py"], self.TRACKED)
        assert report.phantom == [] and report.untouched == []

    def test_bare_name_matches_a_changed_path_by_suffix(self) -> None:
        """GIVEN a bare name matching a changed path's tail
        WHEN it is checked
        THEN it counts as in the diff.
        """
        report = check("`api.py`", ["src/api.py"], self.TRACKED)
        assert report.untouched == []

    def test_missing_path_is_phantom(self) -> None:
        """GIVEN a path neither changed nor tracked
        WHEN it is checked
        THEN it is reported phantom.
        """
        report = check("`src/gone.py`", ["src/api.py"], self.TRACKED)
        assert report.phantom == ["src/gone.py"]

    def test_existing_path_outside_the_diff_is_untouched(self) -> None:
        """GIVEN a tracked path the diff left alone
        WHEN it is checked
        THEN it is untouched, not phantom.
        """
        report = check("`src/other.py`", ["src/api.py"], self.TRACKED)
        assert report.phantom == [] and report.untouched == ["src/other.py"]

    def test_crate_relative_path_is_found_by_suffix(self) -> None:
        """GIVEN a crate-relative path to a tracked file
        WHEN it is checked
        THEN the suffix match finds it, so it is not phantom.
        """
        report = check("`event/mod.rs`", ["src/api.py"], self.TRACKED)
        assert report.phantom == [] and report.untouched == ["event/mod.rs"]

    def test_bare_name_that_is_tracked_is_untouched(self) -> None:
        """GIVEN a bare name of a tracked, unchanged file
        WHEN it is checked
        THEN it is untouched.
        """
        report = check("`other.py`", ["src/api.py"], self.TRACKED)
        assert report.untouched == ["other.py"]

    def test_bare_dotted_identifier_is_ignored(self) -> None:
        """GIVEN dotted code identifiers no file matches
        WHEN they are checked
        THEN nothing is reported.
        """
        text = "Calls `Dispatchers.IO` and `LocalModelStore.record`."
        report = check(text, ["src/api.py"], self.TRACKED)
        assert report.phantom == [] and report.untouched == []


@pytest.fixture
def branch_repo(tmp_path: Path) -> tuple[Path, str]:
    repo = tmp_path / "repo"
    (repo / "src").mkdir(parents=True)
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "check@example.invalid")
    _git(repo, "config", "user.name", "Check")
    (repo / "src" / "api.py").write_text("a = 1\n")
    (repo / "src" / "other.py").write_text("b = 1\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "chore: seed")
    base = _git(repo, "rev-parse", "HEAD")
    (repo / "src" / "api.py").write_text("a = 2\n")
    _git(repo, "commit", "-qam", "fix: change api")
    return repo, base


class TestMain:
    def _run(self, repo: Path, base: str, text: str, *extra: str) -> int:
        desc = repo / "desc.md"
        desc.write_text(text)
        return main(["--repo", str(repo), "--base", base, str(desc), *extra])

    def test_exits_zero_when_every_path_is_in_the_diff(
        self, branch_repo: tuple[Path, str]
    ) -> None:
        """GIVEN a description naming only changed files
        WHEN the CLI runs
        THEN it exits 0.
        """
        repo, base = branch_repo
        assert self._run(repo, base, "Changes `src/api.py`.") == 0

    def test_exits_one_on_a_phantom_path(
        self, branch_repo: tuple[Path, str], capsys: pytest.CaptureFixture[str]
    ) -> None:
        """GIVEN a description naming a file that does not exist
        WHEN the CLI runs
        THEN it exits 1 and prints the phantom line.
        """
        repo, base = branch_repo
        assert self._run(repo, base, "Changes `src/missing.py`.") == 1
        assert "phantom: src/missing.py" in capsys.readouterr().out

    def test_untouched_path_warns_by_default(
        self, branch_repo: tuple[Path, str], capsys: pytest.CaptureFixture[str]
    ) -> None:
        """GIVEN a description naming a tracked, unchanged file
        WHEN the CLI runs without --strict
        THEN it warns and exits 0.
        """
        repo, base = branch_repo
        assert self._run(repo, base, "Called from `src/other.py`.") == 0
        assert "not in diff: src/other.py" in capsys.readouterr().out

    def test_counts_uncommitted_and_untracked_files_as_in_the_diff(
        self, branch_repo: tuple[Path, str]
    ) -> None:
        """GIVEN an edited file and a new untracked file, neither committed
        WHEN the CLI runs under --strict
        THEN both count as changed, because drafts precede the commit.
        """
        repo, base = branch_repo
        (repo / "src" / "other.py").write_text("b = 2\n")
        (repo / "src" / "new.py").write_text("c = 1\n")
        text = "Changes `src/other.py` and adds `src/new.py`."
        assert self._run(repo, base, text, "--strict") == 0

    def test_a_renamed_file_keeps_its_old_name_in_the_diff(
        self, branch_repo: tuple[Path, str]
    ) -> None:
        """GIVEN a committed rename
        WHEN the description names the old and new paths
        THEN both are in the diff and the run passes.
        """
        repo, base = branch_repo
        _git(repo, "mv", "src/other.py", "src/moved.py")
        _git(repo, "commit", "-qm", "refactor: move other")
        text = "Moves `src/other.py` to `src/moved.py`."
        assert self._run(repo, base, text, "--strict") == 0

    def test_reads_the_description_from_stdin(
        self,
        branch_repo: tuple[Path, str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """GIVEN a description piped on stdin with a phantom path
        WHEN the CLI reads `-`
        THEN it exits 1.
        """
        repo, base = branch_repo
        monkeypatch.setattr("sys.stdin", io.StringIO("Adds `src/missing.py`."))
        assert main(["--repo", str(repo), "--base", base, "-"]) == 1

    def test_untouched_path_fails_under_strict(
        self, branch_repo: tuple[Path, str]
    ) -> None:
        """GIVEN a description naming a tracked, unchanged file
        WHEN the CLI runs with --strict
        THEN it exits 1.
        """
        repo, base = branch_repo
        text = "Called from `src/other.py`."
        assert self._run(repo, base, text, "--strict") == 1

    def test_unresolvable_base_exits_two_and_names_the_base(
        self, branch_repo: tuple[Path, str], capsys: pytest.CaptureFixture[str]
    ) -> None:
        """GIVEN a --base that git cannot resolve
        WHEN the CLI runs
        THEN it exits 2 and names the base, so a git failure is not read
        as a phantom path.
        """
        repo, _ = branch_repo
        assert self._run(repo, "origin/no-such-branch", "Changes `src/api.py`.") == 2
        assert "origin/no-such-branch" in capsys.readouterr().err
