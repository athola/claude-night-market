"""conserve's coordination workspace is runtime state, never a commit.

``plugins/conserve/scripts/coordination_workspace.py`` writes
``.coordination/`` in the working directory and archives it to
``.coordination-archive/<timestamp>``. Run from this checkout, both
showed up in ``git status`` and could be swept into a commit.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    "path",
    [
        ".coordination/tasks.json",
        ".coordination-archive/20260923-120000/tasks.json",
        "plugins/conserve/.coordination/tasks.json",
    ],
)
def test_coordination_workspace_paths_are_git_ignored(path: str) -> None:
    result = subprocess.run(
        ["git", "check-ignore", "-q", path],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, f"{path} is not ignored: {result.stderr}"
