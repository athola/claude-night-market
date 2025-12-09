"""Tests for usage_logger.py following TDD/BDD principles."""

import json

# Import the module under test
import sys
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from usage_logger import (
    GeminiUsageLogger,
    UsageEntry,
    main,
)


class TestUsageEntry:
    """Test UsageEntry dataclass."""

    def test_usage_entry_creation_minimal(self) -> None:
        """Given minimal required data when creating UsageEntry then should instantiate correctly."""
        entry = UsageEntry(command="test command", estimated_tokens=100)

        assert entry.command == "test command"
        assert entry.estimated_tokens == 100
        assert entry.actual_tokens is None
        assert entry.success is True
        assert entry.duration is None
        assert entry.error is None

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

    def test_initialization(self, tmp_path) -> None:
        """Given temp directory when initializing logger then should set correct paths."""
        with patch("pathlib.Path.home", return_value=tmp_path):
            logger = GeminiUsageLogger()

        expected_log_dir = tmp_path / ".claude" / "hooks" / "gemini" / "logs"
        assert logger.log_dir == expected_log_dir
        assert logger.usage_log == expected_log_dir / "usage.jsonl"
        assert logger.session_file == expected_log_dir / "current_session.json"

    @patch("builtins.open", new_callable=mock_open)
    @patch("usage_logger.GeminiUsageLogger._get_session_id")
    def test_log_usage_success(self, mock_session_id, mock_file, tmp_path) -> None:
        """Given successful entry when logging usage then should write to log and update session."""
        mock_session_id.return_value = "test_session_123"

        with patch("pathlib.Path.home", return_value=tmp_path):
            logger = GeminiUsageLogger()

        entry = UsageEntry(
            command="gemini -p test",
            estimated_tokens=100,
            actual_tokens=150,
            success=True,
            duration=2.5,
        )

        logger.log_usage(entry)

        # Verify log file was written to
        mock_file.assert_called()

        # Get the write calls and verify the log entry
        write_calls = mock_file.return_value.write.call_args_list
        written_data = write_calls[0][0][0]  # First write call, first argument

        log_entry = json.loads(written_data.strip())
        assert log_entry["command"] == "gemini -p test"
        assert log_entry["estimated_tokens"] == 100
        assert log_entry["actual_tokens"] == 150
        assert log_entry["success"] is True
        assert log_entry["duration_seconds"] == 2.5
        assert log_entry["session_id"] == "test_session_123"

    @patch("builtins.open", new_callable=mock_open)
    @patch("usage_logger.GeminiUsageLogger._get_session_id")
    def test_log_usage_failure(self, mock_session_id, mock_file, tmp_path) -> None:
        """Given failed entry when logging usage then should record error information."""
        mock_session_id.return_value = "test_session_123"

        with patch("pathlib.Path.home", return_value=tmp_path):
            logger = GeminiUsageLogger()

        entry = UsageEntry(
            command="gemini -p test",
            estimated_tokens=100,
            success=False,
            duration=1.0,
            error="API rate limit exceeded",
        )

        logger.log_usage(entry)

        # Get the write calls and verify the log entry
        write_calls = mock_file.return_value.write.call_args_list
        written_data = write_calls[0][0][0]

        log_entry = json.loads(written_data.strip())
        assert log_entry["success"] is False
        assert log_entry["error"] == "API rate limit exceeded"
        assert log_entry["actual_tokens"] == 100  # Should fallback to estimated

    def test_get_session_id_new_session(self, tmp_path) -> None:
        """Given no existing session when getting session ID then should create new session."""
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

    def test_get_session_id_existing_session(self, tmp_path) -> None:
        """Given existing recent session when getting session ID then should reuse existing."""
        with patch("pathlib.Path.home", return_value=tmp_path):
            logger = GeminiUsageLogger()

        # Create an existing session file
        existing_session = {
            "session_id": "existing_session_456",
            "start_time": datetime.now().isoformat(),
            "last_activity": (datetime.now() - timedelta(minutes=30)).isoformat(),
        }

        logger.session_file.parent.mkdir(parents=True, exist_ok=True)
        with open(logger.session_file, "w") as f:
            json.dump(existing_session, f)

        session_id = logger._get_session_id()

        assert session_id == "existing_session_456"

    def test_get_session_id_expired_session(self, tmp_path) -> None:
        """Given expired session when getting session ID then should create new session."""
        with patch("pathlib.Path.home", return_value=tmp_path):
            logger = GeminiUsageLogger()

        # Create an expired session file (older than 1 hour)
        expired_session = {
            "session_id": "expired_session_789",
            "start_time": (datetime.now() - timedelta(hours=2)).isoformat(),
            "last_activity": (datetime.now() - timedelta(hours=2)).isoformat(),
        }

        logger.session_file.parent.mkdir(parents=True, exist_ok=True)
        with open(logger.session_file, "w") as f:
            json.dump(expired_session, f)

        with patch("time.time", return_value=1640995200):
            session_id = logger._get_session_id()

        # Should create a new session
        assert session_id == "session_1640995200"
        assert session_id != "expired_session_789"

    def test_get_session_id_invalid_file(self, tmp_path) -> None:
        """Given corrupt session file when getting session ID then should create new session."""
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

    @patch("builtins.open", new_callable=mock_open)
    @patch("usage_logger.GeminiUsageLogger._get_session_id")
    def test_update_session_stats(self, mock_session_id, mock_file, tmp_path) -> None:
        """Given log entry when updating session stats then should increment counters."""
        mock_session_id.return_value = "test_session"

        with patch("pathlib.Path.home", return_value=tmp_path):
            logger = GeminiUsageLogger()

        # Create initial session data
        initial_session = {
            "session_id": "test_session",
            "total_requests": 5,
            "total_tokens": 1000,
            "successful_requests": 4,
        }

        mock_file.return_value.__enter__.return_value.read.return_value = json.dumps(
            initial_session,
        )

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "actual_tokens": 200,
            "success": True,
        }

        logger._update_session_stats(log_entry)

        # Verify the updated session data was written
        write_calls = mock_file.return_value.write.call_args_list
        written_data = write_calls[0][0][0]

        updated_session = json.loads(written_data)
        assert updated_session["total_requests"] == 6
        assert updated_session["total_tokens"] == 1200
        assert updated_session["successful_requests"] == 5

    @patch("builtins.open", new_callable=mock_open)
    @patch("usage_logger.GeminiUsageLogger._get_session_id")
    def test_update_session_stats_no_file(
        self, mock_session_id, mock_file, tmp_path
    ) -> None:
        """Given no session file when updating stats then should create new session data."""
        mock_session_id.return_value = "test_session"

        with patch("pathlib.Path.home", return_value=tmp_path):
            logger = GeminiUsageLogger()

        # Mock file not existing for read
        mock_file.side_effect = [FileNotFoundError, mock_open().return_value]

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "actual_tokens": 150,
            "success": False,
        }

        logger._update_session_stats(log_entry)

        # Verify new session data was created
        write_calls = mock_file.return_value.write.call_args_list
        if write_calls:  # Only check if write was attempted
            written_data = write_calls[0][0][0]
            updated_session = json.loads(written_data)
            assert updated_session["total_requests"] == 1
            assert updated_session["total_tokens"] == 150
            assert updated_session["successful_requests"] == 0

    def test_get_usage_summary_no_log(self, tmp_path) -> None:
        """Given no usage log when getting summary then should return empty stats."""
        with patch("pathlib.Path.home", return_value=tmp_path):
            logger = GeminiUsageLogger()

        summary = logger.get_usage_summary()

        assert summary["total_requests"] == 0
        assert summary["total_tokens"] == 0
        assert summary["success_rate"] == 0.0
        assert summary["hours_analyzed"] == 24

    def test_get_usage_summary_with_data(self, tmp_path) -> None:
        """Given usage log with data when getting summary then should calculate correctly."""
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
        assert summary["success_rate"] == 66.7  # 2/3 * 100, rounded

    def test_get_usage_summary_time_filtering(self, tmp_path) -> None:
        """Given mixed time data when getting summary then should only include recent entries."""
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

    def test_get_recent_errors_no_log(self, tmp_path) -> None:
        """Given no usage log when getting recent errors then should return empty list."""
        with patch("pathlib.Path.home", return_value=tmp_path):
            logger = GeminiUsageLogger()

        errors = logger.get_recent_errors()

        assert errors == []

    def test_get_recent_errors_with_errors(self, tmp_path) -> None:
        """Given usage log with errors when getting recent errors then should return error entries."""
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

    def test_get_recent_errors_limit_count(self, tmp_path) -> None:
        """Given many errors when getting recent errors with limit then should return only requested count."""
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


class TestUsageLoggerCli:
    """Test CLI functionality of usage logger."""

    @patch("usage_logger.GeminiUsageLogger")
    @patch(
        "sys.argv",
        ["usage_logger.py", "--log", "gemini test", "150", "true", "2.5"],
    )
    def test_cli_log_usage_success(self, mock_logger_class) -> None:
        """Given valid log arguments when running CLI then should log usage."""
        mock_logger = MagicMock()
        mock_logger_class.return_value = mock_logger

        with patch("builtins.print") as mock_print:
            # main imported at top level

            main()

        # Verify UsageEntry was created with correct data
        created_entry = mock_logger.log_usage.call_args[0][0]
        assert isinstance(created_entry, UsageEntry)
        assert created_entry.command == "gemini test"
        assert created_entry.estimated_tokens == 150
        assert created_entry.success is True
        assert created_entry.duration == 2.5

        mock_print.assert_any_call("Logged usage for gemini test")

    @patch("usage_logger.GeminiUsageLogger")
    @patch(
        "sys.argv",
        ["usage_logger.py", "--log", "gemini test", "invalid", "true", "2.5"],
    )
    def test_cli_log_usage_invalid_tokens(self, mock_logger_class) -> None:
        """Given invalid tokens argument when running CLI then should show error."""
        mock_logger = MagicMock()
        mock_logger_class.return_value = mock_logger

        with patch("builtins.print") as mock_print:
            # main imported at top level

            main()

        mock_logger.log_usage.assert_not_called()
        mock_print.assert_any_call("Error parsing arguments: invalid literal for int()")

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

        mock_print.assert_any_call("Gemini Usage Report")
        mock_print.assert_any_call("=" * 20)
        mock_print.assert_any_call("Total requests: 25")
        mock_print.assert_any_call("Success rate: 92.5%")
        mock_print.assert_any_call("Total tokens: 5000")

    @patch("usage_logger.GeminiUsageLogger")
    @patch("sys.argv", ["usage_logger.py", "--validate"])
    def test_cli_validate(self, mock_logger_class) -> None:
        """Given --validate flag when running CLI then should show validation info."""
        mock_logger = MagicMock()
        mock_logger.log_dir = Path("/test/logs")
        mock_logger.usage_log = Path("/test/logs/usage.jsonl")
        mock_logger.session_file = Path("/test/logs/session.json")
        mock_logger_class.return_value = mock_logger

        with patch("builtins.print") as mock_print:
            # main imported at top level

            main()

        mock_print.assert_any_call("Usage logger validation:")
        mock_print.assert_any_call("Log directory: /test/logs")
        mock_print.assert_any_call("Usage log: /test/logs/usage.jsonl")
        mock_print.assert_any_call("Session file: /test/logs/session.json")
        mock_print.assert_any_call("Configuration is valid")

    @patch("usage_logger.GeminiUsageLogger")
    @patch("sys.argv", ["usage_logger.py", "--status"])
    def test_cli_status(self, mock_logger_class) -> None:
        """Given --status flag when running CLI then should show status info."""
        mock_logger = MagicMock()
        mock_logger.log_dir.exists.return_value = True
        mock_logger.session_file.exists.return_value = True
        mock_logger_class.return_value = mock_logger

        with patch("builtins.print") as mock_print:
            # main imported at top level

            main()

        mock_print.assert_any_call("Usage logger status:")
        mock_print.assert_any_call("Log directory exists: True")
        mock_print.assert_any_call("Current session active: True")

    @patch("usage_logger.GeminiUsageLogger")
    @patch("sys.argv", ["usage_logger.py"])
    def test_cli_no_arguments(self, mock_logger_class) -> None:
        """Given no arguments when running CLI then should show usage help."""
        mock_logger = MagicMock()
        mock_logger_class.return_value = mock_logger

        with patch("builtins.print") as mock_print:
            # main imported at top level

            main()

        mock_print.assert_any_call(
            "Usage: usage-logger --log <command> <tokens> <success> <duration>",
        )
        mock_print.assert_any_call("       usage-logger --report")
        mock_print.assert_any_call("       usage-logger --validate")
        mock_print.assert_any_call("       usage-logger --status")
