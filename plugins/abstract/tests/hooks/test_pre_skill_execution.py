"""Input-contract test for the pre_skill_execution PreToolUse hook.

The hook must read the Skill payload Claude Code provides on stdin and
write a pre-execution state file that the PostToolUse logger later reads
to compute duration. Reading the non-existent ``CLAUDE_TOOL_*`` env vars
made it a silent no-op.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

HOOK = Path(__file__).resolve().parents[2] / "hooks" / "pre_skill_execution.py"

_LEGACY_ENV = ("CLAUDE_TOOL_NAME", "CLAUDE_TOOL_INPUT", "CLAUDE_SESSION_ID")


def _run(payload: dict, claude_home: Path):
    env = dict(os.environ)
    env["CLAUDE_HOME"] = str(claude_home)
    for key in _LEGACY_ENV:
        env.pop(key, None)
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
        check=False,
    )


def test_writes_state_file_from_stdin(tmp_path):
    """A Skill payload on stdin writes a pre-execution state file."""
    payload = {
        "tool_name": "Skill",
        "tool_input": {"skill": "superpowers:test-driven-development"},
        "session_id": "abc-123",
    }
    result = _run(payload, tmp_path)
    assert result.returncode == 0, result.stderr

    state_dir = tmp_path / "skills" / "observability"
    states = list(state_dir.glob("*.json"))
    assert states, f"no state file written; stderr={result.stderr}"
    state = json.loads(states[0].read_text())
    assert state["skill"] == "superpowers:test-driven-development"


def test_non_skill_payload_writes_no_state(tmp_path):
    payload = {"tool_name": "Bash", "tool_input": {"command": "ls"}}
    result = _run(payload, tmp_path)
    assert result.returncode == 0, result.stderr
    state_dir = tmp_path / "skills" / "observability"
    assert not (state_dir.exists() and list(state_dir.glob("*.json")))
