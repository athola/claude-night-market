"""Tests for walking a whole work item, not just one task.

The walker is where a night either produces reviewable branches or
produces a mess. What is pinned here: dependency order is honored, each
passing task becomes its own commit, a failing task parks the item
instead of pressing on, and the on-plan token ceiling stops the run
with everything already committed still committed.
"""

from __future__ import annotations

from pathlib import Path

import night_run
import pytest
from budget import Budget


class FakeRunner:
    """A scripted runner that records every command, in order."""

    def __init__(self, script: dict[str, tuple[int, str]] | None = None) -> None:
        """Map a command substring to the (exit code, output) it yields."""
        self.script = script or {}
        self.calls: list[str] = []
        self.invocations: list[tuple[str, Path | None]] = []

    def run(self, command: str, cwd: Path | None = None, timeout: int = 0):
        del timeout
        self.calls.append(command)
        self.invocations.append((command, cwd))
        for key, (code, out) in self.script.items():
            if key in command:
                return night_run.Completed(returncode=code, output=out)
        return night_run.Completed(returncode=0, output="")


def mktask(tid: str, deps: list[str], expect: str = "pass") -> dict:
    return {
        "id": tid,
        "title": f"task {tid}",
        "change": "do it",
        "files": [f"a/{tid}.py"],
        "evidence": {
            "command": f"pytest -q -k {tid}",
            "expect": expect,
            "match": "1 failed" if expect == "fail" else "1 passed",
        },
        "depends_on": deps,
    }


HANDOFF = {
    "item": "NS-001",
    "branch": "night/NS-001",
    "base_branch": "main",
    "worktree": ".egregore/worktrees/NS-001",
    "scope": {"allow_paths": ["a/"], "max_diff_lines": 200},
    "commands": {
        "setup": "uv sync",
        "test": "pytest -q",
        "full_test": "pytest -q",
    },
    "budget": {
        "max_tasks": 6,
        "max_attempts_per_task": 1,
        "implementer_timeout_s": 900,
        "claude_token_ceiling": 120000,
    },
    "implementer": {"provider": "auto", "allow_on_plan_fallback": False},
    "babysitter": {"model": "sonnet"},
}


def passing_sitter(**_):
    return ("PASS", "", "")


class TestTopoSort:
    """Dependency order, decided once and not by the model."""

    def test_dependencies_come_first(self) -> None:
        tasks = [mktask("T2", ["T1"]), mktask("T1", [])]
        assert [t["id"] for t in night_run.topo_sort(tasks)] == ["T1", "T2"]

    def test_independent_tasks_keep_their_declared_order(self) -> None:
        tasks = [mktask("T1", []), mktask("T2", []), mktask("T3", [])]
        assert [t["id"] for t in night_run.topo_sort(tasks)] == ["T1", "T2", "T3"]

    def test_a_diamond_resolves(self) -> None:
        tasks = [
            mktask("T4", ["T2", "T3"]),
            mktask("T2", ["T1"]),
            mktask("T3", ["T1"]),
            mktask("T1", []),
        ]
        order = [t["id"] for t in night_run.topo_sort(tasks)]
        assert order[0] == "T1"
        assert order[-1] == "T4"
        assert order.index("T2") < order.index("T4")

    def test_a_cycle_raises_rather_than_guessing(self) -> None:
        tasks = [mktask("T1", ["T2"]), mktask("T2", ["T1"])]
        with pytest.raises(ValueError, match="cycle"):
            night_run.topo_sort(tasks)


class TestWorktreeSetup:
    """The item gets its own tree, cut from the declared base."""

    def test_worktree_is_created_from_the_base_branch(self, tmp_path: Path) -> None:
        runner = FakeRunner({"pytest": (0, "1 passed")})
        night_run.run_item(
            HANDOFF,
            [mktask("T1", [], expect="fail")],
            tmp_path,
            runner,
            babysitter=passing_sitter,
        )
        add = [c for c in runner.calls if "worktree add" in c]
        assert add, "the item must get its own worktree"
        assert "night/NS-001" in add[0]
        assert "main" in add[0]

    def test_setup_command_runs_before_any_task(self, tmp_path: Path) -> None:
        runner = FakeRunner({"pytest": (0, "1 passed")})
        night_run.run_item(
            HANDOFF,
            [mktask("T1", [], expect="fail")],
            tmp_path,
            runner,
            babysitter=passing_sitter,
        )
        setup = next(i for i, c in enumerate(runner.calls) if "uv sync" in c)
        first_dispatch = next(
            i for i, c in enumerate(runner.calls) if "delegation_executor" in c
        )
        assert setup < first_dispatch


class TestCommitPerTask:
    """One commit per task, so the morning diff reads in order."""

    def test_each_passing_task_is_committed(self, tmp_path: Path) -> None:
        runner = FakeRunner(
            {"pytest -q -k T1": (1, "1 failed"), "pytest": (0, "1 passed")}
        )
        result = night_run.run_item(
            HANDOFF,
            [mktask("T1", [], expect="fail"), mktask("T2", ["T1"])],
            tmp_path,
            runner,
            babysitter=passing_sitter,
        )
        commits = [c for c in runner.calls if "git" in c and "commit" in c]
        assert len(commits) == 2
        assert "T1" in commits[0]
        assert "T2" in commits[1]
        assert result.committed == ["T1", "T2"]

    def test_a_failing_task_is_not_committed_and_parks_the_item(
        self, tmp_path: Path
    ) -> None:
        runner = FakeRunner({"pytest": (1, "1 failed")})
        result = night_run.run_item(
            HANDOFF,
            [mktask("T1", [], expect="fail"), mktask("T2", ["T1"])],
            tmp_path,
            runner,
            babysitter=lambda **_: ("FAIL", "not done", ""),
        )
        assert result.status == "parked_task"
        assert result.committed == ["T1"]
        assert "T2" in result.reason

    def test_a_later_task_does_not_run_after_a_park(self, tmp_path: Path) -> None:
        runner = FakeRunner({"pytest": (1, "1 failed")})
        night_run.run_item(
            HANDOFF,
            [mktask("T1", []), mktask("T2", ["T1"])],
            tmp_path,
            runner,
            babysitter=lambda **_: ("FAIL", "no", ""),
        )
        assert not any("-k T2" in c for c in runner.calls)


class TestFullSuite:
    """The item is only ready when the whole suite agrees."""

    def test_full_suite_runs_after_every_task_passes(self, tmp_path: Path) -> None:
        runner = FakeRunner(
            {"pytest -q -k T1": (1, "1 failed"), "pytest": (0, "1 passed")}
        )
        result = night_run.run_item(
            HANDOFF,
            [mktask("T1", [], expect="fail")],
            tmp_path,
            runner,
            babysitter=passing_sitter,
        )
        assert result.status == "ready"
        assert result.full_suite is not None
        assert result.full_suite["exit"] == 0

    def test_a_red_full_suite_does_not_report_ready(self, tmp_path: Path) -> None:
        runner = FakeRunner(
            {
                "pytest -q -k T1": (1, "1 failed"),
                "-q -k": (0, "1 passed"),
                "pytest -q": (1, "3 failed"),
            }
        )
        result = night_run.run_item(
            HANDOFF,
            [mktask("T1", [], expect="fail")],
            tmp_path,
            runner,
            babysitter=passing_sitter,
        )
        assert result.status == "full_suite_red"


class TestTokenCeiling:
    """The ceiling stops the run; it does not discard what already passed."""

    def test_the_ceiling_stops_the_run(self, tmp_path: Path) -> None:
        handoff = {
            **HANDOFF,
            "budget": {**HANDOFF["budget"], "claude_token_ceiling": 1},
        }
        runner = FakeRunner(
            {"pytest -q -k T1": (1, "1 failed"), "pytest": (0, "1 passed")}
        )
        # A ceiling of 1 admits nothing at all, which is the correct
        # reading of a ceiling of 1.
        result = night_run.run_item(
            handoff,
            [mktask("T1", [], expect="fail"), mktask("T2", ["T1"])],
            tmp_path,
            runner,
            babysitter=passing_sitter,
        )
        assert result.status == "parked_budget"
        assert "ceiling" in result.reason

    def test_work_done_before_the_ceiling_stays_committed(self, tmp_path: Path) -> None:
        """A ceiling stops the run. It does not roll back proven work."""
        # 40 chars of diff plus a short tail costs roughly 12 tokens per
        # check, so 20 admits T1's check and refuses T2's.
        handoff = {
            **HANDOFF,
            "budget": {**HANDOFF["budget"], "claude_token_ceiling": 20},
        }
        runner = FakeRunner(
            {
                "git diff --unified=0": (0, "x" * 40),
                "pytest -q -k T1": (1, "1 failed"),
                "pytest": (0, "1 passed"),
            }
        )
        result = night_run.run_item(
            handoff,
            [mktask("T1", [], expect="fail"), mktask("T2", ["T1"])],
            tmp_path,
            runner,
            babysitter=passing_sitter,
        )
        assert result.status == "parked_budget"
        assert result.committed == ["T1"], "the ceiling must not discard a proven task"
        assert any("commit" in c and "T1" in c for c in runner.calls)

    def test_spend_accumulates_into_the_shared_budget(self, tmp_path: Path) -> None:
        budget = Budget()
        runner = FakeRunner(
            {"pytest -q -k T1": (1, "1 failed"), "pytest": (0, "1 passed")}
        )
        night_run.run_item(
            HANDOFF,
            [mktask("T1", [], expect="fail")],
            tmp_path,
            runner,
            babysitter=passing_sitter,
            budget=budget,
        )
        assert budget.estimated_tokens_used > 0


class TestProofFile:
    """Every item leaves a ledger a human reads without rerunning anything."""

    def test_proof_is_written_next_to_the_item(self, tmp_path: Path) -> None:
        item_dir = tmp_path / "items" / "NS-001"
        item_dir.mkdir(parents=True)
        runner = FakeRunner(
            {"pytest -q -k T1": (1, "1 failed"), "pytest": (0, "1 passed")}
        )
        result = night_run.run_item(
            HANDOFF,
            [mktask("T1", [], expect="fail")],
            tmp_path,
            runner,
            babysitter=passing_sitter,
        )
        proof = night_run.write_proof(item_dir, result)
        assert proof.exists()
        text = proof.read_text()
        assert "NS-001" in text
        assert "| T1 |" in text
        assert result.status in text


class TestCeilingIsHard:
    """A ceiling that can be overshot is not a ceiling.

    Checking only between tasks lets a run exceed its limit by a whole
    task's cost. The check belongs where the spend happens: immediately
    before the babysitter call that would cross the line.
    """

    def test_the_ceiling_is_never_exceeded(self, tmp_path: Path) -> None:
        handoff = {
            **HANDOFF,
            "budget": {**HANDOFF["budget"], "claude_token_ceiling": 150},
        }
        runner = FakeRunner(
            {
                "git diff --unified=0": (0, "x" * 400),
                "pytest -q -k T1": (1, "1 failed"),
                "pytest": (0, "1 passed"),
            }
        )
        result = night_run.run_item(
            handoff,
            [mktask("T1", [], expect="fail"), mktask("T2", ["T1"])],
            tmp_path,
            runner,
            babysitter=passing_sitter,
        )
        assert result.estimated_tokens <= 150, (
            f"spent {result.estimated_tokens} against a ceiling of 150"
        )
        assert result.status == "parked_budget"

    def test_a_run_that_fits_is_not_parked(self, tmp_path: Path) -> None:
        runner = FakeRunner(
            {
                "git diff --unified=0": (0, "x" * 40),
                "pytest -q -k T1": (1, "1 failed"),
                "pytest": (0, "1 passed"),
            }
        )
        result = night_run.run_item(
            HANDOFF,
            [mktask("T1", [], expect="fail"), mktask("T2", ["T1"])],
            tmp_path,
            runner,
            babysitter=passing_sitter,
        )
        assert result.status == "ready"
        assert result.committed == ["T1", "T2"]

    def test_the_task_that_would_cross_the_line_is_not_committed(
        self, tmp_path: Path
    ) -> None:
        handoff = {
            **HANDOFF,
            "budget": {**HANDOFF["budget"], "claude_token_ceiling": 150},
        }
        runner = FakeRunner(
            {
                "git diff --unified=0": (0, "x" * 400),
                "pytest -q -k T1": (1, "1 failed"),
                "pytest": (0, "1 passed"),
            }
        )
        result = night_run.run_item(
            handoff,
            [mktask("T1", [], expect="fail"), mktask("T2", ["T1"])],
            tmp_path,
            runner,
            babysitter=passing_sitter,
        )
        assert "T2" not in result.committed


class TestRateLimitParksTheRun:
    """A refusal from the provider or the judge stops the night cleanly.

    The reset instant lands in the same `cooldown_until` that
    `scripts/watchdog.sh` already reads, so the OS timer egregore already
    installs becomes the resume-at-renewal scheduler. No second scheduler
    is introduced, because the reset semantics of the usage windows are
    not publicly documented and a second scheduler would have to guess.
    """

    def test_a_rate_limited_evidence_run_parks_the_item(self, tmp_path: Path) -> None:
        runner = FakeRunner(
            {
                "pytest": (
                    1,
                    "API Error: Request rejected (429)\n"
                    "anthropic-ratelimit-tokens-reset: 2099-01-01T00:00:00Z",
                )
            }
        )
        budget = Budget()
        result = night_run.run_item(
            HANDOFF,
            [mktask("T1", [], expect="fail")],
            tmp_path,
            runner,
            babysitter=passing_sitter,
            budget=budget,
        )
        assert result.status == "parked_rate_limit"
        assert budget.cooldown_until is not None
        assert budget.cooldown_until.startswith("2099-01-01")

    def test_an_unparseable_rate_limit_still_parks_with_a_wait(
        self, tmp_path: Path
    ) -> None:
        runner = FakeRunner({"pytest": (1, "API Error: Request rejected (429)")})
        budget = Budget()
        result = night_run.run_item(
            HANDOFF,
            [mktask("T1", [], expect="fail")],
            tmp_path,
            runner,
            babysitter=passing_sitter,
            budget=budget,
        )
        assert result.status == "parked_rate_limit"
        assert budget.cooldown_until is not None

    def test_a_spend_cap_is_named_separately(self, tmp_path: Path) -> None:
        """Waiting out a spend cap can mean waiting until next month."""
        runner = FakeRunner(
            {
                "pytest": (
                    1,
                    "You have reached your API usage limits: You will regain "
                    "access on 2099-09-01 at 00:00 UTC.",
                )
            }
        )
        result = night_run.run_item(
            HANDOFF,
            [mktask("T1", [], expect="fail")],
            tmp_path,
            runner,
            babysitter=passing_sitter,
        )
        assert result.status == "parked_spend_limit"

    def test_an_ordinary_test_failure_is_not_mistaken_for_a_limit(
        self, tmp_path: Path
    ) -> None:
        runner = FakeRunner({"pytest": (1, "1 failed: assert 4 == 5")})
        result = night_run.run_item(
            HANDOFF,
            [mktask("T1", [])],
            tmp_path,
            runner,
            babysitter=lambda **_: ("FAIL", "no", ""),
        )
        assert result.status == "parked_task"


#: A runner script whose keys are ordered most-specific first, because
#: FakeRunner returns the first substring match.
def dirty_script(exit_code: int = 1) -> dict:
    """Scripted git output for a tree with one edited and one new file."""
    return {
        "git diff --name-only": (0, "a/T1.py\n"),
        "git diff --numstat": (0, "3\t1\ta/T1.py\n"),
        "git diff --unified=0": (0, "@@ -1 +1 @@\n-old\n+new\n"),
        "git status --porcelain": (0, " M a/T1.py\n?? a/scratch.tmp\n"),
        "git diff": (0, "diff --git a/a/T1.py b/a/T1.py\n+new line\n"),
        "pytest": (exit_code, "1 failed"),
    }


class TestWorktreeIsCutFromTheProjectRoot:
    """Where `git worktree add` runs decides which repository is cut."""

    def test_the_worktree_add_runs_in_the_project_root(self, tmp_path: Path) -> None:
        """It must not inherit whatever directory the process is in.

        With ``cwd=None`` the command runs wherever the driver happens to
        have been started, so a night run launched from another checkout
        would cut the item's worktree out of the wrong repository.
        """
        runner = FakeRunner({"pytest": (0, "1 passed")})
        night_run.run_item(
            HANDOFF,
            [mktask("T1", [], expect="fail")],
            tmp_path,
            runner,
            babysitter=passing_sitter,
        )
        add = [(c, cwd) for c, cwd in runner.invocations if "worktree add" in c]
        assert add, "the item must get its own worktree"
        assert add[0][1] == tmp_path


class TestParkLeavesACleanTree:
    """A parked item must not leave unjudged edits lying in the worktree.

    The task that did not finish was still dispatched, so the implementer
    already wrote something. It carries no proof row and no commit. Left
    in place it is invisible to the morning review and it is re-applied
    on top of itself when the task is dispatched again.
    """

    def test_a_parked_task_reverts_what_it_left_behind(self, tmp_path: Path) -> None:
        runner = FakeRunner(dirty_script())
        result = night_run.run_item(
            HANDOFF,
            [mktask("T1", [])],
            tmp_path,
            runner,
            babysitter=passing_sitter,
        )
        assert result.status == "parked_task"
        reverts = [c for c in runner.calls if "checkout -- ." in c]
        assert reverts, "the parked tree must be reverted to HEAD"

    def test_what_was_discarded_is_recorded_before_it_is_reverted(
        self, tmp_path: Path
    ) -> None:
        runner = FakeRunner(dirty_script())
        result = night_run.run_item(
            HANDOFF, [mktask("T1", [])], tmp_path, runner, babysitter=passing_sitter
        )
        assert result.discarded is not None
        assert "a/T1.py" in result.discarded.files
        assert result.discarded.diff

    def test_untracked_files_are_recorded_and_not_deleted(self, tmp_path: Path) -> None:
        """Recording beats a blind clean, which would take setup with it."""
        runner = FakeRunner(dirty_script())
        result = night_run.run_item(
            HANDOFF, [mktask("T1", [])], tmp_path, runner, babysitter=passing_sitter
        )
        assert result.discarded is not None
        assert "a/scratch.tmp" in result.discarded.untracked
        assert not [c for c in runner.calls if "clean -fd" in c]

    def test_the_ceiling_park_also_cleans_up(self, tmp_path: Path) -> None:
        handoff = dict(HANDOFF)
        handoff["budget"] = {**HANDOFF["budget"], "claude_token_ceiling": 1}
        runner = FakeRunner(dirty_script(exit_code=0))
        result = night_run.run_item(
            handoff, [mktask("T1", [])], tmp_path, runner, babysitter=passing_sitter
        )
        assert result.status == "parked_budget"
        assert [c for c in runner.calls if "checkout -- ." in c]

    def test_a_clean_tree_records_nothing(self, tmp_path: Path) -> None:
        """No discard section when the implementer left nothing behind."""
        runner = FakeRunner({"pytest": (1, "1 failed")})
        result = night_run.run_item(
            HANDOFF, [mktask("T1", [])], tmp_path, runner, babysitter=passing_sitter
        )
        assert result.status == "parked_task"
        assert result.discarded is None

    def test_the_proof_shows_what_was_discarded(self, tmp_path: Path) -> None:
        runner = FakeRunner(dirty_script())
        result = night_run.run_item(
            HANDOFF, [mktask("T1", [])], tmp_path, runner, babysitter=passing_sitter
        )
        proof = night_run.write_proof(tmp_path / "item", result).read_text()
        assert "Discarded at park" in proof
        assert "a/T1.py" in proof
        assert "a/scratch.tmp" in proof
