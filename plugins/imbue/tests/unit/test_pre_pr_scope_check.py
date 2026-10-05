"""pre_pr_scope_check.sh measures the branch from its merge-base.

Shell review S1-5 and S1-6. With no argument it assumed `main`. In a
master-based repo it died after the header with exit 128 and no
verdict. It also diffed against the base tip, so commits on the base
after the fork counted as branch work.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "pre_pr_scope_check.sh"


def _env(home: Path) -> dict[str, str]:
    env = {
        k: v for k, v in os.environ.items() if not k.startswith(("GIT_", "SCOPE_GUARD"))
    }
    env.update(
        HOME=str(home),
        GIT_AUTHOR_NAME="t",
        GIT_AUTHOR_EMAIL="t@t",
        GIT_COMMITTER_NAME="t",
        GIT_COMMITTER_EMAIL="t@t",
    )
    return env


def _git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", *args], cwd=repo, env=_env(repo), check=True, capture_output=True
    )


def _commit_lines(repo: Path, name: str, count: int) -> None:
    (repo / name).write_text("".join(f"{name} {i}\n" for i in range(count)))
    _git(repo, "add", name)
    _git(repo, "commit", "-q", "-m", name)


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A master-based repo whose `feature` forked before master grew 3000 lines."""
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init", "-q", "-b", "master")
    _commit_lines(root, "base.txt", 1)
    _git(root, "branch", "feature")
    _commit_lines(root, "upstream.txt", 3000)
    _git(root, "checkout", "-q", "feature")
    _commit_lines(root, "mine.txt", 1)
    return root


def _run(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["/bin/bash", str(SCRIPT), *args],
        cwd=repo,
        env=_env(repo.parent),
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )


def test_a_master_repo_gets_a_verdict_without_an_argument(repo: Path) -> None:
    result = _run(repo)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Base branch: master" in result.stdout
    assert "GREEN ZONE" in result.stdout


def test_upstream_commits_are_not_counted(repo: Path) -> None:
    """A one-line branch read 3001 lines and landed in the red zone."""
    result = _run(repo, "master")
    assert result.returncode == 0, result.stdout
    assert "RED" not in result.stdout


def test_a_named_base_that_does_not_exist_is_an_error(repo: Path) -> None:
    result = _run(repo, "no-such-branch")
    assert result.returncode == 3
    assert "no-such-branch" in result.stderr
