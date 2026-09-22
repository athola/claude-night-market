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

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

HOOK_PATH = Path(__file__).resolve().parents[3] / "hooks" / "guard_scope_ramp.py"


@pytest.fixture
def hook():
    """Import the hook module so its state helpers can be unit-tested."""
    spec = importlib.util.spec_from_file_location("guard_scope_ramp", HOOK_PATH)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["guard_scope_ramp"] = mod
    spec.loader.exec_module(mod)
    return mod


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
        # Isolate rung state in a per-test dir so it cannot bleed across runs.
        session_id = "sess-ledger-write"
        env = os.environ.copy()
        env.pop("IMBUE_RAMP_OK", None)
        env.update(
            {
                "IMBUE_RAMP_OK": "1",
                "VOW_SHADOW_MODE": "1",
                "IMBUE_STATE_DIR": str(tmp_path / "state"),
            }
        )
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


@pytest.mark.skipif(
    not hasattr(os, "O_NOFOLLOW"), reason="symlink hardening is POSIX-only"
)
class TestStateFileSecurity:
    """Feature: refuse to follow symlinks at the session-state path (CWE-59)."""

    @pytest.mark.unit
    def test_save_does_not_follow_a_planted_symlink(self, hook, tmp_path, monkeypatch):
        """A symlink at the state path must not be truncated/overwritten."""
        monkeypatch.setenv("IMBUE_STATE_DIR", str(tmp_path))
        victim = tmp_path / "victim.txt"
        victim.write_text("precious")
        state_path = hook._state_path("attacker")
        state_path.symlink_to(victim)

        hook._save_state(state_path, {"rung": 999})

        # The victim file is untouched; the symlink was not followed.
        assert victim.read_text() == "precious"

    @pytest.mark.unit
    def test_load_does_not_follow_a_planted_symlink(self, hook, tmp_path, monkeypatch):
        """A symlinked state path yields the safe default, not the target."""
        monkeypatch.setenv("IMBUE_STATE_DIR", str(tmp_path))
        secret = tmp_path / "secret.txt"
        secret.write_text('{"rung": 9999, "increments": 7}')
        state_path = hook._state_path("attacker")
        state_path.symlink_to(secret)

        state = hook._load_state(state_path)

        assert state == {"rung": hook.RUNG_START, "increments": 0}

    @pytest.mark.unit
    def test_state_dir_is_private(self, hook, tmp_path, monkeypatch):
        """The default per-user state dir is created mode 0o700."""
        monkeypatch.delenv("IMBUE_STATE_DIR", raising=False)
        monkeypatch.setenv("TMPDIR", str(tmp_path))
        d = hook._state_dir()
        assert (d.stat().st_mode & 0o777) == 0o700

    @pytest.mark.unit
    def test_roundtrip_through_secure_helpers(self, hook, tmp_path, monkeypatch):
        """A normal save/load still works under the hardened path."""
        monkeypatch.setenv("IMBUE_STATE_DIR", str(tmp_path))
        path = hook._state_path("normal")
        hook._save_state(path, {"rung": 60, "increments": 2})
        assert hook._load_state(path) == {"rung": 60, "increments": 2}


class TestExplicitStakes:
    """Where the authoritative risk tier comes from."""

    @pytest.mark.unit
    def test_environment_outranks_the_marker_file(self, hook, tmp_path, monkeypatch):
        """
        GIVEN both IMBUE_STAKES and a .imbue/stakes file
        WHEN the stakes are read
        THEN the environment value wins

        The env var is how `leyline:risk-classification` hands the tier
        over for one turn; a stale marker file outranking it would pin
        the rung to whatever the repo was last classified as.
        """
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".imbue").mkdir()
        (tmp_path / ".imbue" / "stakes").write_text("low\n")
        monkeypatch.setenv("IMBUE_STAKES", "high")

        assert hook._explicit_stakes() == "high"

    @pytest.mark.unit
    def test_the_marker_file_is_read_when_the_environment_is_silent(
        self, hook, tmp_path, monkeypatch
    ):
        """
        GIVEN no IMBUE_STAKES and a .imbue/stakes file
        WHEN the stakes are read
        THEN the file's single line is returned, stripped
        """
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".imbue").mkdir()
        (tmp_path / ".imbue" / "stakes").write_text("  high  \n")
        monkeypatch.delenv("IMBUE_STAKES", raising=False)

        assert hook._explicit_stakes() == "high"

    @pytest.mark.unit
    @pytest.mark.parametrize("contents", ["", "   \n"], ids=["empty", "whitespace"])
    def test_an_empty_marker_reads_as_no_signal(
        self, hook, tmp_path, monkeypatch, contents
    ):
        """
        GIVEN a .imbue/stakes file holding nothing
        WHEN the stakes are read
        THEN None comes back rather than an empty string

        Callers branch on None to fall back to path-regex. An empty
        string is a tier name no rung table has.
        """
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".imbue").mkdir()
        (tmp_path / ".imbue" / "stakes").write_text(contents)
        monkeypatch.delenv("IMBUE_STAKES", raising=False)

        assert hook._explicit_stakes() is None

    @pytest.mark.unit
    def test_a_missing_marker_reads_as_no_signal(self, hook, tmp_path, monkeypatch):
        """
        GIVEN neither the env var nor the marker file
        WHEN the stakes are read
        THEN None comes back and nothing raises

        Most repositories have no .imbue directory at all, so this is
        the common path, not the error path.
        """
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("IMBUE_STAKES", raising=False)

        assert hook._explicit_stakes() is None


class TestRampToken:
    """The recorded-demonstration token that permits one rung jump."""

    @pytest.mark.unit
    @pytest.mark.parametrize("value", ["0", "false", "no", " no "])
    def test_an_off_value_is_not_a_token(self, hook, tmp_path, monkeypatch, value):
        """
        GIVEN IMBUE_RAMP_OK set to a disabling value and no token file
        WHEN the token is checked
        THEN no token is present

        Every off spelling must read as off: one that did not would
        hand out a free rung jump to anyone who wrote "no".
        """
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("IMBUE_RAMP_OK", value)

        assert hook._ramp_token_present() is False

    @pytest.mark.unit
    def test_any_other_environment_value_is_a_token(self, hook, tmp_path, monkeypatch):
        """
        GIVEN IMBUE_RAMP_OK set to 1
        WHEN the token is checked
        THEN a token is present
        """
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("IMBUE_RAMP_OK", "1")

        assert hook._ramp_token_present() is True

    @pytest.mark.unit
    def test_the_on_disk_token_is_found_without_the_environment(
        self, hook, tmp_path, monkeypatch
    ):
        """
        GIVEN no IMBUE_RAMP_OK and a .imbue/ramp-ok file
        WHEN the token is checked
        THEN a token is present
        """
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("IMBUE_RAMP_OK", raising=False)
        (tmp_path / ".imbue").mkdir()
        (tmp_path / ".imbue" / "ramp-ok").write_text("")

        assert hook._ramp_token_present() is True

    @pytest.mark.unit
    def test_consuming_removes_the_on_disk_token(self, hook, tmp_path, monkeypatch):
        """
        GIVEN a .imbue/ramp-ok file
        WHEN the token is consumed
        THEN the file is gone and the token no longer reads as present

        The docstring calls this a once-per-demonstration ramp. A token
        that survived consumption would ramp every increment after it.
        """
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("IMBUE_RAMP_OK", raising=False)
        (tmp_path / ".imbue").mkdir()
        token = tmp_path / ".imbue" / "ramp-ok"
        token.write_text("")

        hook._consume_ramp_token()

        assert not token.exists()
        assert hook._ramp_token_present() is False

    @pytest.mark.unit
    def test_consuming_an_absent_token_is_silent(self, hook, tmp_path, monkeypatch):
        """
        GIVEN no token file
        WHEN the token is consumed
        THEN nothing raises

        The env-based token has no file behind it, so this path runs on
        every env-granted ramp.
        """
        monkeypatch.chdir(tmp_path)

        hook._consume_ramp_token()


class TestRampLedger:
    """The append-only record of every ramp decision."""

    @pytest.mark.unit
    def test_each_entry_is_one_json_line(self, hook, tmp_path, monkeypatch):
        """
        GIVEN two ramp decisions
        WHEN each is appended
        THEN the ledger holds two lines, each parsing on its own

        The file is read line by line downstream, so an entry spanning
        lines takes the rest of the ledger with it.
        """
        monkeypatch.chdir(tmp_path)

        hook._append_ledger({"rung": 40, "decision": "allow"})
        hook._append_ledger({"rung": 60, "decision": "deny"})

        lines = (tmp_path / ".imbue" / "ramp-ledger.jsonl").read_text().splitlines()
        assert [json.loads(line)["rung"] for line in lines] == [40, 60]

    @pytest.mark.unit
    def test_the_parent_directory_is_created(self, hook, tmp_path, monkeypatch):
        """
        GIVEN a repository with no .imbue directory
        WHEN a ledger entry is appended
        THEN the directory is created rather than the write failing

        The first ramp in any repository takes this path.
        """
        monkeypatch.chdir(tmp_path)

        hook._append_ledger({"rung": 40})

        assert (tmp_path / ".imbue" / "ramp-ledger.jsonl").exists()

    @pytest.mark.unit
    def test_a_failed_write_warns_and_does_not_raise(
        self, hook, tmp_path, monkeypatch, capsys
    ):
        """
        GIVEN a .imbue path that is a file rather than a directory
        WHEN a ledger entry is appended
        THEN the failure is reported on stderr and nothing propagates

        The ledger is best-effort: an unwritable one must not turn a
        PreToolUse hook into a blocked tool call.
        """
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".imbue").write_text("not a directory")

        hook._append_ledger({"rung": 40})

        assert "ledger write failed" in capsys.readouterr().err
