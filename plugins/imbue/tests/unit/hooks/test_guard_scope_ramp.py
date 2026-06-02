# ruff: noqa: D101,D102,D103,D205,D212,E501
"""Tests for the scope-ramp guard hook (end-to-end subprocess).

Feature: Hold each increment to the current ambition rung

As the imbue verification spine
I want the guard hook to flag a code increment that jumps past the
current rung without a recorded demonstration
So that the agent ramps ambition a notch at a time, keeping the
human's understanding in pace with the output.

Each test uses a unique session id so the on-disk rung state never
bleeds between cases.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

HOOK_PATH = Path(__file__).resolve().parents[3] / "hooks" / "guard_scope_ramp.py"


def run_hook(
    tool_name: str,
    tool_input: dict,
    session_id: str,
    env_overrides: dict | None = None,
) -> tuple[int, dict | None]:
    env = os.environ.copy()
    env.pop("IMBUE_RAMP_OK", None)
    if env_overrides:
        env.update(env_overrides)
    payload = json.dumps(
        {"tool_name": tool_name, "tool_input": tool_input, "session_id": session_id}
    )
    result = subprocess.run(
        [str(HOOK_PATH)],
        input=payload,
        capture_output=True,
        text=True,
        timeout=10,
        env=env,
        check=False,
    )
    parsed = json.loads(result.stdout) if result.stdout.strip() else None
    return result.returncode, parsed


def _big_content(lines: int) -> str:
    return "\n".join(f"line {i}" for i in range(lines)) + "\n"


class TestGuardScopeRampHook:
    @pytest.mark.unit
    def test_small_increment_is_silent(self):
        """Scenario: a bounded slice within the start rung produces no output."""
        code, out = run_hook(
            "Write",
            {"file_path": "src/util.py", "content": _big_content(10)},
            "sess-small",
        )
        assert code == 0
        assert out is None

    @pytest.mark.unit
    def test_non_code_tool_is_silent(self):
        code, out = run_hook("Bash", {"command": "ls"}, "sess-bash")
        assert code == 0
        assert out is None

    @pytest.mark.unit
    def test_over_rung_warns_in_shadow_mode(self):
        """Scenario: a 120-line one-shot warns under the shadow default."""
        code, out = run_hook(
            "Write",
            {"file_path": "src/util.py", "content": _big_content(120)},
            "sess-over-warn",
            {"VOW_SHADOW_MODE": "1"},
        )
        assert code == 0
        assert out is not None
        assert out["hookSpecificOutput"]["permissionDecision"] == "warn"
        assert "rung" in out["hookSpecificOutput"]["permissionDecisionReason"]

    @pytest.mark.unit
    def test_over_rung_blocks_when_blocking_enabled(self):
        code, out = run_hook(
            "Write",
            {"file_path": "src/util.py", "content": _big_content(120)},
            "sess-over-block",
            {"VOW_SHADOW_MODE": "0"},
        )
        assert code == 0
        assert out is not None
        assert out["hookSpecificOutput"]["permissionDecision"] == "block"

    @pytest.mark.unit
    def test_high_stakes_reason_demands_explanation(self):
        _, out = run_hook(
            "Write",
            {"file_path": "src/auth/login.py", "content": _big_content(60)},
            "sess-high-stakes",
            {"VOW_SHADOW_MODE": "1"},
        )
        assert out is not None
        reason = out["hookSpecificOutput"]["permissionDecisionReason"]
        assert "explain" in reason.lower()

    @pytest.mark.unit
    def test_ramp_token_via_env_widens_rung(self):
        """Scenario: a recorded demonstration (IMBUE_RAMP_OK) lifts the rung.

        A 55-line increment is over the start rung of 40, but with a ramp
        token the rung widens to 60 and the same increment is allowed.
        """
        code, out = run_hook(
            "Write",
            {"file_path": "src/util.py", "content": _big_content(55)},
            "sess-token",
            {"IMBUE_RAMP_OK": "1", "VOW_SHADOW_MODE": "1"},
        )
        assert code == 0
        assert out is None

    @pytest.mark.unit
    def test_explicit_critical_stakes_tightens_rung(self):
        """Scenario: a CRITICAL tier from risk-classification quarters the rung.

        A 12-line slice on an ordinary path is within GREEN's rung of 40
        but over CRITICAL's rung of 10, so the explicit tier flags it and
        the reason demands an explanation.
        """
        _, out = run_hook(
            "Write",
            {"file_path": "src/util.py", "content": _big_content(12)},
            "sess-critical",
            {"IMBUE_STAKES": "CRITICAL", "VOW_SHADOW_MODE": "1"},
        )
        assert out is not None
        reason = out["hookSpecificOutput"]["permissionDecisionReason"]
        assert "explain" in reason.lower()

    @pytest.mark.unit
    def test_ramp_writes_a_ledger_entry(self, tmp_path):
        """Scenario: consuming a token widens the rung and records the notch.

        The hook runs in a temp cwd so the `.imbue/ramp-ledger.jsonl`
        artifact lands there. A 55-line slice with a ramp token widens the
        rung 40->60 and appends one ledger entry capturing the notch.
        """
        # State is /tmp-global keyed by session id (vow-hook convention), so
        # isolate this case by clearing its state file before the run.
        session_id = "sess-ledger-write"
        Path(f"/tmp/imbue_scope_ramp_{session_id}.json").unlink(missing_ok=True)
        env = os.environ.copy()
        env.pop("IMBUE_RAMP_OK", None)
        env.update({"IMBUE_RAMP_OK": "1", "VOW_SHADOW_MODE": "1"})
        payload = json.dumps(
            {
                "tool_name": "Write",
                "tool_input": {"file_path": "src/util.py", "content": _big_content(55)},
                "session_id": session_id,
            }
        )
        result = subprocess.run(
            [str(HOOK_PATH)],
            input=payload,
            capture_output=True,
            text=True,
            timeout=10,
            env=env,
            cwd=str(tmp_path),
            check=False,
        )
        assert result.returncode == 0
        ledger = tmp_path / ".imbue" / "ramp-ledger.jsonl"
        assert ledger.exists()
        entry = json.loads(ledger.read_text().strip())
        assert entry["rung_before"] == 40
        assert entry["rung_after"] == 60
        assert entry["gate"] == "evidence"
        assert "timestamp" in entry

    @pytest.mark.unit
    def test_malformed_stdin_does_not_crash(self):
        result = subprocess.run(
            [str(HOOK_PATH)],
            input="not json",
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        assert result.returncode == 0
