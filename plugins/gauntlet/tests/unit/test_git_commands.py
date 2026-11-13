"""Commit detection matches what the harness `if` gate admits.

The gate tests each shell segment on its own, so a hook that only
checks the start of the whole command skips `git add -A && git commit`,
the form agents use most.
"""

from __future__ import annotations

import pytest

from gauntlet.git_commands import is_git_commit


@pytest.mark.unit
@pytest.mark.parametrize(
    "command",
    [
        "git commit -m x",
        "git   commit --amend",
        "git add -A && git commit -m x",
        "cd repo && git commit -m x",
        "git status; git commit -m x",
        "git -C repo commit -m x",
        "git -c user.name=x commit -m x",
    ],
)
def test_commit_forms_are_detected(command: str) -> None:
    assert is_git_commit(command)


@pytest.mark.unit
@pytest.mark.parametrize(
    "command",
    [
        "git status",
        "git log --grep commit",
        "echo 'git commit'",
        "git push",
        "git commit-tree HEAD^{tree} -m x",
        "git commit-graph write",
    ],
)
def test_non_commit_commands_are_not_detected(command: str) -> None:
    assert not is_git_commit(command)
