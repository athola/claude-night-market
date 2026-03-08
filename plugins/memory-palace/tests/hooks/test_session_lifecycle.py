"""Tests for the session lifecycle Stop hook.

Feature: Record session metadata at session end

As a Claude Code user
I want each session automatically recorded when it ends
So that history is captured without any manual action.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# ---------------------------------------------------------------------------
# We test the hook module's internal helpers directly, not via subprocess.
# Add the hooks directory to sys.path so we can import session_lifecycle.
# ---------------------------------------------------------------------------
PLUGIN_ROOT = Path(__file__).resolve().parents[2]
HOOKS_DIR = PLUGIN_ROOT / "hooks"

if str(HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(HOOKS_DIR))

import session_lifecycle as lc  # noqa: E402 (import after sys.path manipulation)

from memory_palace.session_history import SessionHistoryManager  # noqa: E402

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _minimal_payload(**overrides: object) -> dict:
    """Return a minimal valid Stop hook payload."""
    base: dict = {
        "hook_event_name": "Stop",
        "stop_reason": "end_turn",
        "stats": {
            "tool_uses": 5,
            "duration_ms": 90000,
            "context_tokens_used": 4000,
            "context_window_size": 20000,
        },
        "tools_used": ["Read", "Edit"],
        "files_modified": ["src/parser.py"],
        "transcript_summary": "Refactored the parser module.",
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# TestDeriveSessionId
# ---------------------------------------------------------------------------


class TestDeriveSessionId:
    """
    Feature: Stable session ID derivation

    As the session lifecycle hook
    I want a filesystem-safe session ID derived from available env/payload data
    So that each session has a unique, deterministic identifier.
    """

    @pytest.mark.unit
    def test_returns_string(self) -> None:
        """
        Scenario: Session ID is always a non-empty string
        Given any payload
        When _derive_session_id() is called
        Then a non-empty string is returned.
        """
        result = lc._derive_session_id({})
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.unit
    def test_contains_date_prefix(self) -> None:
        """
        Scenario: Session ID starts with a YYYYMMDD prefix
        Given a payload
        When _derive_session_id() is called
        Then the first 8 characters are a valid date string.
        """
        result = lc._derive_session_id({})
        prefix = result[:8]
        assert prefix.isdigit(), f"Expected date prefix, got: {prefix!r}"
        assert len(prefix) == 8

    @pytest.mark.unit
    def test_uses_payload_session_id_when_present(self) -> None:
        """
        Scenario: Payload provides an explicit session_id
        Given a payload with session_id='abc123'
        When _derive_session_id() is called
        Then the same call with the same env produces the same result.
        """
        payload = {"session_id": "abc123"}
        with patch.dict("os.environ", {}, clear=False):
            r1 = lc._derive_session_id(payload)
            r2 = lc._derive_session_id(payload)
        assert r1 == r2

    @pytest.mark.unit
    def test_different_payloads_produce_different_ids(self) -> None:
        """
        Scenario: Different payloads yield different IDs
        Given two payloads with different session_id values
        When _derive_session_id() is called on each
        Then the two results differ.
        """
        r1 = lc._derive_session_id({"session_id": "alpha"})
        r2 = lc._derive_session_id({"session_id": "beta"})
        assert r1 != r2

    @pytest.mark.unit
    def test_id_is_filesystem_safe(self) -> None:
        """
        Scenario: Session ID is safe for use as a filename
        Given any payload
        When _derive_session_id() is called
        Then the result contains only alphanumeric characters and hyphens.
        """
        result = lc._derive_session_id({"session_id": "any/path with spaces!"})
        assert re.match(r"^[A-Za-z0-9\-]+$", result), (
            f"Unsafe characters in session ID: {result!r}"
        )


# ---------------------------------------------------------------------------
# TestSafeFloat
# ---------------------------------------------------------------------------


class TestSafeFloat:
    """
    Feature: Safe numeric conversion

    As the hook builder
    I want payload numeric fields converted to float without crashing
    So that missing or malformed stats do not break session recording.
    """

    @pytest.mark.unit
    def test_converts_int(self) -> None:
        assert lc._safe_float(42) == 42.0

    @pytest.mark.unit
    def test_converts_string_number(self) -> None:
        assert lc._safe_float("3.14") == pytest.approx(3.14)

    @pytest.mark.unit
    def test_returns_default_for_none(self) -> None:
        assert lc._safe_float(None) == 0.0

    @pytest.mark.unit
    def test_returns_default_for_bad_string(self) -> None:
        assert lc._safe_float("not-a-number", default=99.0) == 99.0

    @pytest.mark.unit
    def test_custom_default(self) -> None:
        assert lc._safe_float(None, default=7.5) == 7.5


# ---------------------------------------------------------------------------
# TestBuildRecord
# ---------------------------------------------------------------------------


class TestBuildRecord:
    """
    Feature: SessionRecord construction from Stop payload

    As the session lifecycle hook
    I want to convert a raw Stop hook payload into a typed SessionRecord
    So that the data is validated and normalised before persisting.
    """

    @pytest.mark.unit
    def test_basic_fields_populated(self) -> None:
        """
        Scenario: All standard payload fields are mapped correctly
        Given a complete Stop payload
        When _build_record() is called
        Then the record carries matching field values.
        """
        payload = _minimal_payload()
        record = lc._build_record(payload)

        assert record.tools_used == ["Read", "Edit"]
        assert record.files_modified == ["src/parser.py"]
        assert record.summary == "Refactored the parser module."
        assert record.outcome == "completed"

    @pytest.mark.unit
    def test_outcome_completed_for_end_turn(self) -> None:
        """
        Scenario: stop_reason 'end_turn' maps to outcome 'completed'
        Given stop_reason='end_turn'
        When _build_record() is called
        Then outcome is 'completed'.
        """
        record = lc._build_record(_minimal_payload(stop_reason="end_turn"))
        assert record.outcome == "completed"

    @pytest.mark.unit
    def test_outcome_interrupted_for_max_tokens(self) -> None:
        """
        Scenario: stop_reason 'max_tokens' maps to outcome 'interrupted'
        Given stop_reason='max_tokens'
        When _build_record() is called
        Then outcome is 'interrupted'.
        """
        record = lc._build_record(_minimal_payload(stop_reason="max_tokens"))
        assert record.outcome == "interrupted"

    @pytest.mark.unit
    def test_outcome_completed_for_stop_sequence(self) -> None:
        """
        Scenario: stop_reason 'stop_sequence' maps to outcome 'completed'
        Given stop_reason='stop_sequence'
        When _build_record() is called
        Then outcome is 'completed'.
        """
        record = lc._build_record(_minimal_payload(stop_reason="stop_sequence"))
        assert record.outcome == "completed"

    @pytest.mark.unit
    def test_duration_converted_from_ms(self) -> None:
        """
        Scenario: Duration in milliseconds is converted to seconds
        Given stats.duration_ms=120000
        When _build_record() is called
        Then duration_seconds is 120.0.
        """
        payload = _minimal_payload(stats={"duration_ms": 120000})
        record = lc._build_record(payload)
        assert record.duration_seconds == pytest.approx(120.0)

    @pytest.mark.unit
    def test_context_usage_calculated(self) -> None:
        """
        Scenario: Context peak is computed as tokens_used / window_size
        Given context_tokens_used=8000, context_window_size=20000
        When _build_record() is called
        Then context_usage_peak is 0.4.
        """
        stats = {"context_tokens_used": 8000, "context_window_size": 20000}
        record = lc._build_record(_minimal_payload(stats=stats))
        assert record.context_usage_peak == pytest.approx(0.4)

    @pytest.mark.unit
    def test_context_usage_capped_at_one(self) -> None:
        """
        Scenario: Context usage never exceeds 1.0
        Given tokens_used > window_size (overflow scenario)
        When _build_record() is called
        Then context_usage_peak is capped at 1.0.
        """
        stats = {"context_tokens_used": 25000, "context_window_size": 20000}
        record = lc._build_record(_minimal_payload(stats=stats))
        assert record.context_usage_peak == pytest.approx(1.0)

    @pytest.mark.unit
    def test_context_usage_zero_when_no_window_size(self) -> None:
        """
        Scenario: No window size available, avoid division by zero
        Given context_window_size=0
        When _build_record() is called
        Then context_usage_peak is 0.0.
        """
        stats = {"context_tokens_used": 5000, "context_window_size": 0}
        record = lc._build_record(_minimal_payload(stats=stats))
        assert record.context_usage_peak == 0.0

    @pytest.mark.unit
    def test_missing_stats_key_uses_defaults(self) -> None:
        """
        Scenario: Payload has no 'stats' key
        Given a payload with stats=None
        When _build_record() is called
        Then duration_seconds and context_usage_peak default to 0.0.
        """
        payload = _minimal_payload()
        payload.pop("stats", None)
        record = lc._build_record(payload)
        assert record.duration_seconds == 0.0
        assert record.context_usage_peak == 0.0

    @pytest.mark.unit
    def test_tools_used_empty_when_absent(self) -> None:
        """
        Scenario: Payload has no tools_used field
        Given tools_used is absent
        When _build_record() is called
        Then record.tools_used is an empty list.
        """
        payload = _minimal_payload()
        payload.pop("tools_used", None)
        record = lc._build_record(payload)
        assert record.tools_used == []

    @pytest.mark.unit
    def test_files_modified_empty_when_absent(self) -> None:
        """
        Scenario: Payload has no files_modified field
        Given files_modified is absent
        When _build_record() is called
        Then record.files_modified is an empty list.
        """
        payload = _minimal_payload()
        payload.pop("files_modified", None)
        record = lc._build_record(payload)
        assert record.files_modified == []

    @pytest.mark.unit
    def test_session_id_from_payload(self) -> None:
        """
        Scenario: Payload provides an explicit session_id
        Given session_id='explicit-id-001' in payload
        When _build_record() is called
        Then record.session_id is 'explicit-id-001'.
        """
        payload = _minimal_payload(session_id="explicit-id-001")
        record = lc._build_record(payload)
        assert record.session_id == "explicit-id-001"

    @pytest.mark.unit
    def test_ended_at_is_iso_string(self) -> None:
        """
        Scenario: ended_at is always set to current time
        Given any payload
        When _build_record() is called
        Then record.ended_at is a non-empty ISO date string.
        """
        record = lc._build_record(_minimal_payload())
        assert isinstance(record.ended_at, str)
        assert "T" in record.ended_at  # ISO 8601 separator

    @pytest.mark.unit
    def test_metadata_includes_stop_reason(self) -> None:
        """
        Scenario: stop_reason is preserved in metadata
        Given stop_reason='end_turn'
        When _build_record() is called
        Then record.metadata['stop_reason'] is 'end_turn'.
        """
        record = lc._build_record(_minimal_payload(stop_reason="end_turn"))
        assert record.metadata.get("stop_reason") == "end_turn"

    @pytest.mark.unit
    def test_metadata_includes_tool_use_count(self) -> None:
        """
        Scenario: tool_uses stat is preserved in metadata
        Given stats.tool_uses=7
        When _build_record() is called
        Then record.metadata['tool_use_count'] is 7.
        """
        stats = {"tool_uses": 7, "duration_ms": 0}
        record = lc._build_record(_minimal_payload(stats=stats))
        assert record.metadata.get("tool_use_count") == 7


# ---------------------------------------------------------------------------
# TestMainIntegration
# ---------------------------------------------------------------------------


class TestMainIntegration:
    """
    Feature: End-to-end hook execution via main()

    As the Claude Code hook runner
    I want session_lifecycle.main() to process Stop payloads cleanly
    So that sessions are recorded and the hook exits 0 on success.
    """

    @pytest.mark.unit
    def test_main_records_session(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Scenario: Valid Stop payload causes a session file to be written
        Given a valid Stop payload on stdin
        When main() runs
        Then a session JSON file exists in data/sessions/.
        """
        import io

        payload = _minimal_payload(session_id="test-main-001")
        monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(payload)))

        # Redirect SessionHistoryManager to tmp_path

        def _fake_manager(*_args: object, **_kwargs: object) -> SessionHistoryManager:
            return SessionHistoryManager(data_dir=tmp_path)

        monkeypatch.setattr(lc, "SessionHistoryManager", _fake_manager)

        with pytest.raises(SystemExit) as exc_info:
            lc.main()
        assert exc_info.value.code == 0

        session_file = tmp_path / "sessions" / "test-main-001.json"
        assert session_file.exists(), f"Expected {session_file} to exist"

    @pytest.mark.unit
    def test_main_exits_zero_on_invalid_json(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Scenario: Malformed JSON payload does not crash the hook
        Given invalid JSON on stdin
        When main() runs
        Then it exits with code 0 (never blocks the session).
        """
        import io

        monkeypatch.setattr("sys.stdin", io.StringIO("{ not valid json }"))

        with pytest.raises(SystemExit) as exc_info:
            lc.main()
        assert exc_info.value.code == 0

    @pytest.mark.unit
    def test_main_exits_zero_when_module_unavailable(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Scenario: session_history module is not importable
        Given _HAS_SESSION_HISTORY is False (package unavailable)
        When main() runs
        Then it exits with code 0 silently.
        """
        import io

        monkeypatch.setattr(lc, "_HAS_SESSION_HISTORY", False)
        monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(_minimal_payload())))

        with pytest.raises(SystemExit) as exc_info:
            lc.main()
        assert exc_info.value.code == 0

    @pytest.mark.unit
    def test_main_exits_zero_when_record_raises(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Scenario: Unexpected error during record_session does not crash the hook
        Given record_session() raises an exception
        When main() runs
        Then it exits with code 0 (session end must not be blocked).
        """
        import io

        class _BrokenManager(SessionHistoryManager):
            def record_session(self, record: object) -> object:  # type: ignore[override]
                raise RuntimeError("disk full")

        def _broken(*_a: object, **_kw: object) -> _BrokenManager:
            return _BrokenManager(data_dir=tmp_path)

        monkeypatch.setattr(lc, "SessionHistoryManager", _broken)
        monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(_minimal_payload())))

        with pytest.raises(SystemExit) as exc_info:
            lc.main()
        assert exc_info.value.code == 0

    @pytest.mark.unit
    def test_main_skips_non_stop_events(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Scenario: Non-Stop hook event is ignored
        Given a payload with hook_event_name='PreToolUse'
        When main() runs
        Then no session file is written.
        """
        import io

        mgr = SessionHistoryManager(data_dir=tmp_path)
        monkeypatch.setattr(lc, "SessionHistoryManager", lambda *a, **kw: mgr)

        payload = _minimal_payload()
        payload["hook_event_name"] = "PreToolUse"
        monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(payload)))

        with pytest.raises(SystemExit) as exc_info:
            lc.main()
        assert exc_info.value.code == 0

        sessions_dir = tmp_path / "sessions"
        assert not sessions_dir.exists() or not list(sessions_dir.glob("*.json"))
