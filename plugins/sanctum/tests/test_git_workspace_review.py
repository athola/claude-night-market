# ruff: noqa: D101,D102,D103,PLR2004,E501
"""Contract tests for the git-workspace-review skill.

The skill is instructions, not code: these tests pin the claims in its
SKILL.md that downstream workflows rely on, so dropping a step or a command
from the instructions fails here.
"""

from __future__ import annotations

import re
from pathlib import Path

SKILL_FILE = (
    Path(__file__).resolve().parents[1] / "skills" / "git-workspace-review" / "SKILL.md"
)


def _sections(text: str) -> dict[str, str]:
    """Map each ``## `` heading to the body under it."""
    parts = re.split(r"^## (.+)$", text, flags=re.MULTILINE)
    return {parts[i].strip(): parts[i + 1] for i in range(1, len(parts) - 1, 2)}


def _tracked_todos(text: str) -> list[str]:
    body = _sections(text)["Required Progress Tracking"]
    return re.findall(r"^\d+\. `(git-review:[a-z-]+)`", body, flags=re.MULTILINE)


class TestGitWorkspaceReviewSkill:
    REQUIRED_TODOS = ["git-review:repo-confirmed", "git-review:status-overview"]

    def test_repo_confirmed_step_runs_pwd_and_git_status(self) -> None:
        """The repo-confirmed step checks the directory and the branch status.

        GIVEN the SKILL.md step for `repo-confirmed`
        WHEN its instructions are read
        THEN it runs `pwd` and `git status -sb` and records branch and upstream
        """
        step = _sections(SKILL_FILE.read_text())[
            "Step 1: Confirm Repository (`repo-confirmed`)"
        ]
        assert "`pwd`" in step
        assert "`git status -sb`" in step
        assert "upstream" in step

    def test_diff_steps_name_cached_and_plain_git_diff_forms(self) -> None:
        """The diff steps read the staged set, and the unstaged set as fallback.

        GIVEN the SKILL.md steps for `diff-stat` and `diff-details`
        WHEN their instructions are read
        THEN each names the --cached form and the plain form of its git command
        """
        sections = _sections(SKILL_FILE.read_text())
        stat = sections["Step 4: Review Diff Statistics (`diff-stat`)"]
        details = sections["Step 5: Review Detailed Diff (`diff-details`)"]
        assert "`git diff --cached --stat`" in stat
        assert "`git diff --stat`" in stat
        assert "`git diff --cached`" in details
        assert "`git diff`" in details

    def test_tracked_todos_match_step_headings_in_order(self) -> None:
        """Every tracked todo has a step that completes it, in the same order.

        GIVEN the Required Progress Tracking list
        WHEN it is compared with the numbered step headings
        THEN it starts with the two required todos and each todo names a step
        """
        text = SKILL_FILE.read_text()
        todos = _tracked_todos(text)
        step_ids = re.findall(r"^## Step \d+: .+ \(`([a-z-]+)`\)$", text, re.MULTILINE)

        assert todos[:2] == self.REQUIRED_TODOS
        assert [todo.removeprefix("git-review:") for todo in todos] == step_ids
