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
    ("git", "diff", "HEAD", "--name-only"),
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
                ("git", "diff", "HEAD", "--name-only"): (0, "a/T1.py\n"),
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
        runner = FailOneGitCommand(("git", "diff", "HEAD", "--name-only"))

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

    def test_staged_lines_count_toward_the_cap(self, tmp_path: Path) -> None:
        repo = self._repo(tmp_path)
        runner = night_run.SubprocessRunner()
        (repo / "a.txt").write_text("one\ntwo\nthree\n")
        runner.run(["git", "add", "a.txt"], cwd=repo)

        assert night_run._diff_line_count(runner, repo) == 2

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
