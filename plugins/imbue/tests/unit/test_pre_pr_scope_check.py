"""pre_pr_scope_check.sh measures the branch from its merge-base.

With no argument it assumed `main`. In a
master-based repo it died after the header with exit 128 and no
verdict. It also diffed against the base tip, so commits on the base
after the fork counted as branch work.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from _git_repo import commit_lines as _commit_lines
from _git_repo import forked_repo
from _git_repo import git as _git
from _git_repo import git_env as _env

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "pre_pr_scope_check.sh"


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A master-based repo whose `feature` forked before master grew 3000 lines."""
    root = forked_repo(tmp_path)
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


@pytest.mark.parametrize("remote", ["origin", "upstream"])
def test_a_pre_push_remote_argument_is_not_read_as_the_base(
    repo: Path, tmp_path: Path, remote: str
) -> None:
    """A pre-push hook is run as `hook <remote> <url>`.

    A remote added by hand has no refs/remotes/<remote>/HEAD, so reading
    the remote name as the base branch found no merge-base and blocked
    every push with exit 3.
    """
    bare = tmp_path / f"{remote}.git"
    _git(tmp_path, "init", "-q", "--bare", str(bare))
    _git(repo, "remote", "add", remote, str(bare))
    _git(repo, "push", "-q", remote, "master")

    result = _run(repo, remote, str(bare))

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Base branch: master" in result.stdout


@pytest.mark.parametrize("flag", ["-h", "help", "--usage"])
def test_help_prints_usage_and_exits_zero(repo: Path, flag: str) -> None:
    result = _run(repo, flag)
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines()[0].endswith(
        "Usage: pre_pr_scope_check.sh [-h] [-x|-t] [base-branch]"
    )


def test_xtrace_flag_traces_and_still_takes_the_base(repo: Path) -> None:
    result = _run(repo, "-x", "master")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Base branch: master" in result.stdout
    assert "+ " in result.stderr
