"""The mandated shellcheck gate must scan the repository and be reachable.

``.claude/rules/shell-scripts.md`` says "All shell scripts must pass
``scripts/shellcheck.sh``". Three defects stood between that sentence and
anything a contributor could run.

The scan root came from ``${MYDIR%/*}``, and that expansion returns its
input unchanged when the input has no slash. Invoked the way the script's
own ``usage()`` prints it, ``scripts/shellcheck.sh``, ``MYDIR`` was
``scripts`` and so was the root: 14 files scanned, every hook script
missed, and coverage that moved when the caller typed ``./scripts/...``
instead.

The dialect was pinned to ``sh`` and passed to ``shellcheck -s``, which
overrides the shebang. 37 of the 39 scripts declare bash, so correct bash
was reported as an SC3xxx portability violation against a target no
script claimed.

Sourcing ``logging.sh`` raised SC1091 because shellcheck does not follow
a source without ``-x``, and the runner treated any non-zero exit as a
failure, so the gate failed on itself and could not pass on a clean tree.

The fourth assertion is about wiring. A gate in no Makefile target, no
pre-commit hook and no CI workflow costs more as a claim than it returns
as a check.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
GATE = "scripts/shellcheck.sh"

pytestmark = pytest.mark.skipif(
    shutil.which("shellcheck") is None, reason="shellcheck is not installed"
)


def _run_gate(
    *args: str, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["sh", GATE, *args],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        env=env,
        timeout=600,
        check=False,
    )


def test_gate_scans_hook_scripts_under_plugins() -> None:
    """Invoked the way its own usage() prints it, the gate reaches plugins/."""
    trace = _run_gate("-t")
    invoked = [
        line
        for line in trace.stderr.splitlines()
        if line.lstrip("+ ").startswith("shellcheck ")
    ]
    assert any(
        "plugins/imbue/hooks/user-prompt-submit.sh" in line for line in invoked
    ), (
        "the gate never handed a plugin hook to shellcheck; it scanned "
        f"{len(invoked)} files"
    )


def test_gate_scans_every_tracked_shell_script() -> None:
    """Coverage is the tracked set, not one directory."""
    tracked = subprocess.run(
        ["git", "ls-files", "*.sh"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    trace = _run_gate("-t")
    invoked = [
        line
        for line in trace.stderr.splitlines()
        if line.lstrip("+ ").startswith("shellcheck ")
    ]
    assert len(invoked) == len(tracked), (
        f"gate scanned {len(invoked)} files, git tracks {len(tracked)}"
    )


def test_gate_passes_on_a_clean_tree() -> None:
    """A gate that cannot report success is not a gate."""
    result = _run_gate()
    assert result.returncode == 0, (
        f"scripts/shellcheck.sh failed on the tree:\n{result.stdout}\n{result.stderr}"
    )


def test_gate_fails_loudly_when_shellcheck_is_absent(tmp_path: Path) -> None:
    """A missing checker must not read as a pass.

    Trimming PATH to the system directories is not enough: Ubuntu installs
    shellcheck in ``/usr/bin``. The PATH here links every system tool
    except shellcheck.
    """
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    for system_dir in ("/usr/bin", "/bin"):
        for tool in Path(system_dir).iterdir():
            link = bin_dir / tool.name
            if tool.name != "shellcheck" and not link.exists():
                link.symlink_to(tool)
    env = os.environ.copy()
    env["PATH"] = str(bin_dir)
    result = _run_gate(env=env)
    assert result.returncode != 0
    assert "shellcheck" in result.stderr


def test_gate_fails_when_not_run_inside_a_git_worktree(tmp_path: Path) -> None:
    """An empty file list from a failed ``git ls-files`` is not a pass.

    The list came from a command substitution inside a heredoc, where a
    non-zero exit does not trip ``set -e``, so outside a worktree the gate
    scanned nothing and printed "All scripts passed."
    """
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir()
    for name in ("shellcheck.sh", "logging.sh"):
        shutil.copy(REPO_ROOT / "scripts" / name, scripts_dir / name)
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env["GIT_CEILING_DIRECTORIES"] = str(tmp_path.parent)
    result = subprocess.run(
        ["sh", "scripts/shellcheck.sh"],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        env=env,
        timeout=60,
        check=False,
    )
    assert result.returncode != 0, (
        f"gate passed with no files to scan:\n{result.stdout}\n{result.stderr}"
    )
    assert "All scripts passed" not in result.stdout + result.stderr


def test_gate_is_reachable_from_the_root_lint_target() -> None:
    """The rule's sentence has to name something a contributor can run."""
    makefile = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    assert "scripts/shellcheck.sh" in makefile, (
        "no root Makefile target runs the mandated gate, so it is a claim "
        "rather than a check"
    )
