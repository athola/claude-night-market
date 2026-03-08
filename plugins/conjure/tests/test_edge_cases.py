"""Edge case and error handling tests for conjure plugin.

Uses parametrize for repeated patterns and adds mock verification.
"""

from __future__ import annotations

import json
import os
import queue
import sys
import threading
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from delegation_executor import Delegator, ExecutionResult
from quota_tracker import GeminiQuotaTracker
from usage_logger import GeminiUsageLogger, UsageEntry


class TestDelegationExecutorEdgeCases:
    """Test edge cases for delegation executor."""

    def test_delegator_initialization_with_invalid_config(
        self, tmp_path: Path,
    ) -> None:
        """Invalid config structure falls back to default services."""
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({
            "services": {
                "test_service": {"name": "test"},
            },
        }, indent=2))

        delegator = Delegator(config_dir=tmp_path)
        assert "gemini" in delegator.services

    @patch("subprocess.run")
    def test_service_verification_auth_failure(
        self, mock_run: MagicMock, tmp_path: Path,
    ) -> None:
        """Auth check failure reports authentication issue."""
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="version info"),
            MagicMock(returncode=1, stderr="Authentication failed"),
        ]

        delegator = Delegator(config_dir=tmp_path)
        with patch.dict("os.environ", {}, clear=False):
            if "GEMINI_API_KEY" in os.environ:
                del os.environ["GEMINI_API_KEY"]

        is_available, issues = delegator.verify_service("gemini")

        assert is_available is False
        assert any(
            "authentication" in issue.lower() or "GEMINI_API_KEY" in issue
            for issue in issues
        )

    @pytest.mark.parametrize(
        "file_content",
        [
            "Test with unicode: \u03b1\u03b2\u03b3\u03b4\u03b5\u6f22\u5b57\U00010348",
            "ASCII only content",
            "",
        ],
        ids=["unicode", "ascii", "empty"],
    )
    @patch("subprocess.run")
    def test_execution_with_various_file_content(
        self,
        mock_run: MagicMock,
        tmp_path: Path,
        file_content: str,
    ) -> None:
        """Delegator handles files with various content types."""
        mock_run.return_value = MagicMock(
            returncode=0, stdout="Success", stderr="",
        )

        delegator = Delegator(config_dir=tmp_path)
        test_file = tmp_path / "test.txt"
        test_file.write_text(file_content)

        result = delegator.execute(
            "gemini", "Process content", files=[str(test_file)],
        )

        assert isinstance(result, ExecutionResult)
        assert result.success is True
        # Verify subprocess.run was called with the right service
        mock_run.assert_called_once()
        cmd = mock_run.call_args.args[0]
        assert cmd[0] == "gemini"

    @patch("subprocess.run")
    def test_execution_with_zero_timeout(
        self, mock_run: MagicMock, tmp_path: Path,
    ) -> None:
        """Zero timeout results in a timeout error response."""
        mock_run.side_effect = Exception(
            "Command timed out after 0 seconds",
        )

        delegator = Delegator(config_dir=tmp_path)
        result = delegator.execute("gemini", "prompt", timeout=0)

        assert isinstance(result, ExecutionResult)
        assert result.success is False
        assert "timed out" in result.stderr.lower()


class TestQuotaTrackerEdgeCases:
    """Test edge cases for quota tracker."""

    def test_corrupted_usage_file(self, tmp_path: Path) -> None:
        """Corrupted usage data doesn't crash get_quota_status."""
        usage_file = tmp_path / "usage.json"
        usage_file.write_text(json.dumps({
            "requests": [{
                "timestamp": datetime.now().isoformat(),
                "tokens": -100,
                "success": True,
            }],
            "daily_tokens": -50,
            "last_reset": datetime.now().isoformat(),
        }, indent=2))

        tracker = GeminiQuotaTracker()
        tracker.usage_file = usage_file

        status, _warnings = tracker.get_quota_status()
        assert isinstance(status, str)

    def test_estimate_tokens_empty_input(self) -> None:
        """Empty input yields non-negative token estimate."""
        tracker = GeminiQuotaTracker()
        result = tracker.estimate_task_tokens([], prompt_length=0)

        assert isinstance(result, int)
        assert result >= 0


class TestUsageLoggerEdgeCases:
    """Test edge cases for usage logger."""

    def test_concurrent_access_recreates_corrupted_session(
        self, tmp_path: Path,
    ) -> None:
        """Corrupted session files are recreated safely."""
        session_file = tmp_path / "current_session.json"
        usage_log = tmp_path / "usage.jsonl"
        session_file.write_text("corrupted json content {invalid")

        logger = GeminiUsageLogger()
        logger.session_file = session_file
        logger.usage_log = usage_log

        entry = UsageEntry("test command", 1000, success=True)
        logger.log_usage(entry)

        assert session_file.exists()
        with open(session_file) as f:
            session_data = json.load(f)
            assert "session_id" in session_data

    @pytest.mark.parametrize(
        ("cmd", "tokens", "success"),
        [
            ("cmd1", 10, True),
            ("cmd2", 5, False),
            ("cmd3", 0, True),
        ],
        ids=["success", "failure", "zero-tokens"],
    )
    def test_log_usage_variants(
        self,
        tmp_path: Path,
        cmd: str,
        tokens: int,
        success: bool,
    ) -> None:
        """Various usage entries are logged without error."""
        logger = GeminiUsageLogger()
        logger.session_file = tmp_path / "current_session.json"
        logger.usage_log = tmp_path / "usage.jsonl"

        logger.log_usage(UsageEntry(cmd, tokens, success=success))

        assert logger.session_file.exists()
        assert logger.usage_log.exists()
        # Verify the logged entry
        lines = logger.usage_log.read_text().strip().splitlines()
        last_entry = json.loads(lines[-1])
        assert last_entry["command"] == cmd
        assert last_entry["success"] is success


class TestNetworkErrorEdgeCases:
    """Test network and rate-limit error handling."""

    @pytest.mark.parametrize(
        ("error_msg", "expected_keywords"),
        [
            (
                "HTTP/1.1 429 Too Many Requests\nRetry-After: 60",
                ["429", "too many"],
            ),
            (
                "HTTP/1.1 429 Too Many Requests",
                ["429", "too many"],
            ),
            (
                "Rate limit exceeded. Try again later.",
                ["rate limit"],
            ),
        ],
        ids=["429-with-retry", "429-simple", "rate-limit-text"],
    )
    @patch("subprocess.run")
    def test_rate_limit_errors_are_reported(
        self,
        mock_run: MagicMock,
        tmp_path: Path,
        error_msg: str,
        expected_keywords: list[str],
    ) -> None:
        """Rate-limit errors are captured in result stderr."""
        mock_run.side_effect = Exception(error_msg)
        delegator = Delegator(config_dir=tmp_path)

        result = delegator.execute("gemini", "test prompt")

        assert result.success is False
        assert any(
            kw in result.stderr.lower() for kw in expected_keywords
        )
        # Verify subprocess.run was called
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_missing_api_key_detected(
        self, mock_run: MagicMock, tmp_path: Path,
    ) -> None:
        """Missing API key is detected during verification."""
        delegator = Delegator(config_dir=tmp_path)

        with patch.dict(os.environ, {}, clear=False):
            if "GEMINI_API_KEY" in os.environ:
                del os.environ["GEMINI_API_KEY"]

            is_available, _issues = delegator.verify_service("gemini")
            assert is_available is False

    @patch("subprocess.run")
    def test_empty_api_key_treated_as_missing(
        self, mock_run: MagicMock, tmp_path: Path,
    ) -> None:
        """Empty API key string is treated as missing."""
        delegator = Delegator(config_dir=tmp_path)

        with patch.dict(os.environ, {"GEMINI_API_KEY": ""}, clear=False):
            is_available, issues = delegator.verify_service("gemini")

        # Empty API key should not pass authentication
        assert is_available is False or len(issues) > 0


class TestConcurrentDelegation:
    """Test concurrent filesystem access."""

    @patch("subprocess.run")
    def test_concurrent_execute_calls(
        self, mock_run: MagicMock, tmp_path: Path,
    ) -> None:
        """Concurrent execute calls complete without corruption."""
        mock_run.return_value = MagicMock(
            returncode=0, stdout="ok", stderr="",
        )

        delegator = Delegator(config_dir=tmp_path)
        results_queue: queue.Queue[ExecutionResult] = queue.Queue()
        worker_count = 3

        def delegate_worker(worker_id: int) -> None:
            result = delegator.execute(
                "gemini", f"Task {worker_id}", files=[],
            )
            results_queue.put(result)

        threads = [
            threading.Thread(target=delegate_worker, args=(i,))
            for i in range(worker_count)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        collected = []
        while not results_queue.empty():
            collected.append(results_queue.get())

        assert len(collected) == worker_count
        for result in collected:
            assert isinstance(result, ExecutionResult)
        # Each worker triggered a subprocess call
        assert mock_run.call_count == worker_count
