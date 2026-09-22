"""Tests for sync_wiki.py, the knowledge-corpus clone the interceptor reads.

The script had no tests at all. It is the only thing that puts the wiki
corpus on disk, and ``research_interceptor.py`` searches that corpus
before reaching for the web, so a sync that reports success while
cloning nothing turns search-before-web into web-always with no error.

``_run`` is the one boundary here: it wraps ``subprocess.run`` around
git. It is replaced with a recorder so the argv each command builds is
assertable, and so the failure paths can be driven without a remote.
``WIKI_DIR`` is repointed at tmp_path, because the real one is the
operator's corpus.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

import sync_wiki


class _GitRecorder:
    """Stand in for ``_run``, recording argv and replaying canned results."""

    def __init__(self, results: list[subprocess.CompletedProcess[str]]) -> None:
        self.results = list(results)
        self.calls: list[tuple[list[str], Path | None]] = []

    def __call__(
        self, cmd: list[str], cwd: Path | None = None
    ) -> subprocess.CompletedProcess[str]:
        self.calls.append((cmd, cwd))
        if self.results:
            return self.results.pop(0)
        return _ok()


def _ok(stdout: str = "") -> subprocess.CompletedProcess[str]:
    """Build a CompletedProcess standing for a git call that succeeded."""
    return subprocess.CompletedProcess(
        args=["git"], returncode=0, stdout=stdout, stderr=""
    )


def _fail(stderr: str) -> subprocess.CompletedProcess[str]:
    """Build a CompletedProcess standing for a git call that failed."""
    return subprocess.CompletedProcess(
        args=["git"], returncode=1, stdout="", stderr=stderr
    )


@pytest.fixture
def wiki_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point the module's WIKI_DIR at a throwaway tree."""
    target = tmp_path / "data" / "wiki"
    monkeypatch.setattr(sync_wiki, "WIKI_DIR", target)
    return target


class TestSyncPicksTheRightGitCommand:
    """Feature: clone or pull, decided by what is already on disk."""

    def test_an_existing_clone_is_pulled(
        self, wiki_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """GIVEN a wiki directory that is already a git clone
        WHEN sync runs
        THEN it pulls fast-forward only and does not clone again

        Cloning over an existing corpus would discard any local intake
        not yet pushed, and --ff-only is what keeps a diverged clone
        from silently merging.
        """
        (wiki_dir / ".git").mkdir(parents=True)
        recorder = _GitRecorder([_ok("Already up to date.")])
        monkeypatch.setattr(sync_wiki, "_run", recorder)

        assert sync_wiki.sync() is True
        assert recorder.calls[0][0] == ["git", "pull", "--ff-only"]
        assert recorder.calls[0][1] == wiki_dir

    def test_an_absent_directory_is_cloned(
        self, wiki_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """GIVEN no wiki directory
        WHEN sync runs
        THEN it clones the wiki remote into WIKI_DIR
        """
        recorder = _GitRecorder([_ok()])
        monkeypatch.setattr(sync_wiki, "_run", recorder)

        assert sync_wiki.sync() is True
        assert recorder.calls[0][0] == [
            "git",
            "clone",
            sync_wiki.REPO_URL,
            str(wiki_dir),
        ]

    def test_a_non_repo_directory_is_refused_without_running_git(
        self, wiki_dir: Path, monkeypatch: pytest.MonkeyPatch, capsys
    ) -> None:
        """GIVEN a wiki directory that exists but holds no .git
        WHEN sync runs
        THEN it refuses, says so, and runs no git command

        Cloning into a populated directory fails anyway; pulling from
        it is not possible. Naming the directory is the only way the
        operator learns which one to remove.
        """
        wiki_dir.mkdir(parents=True)
        recorder = _GitRecorder([])
        monkeypatch.setattr(sync_wiki, "_run", recorder)

        assert sync_wiki.sync() is False
        assert recorder.calls == []
        assert str(wiki_dir) in capsys.readouterr().out


class TestFailuresAreReportedOnStderr:
    """Feature: a failed git call is surfaced rather than swallowed."""

    def test_clone_failure_returns_false_and_prints_git_stderr(
        self, wiki_dir: Path, monkeypatch: pytest.MonkeyPatch, capsys
    ) -> None:
        """GIVEN a clone that git rejects
        WHEN clone runs
        THEN it returns False and git's own message reaches stderr

        main() turns the False into a nonzero exit, and the message is
        what distinguishes an auth failure from a missing remote.
        """
        monkeypatch.setattr(
            sync_wiki, "_run", _GitRecorder([_fail("Permission denied (publickey).")])
        )

        assert sync_wiki.clone() is False
        assert "Permission denied (publickey)." in capsys.readouterr().err

    def test_pull_failure_returns_false_and_prints_git_stderr(
        self, wiki_dir: Path, monkeypatch: pytest.MonkeyPatch, capsys
    ) -> None:
        """GIVEN a pull that git rejects as non-fast-forward
        WHEN pull runs
        THEN it returns False and git's own message reaches stderr
        """
        monkeypatch.setattr(
            sync_wiki, "_run", _GitRecorder([_fail("Not possible to fast-forward")])
        )

        assert sync_wiki.pull() is False
        assert "Not possible to fast-forward" in capsys.readouterr().err

    def test_push_failure_returns_false_and_prints_git_stderr(
        self, wiki_dir: Path, monkeypatch: pytest.MonkeyPatch, capsys
    ) -> None:
        """GIVEN a clean tree and a push git rejects
        WHEN push runs
        THEN it returns False and git's own message reaches stderr
        """
        monkeypatch.setattr(
            sync_wiki,
            "_run",
            _GitRecorder([_ok(), _fail("rejected: non-fast-forward")]),
        )

        assert sync_wiki.push() is False
        assert "rejected: non-fast-forward" in capsys.readouterr().err


class TestPushCommitsOnlyWhenThereIsSomethingToCommit:
    """Feature: staging local intake before pushing it."""

    def test_a_dirty_tree_is_staged_and_committed_before_the_push(
        self, wiki_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """GIVEN a wiki clone with uncommitted intake
        WHEN push runs
        THEN add and commit precede the push

        Pushing without committing sends nothing while reporting
        success, which loses the intake the pipeline just wrote.
        """
        recorder = _GitRecorder([_ok(" M Home.md\n"), _ok(), _ok(), _ok()])
        monkeypatch.setattr(sync_wiki, "_run", recorder)

        assert sync_wiki.push() is True
        assert [call[0][:2] for call in recorder.calls] == [
            ["git", "status"],
            ["git", "add"],
            ["git", "commit"],
            ["git", "push"],
        ]

    def test_a_clean_tree_pushes_without_committing(
        self, wiki_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """GIVEN a wiki clone with nothing uncommitted
        WHEN push runs
        THEN only status and push are run

        An empty commit on every sync fills the wiki history with
        entries that change nothing.
        """
        recorder = _GitRecorder([_ok(""), _ok()])
        monkeypatch.setattr(sync_wiki, "_run", recorder)

        assert sync_wiki.push() is True
        assert [call[0][:2] for call in recorder.calls] == [
            ["git", "status"],
            ["git", "push"],
        ]


class TestStatusReportsWhatIsOnDisk:
    """Feature: describing the local clone without changing it."""

    def test_an_uncloned_wiki_names_the_command_that_fixes_it(
        self, wiki_dir: Path, monkeypatch: pytest.MonkeyPatch, capsys
    ) -> None:
        """GIVEN no wiki directory
        WHEN status runs
        THEN the output says it is not cloned and runs no git command
        """
        recorder = _GitRecorder([])
        monkeypatch.setattr(sync_wiki, "_run", recorder)

        sync_wiki.status()

        assert "not cloned" in capsys.readouterr().out
        assert recorder.calls == []

    def test_a_clone_reports_its_page_count_and_clean_tree(
        self, wiki_dir: Path, monkeypatch: pytest.MonkeyPatch, capsys
    ) -> None:
        """GIVEN a clone holding three pages and no local changes
        WHEN status runs
        THEN the page count and a clean-tree line are printed

        The page count is the one number that tells an operator whether
        search-before-web has a corpus to search.
        """
        wiki_dir.mkdir(parents=True)
        for name in ("Home.md", "Guide.md", "Index.md"):
            (wiki_dir / name).write_text("stub", encoding="utf-8")
        monkeypatch.setattr(
            sync_wiki, "_run", _GitRecorder([_ok("abc1234 init (2 days ago)"), _ok("")])
        )

        sync_wiki.status()

        printed = capsys.readouterr().out
        assert "Pages: 3" in printed
        assert "Last commit: abc1234 init (2 days ago)" in printed
        assert "Working tree clean." in printed

    def test_uncommitted_pages_are_counted(
        self, wiki_dir: Path, monkeypatch: pytest.MonkeyPatch, capsys
    ) -> None:
        """GIVEN a clone with two modified pages
        WHEN status runs
        THEN the count of uncommitted changes is reported

        Intake writes into this clone, so a nonzero count is how an
        operator knows a push is owed.
        """
        wiki_dir.mkdir(parents=True)
        monkeypatch.setattr(
            sync_wiki,
            "_run",
            _GitRecorder([_ok("abc1234 init"), _ok(" M Home.md\n M Guide.md\n")]),
        )

        sync_wiki.status()

        assert "Uncommitted changes: 2" in capsys.readouterr().out
