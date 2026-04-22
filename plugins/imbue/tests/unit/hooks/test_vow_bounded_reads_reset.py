"""Tests for vow_bounded_reads_reset hook.

Feature: Reset the bounded-reads counter when implementation starts.

As a Night Market vow enforcement system
I want a minimal reset script triggered by Write/Edit/MultiEdit
So that the read counter is cleared without the full vow_bounded_reads
parsing overhead.
"""

from __future__ import annotations

import importlib.util
import json
import stat
import sys
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.fixture
def hook_module():
    """Import vow_bounded_reads_reset via importlib."""
    hooks_path = Path(__file__).resolve().parents[3] / "hooks"
    module_path = hooks_path / "vow_bounded_reads_reset.py"
    spec = importlib.util.spec_from_file_location(
        "vow_bounded_reads_reset", module_path
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules["vow_bounded_reads_reset"] = mod
    spec.loader.exec_module(mod)
    return mod


def _make_input(tool_name="Write", session_id="test-reset-session"):
    return json.dumps(
        {
            "tool_name": tool_name,
            "session_id": session_id,
            "tool_input": {"file_path": "/some/file.py"},
        }
    )


class TestCounterReset:
    """Feature: Counter file is truncated to zero on write-tool trigger.

    As the hook
    I want to reset the per-session counter file to zero
    So that the next read phase starts fresh.
    """

    @pytest.mark.unit
    def test_reset_zeroes_existing_counter(self, hook_module, tmp_path):
        """
        Scenario: Counter file is reset to zero when write tool fires
        Given a session with 10 reads already counted
        When the reset hook fires on a Write call
        Then the counter file contains count=0
        """
        counter_path = tmp_path / "vow_read_counter_test-reset-session.json"
        counter_path.write_text('{"count": 10}')
        counter_path.chmod(0o600)

        stdin_data = _make_input(tool_name="Write", session_id="test-reset-session")
        with patch.object(hook_module, "_counter_path", return_value=counter_path):
            with patch("sys.stdin", StringIO(stdin_data)):
                with pytest.raises(SystemExit) as exc:
                    hook_module.main()
        assert exc.value.code == 0
        data = json.loads(counter_path.read_text())
        assert data["count"] == 0

    @pytest.mark.unit
    def test_reset_creates_counter_file_when_missing(self, hook_module, tmp_path):
        """
        Scenario: Counter file is created if it does not exist
        Given no prior counter file for the session
        When the reset hook fires
        Then a counter file with count=0 is created
        """
        counter_path = tmp_path / "vow_read_counter_no-prior.json"
        assert not counter_path.exists()

        stdin_data = _make_input(session_id="no-prior")
        with patch.object(hook_module, "_counter_path", return_value=counter_path):
            with patch("sys.stdin", StringIO(stdin_data)):
                with pytest.raises(SystemExit) as exc:
                    hook_module.main()
        assert exc.value.code == 0
        assert counter_path.exists()
        data = json.loads(counter_path.read_text())
        assert data["count"] == 0

    @pytest.mark.unit
    def test_reset_file_has_restrictive_permissions(self, hook_module, tmp_path):
        """
        Scenario: Reset counter file uses 0o600 permissions
        Given the reset hook fires
        When the counter file is written
        Then its mode is 0o600
        """
        counter_path = tmp_path / "vow_read_counter_perms-reset.json"
        stdin_data = _make_input(session_id="perms-reset")
        with patch.object(hook_module, "_counter_path", return_value=counter_path):
            with patch("sys.stdin", StringIO(stdin_data)):
                with pytest.raises(SystemExit):
                    hook_module.main()
        mode = stat.S_IMODE(counter_path.stat().st_mode)
        assert mode == 0o600, f"expected 0o600, got {oct(mode)}"

    @pytest.mark.unit
    def test_reset_emits_no_stdout(self, hook_module, capsys, tmp_path):
        """
        Scenario: Reset hook produces no stdout output
        Given any write-tool call
        When the reset hook fires
        Then no JSON or text is written to stdout
        """
        counter_path = tmp_path / "vow_read_counter_silent-reset.json"
        stdin_data = _make_input(session_id="silent-reset")
        with patch.object(hook_module, "_counter_path", return_value=counter_path):
            with patch("sys.stdin", StringIO(stdin_data)):
                with pytest.raises(SystemExit):
                    hook_module.main()
        captured = capsys.readouterr()
        assert captured.out.strip() == ""


class TestSessionIdResolution:
    """Feature: Session ID is resolved from stdin then env var then default.

    As the hook
    I want consistent session ID resolution
    So that the reset targets the correct per-session counter file.
    """

    @pytest.mark.unit
    def test_session_id_from_stdin(self, hook_module):
        """Scenario: Session ID taken from stdin JSON when present."""
        assert hook_module._get_session_id({"session_id": "s-001"}) == "s-001"

    @pytest.mark.unit
    def test_session_id_falls_back_to_env_var(self, hook_module):
        """Scenario: Env var used when stdin session_id is absent."""
        with patch.dict("os.environ", {"CLAUDE_SESSION_ID": "env-s-001"}):
            assert hook_module._get_session_id({}) == "env-s-001"

    @pytest.mark.unit
    def test_session_id_defaults_to_default(self, hook_module):
        """Scenario: Falls back to 'default' when no source available."""
        env = {
            k: v
            for k, v in __import__("os").environ.items()
            if k != "CLAUDE_SESSION_ID"
        }
        with patch.dict("os.environ", env, clear=True):
            assert hook_module._get_session_id({}) == "default"


class TestMalformedInput:
    """Feature: Reset hook survives malformed or missing stdin.

    As the hook
    I want fail-safe behavior on bad input
    So that a broken stdin payload never interrupts an agent session.
    """

    @pytest.mark.unit
    def test_malformed_json_exits_cleanly(self, hook_module, capsys):
        """Scenario: Non-JSON stdin does not crash the hook."""
        with patch("sys.stdin", StringIO("not valid json")):
            with pytest.raises(SystemExit) as exc:
                hook_module.main()
        assert exc.value.code == 0
        assert capsys.readouterr().out.strip() == ""

    @pytest.mark.unit
    def test_empty_stdin_exits_cleanly(self, hook_module, capsys):
        """Scenario: Empty stdin does not crash the hook."""
        with patch("sys.stdin", StringIO("")):
            with pytest.raises(SystemExit) as exc:
                hook_module.main()
        assert exc.value.code == 0
