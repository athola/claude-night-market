"""Behavior of the canonical git commit detector in leyline/shell_command.py."""

from __future__ import annotations

import pytest

from leyline.shell_command import git_commit_message_offset, is_git_commit


@pytest.mark.parametrize(
    "command",
    [
        "if true; then git commit -m x; fi",
        "for f in a; do git commit -m x; done",
        "{ git commit -m x; }",
        "time git commit -m x",
        "! git commit -m x",
        "out=$(git commit -m x)",
        "`git commit -m x`",
        "git -C 'my repo' commit -m x",
        'git -C "my repo" commit -m x',
        "sudo -u bob git commit -m x",
        "sudo -E git commit -m x",
    ],
)
def test_compound_and_wrapped_commits_are_detected(command: str) -> None:
    """Shell keywords, groups, substitutions and quoted option values hid commits."""
    assert is_git_commit(command)


@pytest.mark.parametrize(
    "command",
    [
        "git commit-tree HEAD^{tree}",
        'echo "then git commit"',
        "git log --grep commit",
        "timeout git-status",
        "sudo -u bob git status",
    ],
)
def test_non_commits_stay_undetected(command: str) -> None:
    assert not is_git_commit(command)


@pytest.mark.parametrize(
    ("command", "feeder"),
    [
        ("printf 'fix' | git commit -F -", "printf"),
        ("cat msg | sed s/a/b/ | git commit --file=-", "cat"),
        ("git add -A && printf 'fix' | git commit --file - -q", "printf"),
    ],
)
def test_message_read_from_stdin_starts_at_the_pipeline(
    command: str, feeder: str
) -> None:
    """With ``-F -`` the message arrives from the commands piped into the commit."""
    offset = git_commit_message_offset(command)
    assert offset is not None
    assert command[offset:].startswith(feeder)


@pytest.mark.parametrize(
    "command",
    [
        "printf 'x' > notes.txt && git commit -m clean",
        "printf 'x' | tee notes.txt; git commit -F msg.txt",
        "echo hi | git commit -m clean",
    ],
)
def test_message_offset_is_the_commit_when_stdin_is_not_the_message(
    command: str,
) -> None:
    offset = git_commit_message_offset(command)
    assert offset is not None
    assert command[offset:].startswith("git commit")


def test_message_offset_is_none_without_a_commit() -> None:
    assert git_commit_message_offset("git status") is None
