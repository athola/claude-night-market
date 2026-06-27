"""Input-contract test for the homeostatic_monitor PostToolUse hook.

The hook must read the Skill payload from stdin (Claude Code contract).
Reading the non-existent ``CLAUDE_TOOL_*`` env vars made it a silent
no-op that never emitted a health verdict.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

HOOK = Path(__file__).resolve().parents[2] / "hooks" / "homeostatic_monitor.py"

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


def _seed_history(claude_home: Path, skill_ref: str, accuracies: list[float]) -> None:
    logs = claude_home / "skills" / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    history = {
        skill_ref: {"accuracies": accuracies, "durations": [100] * len(accuracies)}
    }
    (logs / ".history.json").write_text(json.dumps(history))


def test_emits_health_verdict_from_stdin(tmp_path):
    """A Skill payload on stdin yields a health verdict for a known skill."""
    skill_ref = "superpowers:systematic-debugging"
    _seed_history(tmp_path, skill_ref, [1.0, 1.0, 0.95, 0.9])  # small gap -> healthy
    payload = {"tool_name": "Skill", "tool_input": {"skill": skill_ref}}

    result = _run(payload, tmp_path)
    assert result.returncode == 0, result.stderr
    assert skill_ref in result.stdout, f"no verdict emitted; stdout={result.stdout!r}"
    verdict = json.loads(result.stdout)
    assert verdict["hookSpecificOutput"]["skill"] == skill_ref
