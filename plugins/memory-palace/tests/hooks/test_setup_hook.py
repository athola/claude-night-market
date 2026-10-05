"""Tests for the memory-palace Setup hook, ``hooks/setup.sh``.

Feature: Setup hook survives a machine where nothing has been created yet
  As a contributor on a fresh checkout, a CI runner, or a new HOME
  I want the Setup hook to emit its JSON rather than abort
  So that the harness receives a decision instead of silence.

The hook runs under ``/bin/bash`` here on purpose. Stock macOS ships bash
3.2.57, where an unguarded empty-array expansion is an unbound variable
under ``set -u``, and every task-appending block in the maintenance path
sits behind a directory-existence guard over ``${HOME}/.claude``.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

HOOK_SCRIPT = Path(__file__).parents[2] / "hooks" / "setup.sh"


def _run(
    trigger: str, home: Path, *, terminator: str = "\n"
) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["HOME"] = str(home)
    env["CLAUDE_PROJECT_DIR"] = str(home / "project")
    env.pop("CLAUDE_ENV_FILE", None)
    (home / "project").mkdir(parents=True, exist_ok=True)
    return subprocess.run(
        ["/bin/bash", str(HOOK_SCRIPT)],
        input=json.dumps({"trigger": trigger}) + terminator,
        capture_output=True,
        text=True,
        cwd=str(home / "project"),
        env=env,
        timeout=60,
        check=False,
    )


@pytest.mark.unit
@pytest.mark.parametrize("trigger", ["init", "maintenance"])
def test_setup_emits_parseable_json_with_an_empty_home(
    trigger: str, tmp_path: Path
) -> None:
    """Scenario: no knowledge garden exists yet
    Given a HOME with no ``.claude`` tree
    When the Setup hook runs under stock bash 3.2
    Then it exits 0 and stdout parses as the Setup hook schema.
    """
    result = _run(trigger, tmp_path)
    assert result.returncode == 0, (
        f"hook aborted ({result.returncode}): {result.stderr}"
    )
    payload = json.loads(result.stdout)
    assert payload["hookSpecificOutput"]["hookEventName"] == "Setup"
    assert isinstance(payload["hookSpecificOutput"]["additionalContext"], str)


@pytest.mark.unit
def test_maintenance_does_not_report_an_unbound_array(tmp_path: Path) -> None:
    """Scenario: the empty-array abort is the specific regression guarded
    Given a HOME with no ``.claude`` tree
    When the maintenance trigger fires
    Then stderr carries no ``unbound variable`` diagnostic.
    """
    result = _run("maintenance", tmp_path)
    assert "unbound variable" not in result.stderr


@pytest.mark.unit
def test_maintenance_runs_when_the_input_has_no_trailing_newline(
    tmp_path: Path,
) -> None:
    """Scenario: hook input arrives without a final newline.

    Given a maintenance trigger written with no terminator
    When the Setup hook reads it
    Then it runs maintenance, not the init path (shell review S0-5, S2-10).
    """
    result = _run("maintenance", tmp_path, terminator="")
    assert result.returncode == 0, result.stderr
    context = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
    assert "maintenance" in context.splitlines()[0]


def _context(result: subprocess.CompletedProcess) -> str:
    assert result.returncode == 0, f"hook aborted: {result.stderr}"
    return json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]


@pytest.mark.unit
def test_init_completes_a_garden_missing_its_meta_dir(tmp_path: Path) -> None:
    """Scenario: the garden root exists but meta/ does not.

    Writing meta/index.json failed under set -e and the hook printed
    nothing (shell review S2-11).
    """
    (tmp_path / ".claude" / "knowledge-garden").mkdir(parents=True)
    _context(_run("init", tmp_path))
    assert (tmp_path / ".claude" / "knowledge-garden" / "meta" / "index.json").is_file()


@pytest.mark.unit
def test_maintenance_counts_a_garden_missing_a_category(tmp_path: Path) -> None:
    """Scenario: seeds/ is absent.

    find's nonzero status killed the hook under pipefail (S2-12).
    """
    garden = tmp_path / ".claude" / "knowledge-garden"
    for name in ("seedlings", "evergreen", "compost", "meta"):
        (garden / name).mkdir(parents=True)
    (garden / "evergreen" / "a.md").write_text("x")
    assert "1 active entries" in _context(_run("maintenance", tmp_path))


@pytest.mark.unit
def test_a_corrupt_index_is_reported_not_called_rebuilt(tmp_path: Path) -> None:
    """Scenario: index.json does not parse.

    jq failed inside an && list, the hook still said "Rebuilt index", and
    a stray .tmp was left behind (S2-13).
    """
    meta = tmp_path / ".claude" / "knowledge-garden" / "meta"
    meta.mkdir(parents=True)
    (meta / "index.json").write_text("{broken")
    context = _context(_run("maintenance", tmp_path))
    if shutil.which("jq"):
        assert "Rebuilt index" not in context
        assert "rebuild failed" in context
    assert not (meta / "index.json.tmp").exists()


@pytest.mark.unit
def test_init_creates_the_palace_in_a_git_worktree(tmp_path: Path) -> None:
    """Scenario: the project is a linked worktree, where .git is a file (S2-22)."""
    project = tmp_path / "project"
    project.mkdir()
    (project / ".git").write_text("gitdir: /elsewhere/.git/worktrees/project\n")
    _context(_run("init", tmp_path))
    assert (project / ".claude" / "palace").is_dir()
