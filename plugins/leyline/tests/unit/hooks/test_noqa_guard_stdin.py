"""Input-contract tests for noqa_guard: payload arrives on stdin.

Claude Code delivers the PreToolUse payload (including ``tool_name`` and
``tool_input``) as JSON on stdin. The hook previously read only the
non-existent ``CLAUDE_TOOL_*`` env vars, so it never inspected real edits
and silently allowed inline lint suppressions through.
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

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
    """GIVEN an Edit payload with an inline lint suppression in new_string
    WHEN the payload is delivered on stdin and the hook processes it
    THEN the hook exits 0 and the output contains a deny decision.
    AND permissionDecision equals 'deny'.
    """
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
    """GIVEN an Edit payload with clean new_string (no suppression directives)
    WHEN the payload is delivered on stdin and the hook processes it
    THEN the hook exits 0 and returns an empty JSON object.
    AND no permissionDecision field is present.
    """
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


def test_isatty_raises_oserror_falls_back_to_env_vars(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """GIVEN sys.stdin.isatty() raises OSError (e.g., the fd is not connected)
    WHEN _read_payload() is called
    THEN the OSError is caught and raw stays empty.
    AND the function falls back to CLAUDE_TOOL_NAME / CLAUDE_TOOL_INPUT env vars.
    AND the returned payload carries the values from those env vars.
    """
    spec = importlib.util.spec_from_file_location("_noqa_guard_isatty", HOOK)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    class _RaisingStdin:
        def isatty(self) -> bool:
            raise OSError("file descriptor is not connected")

    monkeypatch.setattr("sys.stdin", _RaisingStdin())
    monkeypatch.setenv("CLAUDE_TOOL_NAME", "Write")
    monkeypatch.setenv("CLAUDE_TOOL_INPUT", json.dumps({"content": "clean code"}))

    result = mod._read_payload()

    assert result["tool_name"] == "Write"
    assert result["tool_input"] == {"content": "clean code"}


def test_malformed_stdin_is_logged_and_fails_open():
    """GIVEN stdin contains bytes that are not valid JSON
    WHEN the hook processes them
    THEN the hook exits 0 and returns an empty JSON object (fail-open).
    AND stderr contains 'malformed stdin payload' so a disabled guard
        is distinguishable from an idle one.

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
