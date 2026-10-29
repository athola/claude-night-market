"""The generated TDD hook must put its advice where the model reads it.

It printed plain text and exited 1, and the hooks.json entry appended
``|| true``. Exit-0 PreToolUse stdout that is not JSON never reaches the
model, and the advice was dropped. The hook stays advisory: it never
blocks a commit, and reports through ``additionalContext``.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

TEMPLATE = (
    Path(__file__).resolve().parents[1]
    / "templates"
    / "hooks"
    / "pre_commit_tdd.py.template"
)


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """An empty git repository to stage files in."""
    if shutil.which("git") is None:
        pytest.skip("git is not installed")
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    return tmp_path


def _stage(repo: Path, *names: str) -> None:
    for name in names:
        target = repo / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("x = 1\n")
    subprocess.run(["git", "add", *names], cwd=repo, check=True)


def _run_hook(repo: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(TEMPLATE)],
        cwd=repo,
        input=json.dumps({"tool_name": "Bash"}),
        capture_output=True,
        text=True,
        check=False,
    )


def test_untested_implementation_is_reported_as_additional_context(
    repo: Path,
) -> None:
    """The advice reaches the model and the commit is not blocked."""
    _stage(repo, "src/app.py")

    result = _run_hook(repo)

    assert result.returncode == 0
    output = json.loads(result.stdout)["hookSpecificOutput"]
    assert output["hookEventName"] == "PreToolUse"
    assert "src/app.py" in output["additionalContext"]
    assert "permissionDecision" not in output


def test_implementation_with_tests_produces_no_output(repo: Path) -> None:
    """A compliant commit adds nothing to the context."""
    _stage(repo, "src/app.py", "tests/test_app.py")

    result = _run_hook(repo)

    assert result.returncode == 0
    assert result.stdout == ""


def test_nothing_staged_produces_no_output(repo: Path) -> None:
    """No staged Python files means no advice."""
    result = _run_hook(repo)

    assert result.returncode == 0
    assert result.stdout == ""


def test_a_machine_without_git_gets_no_advice_and_no_crash(tmp_path: Path) -> None:
    """With no git on PATH nothing can be staged, and the hook stays advisory."""
    result = subprocess.run(
        [sys.executable, str(TEMPLATE)],
        cwd=tmp_path,
        input=json.dumps({"tool_name": "Bash"}),
        capture_output=True,
        text=True,
        check=False,
        env={"PATH": str(tmp_path)},
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout == ""
