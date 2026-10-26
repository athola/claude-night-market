"""Tests for usage_logger.py following TDD/BDD principles."""

from __future__ import annotations

import json
import os
import subprocess

# Import the module under test
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tests.scripts._writer_race import race_two_writers

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from usage_logger import (
    GeminiUsageLogger,
    UsageEntry,
    main,
)


def _seed_live_session(logger: GeminiUsageLogger, session_id: str) -> None:
    """Write a session file whose last activity is now, so it is reused."""
    now = datetime.now(timezone.utc).isoformat()
    logger.session_file.write_text(
        json.dumps({"session_id": session_id, "start_time": now, "last_activity": now})
    )


class TestUsageEntry:
    """Test UsageEntry dataclass."""

    @pytest.mark.bdd
    def test_usage_entry_creation_minimal(self) -> None:
        """Given minimal required data when creating UsageEntry then should.

        instantiate correctly.
        """
        entry = UsageEntry(command="test command", estimated_tokens=100)

        assert entry.command == "test command"
        assert entry.estimated_tokens == 100
        assert entry.actual_tokens is None
        assert entry.success is True
        assert entry.duration is None
        assert entry.error is None

    @pytest.mark.bdd
    def test_usage_entry_creation_full(self) -> None:
        """Given all data when creating UsageEntry then should store all fields."""
        entry = UsageEntry(
            command="test command",
            estimated_tokens=100,
            actual_tokens=150,
            success=False,
            duration=2.5,
            error="Something went wrong",
        )

        assert entry.command == "test command"
        assert entry.estimated_tokens == 100
        assert entry.actual_tokens == 150
        assert entry.success is False
        assert entry.duration == 2.5
        assert entry.error == "Something went wrong"


class TestGeminiUsageLogger:
    """Test GeminiUsageLogger class functionality."""

    @pytest.mark.bdd
    def test_initialization(self, tmp_path) -> None:
        """Given temp directory when initializing logger then should set.

        correct paths.
        """
        with patch("pathlib.Path.home", return_value=tmp_path):
            logger = GeminiUsageLogger()

        expected_log_dir = tmp_path / ".claude" / "hooks" / "gemini" / "logs"
        assert logger.log_dir == expected_log_dir
        assert logger.usage_log == expected_log_dir / "usage.jsonl"
        assert logger.session_file == expected_log_dir / "current_session.json"

    @pytest.mark.bdd
    def test_log_usage_success(self, tmp_path) -> None:
        """Given successful entry when logging usage then should write to log and.

        tag it with the live session.
        """
        with patch("pathlib.Path.home", return_value=tmp_path):
            logger = GeminiUsageLogger()
        _seed_live_session(logger, "test_session_123")

        entry = UsageEntry(
            command="gemini -p test",
            estimated_tokens=100,
            actual_tokens=150,
            success=True,
            duration=2.5,
        )

        logger.log_usage(entry)

        lines = logger.usage_log.read_text().splitlines()
        assert len(lines) == 1
        log_entry = json.loads(lines[0])
        assert log_entry["command"] == "gemini -p test"
        assert log_entry["estimated_tokens"] == 100
        assert log_entry["actual_tokens"] == 150
        assert log_entry["success"] is True
        assert log_entry["duration_seconds"] == 2.5
        assert log_entry["session_id"] == "test_session_123"

    @pytest.mark.bdd
    def test_log_usage_failure(self, tmp_path) -> None:
        """Given failed entry when logging usage then should record error.

        information.
        """
        with patch("pathlib.Path.home", return_value=tmp_path):
            logger = GeminiUsageLogger()
        _seed_live_session(logger, "test_session_123")

        entry = UsageEntry(
            command="gemini -p test",
            estimated_tokens=100,
            success=False,
            duration=1.0,
            error="API rate limit exceeded",
        )

        logger.log_usage(entry)

        log_entry = json.loads(logger.usage_log.read_text().splitlines()[0])
        assert log_entry["success"] is False
        assert log_entry["error"] == "API rate limit exceeded"
        assert log_entry["actual_tokens"] == 100  # Should fallback to estimated
        assert log_entry["session_id"] == "test_session_123"

    @pytest.mark.bdd
    def test_get_session_id_new_session(self, tmp_path) -> None:
        """Given no existing session when getting session ID then should create new.

        session.
        """
        with patch("pathlib.Path.home", return_value=tmp_path):
            logger = GeminiUsageLogger()

        with patch("time.time", return_value=1640995200):  # Fixed timestamp
            session_id = logger._get_session_id()

        assert session_id == "session_1640995200"

        # Verify session file was created
        assert logger.session_file.exists()

        with open(logger.session_file) as f:
            session_data = json.load(f)

        assert session_data["session_id"] == session_id
        assert "start_time" in session_data
        assert "last_activity" in session_data

    @pytest.mark.bdd
    def test_get_session_id_existing_session(self, tmp_path) -> None:
        """Given existing recent session when getting session ID then should reuse.

        existing.
        """
        with patch("pathlib.Path.home", return_value=tmp_path):
            logger = GeminiUsageLogger()

        # Create an existing session file - use timezone-aware datetimes
        # because the source uses datetime.now(timezone.utc) for comparison
        existing_session = {
            "session_id": "existing_session_456",
            "start_time": datetime.now(timezone.utc).isoformat(),
            "last_activity": (
                datetime.now(timezone.utc) - timedelta(minutes=30)
            ).isoformat(),
        }

        logger.session_file.parent.mkdir(parents=True, exist_ok=True)
        with open(logger.session_file, "w") as f:
            json.dump(existing_session, f)

        session_id = logger._get_session_id()

        assert session_id == "existing_session_456"

    @pytest.mark.bdd
    def test_get_session_id_expired_session(self, tmp_path) -> None:
        """Given expired session when getting session ID then should create new.

        session.
        """
        with patch("pathlib.Path.home", return_value=tmp_path):
            logger = GeminiUsageLogger()

        # Create an expired session file (older than 1 hour)
        # Use timezone-aware datetimes to match the source's datetime.now(timezone.utc)
        expired_session = {
            "session_id": "expired_session_789",
            "start_time": (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat(),
            "last_activity": (
                datetime.now(timezone.utc) - timedelta(hours=2)
            ).isoformat(),
        }

        logger.session_file.parent.mkdir(parents=True, exist_ok=True)
        with open(logger.session_file, "w") as f:
            json.dump(expired_session, f)

        with patch("time.time", return_value=1640995200):
            session_id = logger._get_session_id()

        # Should create a new session
        assert session_id == "session_1640995200"
        assert session_id != "expired_session_789"

    @pytest.mark.bdd
    def test_get_session_id_invalid_file(self, tmp_path) -> None:
        """Given corrupt session file when getting session ID then should create.

        new session.
        """
        with patch("pathlib.Path.home", return_value=tmp_path):
            logger = GeminiUsageLogger()

        # Create invalid session file
        logger.session_file.parent.mkdir(parents=True, exist_ok=True)
        with open(logger.session_file, "w") as f:
            f.write("invalid json content")

        with patch("time.time", return_value=1640995200):
            session_id = logger._get_session_id()

        # Should create a new session despite file corruption
        assert session_id == "session_1640995200"

    @pytest.mark.bdd
    def test_update_session_stats(self, tmp_path) -> None:
        """Given log entry when updating session stats then should increment.

        counters.
        """
        with patch("pathlib.Path.home", return_value=tmp_path):
            logger = GeminiUsageLogger()

        # Write a real session file with initial data
        initial_session = {
            "session_id": "test_session",
            "total_requests": 5,
            "total_tokens": 1000,
            "successful_requests": 4,
        }
        logger.session_file.parent.mkdir(parents=True, exist_ok=True)
        with open(logger.session_file, "w") as f:
            json.dump(initial_session, f)

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "actual_tokens": 200,
            "success": True,
        }

        logger._update_session_stats(log_entry)

        # Read back the updated session file and verify counters
        with open(logger.session_file) as f:
            updated_session = json.load(f)

        assert updated_session["total_requests"] == 6
        assert updated_session["total_tokens"] == 1200
        assert updated_session["successful_requests"] == 5

    def test_update_session_stats_no_file(self, tmp_path) -> None:
        """Given no session file when updating stats then should create new.

        session data.
        """
        with patch("pathlib.Path.home", return_value=tmp_path):
            logger = GeminiUsageLogger()
        assert not logger.session_file.exists()

        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actual_tokens": 150,
            "success": False,
        }

        logger._update_session_stats(log_entry)

        updated_session = json.loads(logger.session_file.read_text())
        assert updated_session["session_id"].startswith("session_")
        assert updated_session["total_requests"] == 1
        assert updated_session["total_tokens"] == 150
        assert updated_session.get("successful_requests", 0) == 0

    @pytest.mark.bdd
    def test_get_usage_summary_no_log(self, tmp_path) -> None:
        """Given no usage log when getting summary then should return empty stats."""
        with patch("pathlib.Path.home", return_value=tmp_path):
            logger = GeminiUsageLogger()

        summary = logger.get_usage_summary()

        assert summary["total_requests"] == 0
        assert summary["total_tokens"] == 0
        assert summary["success_rate"] == 0.0
        # hours_analyzed is not included in the early-return path (no log file)

    @pytest.mark.bdd
    def test_get_usage_summary_with_data(self, tmp_path) -> None:
        """Given usage log with data when getting summary then should calculate.

        correctly.
        """
        with patch("pathlib.Path.home", return_value=tmp_path):
            logger = GeminiUsageLogger()

        # Create sample log entries
        now = datetime.now()
        entries = [
            {
                "timestamp": (now - timedelta(minutes=30)).isoformat(),
                "command": "gemini test1",
                "estimated_tokens": 100,
                "actual_tokens": 120,
                "success": True,
                "duration_seconds": 2.0,
                "error": None,
                "session_id": "session1",
            },
            {
                "timestamp": (now - timedelta(minutes=15)).isoformat(),
                "command": "gemini test2",
                "estimated_tokens": 200,
                "actual_tokens": 180,
                "success": True,
                "duration_seconds": 1.5,
                "error": None,
                "session_id": "session1",
            },
            {
                "timestamp": (now - timedelta(minutes=5)).isoformat(),
                "command": "gemini test3",
                "estimated_tokens": 150,
                "actual_tokens": 150,
                "success": False,
                "duration_seconds": 0.5,
                "error": "API error",
                "session_id": "session1",
            },
        ]

        logger.usage_log.parent.mkdir(parents=True, exist_ok=True)
        with open(logger.usage_log, "w") as f:
            f.writelines(json.dumps(entry) + "\n" for entry in entries)

        summary = logger.get_usage_summary(hours=1)  # Last hour

        assert summary["total_requests"] == 3
        assert summary["total_tokens"] == 450  # 120 + 180 + 150
        assert summary["successful_requests"] == 2
        # 2/3 * 100 = 66.666..., so use approx for floating point comparison
        assert summary["success_rate"] == pytest.approx(66.7, abs=0.1)

    @pytest.mark.bdd
    def test_get_usage_summary_time_filtering(self, tmp_path) -> None:
        """Given mixed time data when getting summary then should only include.

        recent entries.
        """
        with patch("pathlib.Path.home", return_value=tmp_path):
            logger = GeminiUsageLogger()

        now = datetime.now()
        entries = [
            {
                "timestamp": (now - timedelta(hours=2)).isoformat(),  # Too old
                "command": "old request",
                "actual_tokens": 100,
                "success": True,
            },
            {
                "timestamp": (now - timedelta(minutes=30)).isoformat(),  # Recent
                "command": "new request",
                "actual_tokens": 200,
                "success": True,
            },
        ]

        logger.usage_log.parent.mkdir(parents=True, exist_ok=True)
        with open(logger.usage_log, "w") as f:
            f.writelines(json.dumps(entry) + "\n" for entry in entries)

        summary = logger.get_usage_summary(hours=1)  # Last hour only

        assert summary["total_requests"] == 1  # Only the recent request
        assert summary["total_tokens"] == 200

    @pytest.mark.bdd
    def test_get_recent_errors_no_log(self, tmp_path) -> None:
        """Given no usage log when getting recent errors then should return.

        empty list.
        """
        with patch("pathlib.Path.home", return_value=tmp_path):
            logger = GeminiUsageLogger()

        errors = logger.get_recent_errors()

        assert errors == []

    @pytest.mark.bdd
    def test_get_recent_errors_with_errors(self, tmp_path) -> None:
        """Given usage log with errors when getting recent errors then should.

        return error entries.
        """
        with patch("pathlib.Path.home", return_value=tmp_path):
            logger = GeminiUsageLogger()

        now = datetime.now()
        entries = [
            {
                "timestamp": (now - timedelta(minutes=30)).isoformat(),
                "command": "gemini success",
                "success": True,
                "error": None,
            },
            {
                "timestamp": (now - timedelta(minutes=20)).isoformat(),
                "command": "gemini error1",
                "success": False,
                "error": "Rate limit exceeded",
            },
            {
                "timestamp": (now - timedelta(minutes=10)).isoformat(),
                "command": "gemini error2",
                "success": False,
                "error": "API key invalid",
            },
        ]

        logger.usage_log.parent.mkdir(parents=True, exist_ok=True)
        with open(logger.usage_log, "w") as f:
            f.writelines(json.dumps(entry) + "\n" for entry in entries)

        errors = logger.get_recent_errors(count=5)

        assert len(errors) == 2
        assert errors[0]["error"] == "Rate limit exceeded"
        assert errors[1]["error"] == "API key invalid"

    @pytest.mark.bdd
    def test_get_recent_errors_limit_count(self, tmp_path) -> None:
        """Given many errors when getting recent errors with limit then should.

        return only requested count.
        """
        with patch("pathlib.Path.home", return_value=tmp_path):
            logger = GeminiUsageLogger()

        entries = []
        for i in range(10):
            entries.append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "command": f"gemini error{i}",
                    "success": False,
                    "error": f"Error {i}",
                },
            )

        logger.usage_log.parent.mkdir(parents=True, exist_ok=True)
        with open(logger.usage_log, "w") as f:
            f.writelines(json.dumps(entry) + "\n" for entry in entries)

        errors = logger.get_recent_errors(count=3)

        assert len(errors) == 3
        # Should return the last 3 errors
        assert errors[0]["error"] == "Error 7"
        assert errors[1]["error"] == "Error 8"
        assert errors[2]["error"] == "Error 9"


class TestUsageLogRotation:
    """The usage log rotates to one backup so it cannot grow without bound."""

    @staticmethod
    def _logger(tmp_path: Path) -> GeminiUsageLogger:
        with patch("pathlib.Path.home", return_value=tmp_path):
            return GeminiUsageLogger()

    @staticmethod
    def _write(path: Path, entries: list[dict]) -> None:
        path.write_text("".join(json.dumps(e) + "\n" for e in entries))

    @staticmethod
    def _entry(name: str, success: bool = True) -> dict:
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "command": name,
            "actual_tokens": 10,
            "success": success,
            "error": None if success else name,
        }

    @pytest.mark.unit
    def test_log_usage_rotates_when_log_reaches_max_bytes(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A full log moves to usage.jsonl.1 and the new entry starts a fresh log."""
        monkeypatch.setattr("usage_logger.MAX_LOG_BYTES", 100)
        logger = self._logger(tmp_path)
        old = "x" * 120 + "\n"
        logger.usage_log.write_text(old)

        logger.log_usage(UsageEntry(command="gemini new", estimated_tokens=5))

        backup = logger.usage_log.with_name("usage.jsonl.1")
        assert backup.read_text() == old
        lines = logger.usage_log.read_text().splitlines()
        assert len(lines) == 1
        assert json.loads(lines[0])["command"] == "gemini new"

    @pytest.mark.unit
    def test_log_usage_keeps_appending_below_max_bytes(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Under the limit the log is appended to and no backup appears."""
        monkeypatch.setattr("usage_logger.MAX_LOG_BYTES", 10_000)
        logger = self._logger(tmp_path)
        logger.log_usage(UsageEntry(command="a", estimated_tokens=1))
        logger.log_usage(UsageEntry(command="b", estimated_tokens=1))

        assert len(logger.usage_log.read_text().splitlines()) == 2
        assert not logger.usage_log.with_name("usage.jsonl.1").exists()

    @pytest.mark.unit
    def test_rotation_replaces_the_previous_backup(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Only one backup is kept, so disk use stays near twice the limit."""
        monkeypatch.setattr("usage_logger.MAX_LOG_BYTES", 100)
        logger = self._logger(tmp_path)
        backup = logger.usage_log.with_name("usage.jsonl.1")
        backup.write_text("oldest\n")
        logger.usage_log.write_text("y" * 120 + "\n")

        logger.log_usage(UsageEntry(command="c", estimated_tokens=1))

        assert backup.read_text() == "y" * 120 + "\n"

    @pytest.mark.unit
    def test_usage_summary_counts_entries_on_both_sides_of_a_rotation(
        self, tmp_path: Path
    ) -> None:
        """A 24h window that spans a rotation still sees every entry in it."""
        logger = self._logger(tmp_path)
        self._write(logger.usage_log.with_name("usage.jsonl.1"), [self._entry("a")])
        self._write(logger.usage_log, [self._entry("b"), self._entry("c")])

        assert logger.get_usage_summary(hours=24)["total_requests"] == 3

    @pytest.mark.unit
    def test_recent_errors_read_backup_before_current_log(self, tmp_path: Path) -> None:
        """Errors come back oldest first across the backup and the live log."""
        logger = self._logger(tmp_path)
        self._write(
            logger.usage_log.with_name("usage.jsonl.1"),
            [self._entry("e1", success=False), self._entry("e2", success=False)],
        )
        self._write(logger.usage_log, [self._entry("e3", success=False)])

        errors = logger.get_recent_errors(count=2)

        assert [e["error"] for e in errors] == ["e2", "e3"]


class TestUsageLogRotationFailure:
    """A rotation that cannot rename the log still records the entry."""

    @pytest.mark.unit
    def test_failed_rotation_keeps_appending(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Delegator already tolerates this; the Gemini logger must too."""
        monkeypatch.setattr("usage_logger.MAX_LOG_BYTES", 10)
        with patch("pathlib.Path.home", return_value=tmp_path):
            logger = GeminiUsageLogger()
        logger.usage_log.write_text("x" * 20 + "\n")

        def _refuse(self: Path, target: Path) -> Path:
            raise PermissionError("read-only log directory")

        monkeypatch.setattr(Path, "replace", _refuse)
        logger.log_usage(UsageEntry(command="gemini new", estimated_tokens=1))

        assert "gemini new" in logger.usage_log.read_text()


class TestUsageLogMalformedLines:
    """A valid-JSON line that is not an object is skipped, not fatal."""

    @pytest.mark.unit
    @pytest.mark.parametrize("bad_line", ["[1, 2]", "42", "null", '"text"'])
    def test_readers_skip_non_object_lines(self, tmp_path: Path, bad_line: str) -> None:
        """Summary and error readers count only the object line."""
        with patch("pathlib.Path.home", return_value=tmp_path):
            logger = GeminiUsageLogger()
        good = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "command": "c",
            "actual_tokens": 3,
            "success": False,
            "error": "boom",
        }
        logger.usage_log.write_text(bad_line + "\n" + json.dumps(good) + "\n")

        assert logger.get_usage_summary(hours=24)["total_requests"] == 1
        assert [e["error"] for e in logger.get_recent_errors(5)] == ["boom"]


class TestUsageLoggerCli:
    """Test CLI functionality of usage logger."""

    @patch("usage_logger.GeminiUsageLogger")
    @patch(
        "sys.argv",
        ["usage_logger.py", "--log", "gemini test", "150", "true", "2.5"],
    )
    @pytest.mark.bdd
    def test_cli_log_usage_success(self, mock_logger_class) -> None:
        """Given valid log arguments when running CLI then should log usage."""
        mock_logger = MagicMock()
        mock_logger_class.return_value = mock_logger

        with patch("builtins.print"):
            # main imported at top level

            main()

        # Verify UsageEntry was created with correct data
        created_entry = mock_logger.log_usage.call_args[0][0]
        assert isinstance(created_entry, UsageEntry)
        assert created_entry.command == "gemini test"
        assert created_entry.estimated_tokens == 150
        assert created_entry.success is True
        assert created_entry.duration == 2.5
        # The real CLI does not print anything on successful --log (no print call)

    @patch("usage_logger.GeminiUsageLogger")
    @patch(
        "sys.argv",
        ["usage_logger.py", "--log", "gemini test", "invalid", "true", "2.5"],
    )
    @pytest.mark.bdd
    def test_cli_log_usage_invalid_tokens(self, mock_logger_class) -> None:
        """Given invalid tokens argument when running CLI then should exit non-zero.

        A malformed --log argument used to be swallowed with `pass`, so the
        CLI wrote nothing and still exited 0 and a caller checking the exit
        code read a constant.
        """
        mock_logger = MagicMock()
        mock_logger_class.return_value = mock_logger

        with patch("builtins.print"), pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1
        mock_logger.log_usage.assert_not_called()

    @patch("usage_logger.GeminiUsageLogger")
    @patch("sys.argv", ["usage_logger.py", "--report"])
    def test_cli_report(self, mock_logger_class) -> None:
        """Given --report flag when running CLI then should show usage report."""
        mock_logger = MagicMock()
        mock_logger.get_usage_summary.return_value = {
            "total_requests": 25,
            "success_rate": 92.5,
            "total_tokens": 5000,
        }
        mock_logger_class.return_value = mock_logger

        with patch("builtins.print") as mock_print:
            # main imported at top level

            main()

        # Real CLI output: "Requests: {n}", "Tokens: {n}", "Success rate: {n:.1f}%"
        mock_print.assert_any_call("Requests: 25")
        mock_print.assert_any_call("Tokens: 5000")
        mock_print.assert_any_call("Success rate: 92.5%")

    @patch("usage_logger.GeminiUsageLogger")
    @patch("sys.argv", ["usage_logger.py", "--validate"])
    def test_cli_validate(self, mock_logger_class, tmp_path) -> None:
        """Given --validate flag when running CLI then should show validation info."""
        # A writable directory with no log files yet: the state on a first run.
        # Nothing has been logged, but nothing is broken either, so this passes.
        mock_logger = MagicMock()
        mock_logger.log_dir = tmp_path
        mock_logger.usage_log = tmp_path / "usage.jsonl"
        mock_logger.session_file = tmp_path / "session.json"
        mock_logger_class.return_value = mock_logger

        with patch("builtins.print") as mock_print:
            # main imported at top level

            main()

        # Real CLI output: "Log directory: {path}", "Log exists: {bool}",
        # "Session file exists: {bool}"
        mock_print.assert_any_call(f"Log directory: {tmp_path}")
        mock_print.assert_any_call("Log exists: False")
        mock_print.assert_any_call("Session file exists: False")

    @patch("usage_logger.GeminiUsageLogger")
    @patch("sys.argv", ["usage_logger.py", "--validate"])
    def test_cli_validate_fails_on_corrupt_log(
        self, mock_logger_class, tmp_path
    ) -> None:
        """Given an unparseable usage log, --validate must exit nonzero."""
        usage_log = tmp_path / "usage.jsonl"
        usage_log.write_text('{"ok": 1}\nnot json at all\n')

        mock_logger = MagicMock()
        mock_logger.log_dir = tmp_path
        mock_logger.usage_log = usage_log
        mock_logger.session_file = tmp_path / "session.json"
        mock_logger_class.return_value = mock_logger

        # Appending to a log that can no longer be read compounds the damage,
        # so validation has to fail rather than report the config as healthy.
        with pytest.raises(SystemExit) as excinfo:
            main()
        assert excinfo.value.code == 1

    @patch("usage_logger.GeminiUsageLogger")
    @patch("sys.argv", ["usage_logger.py", "--status"])
    def test_cli_status(self, mock_logger_class) -> None:
        """Given --status flag when running CLI then should show status info."""
        mock_logger = MagicMock()
        # session_file.exists() returns False -> "No active session" branch
        mock_logger.session_file.exists.return_value = False
        mock_logger_class.return_value = mock_logger

        with patch("builtins.print") as mock_print:
            main()

        # Real CLI: if session file doesn't exist, prints "No active session"
        mock_print.assert_any_call("No active session")

    @pytest.mark.bdd
    @patch("usage_logger.GeminiUsageLogger")
    @patch("sys.argv", ["usage_logger.py"])
    def test_cli_no_arguments(self, mock_logger_class) -> None:
        """Given no arguments when running CLI then should show usage help."""
        mock_logger = MagicMock()
        mock_logger_class.return_value = mock_logger

        with patch("builtins.print") as mock_print:
            # main imported at top level

            main()

        # Real CLI prints only "Use --help for available commands" when no args given
        mock_print.assert_any_call("Use --help for available commands")


class TestUsageSummaryBadTimestamp:
    """A line with an unparseable timestamp is skipped, not fatal to --summary."""

    @pytest.mark.unit
    @pytest.mark.parametrize("bad_timestamp", ["yesterday", 123])
    def test_summary_skips_line_with_bad_timestamp(
        self, tmp_path: Path, bad_timestamp: object
    ) -> None:
        """A non-ISO string or a number skips that line, not the summary."""
        with patch("pathlib.Path.home", return_value=tmp_path):
            logger = GeminiUsageLogger()
        good = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actual_tokens": 7,
            "success": True,
        }
        bad = {**good, "timestamp": bad_timestamp}
        logger.usage_log.write_text(json.dumps(bad) + "\n" + json.dumps(good) + "\n")

        summary = logger.get_usage_summary(hours=24)

        assert summary["total_requests"] == 1
        assert summary["total_tokens"] == 7


class TestConcurrentRotation:
    """Two processes that both find the log full must rotate it once."""

    @pytest.mark.unit
    def test_concurrent_writers_rotate_once_and_keep_the_full_backup(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The second writer re-checks the size under the lock and appends."""
        monkeypatch.setattr("usage_logger.MAX_LOG_BYTES", 1000)
        with patch("pathlib.Path.home", return_value=tmp_path):
            first = GeminiUsageLogger()
            second = GeminiUsageLogger()
        # Over the limit, while one appended entry stays under it.
        full = "x" * 1100 + "\n"
        first.usage_log.write_text(full)

        errors = race_two_writers(
            monkeypatch,
            first.usage_log,
            lambda: first.log_usage(UsageEntry(command="a", estimated_tokens=1)),
            lambda: second.log_usage(UsageEntry(command="b", estimated_tokens=1)),
        )

        assert errors == []
        assert first.usage_backup.read_text() == full
        live = [json.loads(line)["command"] for line in first.usage_log.open()]
        assert sorted(live) == ["a", "b"]


def test_recent_errors_skip_a_line_that_is_not_json(tmp_path: Path) -> None:
    """A truncated log line does not hide the errors around it.

    GIVEN a usage log holding an unparsable line and a failed request
    WHEN recent errors are read
    THEN only the failed request is returned.
    """
    with patch("pathlib.Path.home", return_value=tmp_path):
        logger = GeminiUsageLogger()
    failed = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "command": "c",
        "success": False,
        "error": "boom",
    }
    logger.usage_log.write_text('{"truncated": \n' + json.dumps(failed) + "\n")

    errors = logger.get_recent_errors(5)

    assert [entry["error"] for entry in errors] == ["boom"]


def test_cli_log_rejects_a_success_value_that_is_not_true_or_false(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--log exits 1 and names the bad success value instead of logging.

    GIVEN --log arguments whose success field is "maybe"
    WHEN the CLI runs
    THEN it exits 1 AND stderr says success must be true or false
    AND nothing is logged.
    """
    argv = ["usage_logger.py", "--log", "gemini test", "150", "maybe", "2.5"]

    with (
        patch("usage_logger.GeminiUsageLogger") as logger_class,
        patch("sys.argv", argv),
        pytest.raises(SystemExit) as exc_info,
    ):
        main()

    assert exc_info.value.code == 1
    assert "success must be true or false, got 'maybe'" in capsys.readouterr().err
    logger_class.return_value.log_usage.assert_not_called()


class TestStatusScriptImportPath:
    """Feature: bin/status.sh imports the logger with only scripts/ on the path."""

    @pytest.mark.unit
    def test_logger_imports_by_bare_name_with_only_scripts_on_the_path(
        self, tmp_path: Path
    ) -> None:
        """The bare-name fallback import keeps the status report working.

        GIVEN PYTHONPATH holding only the scripts directory, as status.sh sets it
        WHEN a fresh interpreter imports usage_logger and asks for a summary
        THEN it exits 0 and prints the summary keys

        status.sh sends this interpreter's stderr to /dev/null and prints
        "Usage logger unavailable" on any failure, so a broken fallback
        import would never surface as an error. -S drops site-packages:
        the venv's editable install would otherwise make the package
        import succeed and the fallback would go unexercised.
        """
        scripts_dir = Path(__file__).resolve().parents[2] / "scripts"
        probe = (
            "from usage_logger import GeminiUsageLogger\n"
            "print(sorted(GeminiUsageLogger().get_usage_summary()))\n"
        )
        env = {
            **os.environ,
            "PYTHONPATH": str(scripts_dir),
            "HOME": str(tmp_path),
        }

        completed = subprocess.run(
            [sys.executable, "-S", "-c", probe],
            cwd=tmp_path,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

        assert completed.returncode == 0, completed.stderr
        assert "total_requests" in completed.stdout
