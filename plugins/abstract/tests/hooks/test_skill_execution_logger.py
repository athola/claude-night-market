"""Input-contract tests for the skill_execution_logger PostToolUse hook.

Claude Code delivers hook payloads as JSON on **stdin**, not via
``CLAUDE_TOOL_*`` environment variables. These tests drive the hook the
way the runtime actually does and assert that a real (non-synthetic)
skill invocation produces a telemetry entry carrying the real session id.

Regression guard for the silent no-op that drained the ``[Learning]``
discussion pipeline: the hook read tool data from environment variables
the runtime never sets, so every real invocation exited 0 without
logging anything.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

HOOK = Path(__file__).resolve().parents[2] / "hooks" / "skill_execution_logger.py"

_LEGACY_ENV = (
    "CLAUDE_TOOL_NAME",
    "CLAUDE_TOOL_INPUT",
    "CLAUDE_TOOL_OUTPUT",
    "CLAUDE_SESSION_ID",
)


def _run(payload: dict, claude_home: Path, extra_env: dict | None = None):
    """Run the hook as a subprocess feeding ``payload`` as JSON on stdin."""
    env = dict(os.environ)
    env["CLAUDE_HOME"] = str(claude_home)
    # Clear legacy env vars so the stdin path is exercised in isolation.
    for key in _LEGACY_ENV:
        env.pop(key, None)
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
        check=False,
    )


def _entries(claude_home: Path, plugin: str, skill: str) -> list[dict]:
    log_dir = claude_home / "skills" / "logs" / plugin / skill
    files = sorted(log_dir.glob("*.jsonl"))
    out: list[dict] = []
    for f in files:
        out.extend(
            json.loads(line) for line in f.read_text().splitlines() if line.strip()
        )
    return out


def test_logs_real_skill_invocation_from_stdin(tmp_path):
    """A Skill PostToolUse payload on stdin writes a telemetry entry."""
    payload = {
        "hook_event_name": "PostToolUse",
        "tool_name": "Skill",
        "tool_input": {"skill": "superpowers:systematic-debugging"},
        "tool_response": {"success": True},
        "session_id": "11111111-2222-3333-4444-555555555555",
    }
    result = _run(payload, tmp_path)
    assert result.returncode == 0, result.stderr

    entries = _entries(tmp_path, "superpowers", "systematic-debugging")
    assert entries, f"no telemetry written; stderr={result.stderr}"
    assert entries[-1]["skill"] == "superpowers:systematic-debugging"
    # The real session id must survive into the entry (proves it is not
    # treated as a synthetic 'test-session' record by aggregation).
    assert entries[-1]["context"]["session_id"] == payload["session_id"]


def test_non_skill_payload_writes_nothing(tmp_path):
    """A non-Skill tool payload on stdin is ignored."""
    payload = {
        "tool_name": "Bash",
        "tool_input": {"command": "ls"},
        "session_id": "deadbeef",
    }
    result = _run(payload, tmp_path)
    assert result.returncode == 0, result.stderr
    assert not list((tmp_path / "skills" / "logs").rglob("*.jsonl"))
