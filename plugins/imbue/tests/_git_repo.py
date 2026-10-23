"""Throwaway git repositories for the scope-guard script and hook tests.

Importable as a top-level module because pytest puts this directory on
sys.path for the conftest beside it.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path


def git_env(home: Path, **extra: str) -> dict[str, str]:
    """The caller's environment with git identity pinned and no GIT_/SCOPE_GUARD leak."""
    env = {
        k: v for k, v in os.environ.items() if not k.startswith(("GIT_", "SCOPE_GUARD"))
    }
    env.update(
        HOME=str(home),
        GIT_AUTHOR_NAME="t",
        GIT_AUTHOR_EMAIL="t@t",
        GIT_COMMITTER_NAME="t",
        GIT_COMMITTER_EMAIL="t@t",
        **extra,
    )
    return env


def git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", *args], cwd=repo, env=git_env(repo), check=True, capture_output=True
    )


def commit_lines(repo: Path, name: str, count: int) -> None:
    (repo / name).write_text("".join(f"{name} {i}\n" for i in range(count)))
    git(repo, "add", name)
    git(repo, "commit", "-q", "-m", name)


def forked_repo(tmp_path: Path) -> Path:
    """A master-based repo on branch `feature`, forked before master grew 3000 lines."""
    root = tmp_path / "repo"
    root.mkdir()
    git(root, "init", "-q", "-b", "master")
    commit_lines(root, "base.txt", 1)
    git(root, "branch", "feature")
    commit_lines(root, "upstream.txt", 3000)
    git(root, "checkout", "-q", "feature")
    return root
