"""Input-contract tests for noqa_guard: payload arrives on stdin.

Claude Code delivers the PreToolUse payload (including ``tool_name`` and
``tool_input``) as JSON on stdin. The hook previously read only the
non-existent ``CLAUDE_TOOL_*`` env vars, so it never inspected real edits
and silently allowed inline lint suppressions through.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

HOOK = Path(__file__).resolve().parents[3] / "hooks" / "noqa_guard.py"

_LEGACY_ENV = ("CLAUDE_TOOL_NAME", "CLAUDE_TOOL_INPUT")


def _run_stdin(payload: dict):
    env = dict(os.environ)
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


def test_blocks_noqa_edit_delivered_on_stdin():
    """An Edit adding '# noqa' on stdin is denied."""
    payload = {
        "tool_name": "Edit",
        "tool_input": {"new_string": "x = 1  # noqa\n"},
    }
    result = _run_stdin(payload)
    assert result.returncode == 0, result.stderr
    out = json.loads(result.stdout)
    decision = out.get("hookSpecificOutput", {}).get("permissionDecision")
    assert decision == "deny", f"expected deny, got {result.stdout!r}"


def test_allows_clean_edit_on_stdin():
    """An Edit with no suppression on stdin is allowed."""
    payload = {
        "tool_name": "Edit",
        "tool_input": {"new_string": "x = 1\n"},
    }
    result = _run_stdin(payload)
    assert result.returncode == 0, result.stderr
    assert out_is_empty(result.stdout)


def out_is_empty(stdout: str) -> bool:
    try:
        return json.loads(stdout) == {}
    except json.JSONDecodeError:
        return False


def test_malformed_stdin_is_logged_and_fails_open():
    """Malformed stdin logs to stderr while failing open (allow).

    Guards the C1 fix: the guard fails open by design (crash-proof), but
    the JSON-decode path used to log nothing, making a disabled guard
    indistinguishable from an idle one. Reverting the stderr write fails
    this. Fail-open is asserted too so the contract is pinned.
    """
    env = dict(os.environ)
    for key in _LEGACY_ENV:
        env.pop(key, None)
    result = subprocess.run(
        [sys.executable, str(HOOK)],
        input="not json {{{",
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert out_is_empty(result.stdout)
    assert "malformed stdin payload" in result.stderr
