"""Scope-guard measures the branch's own work, from either default branch.

Shell review S2-4 to S2-8. Both hooks diffed against the base branch
tip, so commits landing on main after the fork counted as branch work.
The SessionStart hook knew only `main`, so in a master-based repo it
never warned. Its reminder carried a literal backslash-n. And the
maintenance skip matched "/status" anywhere in the prompt, including
inside a file path.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

HOOKS = Path(__file__).resolve().parents[3] / "hooks"
PLUGIN_ROOT = HOOKS.parent


def _git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", *args], cwd=repo, env=_env(repo), check=True, capture_output=True
    )


def _env(home: Path) -> dict[str, str]:
    env = {
        k: v for k, v in os.environ.items() if not k.startswith(("GIT_", "SCOPE_GUARD"))
    }
    env.update(
        HOME=str(home),
        XDG_CACHE_HOME=str(home / "cache"),
        SCOPE_GUARD_CACHE_TTL="0",
        CLAUDE_PLUGIN_ROOT=str(PLUGIN_ROOT),
        GIT_AUTHOR_NAME="t",
        GIT_AUTHOR_EMAIL="t@t",
        GIT_COMMITTER_NAME="t",
        GIT_COMMITTER_EMAIL="t@t",
    )
    return env


def _commit_lines(repo: Path, name: str, count: int) -> None:
    (repo / name).write_text("".join(f"line {i}\n" for i in range(count)))
    _git(repo, "add", name)
    _git(repo, "commit", "-q", "-m", name)


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A master-based repo on branch `feature`, forked before master grew."""
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init", "-q", "-b", "master")
    _commit_lines(root, "base.txt", 1)
    _git(root, "branch", "feature")
    _commit_lines(root, "upstream.txt", 3000)
    _git(root, "checkout", "-q", "feature")
    return root


def _context(repo: Path, hook: str, stdin: str) -> str:
    result = subprocess.run(
        ["/bin/bash", str(HOOKS / hook)],
        input=stdin,
        cwd=repo,
        env=_env(repo.parent),
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    out = json.loads(result.stdout)
    return out.get("hookSpecificOutput", {}).get("additionalContext", "")


PROMPT = '{"prompt": "add a feature"}\n'
START = '{"source": "startup"}\n'


@pytest.mark.parametrize(
    ("hook", "stdin"),
    [
        ("user-prompt-submit.sh", PROMPT),
        ("session-start.sh", START),
    ],
)
def test_upstream_commits_are_not_branch_work(
    repo: Path, hook: str, stdin: str
) -> None:
    """3000 lines landed on master after the fork; the branch has none."""
    assert "RED" not in _context(repo, hook, stdin)


@pytest.mark.parametrize(
    ("hook", "stdin"),
    [
        ("user-prompt-submit.sh", PROMPT),
        ("session-start.sh", START),
    ],
)
def test_a_large_branch_off_master_is_red(repo: Path, hook: str, stdin: str) -> None:
    """SessionStart tried only `main` and stayed silent here."""
    _commit_lines(repo, "feature.txt", 2500)
    assert "RED" in _context(repo, hook, stdin)


def test_session_reminder_uses_real_newlines(repo: Path) -> None:
    """The reminder decoded with a literal backslash-n."""
    _commit_lines(repo, "feature.txt", 2500)
    context = _context(repo, "session-start.sh", START)
    assert "\\n" not in context
    assert "\n\n**SCOPE-GUARD RED ZONE**" in context


@pytest.mark.parametrize(
    "prompt",
    [
        "add a feature to src/status_page.py",
        "fix docs/catchup/notes.md",
    ],
)
def test_a_path_containing_a_command_name_is_still_checked(
    repo: Path, prompt: str
) -> None:
    """The skip matched "/status" anywhere, so the guard went quiet."""
    _commit_lines(repo, "feature.txt", 2500)
    stdin = json.dumps({"prompt": prompt}) + "\n"
    assert "RED" in _context(repo, "user-prompt-submit.sh", stdin)


@pytest.mark.parametrize("prompt", ["/status", "  /catchup now", "/sanctum:catchup"])
def test_a_maintenance_command_is_still_skipped(repo: Path, prompt: str) -> None:
    _commit_lines(repo, "feature.txt", 2500)
    stdin = json.dumps({"prompt": prompt}) + "\n"
    assert _context(repo, "user-prompt-submit.sh", stdin) == ""
