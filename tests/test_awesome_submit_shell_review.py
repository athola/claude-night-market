"""awesome-submit.sh: a dry run changes nothing, and a rerun can push.

`--dry-run` created and synced forks before
it reached its own dry-run check. A rerun after a failed `gh pr create`
could not push: the shallow single-branch clone has no tracking ref for
the branch, so `--force-with-lease` was rejected as stale, and set -e
abandoned every remaining target.

Each target also carries its own submission rules. SamurAIGPT/awesome-openclaw
was transferred and renamed to a Meta Muse connector catalog, and the script
followed the redirect: it opened a PR there and appended the entry after the
README footer, outside any list. vincentkoc/awesome-openclaw takes no PR
without an approved issue and asks maintainers to disclose affiliation.

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
TARGET = "vincentkoc/awesome-openclaw"
SECTION = "## Skills and Skill Indexes"
REPOS = (
    "vincentkoc_awesome-openclaw",
    "alice_awesome-openclaw-vincentkoc",
)
README = f"# Awesome\n\n{SECTION}\n\n- other skill index\n\n## Plugins\n\n- a plugin\n"

GH_SHIM = """#!/bin/sh
printf '%s\\n' "$*" >> "{calls}"
case "$1 $2" in
  "auth status") exit 0 ;;
  "api user") echo alice ;;
  "api repos/"*) echo "{full_name}" ;;
  "pr list") exit 0 ;;
  "pr create") printf '%s\\n' "$*" > "{pr_args}" ;;
  "repo view") echo name ;;
  "repo sync") [ -n "{sync_fails}" ] && {{ echo "sync conflict" >&2; exit 1; }} ;;
  "repo clone")
    src=$(printf '%s' "$3" | tr / _); dest="$4"; shift 4
    [ "$1" = "--" ] && shift
    git clone -q "$@" "file://{remotes}/$src" "$dest" ;;
esac
exit 0
"""


def _git(cwd: Path, *args: str) -> None:
    # A CI runner has no git identity, and Linux git will not guess one
    # from the hostname the way macOS git does.
    subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@t", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
    )


def _sandbox(
    tmp_path: Path,
    *,
    sync_fails: bool = False,
    readme: str = README,
    full_name: str = TARGET,
) -> tuple[Path, Path, dict[str, str]]:
    repo = tmp_path / "repo"
    (repo / "scripts").mkdir(parents=True)
    shutil.copy2(ROOT / "scripts" / "awesome-submit.sh", repo / "scripts")
    # The script sources its logging library from its own directory.
    shutil.copy2(ROOT / "scripts" / "logging.sh", repo / "scripts")
    remotes = tmp_path / "remotes"
    seed = tmp_path / "seed"
    seed.mkdir()
    _git(seed, "init", "-q", "-b", "main")
    (seed / "README.md").write_text(readme)
    _git(seed, "add", "README.md")
    _git(seed, "commit", "-q", "-m", "seed")
    for name in REPOS:
        _git(tmp_path, "clone", "-q", "--bare", str(seed), str(remotes / name))
    calls = tmp_path / "gh-calls.log"
    shims = tmp_path / "shims"
    shims.mkdir()
    gh = shims / "gh"
    gh.write_text(
        GH_SHIM.format(
            calls=calls,
            remotes=remotes,
            sync_fails="yes" if sync_fails else "",
            full_name=full_name,
            pr_args=tmp_path / "pr-args.log",
        )
    )
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


def _calls(tmp_path: Path) -> str:
    return (tmp_path / "gh-calls.log").read_text()


def _pushed_readme(tmp_path: Path, remotes: Path) -> str:
    work = tmp_path / "pushed"
    _git(
        tmp_path,
        "clone",
        "-q",
        "-b",
        f"add-night-market-{VERSION}",
        str(remotes / REPOS[1]),
        str(work),
    )
    return (work / "README.md").read_text()


def test_a_dry_run_creates_and_syncs_nothing(tmp_path: Path) -> None:
    repo, _remotes, env = _sandbox(tmp_path)
    result = _run(repo, env, "--dry-run")
    assert result.returncode == 0, result.stdout + result.stderr
    calls = _calls(tmp_path)
    assert "repo fork" not in calls
    assert "repo sync" not in calls
    assert "pr create" not in calls
    assert result.stdout.count("Dry run") == 1


def test_without_an_approved_issue_nothing_is_forked_or_opened(
    tmp_path: Path,
) -> None:
    """The list closes drive-by PRs: the issue comes first."""
    repo, _remotes, env = _sandbox(tmp_path)
    result = _run(repo, env)
    assert result.returncode == 0, result.stdout + result.stderr
    calls = _calls(tmp_path)
    assert "repo fork" not in calls
    assert "pr create" not in calls
    assert "Add Resource Request" in result.stdout + result.stderr


def test_a_first_run_pushes_a_new_branch(tmp_path: Path) -> None:
    """An empty lease means the branch must not exist yet."""
    repo, _remotes, env = _sandbox(tmp_path)
    result = _run(repo, env, "--issue", f"{TARGET}#42")
    assert result.returncode == 0, result.stdout + result.stderr
    assert _calls(tmp_path).count("pr create") == 1


def test_the_pr_links_the_issue_and_discloses_affiliation(tmp_path: Path) -> None:
    repo, _remotes, env = _sandbox(tmp_path)
    _run(repo, env, "--issue", f"{TARGET}#42")
    pr_args = (tmp_path / "pr-args.log").read_text()
    assert f"{TARGET}#42" in pr_args
    assert "I maintain" in pr_args


def test_the_entry_goes_at_the_end_of_its_section(tmp_path: Path) -> None:
    repo, remotes, env = _sandbox(tmp_path)
    _run(repo, env, "--issue", f"{TARGET}#42")
    readme = _pushed_readme(tmp_path, remotes)
    section = readme.split(SECTION, 1)[1].split("## Plugins", 1)[0]
    assert "night-market" in section
    assert readme.rstrip().endswith("- a plugin")


def test_a_list_without_the_section_is_refused(tmp_path: Path) -> None:
    """No end-of-file append: a line after the footer sits in no list."""
    repo, _remotes, env = _sandbox(tmp_path, readme="# Awesome\n\n## Other\n\n- x\n")
    result = _run(repo, env, "--issue", f"{TARGET}#42")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "pr create" not in _calls(tmp_path)
    assert SECTION in result.stdout + result.stderr


def test_a_renamed_target_is_skipped(tmp_path: Path) -> None:
    """A transferred repo is a different list with its own scope."""
    repo, _remotes, env = _sandbox(
        tmp_path, full_name="Anil-matcha/awesome-muse-connectors"
    )
    result = _run(repo, env, "--issue", f"{TARGET}#42")
    assert result.returncode == 0, result.stdout + result.stderr
    calls = _calls(tmp_path)
    assert "repo fork" not in calls
    assert "pr create" not in calls
    assert "Anil-matcha/awesome-muse-connectors" in result.stdout + result.stderr


def test_a_rerun_pushes_over_a_branch_left_by_a_failed_run(tmp_path: Path) -> None:
    repo, remotes, env = _sandbox(tmp_path)
    branch = f"add-night-market-{VERSION}"
    work = tmp_path / "work"
    _git(tmp_path, "clone", "-q", str(remotes / REPOS[1]), str(work))
    _git(work, "checkout", "-q", "-b", branch)
    (work / "README.md").write_text("earlier attempt\n")
    _git(work, "commit", "-qam", "earlier attempt")
    _git(work, "push", "-q", "origin", branch)
    result = _run(repo, env, "--issue", f"{TARGET}#42")
    assert result.returncode == 0, result.stdout + result.stderr
    assert _calls(tmp_path).count("pr create") == 1


def test_a_failed_fork_sync_skips_the_target(tmp_path: Path) -> None:
    """A stale fork would carry the PR against an old main."""
    repo, _remotes, env = _sandbox(tmp_path, sync_fails=True)
    result = _run(repo, env, "--issue", f"{TARGET}#42")
    calls = _calls(tmp_path)
    assert "repo clone" not in calls
    assert "pr create" not in calls
    assert "fork sync failed" in result.stdout + result.stderr
