"""awesome-submit.sh: a dry run changes nothing, and a rerun can push.

Shell review S0-3 and S0-17. `--dry-run` created and synced forks before
it reached its own dry-run check. A rerun after a failed `gh pr create`
could not push: the shallow single-branch clone has no tracking ref for
the branch, so `--force-with-lease` was rejected as stale, and set -e
abandoned every remaining target.

gh is a shim. `gh repo clone` makes a real shallow clone of a local bare
repository, so the push and its lease check are git's own.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "v9.9.9"
REPOS = (
    "vincentkoc_awesome-openclaw",
    "SamurAIGPT_awesome-openclaw",
    "alice_awesome-openclaw-vincentkoc",
    "alice_awesome-openclaw-SamurAIGPT",
)

GH_SHIM = """#!/bin/sh
printf '%s\\n' "$*" >> "{calls}"
case "$1 $2" in
  "auth status") exit 0 ;;
  "api user") echo alice ;;
  "pr list") exit 0 ;;
  "repo view") echo name ;;
  "repo clone")
    src=$(printf '%s' "$3" | tr / _); dest="$4"; shift 4
    [ "$1" = "--" ] && shift
    git clone -q "$@" "file://{remotes}/$src" "$dest" ;;
esac
exit 0
"""


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


def _sandbox(tmp_path: Path) -> tuple[Path, Path, dict[str, str]]:
    repo = tmp_path / "repo"
    (repo / "scripts").mkdir(parents=True)
    shutil.copy2(ROOT / "scripts" / "awesome-submit.sh", repo / "scripts")
    # The script sources its logging library from its own directory.
    shutil.copy2(ROOT / "scripts" / "logging.sh", repo / "scripts")
    remotes = tmp_path / "remotes"
    seed = tmp_path / "seed"
    seed.mkdir()
    _git(seed, "init", "-q", "-b", "main")
    (seed / "README.md").write_text("# Awesome\n\n## Skills\n\n- other\n")
    _git(seed, "add", "README.md")
    _git(seed, "commit", "-q", "-m", "seed")
    for name in REPOS:
        _git(tmp_path, "clone", "-q", "--bare", str(seed), str(remotes / name))
    calls = tmp_path / "gh-calls.log"
    shims = tmp_path / "shims"
    shims.mkdir()
    gh = shims / "gh"
    gh.write_text(GH_SHIM.format(calls=calls, remotes=remotes))
    gh.chmod(0o755)
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(
        PATH=f"{shims}:{env['PATH']}",
        HOME=str(tmp_path),
        GIT_AUTHOR_NAME="t",
        GIT_AUTHOR_EMAIL="t@t",
        GIT_COMMITTER_NAME="t",
        GIT_COMMITTER_EMAIL="t@t",
    )
    return repo, remotes, env


def _run(repo: Path, env: dict[str, str], *args: str):
    return subprocess.run(
        ["/bin/bash", str(repo / "scripts" / "awesome-submit.sh"), VERSION, *args],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )


def test_a_dry_run_creates_and_syncs_nothing(tmp_path: Path) -> None:
    repo, _remotes, env = _sandbox(tmp_path)
    result = _run(repo, env, "--dry-run")
    assert result.returncode == 0, result.stdout + result.stderr
    calls = (tmp_path / "gh-calls.log").read_text()
    assert "repo fork" not in calls
    assert "repo sync" not in calls
    assert "pr create" not in calls
    assert result.stdout.count("Dry run") == 2


def test_a_rerun_pushes_over_a_branch_left_by_a_failed_run(tmp_path: Path) -> None:
    repo, remotes, env = _sandbox(tmp_path)
    branch = f"add-night-market-{VERSION}"
    for fork in REPOS[2:]:
        work = tmp_path / f"work-{fork}"
        _git(tmp_path, "clone", "-q", str(remotes / fork), str(work))
        _git(work, "checkout", "-q", "-b", branch)
        (work / "README.md").write_text("earlier attempt\n")
        _git(work, "commit", "-qam", "earlier attempt")
        _git(work, "push", "-q", "origin", branch)
    result = _run(repo, env)
    assert result.returncode == 0, result.stdout + result.stderr
    calls = (tmp_path / "gh-calls.log").read_text()
    assert calls.count("pr create") == 2


def test_a_first_run_pushes_a_new_branch(tmp_path: Path) -> None:
    """An empty lease means the branch must not exist yet."""
    repo, _remotes, env = _sandbox(tmp_path)
    result = _run(repo, env)
    assert result.returncode == 0, result.stdout + result.stderr
    assert (tmp_path / "gh-calls.log").read_text().count("pr create") == 2
