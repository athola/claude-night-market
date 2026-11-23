"""A git command that fails stops the walk, and the proof says which one.

Six reads of git output ignored the exit code. A failed ``git diff
--name-only`` read as "nothing changed", so the scope fence passed an
empty list, and a failed ``git checkout -- .`` at park left the edits
in place while the proof said they were reverted. Each case here fails
exactly one git command and checks that the item does not end ready,
that the proof names the command, and that ``main`` reports a broken
walk rather than a finished one.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace
from pathlib import Path

import night_run
import pytest

from tests.test_handoff_gate import write_item
from tests.test_item_walk import HANDOFF, mktask

#: The evidence command ``mktask("T1")`` declares, as argv.
EVIDENCE = ("pytest", "-q", "-k", "T1")


class FailOneGitCommand:
    """Answer every command with exit 0 except one exact git argv.

    Matching the whole argv rather than a substring keeps ``git diff``
    apart from ``git diff --name-only``, which is the distinction the
    discard path depends on.
    """

    def __init__(
        self,
        failing: tuple[str, ...],
        outputs: dict[tuple[str, ...], tuple[int, str]] | None = None,
    ) -> None:
        """Fail ``failing`` exactly; answer the argv in ``outputs`` as scripted."""
        self.failing = failing
        self.outputs = outputs or {}
        self.calls: list[tuple[str, ...]] = []

    def run(
        self,
        command: Sequence[str],
        cwd: Path | None = None,
        timeout: int = 0,
        env=None,
    ) -> night_run.Completed:
        del cwd, timeout, env
        argv = tuple(command)
        self.calls.append(argv)
        if argv == self.failing:
            return night_run.Completed(returncode=128, output="fatal: not a git repo")
        code, output = self.outputs.get(argv, (0, ""))
        return night_run.Completed(returncode=code, output=output)


def _passing_sitter(**_: object) -> tuple[str, str, str]:
    return ("PASS", "", "")


#: Git reads made while a task is judged. The evidence passes, so the
#: walk reaches every one of them unless the failing one stops it.
WALK_READS = [
    ("git", "diff", "HEAD", "--name-only", "--no-renames"),
    ("git", "status", "--porcelain", "-uall"),
    ("git", "diff", "HEAD", "--numstat"),
    ("git", "diff", "HEAD", "--unified=0"),
]

#: Git commands made when a parked item discards what the task left.
DISCARD_COMMANDS = [
    ("git", "diff", "HEAD"),
    ("git", "restore", "--source=HEAD", "--staged", "--worktree", "--", "."),
]


class TestAGitFailureStopsTheWalk:
    """Feature: no git failure is read as an empty answer."""

    @pytest.mark.parametrize("failing", WALK_READS, ids=" ".join)
    def test_a_failed_read_while_judging_a_task(
        self, tmp_path: Path, failing: tuple[str, ...]
    ) -> None:
        runner = FailOneGitCommand(failing, {EVIDENCE: (0, "1 passed")})

        result = night_run.run_item(
            HANDOFF, [mktask("T1", [])], tmp_path, runner, babysitter=_passing_sitter
        )

        assert result.status == "git_failed"
        assert " ".join(failing) in result.reason
        assert result.committed == []

    @pytest.mark.parametrize("failing", DISCARD_COMMANDS, ids=" ".join)
    def test_a_failed_command_while_discarding_at_park(
        self, tmp_path: Path, failing: tuple[str, ...]
    ) -> None:
        """The task fails its evidence, so the item parks and discards."""
        runner = FailOneGitCommand(
            failing,
            {
                EVIDENCE: (1, "1 failed"),
                ("git", "diff", "HEAD", "--name-only", "--no-renames"): (
                    0,
                    "a/T1.py\n",
                ),
            },
        )

        result = night_run.run_item(
            HANDOFF, [mktask("T1", [])], tmp_path, runner, babysitter=_passing_sitter
        )

        assert result.status == "git_failed"
        assert " ".join(failing) in result.reason
        proof = night_run.write_proof(tmp_path / "item", result).read_text()
        assert "git_failed" in proof


class TestMainReportsABrokenWalk:
    """Feature: the exit code tells a git failure from a finished night."""

    def test_main_exits_walk_broken_and_still_writes_the_proof(
        self, tmp_path: Path
    ) -> None:
        item = write_item(tmp_path)
        runner = FailOneGitCommand(
            ("git", "diff", "HEAD", "--name-only", "--no-renames")
        )

        code = night_run.main(
            ["--item-dir", str(item), "--root", str(tmp_path)],
            runner=runner,
            babysitter=_passing_sitter,
        )

        assert code == night_run.WALK_BROKEN_EXIT
        proof = (item / "proof.md").read_text()
        assert "**Status**: git_failed" in proof
        assert "git diff HEAD --name-only" in proof


class TestStagedChangesAreFenced:
    """Feature: a path the implementer staged is judged like any other.

    The fence and the line cap read the unstaged view, so ``git add``
    hid a change from both, and the task commit, which took the whole
    index, then committed it.
    """

    @staticmethod
    def _repo(tmp_path: Path) -> Path:
        runner = night_run.SubprocessRunner()
        for argv in (
            ("git", "init", "-q"),
            ("git", "config", "user.email", "t@example.com"),
            ("git", "config", "user.name", "t"),
        ):
            runner.run(list(argv), cwd=tmp_path)
        (tmp_path / "a.txt").write_text("one\n")
        runner.run(["git", "add", "a.txt"], cwd=tmp_path)
        runner.run(["git", "commit", "-q", "-m", "init"], cwd=tmp_path)
        return tmp_path

    def test_a_staged_new_file_reaches_the_fence(self, tmp_path: Path) -> None:
        repo = self._repo(tmp_path)
        runner = night_run.SubprocessRunner()
        (repo / ".github").mkdir()
        (repo / ".github" / "x.yml").write_text("on: push\n")
        runner.run(["git", "add", ".github/x.yml"], cwd=repo)

        assert ".github/x.yml" in night_run._touched_files(runner, repo)

    def test_a_staged_rename_reports_its_source(self, tmp_path: Path) -> None:
        """A rename out of a fenced path must show the path it emptied."""
        repo = self._repo(tmp_path)
        runner = night_run.SubprocessRunner()
        runner.run(["git", "mv", "a.txt", "allowed.txt"], cwd=repo)

        touched = night_run._touched_files(runner, repo)

        assert {"a.txt", "allowed.txt"} <= set(touched)

    def test_staged_lines_count_toward_the_cap(self, tmp_path: Path) -> None:
        repo = self._repo(tmp_path)
        runner = night_run.SubprocessRunner()
        (repo / "a.txt").write_text("one\ntwo\nthree\n")
        runner.run(["git", "add", "a.txt"], cwd=repo)

        assert night_run._diff_line_count(runner, repo) == 2

    def test_untracked_lines_count_toward_the_cap(self, tmp_path: Path) -> None:
        """A file the implementer created is not in `git diff HEAD`."""
        repo = self._repo(tmp_path)
        runner = night_run.SubprocessRunner()
        (repo / "new.py").write_text("x = 1\n" * 500)

        assert night_run._diff_line_count(runner, repo) == 500

    def test_the_review_diff_shows_an_untracked_file(self, tmp_path: Path) -> None:
        """The babysitter must see a new file, or it reviews an empty diff."""
        repo = self._repo(tmp_path)
        runner = night_run.SubprocessRunner()
        (repo / "a.txt").write_text("one\nchanged\n")
        (repo / "new.py").write_text("print('hi')\n")

        diff = night_run._review_diff(runner, repo)

        assert "+changed" in diff
        assert "new.py" in diff
        assert "+print('hi')" in diff

    def test_an_untracked_nested_repo_adds_no_git_error_to_the_diff(
        self, tmp_path: Path
    ) -> None:
        """Git lists a nested repository as one directory entry.

        ``git diff --no-index`` on a directory exits 1 with "Could not
        access", the same code as a real difference, so the error text
        reached the babysitter as if it were a diff.
        """
        repo = self._repo(tmp_path)
        runner = night_run.SubprocessRunner()
        (repo / "sub").mkdir()
        self._repo(repo / "sub")
        (repo / "new.py").write_text("print('hi')\n")

        diff = night_run._review_diff(runner, repo)

        assert "error:" not in diff
        assert "+print('hi')" in diff
        assert night_run._diff_line_count(runner, repo) == 1

    def test_the_task_commit_leaves_a_staged_stray_out(self, tmp_path: Path) -> None:
        repo = self._repo(tmp_path)
        runner = night_run.SubprocessRunner()
        (repo / "a.txt").write_text("one\ntwo\n")
        (repo / "stray.txt").write_text("x\n")
        runner.run(["git", "add", "stray.txt"], cwd=repo)

        reason = night_run._commit_task(
            runner, repo, {"id": "T1", "title": "t", "files": ["a.txt"]}
        )

        assert reason is None
        shown = runner.run(["git", "show", "--name-only", "--format="], cwd=repo)
        assert shown.output.split() == ["a.txt"]

    def test_discard_reverts_staged_edits_too(self, tmp_path: Path) -> None:
        repo = self._repo(tmp_path)
        runner = night_run.SubprocessRunner()
        (repo / "a.txt").write_text("changed\n")
        runner.run(["git", "add", "a.txt"], cwd=repo)

        discarded = night_run._discard_uncommitted(runner, repo)

        assert discarded is not None
        assert discarded.files == ["a.txt"]
        assert (repo / "a.txt").read_text() == "one\n"
        status = runner.run(["git", "status", "--porcelain"], cwd=repo)
        assert status.output == ""

    def test_a_staged_new_offender_is_removed(self, tmp_path: Path) -> None:
        repo = self._repo(tmp_path)
        runner = night_run.SubprocessRunner()
        (repo / "new.txt").write_text("x\n")
        runner.run(["git", "add", "new.txt"], cwd=repo)

        assert night_run._revert_offenders(runner, repo, ["new.txt"]) == []
        assert not (repo / "new.txt").exists()


class TestImplementerCommitsStayFenced:
    """The fence diffed against HEAD, so an implementer that committed
    moved HEAD and its edits were invisible to the fence (EGR-5).
    """

    def test_fence_sees_commits_made_by_implementer(self, tmp_path: Path) -> None:
        runner = night_run.SubprocessRunner()
        for argv in (
            ("git", "init", "-q"),
            ("git", "config", "user.email", "t@example.com"),
            ("git", "config", "user.name", "t"),
        ):
            runner.run(list(argv), cwd=tmp_path)
        (tmp_path / "a.txt").write_text("one\n")
        runner.run(["git", "add", "a.txt"], cwd=tmp_path)
        runner.run(["git", "commit", "-q", "-m", "init"], cwd=tmp_path)
        base = night_run._head(runner, tmp_path)
        (tmp_path / ".github").mkdir()
        (tmp_path / ".github" / "x.yml").write_text("on: push\n")
        runner.run(["git", "add", "-A"], cwd=tmp_path)
        runner.run(["git", "commit", "-q", "-m", "sneaky"], cwd=tmp_path)

        night_run._uncommit_since(runner, tmp_path, base)

        assert night_run._head(runner, tmp_path) == base
        assert ".github/x.yml" in night_run._touched_files(runner, tmp_path)


class TestAParkedItemResumes:
    """After a park the branch and worktree already exist, and a rerun died
    on `git worktree add -b` with setup_failed (EGR-4).
    """

    @staticmethod
    def _repo(tmp_path: Path) -> tuple[night_run.SubprocessRunner, Path]:

        runner = night_run.SubprocessRunner()
        root = tmp_path / "repo"
        root.mkdir()
        for argv in (
            ("git", "init", "-q", "-b", "main"),
            ("git", "config", "user.email", "t@example.com"),
            ("git", "config", "user.name", "t"),
        ):
            runner.run(list(argv), cwd=root)
        (root / "a.txt").write_text("one\n")
        runner.run(["git", "add", "a.txt"], cwd=root)
        runner.run(["git", "commit", "-q", "-m", "init"], cwd=root)
        handoff = replace(HANDOFF, commands={})
        return runner, root, handoff

    def test_rerun_after_park_reuses_existing_worktree(self, tmp_path: Path) -> None:
        runner, root, handoff = self._repo(tmp_path)
        worktree = tmp_path / "wt"
        assert night_run._prepare_worktree(runner, root, worktree, handoff) is None
        assert night_run._prepare_worktree(runner, root, worktree, handoff) is None

    def test_committed_task_ids_are_read_from_the_branch(self, tmp_path: Path) -> None:
        runner, root, handoff = self._repo(tmp_path)
        worktree = tmp_path / "wt"
        night_run._prepare_worktree(runner, root, worktree, handoff)
        (worktree / "b.txt").write_text("b\n")
        runner.run(["git", "add", "b.txt"], cwd=worktree)
        runner.run(["git", "commit", "-q", "-m", "T1: add b"], cwd=worktree)

        assert night_run._committed_task_ids(runner, worktree, handoff) == {"T1"}


class ScriptedImplementer:
    """Real git, with the implementer and the evidence command scripted.

    ``edits`` maps a task id to the files its implementer writes; when
    ``commit`` is set the implementer also runs ``git commit``, which is
    the move EGR-5 was about. ``fail`` names argv prefixes to answer with
    exit 1 instead of running them.
    """

    def __init__(
        self,
        edits: dict[str, dict[str, str]],
        *,
        commit: bool = False,
        fail: tuple[tuple[str, ...], ...] = (),
    ) -> None:
        """Script the implementer's edits; run every other git command for real."""
        self.git = night_run.SubprocessRunner()
        self.edits = edits
        self.commit = commit
        self.fail = fail
        self.dispatched: list[str] = []
        self.calls: list[tuple[str, ...]] = []

    def run(
        self,
        command: Sequence[str],
        cwd: Path | None = None,
        timeout: int = 0,
        env=None,
    ) -> night_run.Completed:
        argv = tuple(command)
        self.calls.append(argv)
        if any(argv[: len(prefix)] == prefix for prefix in self.fail):
            return night_run.Completed(returncode=1, output=f"{argv[0]} failed")
        if argv[:2] == ("python3", night_run.CONJURE_EXECUTOR):
            tid = argv[3].split(":", 1)[0].removeprefix("Task ")
            self.dispatched.append(tid)
            assert cwd is not None
            for rel, text in self.edits.get(tid, {}).items():
                (cwd / rel).parent.mkdir(parents=True, exist_ok=True)
                (cwd / rel).write_text(text)
            if self.commit:
                self.git.run(["git", "add", "-A"], cwd=cwd)
                self.git.run(["git", "commit", "-q", "-m", "implementer"], cwd=cwd)
            return night_run.Completed(returncode=0, output="done")
        if argv[0] == "pytest":
            return night_run.Completed(returncode=0, output="1 passed")
        if argv[0] != "git":
            return night_run.Completed(returncode=0, output="")
        return self.git.run(list(argv), cwd=cwd, timeout=timeout or 60, env=env)


def _git_repo(path: Path) -> night_run.SubprocessRunner:
    runner = night_run.SubprocessRunner()
    path.mkdir(parents=True, exist_ok=True)
    for argv in (
        ("git", "init", "-q", "-b", "main"),
        ("git", "config", "user.email", "t@example.com"),
        ("git", "config", "user.name", "t"),
    ):
        runner.run(list(argv), cwd=path)
    (path / "a.txt").write_text("one\n")
    runner.run(["git", "add", "a.txt"], cwd=path)
    runner.run(["git", "commit", "-q", "-m", "init"], cwd=path)
    return runner


class TestRunTaskUncommitsTheImplementer:
    """run_task itself must hand implementer commits back to the fence."""

    def test_implementer_commit_of_github_file_is_fenced(self, tmp_path: Path) -> None:
        _git_repo(tmp_path)
        runner = ScriptedImplementer(
            {"T1": {".github/x.yml": "on: push\n", "a/T1.py": "x = 1\n"}},
            commit=True,
        )
        base = night_run._head(runner.git, tmp_path)

        result = night_run.run_task(
            mktask("T1", []), HANDOFF, tmp_path, runner, babysitter=_passing_sitter
        )

        assert night_run._head(runner.git, tmp_path) == base
        assert result.verdict != "PASS"
        assert ".github/x.yml" in result.reason
        assert not (tmp_path / ".github" / "x.yml").exists()

    def test_failed_soft_reset_raises_instead_of_hiding_the_commit(
        self, tmp_path: Path
    ) -> None:
        _git_repo(tmp_path)
        runner = ScriptedImplementer(
            {"T1": {".github/x.yml": "on: push\n"}},
            commit=True,
            fail=(("git", "reset", "--soft"),),
        )

        with pytest.raises(night_run.GitFailed, match="reset --soft"):
            night_run.run_task(
                mktask("T1", []), HANDOFF, tmp_path, runner, babysitter=_passing_sitter
            )


class TestAResumedItem:
    """A rerun of an item picks up where the last night stopped."""

    @staticmethod
    def _handoff(**commands: str) -> night_run.Handoff:
        return replace(HANDOFF, commands=dict(commands))

    def test_resumed_item_dispatches_only_uncommitted_tasks(
        self, tmp_path: Path
    ) -> None:
        root = tmp_path / "repo"
        git = _git_repo(root)
        handoff = self._handoff()
        worktree = root / ".egregore" / "worktrees" / "NS-001"
        assert night_run._prepare_worktree(git, root, worktree, handoff) is None
        (worktree / "a").mkdir()
        (worktree / "a" / "T1.py").write_text("t1 = 1\n")
        git.run(["git", "add", "-A"], cwd=worktree)
        git.run(["git", "commit", "-q", "-m", "T1: task T1"], cwd=worktree)
        runner = ScriptedImplementer({"T2": {"a/T2.py": "t2 = 2\n"}})

        result = night_run.run_item(
            handoff,
            [mktask("T1", []), mktask("T2", ["T1"])],
            root,
            runner,
            babysitter=_passing_sitter,
        )

        assert runner.dispatched == ["T2"]
        assert result.committed == ["T2"]

    def test_resume_with_unresolvable_base_stops_instead_of_replaying(
        self, tmp_path: Path
    ) -> None:
        root = tmp_path / "repo"
        git = _git_repo(root)
        handoff = self._handoff()
        worktree = root / ".egregore" / "worktrees" / "NS-001"
        night_run._prepare_worktree(git, root, worktree, handoff)
        (worktree / "a").mkdir()
        (worktree / "a" / "T1.py").write_text("t1 = 1\n")
        git.run(["git", "add", "-A"], cwd=worktree)
        git.run(["git", "commit", "-q", "-m", "T1: task T1"], cwd=worktree)
        gone = replace(handoff, base_branch="main-deleted")
        runner = ScriptedImplementer({"T1": {"a/T1.py": "t1 = 1\n"}})

        result = night_run.run_item(
            gone, [mktask("T1", [])], root, runner, babysitter=_passing_sitter
        )

        assert runner.dispatched == []
        assert result.status == "git_failed"
        assert "main-deleted" in result.reason

    def test_rerun_after_failed_setup_runs_setup_again(self, tmp_path: Path) -> None:
        root = tmp_path / "repo"
        _git_repo(root)
        handoff = self._handoff(setup="uv sync")
        worktree = root / ".egregore" / "worktrees" / "NS-001"
        failing = ScriptedImplementer({}, fail=(("uv",),))

        first = night_run._prepare_worktree(failing, root, worktree, handoff)
        second = night_run._prepare_worktree(failing, root, worktree, handoff)

        assert first is not None and "uv sync exited 1" in first
        assert second is not None and "uv sync exited 1" in second
        assert failing.calls.count(("uv", "sync")) == 2
