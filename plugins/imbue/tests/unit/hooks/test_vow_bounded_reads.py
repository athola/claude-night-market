"""Tests for vow_bounded_reads hook.

Feature: Warn when discovery read budget is exceeded.

As a Night Market vow enforcement system
I want to count consecutive Read/Grep calls in a session
So that the bounded-discovery-reads vow is tracked and enforced.
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
    """Import vow_bounded_reads via importlib (hook is a standalone script)."""
    hooks_path = Path(__file__).resolve().parents[3] / "hooks"
    module_path = hooks_path / "vow_bounded_reads.py"
    spec = importlib.util.spec_from_file_location("vow_bounded_reads", module_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["vow_bounded_reads"] = mod
    spec.loader.exec_module(mod)
    return mod


def _make_input(tool_name="Read", session_id="test-session-abc"):
    payload = {
        "tool_name": tool_name,
        "session_id": session_id,
        "tool_input": {"file_path": "/some/file.py"},
    }
    return json.dumps(payload)


class TestCounterFilePath:
    """Feature: Counter file path uses session ID.

    As the hook
    I want a per-session counter file
    So that reads are tracked independently per session.
    """

    @pytest.mark.unit
    def test_counter_file_uses_session_id(self, hook_module, tmp_path):
        """
        Scenario: Counter path includes session ID
        Given a session ID
        When _counter_path is called
        Then the returned path contains the session ID
        """
        path = hook_module._counter_path("my-session-123")
        assert "my-session-123" in str(path)

    @pytest.mark.unit
    def test_counter_file_in_tmp(self, hook_module):
        """
        Scenario: Counter file lives under /tmp
        Given any session ID
        When _counter_path is called
        Then the path is under /tmp
        """
        path = hook_module._counter_path("some-session")
        assert str(path).startswith("/tmp")

    @pytest.mark.unit
    def test_counter_path_fallback_when_no_session(self, hook_module):
        """
        Scenario: Counter path falls back gracefully with empty session
        Given an empty session ID
        When _counter_path is called
        Then a valid path is still returned
        """
        path = hook_module._counter_path("")
        assert isinstance(path, Path)


class TestReadWriteCounter:
    """Feature: Counter persistence in JSON file.

    As the hook
    I want to read and write the counter atomically
    So that consecutive reads across tool calls are counted.
    """

    @pytest.mark.unit
    def test_read_counter_returns_zero_when_missing(self, hook_module, tmp_path):
        """
        Scenario: Counter starts at zero when file missing
        Given no counter file exists
        When _read_counter is called
        Then it returns 0
        """
        path = tmp_path / "vow_read_counter_none.json"
        count = hook_module._read_counter(path)
        assert count == 0

    @pytest.mark.unit
    def test_write_then_read_counter(self, hook_module, tmp_path):
        """
        Scenario: Written counter value is read back correctly
        Given a counter file is written with value 7
        When _read_counter is called
        Then it returns 7
        """
        path = tmp_path / "vow_read_counter_test.json"
        hook_module._write_counter(path, 7)
        assert hook_module._read_counter(path) == 7

    @pytest.mark.unit
    def test_read_counter_ignores_corrupt_file(self, hook_module, tmp_path):
        """
        Scenario: Corrupt counter file treated as zero (fail-safe)
        Given a counter file with invalid JSON
        When _read_counter is called
        Then it returns 0 without raising
        """
        path = tmp_path / "vow_read_counter_bad.json"
        path.write_text("not valid json")
        count = hook_module._read_counter(path)
        assert count == 0

    @pytest.mark.unit
    def test_write_counter_uses_restrictive_permissions(self, hook_module, tmp_path):
        """
        Scenario: Counter file is not world-readable on shared systems
        Given a fresh write of the counter
        When the file is inspected
        Then its mode is 0o600 (owner read/write only)
        """
        path = tmp_path / "vow_read_counter_perms.json"
        hook_module._write_counter(path, 3)
        assert path.exists()
        mode = stat.S_IMODE(path.stat().st_mode)
        assert mode == 0o600, f"expected 0o600, got {oct(mode)}"

    @pytest.mark.unit
    def test_write_counter_restricts_perms_on_existing_file(
        self, hook_module, tmp_path
    ):
        """
        Scenario: Overwriting an existing counter retains 0o600 perms
        Given a pre-existing counter file with permissive perms
        When _write_counter is called again
        Then the resulting file is still 0o600
        """
        path = tmp_path / "vow_read_counter_rewrite.json"
        path.write_text('{"count": 1}')
        path.chmod(0o644)
        hook_module._write_counter(path, 2)
        mode = stat.S_IMODE(path.stat().st_mode)
        assert mode == 0o600, f"expected 0o600 after rewrite, got {oct(mode)}"


class TestIsReadTool:
    """Feature: Classify tools as discovery reads.

    As the hook
    I want to know which tools increment the read counter
    So that only Read/Grep/Glob contribute to the discovery budget.
    """

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "tool_name,expected",
        [
            ("Read", True),
            ("Grep", True),
            ("Glob", True),
            ("Write", False),
            ("Edit", False),
            ("MultiEdit", False),
            ("Bash", False),
        ],
        ids=["Read", "Grep", "Glob", "Write", "Edit", "MultiEdit", "Bash"],
    )
    def test_read_tool_classification(self, hook_module, tool_name, expected):
        """
        Scenario: Correctly classify read vs non-read tools
        Given a tool name
        When _is_read_tool is called
        Then it returns True only for Read/Grep/Glob
        """
        assert hook_module._is_read_tool(tool_name) == expected


class TestMainHook:
    """Feature: Hook main() tracks reads and warns over budget.

    As the Claude Code hook runner
    I want the hook to warn when read budget is exceeded
    So that the bounded-discovery vow is surfaced to the developer.
    """

    @pytest.mark.unit
    def test_read_below_budget_passes_silently(self, hook_module, capsys, tmp_path):
        """
        Scenario: Read calls below budget pass without warning
        Given a fresh session with 5 reads counted
        When main() is called with a Read tool
        Then no warning JSON is emitted
        """
        counter_path = tmp_path / "vow_read_counter_test-session.json"
        hook_module._write_counter(counter_path, 5)

        stdin_data = _make_input(tool_name="Read", session_id="test-session")
        with patch.object(hook_module, "_counter_path", return_value=counter_path):
            with patch("sys.stdin", StringIO(stdin_data)):
                with pytest.raises(SystemExit) as exc:
                    hook_module.main()
        assert exc.value.code == 0
        captured = capsys.readouterr()
        assert captured.out.strip() == ""

    @pytest.mark.unit
    def test_warn_when_budget_exceeded(self, hook_module, capsys, tmp_path):
        """
        Scenario: Warning emitted when read count exceeds 15
        Given a session with 15 reads already counted
        When main() is called with a Read tool
        Then output JSON has decision=warn mentioning the budget
        """
        counter_path = tmp_path / "vow_read_counter_test-session2.json"
        hook_module._write_counter(counter_path, 15)

        stdin_data = _make_input(tool_name="Read", session_id="test-session2")
        with patch.object(hook_module, "_counter_path", return_value=counter_path):
            with patch("sys.stdin", StringIO(stdin_data)):
                with pytest.raises(SystemExit) as exc:
                    hook_module.main()
        assert exc.value.code == 0
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        hook_out = output["hookSpecificOutput"]
        assert hook_out["permissionDecision"] == "warn"
        assert "Bounded discovery" in hook_out["permissionDecisionReason"]
        assert (
            "15" in hook_out["permissionDecisionReason"]
            or "16" in hook_out["permissionDecisionReason"]
        )

    @pytest.mark.unit
    def test_non_tracked_tool_exits_silently(self, hook_module, capsys, tmp_path):
        """
        Scenario: Untracked tool types pass through without counter change
        Given a Bash tool call
        When main() runs
        Then no output and counter unchanged
        """
        counter_path = tmp_path / "vow_read_counter_test-session4.json"
        hook_module._write_counter(counter_path, 3)

        stdin_data = json.dumps(
            {
                "tool_name": "Bash",
                "session_id": "test-session4",
                "tool_input": {"command": "git status"},
            }
        )
        with patch.object(hook_module, "_counter_path", return_value=counter_path):
            with patch("sys.stdin", StringIO(stdin_data)):
                with pytest.raises(SystemExit) as exc:
                    hook_module.main()
        assert exc.value.code == 0
        captured = capsys.readouterr()
        assert captured.out.strip() == ""
        # Counter should NOT be incremented for Bash
        assert hook_module._read_counter(counter_path) == 3

    @pytest.mark.unit
    def test_malformed_stdin_exits_cleanly(self, hook_module, capsys):
        """
        Scenario: Malformed stdin does not crash the hook
        Given non-JSON input on stdin
        When main() runs
        Then it exits 0 without output (fail-safe)
        """
        with patch("sys.stdin", StringIO("not valid json")):
            with pytest.raises(SystemExit) as exc:
                hook_module.main()
        assert exc.value.code == 0
        captured = capsys.readouterr()
        assert captured.out.strip() == ""

    @pytest.mark.unit
    def test_session_id_from_stdin_json(self, hook_module, capsys, tmp_path):
        """
        Scenario: Session ID is read from stdin JSON field
        Given a stdin payload with session_id=abc123
        When main() runs
        Then the counter file is named for abc123
        """
        observed_paths = []

        original_counter_path = hook_module._counter_path

        def tracking_counter_path(session_id):
            path = original_counter_path(session_id)
            observed_paths.append((session_id, path))
            # Redirect to tmp_path so we don't write to /tmp during tests
            return tmp_path / path.name

        stdin_data = json.dumps(
            {
                "tool_name": "Read",
                "session_id": "abc123",
                "tool_input": {"file_path": "/x.py"},
            }
        )
        with patch.object(
            hook_module, "_counter_path", side_effect=tracking_counter_path
        ):
            with patch("sys.stdin", StringIO(stdin_data)):
                with pytest.raises(SystemExit):
                    hook_module.main()

        assert any("abc123" in str(p) for _, p in observed_paths)


class TestGetSessionId:
    """Feature: Session ID resolution from stdin, env var, or fallback.

    As the hook
    I want to resolve the session ID from multiple sources
    So that counter files are scoped to the correct session.
    """

    @pytest.mark.unit
    def test_session_id_from_stdin_data(self, hook_module):
        """
        Scenario: Session ID taken from stdin JSON when present
        Given a data dict with session_id='sid-001'
        When _get_session_id is called
        Then it returns 'sid-001'
        """
        assert hook_module._get_session_id({"session_id": "sid-001"}) == "sid-001"

    @pytest.mark.unit
    def test_session_id_falls_back_to_env_var(self, hook_module):
        """
        Scenario: Session ID taken from CLAUDE_SESSION_ID env var when stdin missing
        Given an empty data dict
        And CLAUDE_SESSION_ID=env-session-xyz in the environment
        When _get_session_id is called
        Then it returns 'env-session-xyz'
        """
        with patch.dict("os.environ", {"CLAUDE_SESSION_ID": "env-session-xyz"}):
            assert hook_module._get_session_id({}) == "env-session-xyz"

    @pytest.mark.unit
    def test_session_id_falls_back_to_default(self, hook_module):
        """
        Scenario: Session ID defaults to 'default' when no source available
        Given an empty data dict
        And CLAUDE_SESSION_ID is not set in the environment
        When _get_session_id is called
        Then it returns 'default'
        """
        env = {
            k: v
            for k, v in __import__("os").environ.items()
            if k != "CLAUDE_SESSION_ID"
        }
        with patch.dict("os.environ", env, clear=True):
            assert hook_module._get_session_id({}) == "default"

    @pytest.mark.unit
    def test_stdin_session_id_takes_priority_over_env(self, hook_module):
        """
        Scenario: Stdin session_id wins over env var when both present
        Given a data dict with session_id='from-stdin'
        And CLAUDE_SESSION_ID=from-env in the environment
        When _get_session_id is called
        Then it returns 'from-stdin'
        """
        with patch.dict("os.environ", {"CLAUDE_SESSION_ID": "from-env"}):
            assert (
                hook_module._get_session_id({"session_id": "from-stdin"})
                == "from-stdin"
            )


class TestShadowMode:
    """Feature: Shadow mode controls warn vs. block when budget exceeded.

    As the Night Market vow enforcement system
    I want bounded-reads to warn by default and block when configured
    So that the vow can graduate from advisory to Hard enforcement
    without a disruptive cutover.
    """

    @pytest.mark.unit
    def test_shadow_mode_on_by_default(self, hook_module):
        """
        Scenario: Shadow mode is active when VOW_SHADOW_MODE is unset
        Given VOW_SHADOW_MODE is not in the environment
        When _shadow_mode() is called
        Then it returns True (warn-only)
        """
        env = {
            k: v for k, v in __import__("os").environ.items() if k != "VOW_SHADOW_MODE"
        }
        with patch.dict("os.environ", env, clear=True):
            assert hook_module._shadow_mode() is True

    @pytest.mark.unit
    @pytest.mark.parametrize("value", ["1", "true", "yes", "TRUE"])
    def test_shadow_mode_on_for_truthy_values(self, hook_module, value):
        """
        Scenario: Shadow mode stays on for truthy env var values
        Given VOW_SHADOW_MODE=<truthy>
        When _shadow_mode() is called
        Then it returns True
        """
        with patch.dict("os.environ", {"VOW_SHADOW_MODE": value}):
            assert hook_module._shadow_mode() is True

    @pytest.mark.unit
    @pytest.mark.parametrize("value", ["0", "false", "no", " 0"])
    def test_shadow_mode_off_for_falsy_values(self, hook_module, value):
        """
        Scenario: Shadow mode turns off for falsy env var values
        Given VOW_SHADOW_MODE=<falsy>
        When _shadow_mode() is called
        Then it returns False (blocking enabled)
        """
        with patch.dict("os.environ", {"VOW_SHADOW_MODE": value}):
            assert hook_module._shadow_mode() is False

    @pytest.mark.unit
    def test_warn_decision_in_shadow_mode(self, hook_module, capsys, tmp_path):
        """
        Scenario: Budget exceeded in shadow mode emits warn decision
        Given VOW_SHADOW_MODE=1 (default)
        And a session with 15 reads already counted
        When main() fires a Read call
        Then the output JSON has permissionDecision=warn
        """
        counter_path = tmp_path / "vow_read_counter_shadow-warn.json"
        hook_module._write_counter(counter_path, 15)
        stdin_data = _make_input(tool_name="Read", session_id="shadow-warn")
        with patch.object(hook_module, "_counter_path", return_value=counter_path):
            with patch.dict("os.environ", {"VOW_SHADOW_MODE": "1"}):
                with patch("sys.stdin", StringIO(stdin_data)):
                    with pytest.raises(SystemExit) as exc:
                        hook_module.main()
        assert exc.value.code == 0
        captured = capsys.readouterr()
        hook_out = json.loads(captured.out)["hookSpecificOutput"]
        assert hook_out["permissionDecision"] == "warn"
        assert "Shadow mode" in hook_out["permissionDecisionReason"]
        assert "[vow-bounded-reads] WARN" in captured.err

    @pytest.mark.unit
    def test_block_decision_when_shadow_mode_off(self, hook_module, capsys, tmp_path):
        """
        Scenario: Budget exceeded with VOW_SHADOW_MODE=0 emits block decision
        Given VOW_SHADOW_MODE=0
        And a session with 15 reads already counted
        When main() fires a Read call
        Then the output JSON has permissionDecision=block
        """
        counter_path = tmp_path / "vow_read_counter_shadow-block.json"
        hook_module._write_counter(counter_path, 15)
        stdin_data = _make_input(tool_name="Read", session_id="shadow-block")
        with patch.object(hook_module, "_counter_path", return_value=counter_path):
            with patch.dict("os.environ", {"VOW_SHADOW_MODE": "0"}):
                with patch("sys.stdin", StringIO(stdin_data)):
                    with pytest.raises(SystemExit) as exc:
                        hook_module.main()
        assert exc.value.code == 0
        captured = capsys.readouterr()
        hook_out = json.loads(captured.out)["hookSpecificOutput"]
        assert hook_out["permissionDecision"] == "block"
        assert "[vow-bounded-reads] BLOCK" in captured.err


class TestBudgetBoundary:
    """Feature: Budget boundary is checked with strict greater-than.

    As the hook
    I want reads at exactly the budget to pass silently
    So that count=15 is the last allowed read, not the first blocked one.
    """

    @pytest.mark.unit
    def test_read_at_exact_budget_does_not_warn(self, hook_module, capsys, tmp_path):
        """
        Scenario: Read at exactly budget (count goes 14→15) passes silently
        Given a session with 14 reads already counted
        When main() fires a Read tool
        Then no warning is emitted (budget is 15, check is > not >=)
        """
        counter_path = tmp_path / "vow_read_counter_boundary.json"
        hook_module._write_counter(counter_path, 14)
        stdin_data = _make_input(tool_name="Read", session_id="boundary")
        with patch.object(hook_module, "_counter_path", return_value=counter_path):
            with patch.dict("os.environ", {"VOW_SHADOW_MODE": "0"}):
                with patch("sys.stdin", StringIO(stdin_data)):
                    with pytest.raises(SystemExit) as exc:
                        hook_module.main()
        assert exc.value.code == 0
        captured = capsys.readouterr()
        assert captured.out.strip() == ""
        assert hook_module._read_counter(counter_path) == 15

    @pytest.mark.unit
    def test_write_failure_exits_cleanly(self, hook_module, capsys):
        """
        Scenario: Counter write failure exits 0 without crashing the hook
        Given os.open raises PermissionError (sandbox deny or /tmp full)
        When main() fires a Read tool call
        Then exit code is 0 and stdout is empty (hook must not crash the agent)
        """
        stdin_data = _make_input(tool_name="Read", session_id="perm-error")
        with patch("os.open", side_effect=PermissionError("no space")):
            with patch("sys.stdin", StringIO(stdin_data)):
                with pytest.raises(SystemExit) as exc:
                    hook_module.main()
        assert exc.value.code == 0
        assert capsys.readouterr().out.strip() == ""


class TestIntegration:
    """Integration: read-reset-read cycle correctly restarts the counter.

    As the Night Market vow enforcement system
    I want reads after a reset to start at 1
    So that counter path divergence between the two scripts is caught early.
    """

    @pytest.fixture
    def reset_module(self):
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

    @pytest.mark.unit
    def test_read_reset_read_cycle_restarts_cleanly(
        self, hook_module, reset_module, capsys, tmp_path
    ):
        """
        Scenario: Counter restarts from 1 after a reset
        Given both scripts use the same counter path formula
        When 15 reads are counted, then a reset fires, then a new read fires
        Then the count is 1 and no warning is emitted
        """
        session_id = "integration-cycle"
        counter_path = tmp_path / hook_module._counter_path(session_id).name

        # Phase 1: pre-load counter to budget
        hook_module._write_counter(counter_path, 15)
        assert hook_module._read_counter(counter_path) == 15

        # Phase 2: reset fires on a Write call
        stdin_reset = json.dumps({"tool_name": "Write", "session_id": session_id})
        with patch.object(reset_module, "_counter_path", return_value=counter_path):
            with patch("sys.stdin", StringIO(stdin_reset)):
                with pytest.raises(SystemExit):
                    reset_module.main()
        assert hook_module._read_counter(counter_path) == 0

        # Phase 3: next Read starts fresh at 1 — no warning even with blocking on
        stdin_read = _make_input(tool_name="Read", session_id=session_id)
        with patch.object(hook_module, "_counter_path", return_value=counter_path):
            with patch.dict("os.environ", {"VOW_SHADOW_MODE": "0"}):
                with patch("sys.stdin", StringIO(stdin_read)):
                    with pytest.raises(SystemExit) as exc:
                        hook_module.main()
        assert exc.value.code == 0
        captured = capsys.readouterr()
        assert captured.out.strip() == ""
        assert hook_module._read_counter(counter_path) == 1


class TestAtomicIncrement:
    """Feature: Counter increments are parallel-safe (issue #418).

    As the Night Market vow enforcement system
    I want concurrent Read tool calls to never lose increments
    So that the budget reflects the true number of discovery reads
    even when Claude Code dispatches reads in parallel (2.1.72+).
    """

    @pytest.mark.unit
    def test_atomic_increment_returns_sequential_values(self, hook_module, tmp_path):
        """
        Scenario: Sequential calls return strictly increasing counts
        Given a fresh counter
        When _atomic_increment is called three times in serial
        Then it returns 1, 2, 3 and the persisted count is 3
        """
        path = tmp_path / "vow_read_counter_seq.json"
        assert hook_module._atomic_increment(path) == 1
        assert hook_module._atomic_increment(path) == 2
        assert hook_module._atomic_increment(path) == 3
        assert hook_module._read_counter(path) == 3

    @pytest.mark.unit
    def test_atomic_increment_initial_call_creates_file(self, hook_module, tmp_path):
        """
        Scenario: Counter file is created on first increment
        Given no counter file exists
        When _atomic_increment is called
        Then the file is created with 0o600 perms and count=1
        """
        path = tmp_path / "vow_read_counter_create.json"
        assert not path.exists()
        result = hook_module._atomic_increment(path)
        assert result == 1
        assert path.exists()
        mode = stat.S_IMODE(path.stat().st_mode)
        assert mode == 0o600, f"expected 0o600, got {oct(mode)}"

    @pytest.mark.unit
    def test_atomic_increment_no_lost_updates_under_concurrency(
        self, hook_module, tmp_path
    ):
        """
        Scenario: Concurrent increments from many threads sum correctly
        Given 50 threads each calling _atomic_increment once
        When all threads complete
        Then the persisted count equals 50 (no lost updates)

        Note: this smoke test alone cannot prove flock is doing any
        work, because CPython's GIL serializes the RMW faster than
        threads can race. The deterministic-race tests below
        (`..._prevents_lost_updates_under_injected_race` and the
        paired `..._loses_updates_without_flock_under_injected_race`)
        are what actually gate the flock fix.
        """
        import threading

        path = tmp_path / "vow_read_counter_parallel.json"
        n_threads = 50
        results: list[int] = []
        results_lock = threading.Lock()
        barrier = threading.Barrier(n_threads)

        def worker():
            barrier.wait()  # release all threads at once to maximize contention
            value = hook_module._atomic_increment(path)
            with results_lock:
                results.append(value)

        threads = [threading.Thread(target=worker) for _ in range(n_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Final persisted count must equal the number of increments.
        assert hook_module._read_counter(path) == n_threads, (
            f"lost updates: expected {n_threads} increments, "
            f"got {hook_module._read_counter(path)}"
        )
        # Returned values must form the set 1..n_threads (no duplicates,
        # no skipped values).
        assert sorted(results) == list(range(1, n_threads + 1))

    @pytest.mark.unit
    def test_atomic_increment_prevents_lost_updates_under_injected_race(
        self, hook_module, tmp_path, monkeypatch
    ):
        """
        Scenario: With flock, injected sleep inside the RMW does not lose updates
        Given `os.read` is patched to sleep 5ms after reading
          And 20 threads are released simultaneously to increment
          And `_HAS_FCNTL=True` (flock active)
        When all threads complete
        Then the persisted count equals 20 and every return value is unique

        The injected sleep is what makes this test meaningful. Without
        injection, the GIL serializes the RMW in under a millisecond
        and the unflocked path also passes (review finding B2). With
        the 5ms sleep between `os.read` and `os.write`, the race
        window is large enough that lost updates WOULD occur if flock
        were absent -- which the paired negative-control test below
        demonstrates.
        """
        import os as _os
        import threading
        import time

        if not hook_module._HAS_FCNTL:
            pytest.skip("requires fcntl (POSIX-only)")

        path = tmp_path / "vow_read_counter_flocked_race.json"
        n_threads = 20
        real_read = _os.read

        def slow_read(fd, size):
            data = real_read(fd, size)
            time.sleep(0.005)  # widen RMW window past GIL serialization
            return data

        monkeypatch.setattr(hook_module.os, "read", slow_read)

        results: list[int] = []
        results_lock = threading.Lock()
        barrier = threading.Barrier(n_threads)

        def worker():
            barrier.wait()
            value = hook_module._atomic_increment(path)
            with results_lock:
                results.append(value)

        threads = [threading.Thread(target=worker) for _ in range(n_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert hook_module._read_counter(path) == n_threads, (
            f"flock failed to prevent lost updates under injected race: "
            f"final={hook_module._read_counter(path)} expected={n_threads}"
        )
        assert sorted(results) == list(range(1, n_threads + 1)), (
            f"duplicate or skipped return values: {sorted(results)}"
        )

    @pytest.mark.unit
    def test_atomic_increment_loses_updates_without_flock_under_injected_race(
        self, hook_module, tmp_path, monkeypatch
    ):
        """
        Scenario: Without flock, injected sleep produces lost updates (negative control)
        Given `os.read` is patched to sleep 5ms after reading
          And 20 threads are released simultaneously to increment
          And `_HAS_FCNTL=False` (flock disabled)
        When all threads complete
        Then the persisted count is strictly less than 20

        This is the paired negative control for the positive test
        above: it proves the injected race is real and the positive
        test is actually exercising flock. If this test ever passes
        with `final == n_threads`, the race injection has become
        ineffective and both tests must be revisited (review finding
        B2's core concern).
        """
        import os as _os
        import threading
        import time

        path = tmp_path / "vow_read_counter_unflocked_race.json"
        monkeypatch.setattr(hook_module, "_HAS_FCNTL", False)

        n_threads = 20
        real_read = _os.read

        def slow_read(fd, size):
            data = real_read(fd, size)
            time.sleep(0.005)
            return data

        monkeypatch.setattr(hook_module.os, "read", slow_read)

        barrier = threading.Barrier(n_threads)

        def worker():
            barrier.wait()
            hook_module._atomic_increment(path)

        threads = [threading.Thread(target=worker) for _ in range(n_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        final = hook_module._read_counter(path)
        assert final < n_threads, (
            f"negative control failed: final={final} equals n_threads={n_threads} "
            "-- injected race is not effective, so the paired positive test "
            "cannot distinguish flock from no-flock (review B2)"
        )

    @pytest.mark.unit
    def test_atomic_increment_falls_back_when_fcntl_missing(
        self, hook_module, tmp_path, monkeypatch
    ):
        """
        Scenario: Atomic increment still works when fcntl is unavailable
        Given the runtime has no working fcntl module (e.g. Windows)
        When _atomic_increment is called
        Then it still increments correctly, just without OS-level locking
        """
        path = tmp_path / "vow_read_counter_nofcntl.json"
        monkeypatch.setattr(hook_module, "_HAS_FCNTL", False)
        assert hook_module._atomic_increment(path) == 1
        assert hook_module._atomic_increment(path) == 2
        assert hook_module._read_counter(path) == 2

    @pytest.mark.unit
    def test_atomic_increment_survives_corrupt_file(self, hook_module, tmp_path):
        """
        Scenario: Corrupt counter file is treated as zero, then incremented to 1
        Given a counter file containing garbage
        When _atomic_increment is called
        Then it returns 1 (resets state safely) without raising
        """
        path = tmp_path / "vow_read_counter_corrupt.json"
        path.write_text("not valid json at all")
        assert hook_module._atomic_increment(path) == 1
        assert hook_module._read_counter(path) == 1

    @pytest.mark.unit
    def test_main_uses_atomic_increment(self, hook_module, capsys, tmp_path):
        """
        Scenario: Hook main() drives the counter via _atomic_increment
        Given a fresh counter and a Read tool call
        When main() runs
        Then the counter advances from 0 to 1 atomically (no separate
        read/write call sequence on the file)

        This guards against regression where main() reverts to the
        non-atomic _read_counter + _write_counter pair.
        """
        counter_path = tmp_path / "vow_read_counter_main-atomic.json"
        call_count = {"n": 0}
        original = hook_module._atomic_increment

        def tracking(path):
            call_count["n"] += 1
            return original(path)

        with patch.object(hook_module, "_counter_path", return_value=counter_path):
            with patch.object(hook_module, "_atomic_increment", side_effect=tracking):
                with patch("sys.stdin", StringIO(_make_input())):
                    with pytest.raises(SystemExit) as exc:
                        hook_module.main()
        assert exc.value.code == 0
        assert call_count["n"] == 1, "main() must call _atomic_increment exactly once"
        assert hook_module._read_counter(counter_path) == 1


class TestAtomicReset:
    """Feature: Counter reset is parallel-safe.

    As the Night Market vow enforcement system
    I want the reset hook to coordinate with concurrent reads
    So that a Read in flight cannot clobber a Write-triggered reset.
    """

    @pytest.fixture
    def reset_module(self):
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

    @pytest.mark.unit
    def test_atomic_reset_zeros_counter(self, reset_module, hook_module, tmp_path):
        """
        Scenario: _atomic_reset truncates the counter to zero
        Given a counter file with count=42
        When _atomic_reset is called
        Then the persisted count is 0 and perms are 0o600
        """
        path = tmp_path / "vow_read_counter_reset.json"
        hook_module._write_counter(path, 42)
        reset_module._atomic_reset(path)
        assert hook_module._read_counter(path) == 0
        mode = stat.S_IMODE(path.stat().st_mode)
        assert mode == 0o600, f"expected 0o600, got {oct(mode)}"

    @pytest.mark.unit
    def test_atomic_reset_concurrent_with_increment(
        self, reset_module, hook_module, tmp_path
    ):
        """
        Scenario: Reset interleaved with increments produces consistent state
        Given a counter being incremented concurrently
        When a reset fires mid-stream
        Then the final state is either a low count (post-reset increments
        only) or matches the number of increments that completed before
        the reset — but the file is never corrupt and never negative.
        """
        import threading

        path = tmp_path / "vow_read_counter_reset-race.json"
        n_increments = 30
        barrier = threading.Barrier(n_increments + 1)

        def incrementer():
            barrier.wait()
            hook_module._atomic_increment(path)

        def resetter():
            barrier.wait()
            reset_module._atomic_reset(path)

        threads = [threading.Thread(target=incrementer) for _ in range(n_increments)]
        threads.append(threading.Thread(target=resetter))
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Strict integrity check (review B3): the raw bytes on disk
        # must parse as a single valid JSON object with a non-negative
        # integer `count` field. Going through `_read_counter` alone
        # is not sufficient because that helper returns 0 on parse
        # errors, which would make any corruption silently satisfy a
        # range assertion.
        raw_bytes = path.read_bytes()
        assert raw_bytes, "counter file is empty after reset+increment race"
        try:
            parsed = json.loads(raw_bytes)
        except json.JSONDecodeError as exc:
            pytest.fail(
                f"counter file is corrupt after reset+increment race: "
                f"{exc}; raw bytes = {raw_bytes!r}"
            )
        assert isinstance(parsed, dict), (
            f"counter file parsed to non-dict {type(parsed).__name__}: {parsed!r}"
        )
        assert "count" in parsed, f"counter file missing 'count' key: {parsed!r}"
        count_value = parsed["count"]
        assert isinstance(count_value, int), (
            f"'count' is {type(count_value).__name__}, not int: {count_value!r}"
        )
        assert 0 <= count_value <= n_increments, (
            f"count {count_value} outside [0, {n_increments}] -- "
            "indicates lost write or interleaved update"
        )
