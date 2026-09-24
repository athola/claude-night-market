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
import subprocess
from pathlib import Path

import pytest

HOOK_SCRIPT = Path(__file__).parents[2] / "hooks" / "setup.sh"


def _run(trigger: str, home: Path) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["HOME"] = str(home)
    env["CLAUDE_PROJECT_DIR"] = str(home / "project")
    env.pop("CLAUDE_ENV_FILE", None)
    (home / "project").mkdir(parents=True, exist_ok=True)
    return subprocess.run(
        ["/bin/bash", str(HOOK_SCRIPT)],
        # The hook reads one line with ``read``, which reports failure on
        # an unterminated line and would silently fall back to the init path.
        input=json.dumps({"trigger": trigger}) + "\n",
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
