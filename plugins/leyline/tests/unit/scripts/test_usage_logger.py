"""Tests for scripts/usage_logger.py.

Feature: Session-aware usage logging for audit trails and analytics.

As a plugin operator tracking operations and costs,
I want a JSONL-based usage log that is session-aware and queryable,
So that the audit trail is accurate and I can detect error patterns.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
import usage_logger as _ul_mod
from usage_logger import UsageEvent, UsageLogger, main


class TestUsageEvent:
    """Unit tests for the UsageEvent dataclass."""

    @pytest.mark.unit
    def test_defaults_only_operation_required(self) -> None:
        """GIVEN only 'operation' is provided
        WHEN UsageEvent is constructed
        THEN tokens defaults to 0, success to True, and duration to 0.0.
        AND error_type, error_message, and metadata are all None.
        """
        event = UsageEvent("read-file")

        assert event.operation == "read-file"
        assert event.tokens == 0
        assert event.success is True
        assert event.duration == 0.0
        assert event.error_type is None
        assert event.error_message is None
        assert event.metadata is None

    @pytest.mark.unit
    def test_explicit_fields_are_stored_as_given(self) -> None:
        """GIVEN all fields are supplied explicitly
        WHEN UsageEvent is constructed
        THEN every field is stored at the provided value.
        """
        event = UsageEvent(
            operation="write-file",
            tokens=1500,
            success=False,
            duration=3.14,
            error_type="TimeoutError",
            error_message="operation timed out",
            metadata={"target": "foo.py"},
        )

        assert event.operation == "write-file"
        assert event.tokens == 1500
        assert event.success is False
        assert event.duration == 3.14
        assert event.error_type == "TimeoutError"
        assert event.error_message == "operation timed out"
        assert event.metadata == {"target": "foo.py"}


class TestLogUsage:
    """Tests for UsageLogger.log_usage(event) — observable file effects."""

    @pytest.mark.unit
    def test_log_usage_creates_jsonl_line_with_correct_fields(
        self, tmp_path: Path
    ) -> None:
        """GIVEN a fresh UsageLogger backed by tmp_path
        WHEN log_usage is called with a UsageEvent
        THEN the log file exists and contains exactly one JSONL line.
        AND the line decodes to a dict with operation, service, tokens,
            success, and duration_seconds matching the event.
        """
        logger = UsageLogger(service="test-svc", storage_dir=tmp_path)
        event = UsageEvent("do-work", tokens=200, success=True, duration=0.5)
        logger.log_usage(event)

        log_file = tmp_path / "test-svc.jsonl"
        assert log_file.exists()
        lines = [ln for ln in log_file.read_text().splitlines() if ln.strip()]
        assert len(lines) == 1

        entry = json.loads(lines[0])
        assert entry["operation"] == "do-work"
        assert entry["service"] == "test-svc"
        assert entry["tokens"] == 200
        assert entry["success"] is True
        assert entry["duration_seconds"] == 0.5
        assert entry["session_id"] == logger.session_id

    @pytest.mark.unit
    def test_log_usage_appends_on_repeated_calls(self, tmp_path: Path) -> None:
        """GIVEN a UsageLogger and one prior log entry
        WHEN log_usage is called a second time
        THEN the log file contains exactly two JSONL lines.
        AND each line records its respective operation in order.
        """
        logger = UsageLogger(service="svc", storage_dir=tmp_path)
        logger.log_usage(UsageEvent("op-a"))
        logger.log_usage(UsageEvent("op-b"))

        lines = [
            ln for ln in (tmp_path / "svc.jsonl").read_text().splitlines() if ln.strip()
        ]
        assert len(lines) == 2
        assert json.loads(lines[0])["operation"] == "op-a"
        assert json.loads(lines[1])["operation"] == "op-b"

    @pytest.mark.unit
    def test_log_usage_writes_error_fields_when_set(self, tmp_path: Path) -> None:
        """GIVEN a UsageEvent with error_type and error_message populated
        WHEN log_usage is called
        THEN the JSONL line contains both error fields at their given values.
        AND success is recorded as False.
        """
        logger = UsageLogger(service="svc", storage_dir=tmp_path)
        event = UsageEvent(
            "bad-op",
            success=False,
            error_type="ValueError",
            error_message="unexpected input",
        )
        logger.log_usage(event)

        entry = json.loads((tmp_path / "svc.jsonl").read_text().splitlines()[0])
        assert entry["success"] is False
        assert entry["error_type"] == "ValueError"
        assert entry["error_message"] == "unexpected input"

    @pytest.mark.unit
    def test_session_corruption_falls_back_to_new_session(self, tmp_path: Path) -> None:
        """GIVEN a session file exists but contains malformed JSON
        WHEN UsageLogger is initialized
        THEN it does not raise and instead creates a fresh session.
        AND log_usage writes a valid JSONL entry under that new session.
        """
        session_file = tmp_path / "svc_session.json"
        session_file.write_text("not-valid-json{{{")

        logger = UsageLogger(service="svc", storage_dir=tmp_path)

        assert logger.session_id.startswith("session_")

        logger.log_usage(UsageEvent("probe"))
        log_file = tmp_path / "svc.jsonl"
        assert log_file.exists()
        entry = json.loads(log_file.read_text().splitlines()[0])
        assert entry["operation"] == "probe"


class TestMainCli:
    """Integration tests for the main() CLI entry point.

    main() reads sys.argv and constructs UsageLogger(service=...) using the
    default home-based storage path. Tests inject tmp_path by patching
    UsageLogger.__init__ so no real filesystem side-effects occur.
    """

    @pytest.mark.unit
    def test_main_log_writes_entry_to_file(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """GIVEN sys.argv contains --log with a valid operation payload
        WHEN main() is called
        THEN a JSONL entry is written whose fields match the CLI arguments.
        AND the file is created inside the injected tmp_path storage dir.
        """
        _orig = _ul_mod.UsageLogger.__init__

        def _patched_init(
            self: UsageLogger,
            service: str,
            storage_dir: Path | None = None,
            session_id: str | None = None,
        ) -> None:
            _orig(self, service, storage_dir=tmp_path, session_id=session_id)

        monkeypatch.setattr(_ul_mod.UsageLogger, "__init__", _patched_init)
        monkeypatch.setattr(
            sys,
            "argv",
            [
                "usage_logger",
                "test-svc",
                "--log",
                "fetch-data",
                "100",
                "true",
                "1.2",
            ],
        )

        main()

        log_file = tmp_path / "test-svc.jsonl"
        assert log_file.exists()
        entry = json.loads(log_file.read_text().splitlines()[0])
        assert entry["operation"] == "fetch-data"
        assert entry["tokens"] == 100
        assert entry["success"] is True
        assert entry["duration_seconds"] == 1.2

    @pytest.mark.unit
    def test_main_summary_completes_without_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """GIVEN sys.argv specifies --summary for a service with no prior log entries
        WHEN main() is called
        THEN it completes without raising an exception.
        AND no JSONL log file is created (summary over empty data is a no-op).
        """
        _orig = _ul_mod.UsageLogger.__init__

        def _patched_init(
            self: UsageLogger,
            service: str,
            storage_dir: Path | None = None,
            session_id: str | None = None,
        ) -> None:
            _orig(self, service, storage_dir=tmp_path, session_id=session_id)

        monkeypatch.setattr(_ul_mod.UsageLogger, "__init__", _patched_init)
        monkeypatch.setattr(sys, "argv", ["usage_logger", "empty-svc", "--summary"])

        main()  # must not raise

        assert not (tmp_path / "empty-svc.jsonl").exists()
