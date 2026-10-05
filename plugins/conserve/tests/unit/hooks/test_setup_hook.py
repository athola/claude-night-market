"""Tests for the conserve Setup hook, ``hooks/setup.sh``.

Feature: Setup hook survives a machine where nothing has been created yet
  As a contributor on a fresh checkout, a CI runner, or a new HOME
  I want the Setup hook to emit its JSON rather than abort
  So that the harness receives a decision instead of silence.

Run under ``/bin/bash`` (3.2.57 on stock macOS), which the hook's
``#!/usr/bin/env bash`` resolves to on a stock machine.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

HOOK_SCRIPT = Path(__file__).parents[3] / "hooks" / "setup.sh"


def _run(
    trigger: str, home: Path, *, terminator: str = "\n"
) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["HOME"] = str(home)
    env["CLAUDE_PROJECT_DIR"] = str(home / "project")
    env.pop("CLAUDE_ENV_FILE", None)
    env.pop("CONSERVE_SESSION_STATE_PATH", None)
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
    """Scenario: no conserve state exists yet.

    Given a HOME and project directory with no prior conserve state
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
