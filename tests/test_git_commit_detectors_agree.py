"""One definition of "this Bash command runs git commit".

gauntlet and imbue each kept a copy of the detector and they drifted: they
disagreed on 3 of 10 inputs, so imbue's vows and gauntlet's precommit gate
saw different commits (ARCH-3). The canonical module is
leyline/shell_command.py; both plugins carry a generated copy.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


CANONICAL = _load(
    "shell_command_canonical", ROOT / "plugins/leyline/src/leyline/shell_command.py"
)
COPIES = {
    "gauntlet": ROOT
    / "plugins/gauntlet/src/gauntlet/_vendored_leyline_shell_command.py",
    "imbue": ROOT / "plugins/imbue/hooks/shared/_vendored_leyline_shell_command.py",
}

TABLE = [
    ("git commit -m x", True),
    ("git add -A && git commit -m x", True),
    ("git -C repo commit -m x", True),
    ("git --git-dir .git commit -m x", True),
    ("git --no-pager commit", True),
    ("GIT_AUTHOR_NAME=a git commit -m x", True),
    ("/usr/bin/git commit -m x", True),
    ("command git commit -m x", True),
    ("env FOO=1 git commit -m x", True),
    ("(cd sub && git commit -m x)", True),
    ("git commit-tree HEAD^{tree}", False),
    ('echo "x; git commit -m y"', False),
    ("git log --grep commit", False),
    ("gitk commit", False),
    ("git status", False),
]


@pytest.mark.parametrize(("command", "expected"), TABLE)
def test_canonical_detector(command: str, expected: bool) -> None:
    assert CANONICAL.is_git_commit(command) is expected


@pytest.mark.parametrize("plugin", sorted(COPIES))
def test_git_commit_detectors_agree(plugin: str) -> None:
    copy = _load(f"shell_command_{plugin}", COPIES[plugin])
    for command, expected in TABLE:
        assert copy.is_git_commit(command) is expected, command


@pytest.mark.parametrize(
    ("command", "segment"),
    [
        ("git commit -m x && echo done", "git commit -m x "),
        ("git commit -m 'a; b' | cat", "git commit -m 'a; b' "),
        ("git commit -F - <<EOF\nmsg\nEOF", "git commit -F - <<EOF\nmsg\nEOF"),
        ("git add . && git commit -m y", "git commit -m y"),
    ],
)
def test_git_commit_segment_stops_at_the_next_chain_operator(
    command: str, segment: str
) -> None:
    """The emoji vow read everything after the commit as its message (IMB-15).

    A newline does not end the segment: a heredoc message spans lines.
    """
    start = CANONICAL.git_commit_offset(command)
    end = CANONICAL.git_commit_end(command)
    assert command[start:end] == segment
