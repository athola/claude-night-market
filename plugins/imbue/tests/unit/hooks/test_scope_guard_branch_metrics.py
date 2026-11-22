"""Scope-guard measures the branch's own work, from either default branch.

Both hooks diffed against the base branch
tip, so commits landing on main after the fork counted as branch work.
The SessionStart hook knew only `main`, so in a master-based repo it
never warned. Its reminder carried a literal backslash-n. And the
maintenance skip matched "/status" anywhere in the prompt, including
inside a file path.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
from _git_repo import commit_authored_days_ago, forked_repo, git_env
from _git_repo import commit_lines as _commit_lines

HOOKS = Path(__file__).resolve().parents[3] / "hooks"
PLUGIN_ROOT = HOOKS.parent


def _env(home: Path, **thresholds: str) -> dict[str, str]:
    return git_env(
        home,
        XDG_CACHE_HOME=str(home / "cache"),
        SCOPE_GUARD_CACHE_TTL="0",
        CLAUDE_PLUGIN_ROOT=str(PLUGIN_ROOT),
        **thresholds,
    )


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A master-based repo on branch `feature`, forked before master grew."""
    return forked_repo(tmp_path)


def _context(repo: Path, hook: str, stdin: str, **thresholds: str) -> str:
    result = subprocess.run(
        ["/bin/bash", str(HOOKS / hook)],
        input=stdin,
        cwd=repo,
        env=_env(repo.parent, **thresholds),
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


@pytest.mark.parametrize(
    ("hook", "stdin"),
    [
        ("user-prompt-submit.sh", PROMPT),
        ("session-start.sh", START),
    ],
)
def test_session_start_and_prompt_hook_agree_on_zone_for_same_branch(
    repo: Path, hook: str, stdin: str
) -> None:
    """SessionStart went yellow at 1000 lines while the prompt hook waited
    for 1500, and SessionStart ignored the SCOPE_GUARD_* overrides (IMB-14).

    Both now take pre_pr_scope_check.sh's meaning, where yellow begins
    above SCOPE_GUARD_GREEN_LINES (1000), so the hooks and the pre-PR
    check give one branch one zone (M4).
    """
    _commit_lines(repo, "feature.txt", 900)
    assert "YELLOW" not in _context(repo, hook, stdin)
    _commit_lines(repo, "more.txt", 300)
    assert "YELLOW" in _context(repo, hook, stdin)


@pytest.mark.parametrize(
    ("hook", "stdin"),
    [
        ("user-prompt-submit.sh", PROMPT),
        ("session-start.sh", START),
    ],
)
def test_days_on_branch_count_from_the_author_date(
    repo: Path, hook: str, stdin: str
) -> None:
    """A rebase reset the committer date, so a 20-day branch read 0 days (M3)."""
    commit_authored_days_ago(repo, "old.txt", 20)
    assert "RED" in _context(repo, hook, stdin)


@pytest.mark.parametrize(
    ("hook", "stdin"),
    [
        ("user-prompt-submit.sh", PROMPT),
        ("session-start.sh", START),
    ],
)
def test_hooks_read_the_green_thresholds_the_pre_pr_check_reads(
    repo: Path, hook: str, stdin: str
) -> None:
    """The hooks ignored SCOPE_GUARD_GREEN_*, which the pre-PR check uses (M4)."""
    _commit_lines(repo, "feature.txt", 150)
    assert "YELLOW" in _context(repo, hook, stdin, SCOPE_GUARD_GREEN_LINES="100")
