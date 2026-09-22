"""Tests for scripts/usage_logger.py.

Feature: Session-aware usage logging for audit trails and analytics.

As a plugin operator tracking operations and costs,
I want a JSONL-based usage log that is session-aware and queryable,
So that the audit trail is accurate and I can detect error patterns.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
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


class TestQueryMethods:
    """Feature: querying the JSONL log for operations, errors, and totals.

    The log is append-only and never rewritten, so every reader has to
    survive a truncated or half-written final line. These tests plant
    that line deliberately rather than hoping one turns up.
    """

    @staticmethod
    def _utcnow() -> datetime:
        """Naive UTC, matching what the module writes and compares against.

        The module still calls the deprecated ``datetime.utcnow``; these
        tests get the same naive reading without inheriting the warning,
        so the only DeprecationWarning in the run stays attributable to
        the source (defect D-3).
        """
        return datetime.now(timezone.utc).replace(tzinfo=None)

    @staticmethod
    def _write_log(logger: UsageLogger, lines: list[str]) -> None:
        """Write raw JSONL lines, bypassing log_usage, to control timestamps."""
        logger.log_file.write_text("\n".join(lines) + "\n")

    @staticmethod
    def _entry(
        *,
        stamp: str,
        session: str = "s1",
        tokens: int = 100,
        success: bool = True,
        operation: str = "fetch",
    ) -> str:
        return json.dumps(
            {
                "timestamp": stamp,
                "session_id": session,
                "service": "svc",
                "operation": operation,
                "tokens": tokens,
                "success": success,
                "duration_seconds": 2.0,
            }
        )

    @pytest.fixture
    def logger(self, tmp_path: Path) -> UsageLogger:
        """A logger whose storage is an empty tmp_path."""
        return UsageLogger("svc", storage_dir=tmp_path, session_id="s1")

    @pytest.mark.unit
    def test_recent_operations_is_empty_when_no_log_file_exists(
        self, logger: UsageLogger
    ) -> None:
        """GIVEN no entry has ever been logged
        WHEN get_recent_operations is called
        THEN it returns an empty list rather than raising on the missing file.
        """
        assert not logger.log_file.exists()

        assert logger.get_recent_operations() == []

    @pytest.mark.unit
    def test_recent_operations_excludes_entries_older_than_the_cutoff(
        self, logger: UsageLogger
    ) -> None:
        """GIVEN one entry an hour old and one entry three days old
        WHEN get_recent_operations asks for the last 24 hours
        THEN only the recent entry comes back.
        """
        now = self._utcnow()
        self._write_log(
            logger,
            [
                self._entry(
                    stamp=(now - timedelta(hours=1)).isoformat() + "Z",
                    operation="recent",
                ),
                self._entry(
                    stamp=(now - timedelta(days=3)).isoformat() + "Z",
                    operation="stale",
                ),
            ],
        )

        operations = logger.get_recent_operations(hours=24)

        assert [op["operation"] for op in operations] == ["recent"]

    @pytest.mark.unit
    def test_recent_operations_skips_unreadable_lines(
        self, logger: UsageLogger
    ) -> None:
        """GIVEN a log holding a truncated line, a line with no timestamp,
        a line whose timestamp is not a date, a blank line, and one good entry
        WHEN get_recent_operations reads it
        THEN only the good entry is returned and nothing raises.

        Each bad line exercises a different arm of the except clause:
        JSONDecodeError, KeyError, and ValueError in that order.
        """
        now = self._utcnow()
        self._write_log(
            logger,
            [
                '{"timestamp": "trunca',
                json.dumps({"operation": "no-timestamp"}),
                self._entry(stamp="not-a-date", operation="bad-stamp"),
                "",
                self._entry(
                    stamp=(now - timedelta(minutes=5)).isoformat() + "Z",
                    operation="good",
                ),
            ],
        )

        operations = logger.get_recent_operations(hours=24)

        assert [op["operation"] for op in operations] == ["good"]

    @pytest.mark.unit
    def test_usage_summary_over_no_operations_reports_zeroes(
        self, logger: UsageLogger
    ) -> None:
        """GIVEN an empty log
        WHEN get_usage_summary is called
        THEN every field is zero, and success_rate is 0.0 rather than a
        division by the zero operation count.
        """
        summary = logger.get_usage_summary()

        assert summary == {
            "total_operations": 0,
            "total_tokens": 0,
            "success_rate": 0.0,
            "total_duration": 0.0,
            "estimated_cost": 0.0,
        }

    @pytest.mark.unit
    def test_usage_summary_totals_and_rates_the_operations_it_finds(
        self, logger: UsageLogger
    ) -> None:
        """GIVEN three recent entries of which one failed
        WHEN get_usage_summary is called
        THEN the counts, token total and duration total sum all three,
        the success rate is 2/3, and the cost follows the token total.
        """
        now = self._utcnow()
        stamp = (now - timedelta(minutes=1)).isoformat() + "Z"
        self._write_log(
            logger,
            [
                self._entry(stamp=stamp, tokens=1000),
                self._entry(stamp=stamp, tokens=2000),
                self._entry(stamp=stamp, tokens=3000, success=False),
            ],
        )

        summary = logger.get_usage_summary()

        assert summary["total_operations"] == 3
        assert summary["total_tokens"] == 6000
        assert summary["success_rate"] == pytest.approx(2 / 3)
        assert summary["total_duration"] == pytest.approx(6.0)
        assert summary["estimated_cost"] == pytest.approx(6000 / 1_000_000 * 0.5)

    @pytest.mark.unit
    def test_recent_errors_returns_only_failures_newest_first(
        self, logger: UsageLogger
    ) -> None:
        """GIVEN a log holding two failures and one success
        WHEN get_recent_errors is called
        THEN only the failures come back, in reverse file order.

        The method reads the file backwards so that the count limit
        keeps the newest errors; asserting the order is what holds that.
        """
        stamp = self._utcnow().isoformat() + "Z"
        self._write_log(
            logger,
            [
                self._entry(stamp=stamp, operation="failed-first", success=False),
                self._entry(stamp=stamp, operation="worked"),
                self._entry(stamp=stamp, operation="failed-last", success=False),
            ],
        )

        errors = logger.get_recent_errors()

        assert [e["operation"] for e in errors] == ["failed-last", "failed-first"]

    @pytest.mark.unit
    def test_recent_errors_stops_at_the_requested_count(
        self, logger: UsageLogger
    ) -> None:
        """GIVEN three failures in the log
        WHEN get_recent_errors is asked for two
        THEN it returns the two nearest the end of the file.
        """
        stamp = self._utcnow().isoformat() + "Z"
        self._write_log(
            logger,
            [
                self._entry(stamp=stamp, operation=f"fail-{i}", success=False)
                for i in range(3)
            ],
        )

        errors = logger.get_recent_errors(count=2)

        assert [e["operation"] for e in errors] == ["fail-2", "fail-1"]

    @pytest.mark.unit
    def test_recent_errors_is_empty_when_no_log_file_exists(
        self, logger: UsageLogger
    ) -> None:
        """GIVEN no entry has ever been logged
        WHEN get_recent_errors is called
        THEN it returns an empty list.
        """
        assert logger.get_recent_errors() == []

    @pytest.mark.unit
    def test_session_operations_default_to_the_loggers_own_session(
        self, logger: UsageLogger
    ) -> None:
        """GIVEN entries from this logger's session and from another
        WHEN get_session_operations is called with no argument
        THEN only this session's entries come back.
        """
        stamp = self._utcnow().isoformat() + "Z"
        self._write_log(
            logger,
            [
                self._entry(stamp=stamp, session="s1", operation="mine"),
                self._entry(stamp=stamp, session="other", operation="theirs"),
            ],
        )

        operations = logger.get_session_operations()

        assert [op["operation"] for op in operations] == ["mine"]

    @pytest.mark.unit
    def test_session_operations_accept_an_explicit_session_id(
        self, logger: UsageLogger
    ) -> None:
        """GIVEN an explicit session id that is not the logger's own
        WHEN get_session_operations is called with it
        THEN that session's entries come back and the logger's do not.
        """
        stamp = self._utcnow().isoformat() + "Z"
        self._write_log(
            logger,
            [
                self._entry(stamp=stamp, session="s1", operation="mine"),
                self._entry(stamp=stamp, session="other", operation="theirs"),
            ],
        )

        operations = logger.get_session_operations(session_id="other")

        assert [op["operation"] for op in operations] == ["theirs"]

    @pytest.mark.unit
    def test_session_operations_is_empty_when_no_log_file_exists(
        self, logger: UsageLogger
    ) -> None:
        """GIVEN no entry has ever been logged
        WHEN get_session_operations is called
        THEN it returns an empty list.
        """
        assert logger.get_session_operations() == []
