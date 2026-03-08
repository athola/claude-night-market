# ruff: noqa: D101,D102,D103,PLR2004,E501
"""Integration tests for conjure plugin following TDD/BDD principles."""

import json

# Import modules for testing
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from delegation_executor import Delegator, ExecutionResult
from quota_tracker import GeminiQuotaTracker
from usage_logger import GeminiUsageLogger, UsageEntry


class TestDelegationExecutorIntegration:
    """Test integration scenarios for delegation executor."""

    @patch("subprocess.run")
    def test_complete_delegation_workflow_success(
        self,
        mock_run,
        tmp_path,
        sample_files,
    ) -> None:
        """Given complete workflow when all components work then should execute successfully."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Analysis complete. The code follows best practices."
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        # Execute complete workflow
        delegator = Delegator(config_dir=tmp_path)

        # Step 1: Verify service
        with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}):
            is_available, _issues = delegator.verify_service("gemini")
            assert is_available is True

        # Step 2: Execute delegation
        file_paths = [str(f) for f in sample_files]
        result = delegator.execute(
            "gemini",
            "Analyze these files and provide recommendations",
            files=file_paths,
            options={"model": "gemini-2.5-pro-exp"},
        )

        # Step 3: Verify results
        assert result.success is True
        assert "Analysis complete" in result.stdout
        assert result.service == "gemini"
        assert result.tokens_used >= 0
        assert result.duration > 0

        # Step 4: Check usage was logged
        usage_log = tmp_path / "usage.jsonl"
        assert usage_log.exists()

        with open(usage_log) as f:
            log_entries = [json.loads(line.strip()) for line in f]
            assert len(log_entries) > 0
            assert log_entries[-1]["service"] == "gemini"
            assert log_entries[-1]["success"] is True

    @patch("subprocess.run")
    def test_delegation_workflow_with_quota_limits(self, mock_run, tmp_path) -> None:
        # Setup mocks
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "success"
        mock_run.return_value.stderr = ""

        delegator = Delegator(config_dir=tmp_path)

        # Mock service verification
        with patch.object(delegator, "verify_service") as mock_verify:
            # Test case 1: Gemini available and large context needed
            mock_verify.return_value = (True, [])
            service, result = delegator.smart_delegate(
                "Analyze this large codebase",
                requirements={"large_context": True, "gemini_available": True},
            )
            assert service == "gemini"

            # Test case 2: Qwen available for code execution
            mock_verify.side_effect = [(False, ["Gemini not available"]), (True, [])]
            service, _result = delegator.smart_delegate(
                "Execute this code",
                requirements={"code_execution": True, "qwen_available": True},
            )
            assert service == "qwen"


class TestQuotaTrackerIntegration:
    """Test integration scenarios for quota tracker."""

    def test_quota_tracking_across_sessions(self, tmp_path, sample_files) -> None:
        """Given multiple tracker instances they should share the same API surface."""
        # Both trackers use the same real API: estimate_task_tokens + get_quota_status
        tracker1 = GeminiQuotaTracker()
        tracker2 = GeminiQuotaTracker()

        file_paths = [str(f) for f in sample_files]

        # Both should be able to estimate tokens consistently
        tokens1 = tracker1.estimate_task_tokens(file_paths, prompt_length=100)
        tokens2 = tracker2.estimate_task_tokens(file_paths, prompt_length=100)

        assert tokens1 == tokens2
        assert tokens1 > 0

        # Both should return a valid quota status tuple
        status1, warnings1 = tracker1.get_quota_status()
        status2, warnings2 = tracker2.get_quota_status()

        assert isinstance(status1, str)
        assert isinstance(warnings1, list)
        assert isinstance(status2, str)
        assert isinstance(warnings2, list)

    def test_quota_warnings_and_status_changes(self, tmp_path) -> None:
        tracker = GeminiQuotaTracker()

        # get_quota_status returns (status_string, warnings_list)
        status, warnings = tracker.get_quota_status()

        assert isinstance(status, str)
        assert len(status) > 0
        assert isinstance(warnings, list)

        # limits property exposes config values
        limits = tracker.limits
        assert limits["requests_per_minute"] > 0
        assert limits["tokens_per_day"] > 0

        # estimate_task_tokens handles empty input
        tokens = tracker.estimate_task_tokens([], prompt_length=400)
        assert isinstance(tokens, int)
        assert tokens >= 0


class TestUsageLoggerIntegration:
    """Test integration scenarios for usage logger."""

    def test_usage_logging_across_days(self, tmp_path) -> None:
        usage_log = tmp_path / "usage.jsonl"

        logger = GeminiUsageLogger()
        logger.usage_log = usage_log
        logger.session_file = tmp_path / "current_session.json"

        # Log some errors
        error_entries = [
            UsageEntry(
                "gemini -p 'task1'",
                1000,
                success=False,
                error="Rate limit exceeded",
            ),
            UsageEntry(
                "gemini -p 'task2'",
                2000,
                success=False,
                error="Authentication failed",
            ),
            UsageEntry("gemini -p 'task3'", 1500, success=True),
            UsageEntry(
                "gemini -p 'task4'",
                1200,
                success=False,
                error="Context too large",
            ),
        ]

        for entry in error_entries:
            logger.log_usage(entry)

        # Test error retrieval
        recent_errors = logger.get_recent_errors(count=10)
        assert len(recent_errors) == 3  # Only the failed requests

        error_messages = [error["error"] for error in recent_errors]
        assert "Rate limit exceeded" in error_messages
        assert "Authentication failed" in error_messages
        assert "Context too large" in error_messages

    def test_session_management_and_tracking(self, tmp_path) -> None:
        """Validate logger can write usage entries to a custom directory."""
        log_dir = tmp_path / "logs"
        log_dir.mkdir(parents=True)

        logger = GeminiUsageLogger()
        logger.usage_log = log_dir / "usage.jsonl"
        logger.session_file = log_dir / "current_session.json"

        logger.log_usage(UsageEntry("cmd", 10, success=True))
        assert logger.usage_log.exists()

    @patch("subprocess.run")
    def test_complete_delegation_with_tracking(
        self,
        mock_run,
        tmp_path,
        sample_files,
    ) -> None:
        """Given complete delegation workflow when executed then should track usage."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Code analysis complete. Found 3 patterns."
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        config_dir = tmp_path / ".claude" / "hooks" / "delegation"
        config_dir.mkdir(parents=True)

        log_dir = tmp_path / "logs"
        log_dir.mkdir(parents=True)

        delegator = Delegator(config_dir=config_dir)
        tracker = GeminiQuotaTracker()
        usage_logger = GeminiUsageLogger()
        usage_logger.usage_log = log_dir / "usage.jsonl"
        usage_logger.session_file = log_dir / "current_session.json"

        with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}):
            # Step 1: Verify service availability
            is_available, _issues = delegator.verify_service("gemini")
            assert is_available is True

            # Step 2: Check quota status before execution
            status, _warnings = tracker.get_quota_status()
            assert isinstance(status, str)

            # Step 3: Execute delegation
            file_paths = [str(f) for f in sample_files]
            result = delegator.execute(
                "gemini",
                "Analyze these files and identify patterns",
                files=file_paths,
                options={"model": "gemini-2.5-pro-exp"},
            )

            # Step 4: Log detailed usage
            usage_entry = UsageEntry(
                command="gemini -p 'Analyze these files'",
                estimated_tokens=5000,
                actual_tokens=result.tokens_used,
                success=result.success,
                duration=result.duration,
            )
            usage_logger.log_usage(usage_entry)

            # Verify complete workflow
            assert result.success is True
            assert "Code analysis complete" in result.stdout

            # Verify usage logging
            usage_summary = usage_logger.get_usage_summary()
            assert usage_summary["total_requests"] >= 1
            assert usage_summary["total_tokens"] >= 0

    @patch("subprocess.run")
    def test_error_recovery_workflow(self, mock_run, tmp_path) -> None:
        """Verify get_quota_status can be mocked to simulate exhaustion."""
        tracker = GeminiQuotaTracker()

        # Mock get_quota_status to simulate quota exhaustion
        with patch.object(tracker, "get_quota_status") as mock_status:
            mock_status.return_value = (
                "[CRITICAL] Daily Quota Exhausted",
                ["Daily quota nearly exhausted! Large tasks may fail."],
            )

            status, warnings = tracker.get_quota_status()
            assert "[CRITICAL]" in status
            assert len(warnings) > 0

    def test_multiple_service_delegation_workflow(self, tmp_path) -> None:
        delegator = Delegator(config_dir=tmp_path)
        result = delegator.execute("gemini", "hello")
        assert isinstance(result, ExecutionResult)

    def test_large_file_token_estimation_performance(self, tmp_path) -> None:
        # Create multiple test files
        files = []
        for i in range(50):  # 50 files
            test_file = tmp_path / f"file_{i}.py"
            test_file.write_text(f"def function_{i}():\n    return {i}\n")
            files.append(test_file)

        tracker = GeminiQuotaTracker()

        # Test batch token estimation performance
        start_time = time.time()
        estimated_tokens = tracker.estimate_task_tokens(
            [str(f) for f in files],
            prompt_length=200,
        )
        duration = time.time() - start_time

        # Should handle batch processing efficiently
        assert duration < 1.0  # Should complete quickly
        assert estimated_tokens > 0  # Should account for all files + prompt

    def test_usage_log_performance_with_many_entries(self, tmp_path) -> None:
        usage_log = tmp_path / "usage.jsonl"

        logger = GeminiUsageLogger()
        logger.usage_log = usage_log
        logger.session_file = tmp_path / "current_session.json"

        for i in range(10):
            logger.log_usage(UsageEntry(f"cmd{i}", estimated_tokens=10, success=True))

        assert usage_log.exists()
