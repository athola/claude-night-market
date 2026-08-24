"""A live single-item night run, end to end, against a real repository.

The unit tests drive the walker with a scripted runner. This one drives
it with the real thing: a real ``git init``, a real worktree, a real
pytest process, real diffs, real metering. What it costs in speed it
buys back in the one question the fakes cannot answer, which is whether
the pieces fit together outside the test's own imagination.

Only the provider that writes the code is scripted. It is a real file,
committed into the throwaway repository at the path the driver dispatches
to, so the dispatch is genuine even though the author is not a model.
Set ``EGREGORE_E2E_LIVE=1`` to put the real ``claude`` CLI in the
babysitter's seat instead; that is left out of the default run because
pre-commit runs this suite and a commit should not depend on a network
call or spend on-plan tokens.

This test is also the regression guard for two defects the scripted
tests could not have caught:

- The worktree is cut from ``root``. It deliberately never chdirs, so a
  driver that passed ``cwd=None`` would create the worktree wherever
  pytest happened to be running, which is this repository.
- A parked item leaves a clean tree. The second task's implementer runs
  before the ceiling stops the run, so its edit is on disk with no
  commit and no proof row.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import night_run
import pytest
from claude_babysitter import ClaudeBabysitter

pytestmark = pytest.mark.skipif(
    subprocess.run(["git", "--version"], capture_output=True, check=False).returncode
    != 0,
    reason="the end-to-end run needs git",
)

LIVE = os.environ.get("EGREGORE_E2E_LIVE") == "1"

#: On-plan ceiling for the run. The first task's judgment costs about 60
#: estimated tokens and the second about 115, so this clears the first
#: with room for the pytest output to grow and still stops the second.
CEILING = 120

IMPLEMENTER = '''#!/usr/bin/env python3
"""Stands in for a delegated provider CLI. Writes the task's code."""
import pathlib
import sys

prompt = sys.argv[2]
if "T1" in prompt:
    snippet = "\\n\\ndef add(a, b):\\n    return a + b\\n"
elif "T2" in prompt:
    snippet = "\\n\\ndef mul(a, b):\\n    return a * b\\n"
else:
    print("no task recognised")
    sys.exit(1)
target = pathlib.Path("calc.py")
target.write_text(target.read_text() + snippet)
print("scripted implementer wrote the change")
'''


def _git(*args: str, cwd: Path) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


@pytest.fixture
def project(tmp_path: Path) -> Path:
    """Build a throwaway repository with two failing tests."""
    repo = tmp_path / "project"
    (repo / "tests").mkdir(parents=True)
    (repo / "plugins/conjure/scripts").mkdir(parents=True)

    (repo / "calc.py").write_text('"""A calculator."""\n')
    (repo / "tests/test_add.py").write_text(
        "from calc import add\n\n\ndef test_add():\n    assert add(2, 3) == 5\n"
    )
    (repo / "tests/test_mul.py").write_text(
        "from calc import mul\n\n\ndef test_mul():\n    assert mul(2, 3) == 6\n"
    )
    executor = repo / "plugins/conjure/scripts/delegation_executor.py"
    executor.write_text(IMPLEMENTER)
    executor.chmod(0o755)

    # A real Python repository ignores its own build artifacts. Without
    # this the worktree accumulates `__pycache__/` and `.pytest_cache/`
    # from running the evidence command, and the scope fence -- which
    # reads `git status --porcelain`, and so honors .gitignore -- reports
    # them as edits outside the task's allowlist. The fence is right to
    # do that; the fixture was the thing that did not match reality.
    (repo / ".gitignore").write_text("__pycache__/\n.pytest_cache/\n*.pyc\n")

    _git("init", "-q", "-b", "main", cwd=repo)
    _git("config", "user.email", "night@example.invalid", cwd=repo)
    _git("config", "user.name", "Night Run", cwd=repo)
    _git("add", "-A", cwd=repo)
    _git("commit", "-qm", "the repository before the night shift", cwd=repo)
    return repo


def _task(tid: str, name: str, change: str) -> dict:
    return {
        "id": tid,
        "title": f"add {name}()",
        "change": change,
        "files": ["calc.py"],
        "evidence": {
            "command": f"{sys.executable} -m pytest tests/test_{name}.py -q",
            "expect": "pass",
        },
    }


TASKS = [
    _task("T1", "add", "add a function add(a, b) to calc.py returning a + b"),
    {
        **_task("T2", "mul", "add a function mul(a, b) to calc.py returning a * b"),
        "depends_on": ["T1"],
    },
]


def _babysitter():
    if LIVE:
        return ClaudeBabysitter(timeout=180)

    def scripted(**_):
        return ("PASS", "scripted babysitter", "")

    return scripted


@pytest.fixture
def walked(project: Path):
    """Walk the item once and hand back the result and the worktree."""
    handoff = {
        "item": "E2E-1",
        "branch": "night/e2e-1",
        "base_branch": "main",
        "worktree": ".egregore/worktrees/E2E-1",
        "scope": {"allow_paths": ["calc.py"], "max_diff_lines": 50},
        "implementer": {"provider": "auto", "allow_on_plan_fallback": False},
        "commands": {"full_test": f"{sys.executable} -m pytest tests -q"},
        "budget": {
            "max_attempts_per_task": 1,
            "implementer_timeout_s": 120,
            "claude_token_ceiling": CEILING,
        },
    }
    result = night_run.run_item(
        handoff, TASKS, project, night_run.SubprocessRunner(), babysitter=_babysitter()
    )
    return result, project / ".egregore/worktrees/E2E-1"


class TestALiveItemWalk:
    """The run the plan promised: one item, stopped by its own ceiling."""

    def test_it_stops_at_the_on_plan_ceiling(self, walked) -> None:
        result, _ = walked
        assert result.status == "parked_budget"
        assert "ceiling" in result.reason

    def test_the_task_that_passed_stays_committed(self, walked) -> None:
        """Prove that a stop is not a rollback."""
        result, worktree = walked
        assert result.committed == ["T1"]
        log = subprocess.run(
            ["git", "log", "--oneline"],
            cwd=worktree,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        assert "T1:" in log

    def test_the_ceiling_is_not_crossed(self, walked) -> None:
        """Check the ceiling holds: it is tested before the spend."""
        result, _ = walked
        assert result.estimated_tokens <= CEILING

    def test_the_evidence_is_a_real_pytest_exit_code(self, walked) -> None:
        result, _ = walked
        rows = [row for task in result.tasks for row in task.ledger]
        assert rows
        assert rows[0]["exit"] == 0


class TestTheWorktreeIsCutFromTheProject:
    """Regression guard: this module never chdirs."""

    def test_the_worktree_lands_under_the_project_root(self, walked) -> None:
        _, worktree = walked
        assert worktree.is_dir()
        assert (worktree / "calc.py").is_file()

    def test_no_worktree_was_cut_from_this_repository(self, walked) -> None:
        """Prove the driver did not use the process's own directory."""
        _, _ = walked
        assert not (Path.cwd() / ".egregore/worktrees/E2E-1").exists()


class TestTheParkedTreeIsClean:
    """Regression guard: the unjudged task's edit is recorded, not left."""

    def test_the_second_task_edit_is_reverted(self, walked) -> None:
        _, worktree = walked
        calc = (worktree / "calc.py").read_text()
        assert "def add" in calc
        assert "def mul" not in calc

    def test_git_reports_a_clean_tree(self, walked) -> None:
        _, worktree = walked
        porcelain = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=worktree,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        assert " M calc.py" not in porcelain

    def test_what_was_discarded_is_in_the_proof(self, walked, tmp_path: Path) -> None:
        result, _ = walked
        assert result.discarded is not None
        assert "calc.py" in result.discarded.files
        proof = night_run.write_proof(tmp_path / "item", result).read_text()
        assert "Discarded at park" in proof
        assert "def mul" in proof
