"""Integration tests for conjure plugin following TDD/BDD principles."""

import json

# Import modules for testing
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from delegation_executor import Delegator
from quota_tracker import GeminiQuotaTracker
from usage_logger import GeminiUsageLogger, UsageEntry


class TestDelegationExecutorIntegration:
    """Test integration scenarios for delegation executor."""

    @patch("subprocess.run")
    @patch("delegation_executor.tiktoken.get_encoding")
    def test_complete_delegation_workflow_success(
        self,
        mock_encoder,
        mock_run,
        tmp_path,
        sample_files,
    ) -> None:
        """Given complete workflow when all components work then should execute successfully."""
        # Setup mocks
        mock_encoder_instance = MagicMock()
        mock_encoder_instance.encode.return_value = list(range(1000))  # 1000 tokens
        mock_encoder.return_value = mock_encoder_instance

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

        # Step 2: Estimate tokens
        file_paths = [str(f) for f in sample_files]
        estimated_tokens = delegator.estimate_tokens(file_paths, "Analyze these files")
        assert estimated_tokens > 1000  # Should include file content

        # Step 3: Execute delegation
        result = delegator.execute(
            "gemini",
            "Analyze these files and provide recommendations",
            files=file_paths,
            options={"model": "gemini-2.5-pro-exp"},
        )

        # Step 4: Verify results
        assert result.success is True
        assert "Analysis complete" in result.stdout
        assert result.service == "gemini"
        assert result.tokens_used > 0
        assert result.duration > 0

        # Step 5: Check usage was logged
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

    @patch("quota_tracker.tiktoken.get_encoding")
    def test_quota_tracking_across_sessions(
        self, mock_encoder, tmp_path, sample_files
    ) -> None:
        """Given multiple sessions when tracking quota then should maintain accurate state."""
        # Setup mock encoder
        mock_encoder_instance = MagicMock()
        mock_encoder_instance.encode.return_value = list(range(500))
        mock_encoder.return_value = mock_encoder_instance

        usage_file = tmp_path / "usage.json"

        with patch.object(GeminiQuotaTracker, "usage_file", usage_file):
            # Session 1: Record usage
            tracker1 = GeminiQuotaTracker()
            tracker1.record_request(estimated_tokens=1000, success=True)
            tracker1.record_request(estimated_tokens=500, success=False)

            # Session 2: Continue with same tracker
            tracker2 = GeminiQuotaTracker()
            current_usage = tracker2.get_current_usage()

            assert current_usage["daily_tokens"] == 1000  # Only successful requests
            assert current_usage["requests_today"] == 2

    def test_quota_warnings_and_status_changes(self, tmp_path) -> None:
        mock_tracker = MagicMock()
        mock_tracker.estimate_task_tokens.return_value = 50000
        mock_tracker.can_handle_task.return_value = (True, [])
        mock_tracker_class.return_value = mock_tracker

        # Test quota-aware execution
        with patch.object(GeminiQuotaTracker, "usage_file", tmp_path / "usage.json"):
            tracker = GeminiQuotaTracker()

            # Test task can be handled
            can_handle, issues = tracker.can_handle_task(estimated_tokens=50000)
            assert can_handle is True
            assert len(issues) == 0

            # Test quota exceeded scenario
            mock_tracker.can_handle_task.return_value = (False, ["Rate limit exceeded"])
            can_handle, issues = tracker.can_handle_task(estimated_tokens=50000)
            assert can_handle is False
            assert len(issues) > 0


class TestUsageLoggerIntegration:
    """Test integration scenarios for usage logger."""

    def test_usage_logging_across_days(self, tmp_path) -> None:
        usage_log = tmp_path / "usage.jsonl"

        with patch.object(GeminiUsageLogger, "usage_log", usage_log):
            logger = GeminiUsageLogger()

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

    @patch("subprocess.run")
    @patch("delegation_executor.tiktoken.get_encoding")
    def test_complete_delegation_with_tracking(
        self,
        mock_encoder,
        mock_run,
        tmp_path,
        sample_files,
    ) -> None:
        """Given complete delegation workflow when executed then should track usage and quota."""
        # Setup mocks
        mock_encoder_instance = MagicMock()
        mock_encoder_instance.encode.return_value = list(range(2000))
        mock_encoder.return_value = mock_encoder_instance

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Code analysis complete. Found 3 patterns."
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        # Create shared configuration directory
        config_dir = tmp_path / ".claude" / "hooks" / "delegation"
        config_dir.mkdir(parents=True)

        # Initialize components with shared config
        delegator = Delegator(config_dir=config_dir)
        quota_tracker = GeminiQuotaTracker()
        usage_logger = GeminiUsageLogger()

        with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}):
            # Step 1: Verify service availability
            is_available, _issues = delegator.verify_service("gemini")
            assert is_available is True

            # Step 2: Check quota before execution
            can_handle, _quota_issues = quota_tracker.can_handle_task(
                estimated_tokens=5000,
            )
            assert can_handle is True

            # Step 3: Execute delegation
            file_paths = [str(f) for f in sample_files]
            result = delegator.execute(
                "gemini",
                "Analyze these files and identify patterns",
                files=file_paths,
                options={"model": "gemini-2.5-pro-exp"},
            )

            # Step 4: Record usage in quota tracker
            quota_tracker.record_request(
                estimated_tokens=result.tokens_used or 5000,
                success=result.success,
            )

            # Step 5: Log detailed usage
            usage_entry = UsageEntry(
                command=f"gemini -p 'Analyze these files' @{' @'.join(file_paths)}",
                estimated_tokens=5000,
                actual_tokens=result.tokens_used,
                success=result.success,
                duration=result.duration,
            )
            usage_logger.log_usage(usage_entry)

            # Verify complete workflow
            assert result.success is True
            assert "Code analysis complete" in result.stdout

            # Verify quota tracking
            current_quota = quota_tracker.get_current_usage()
            assert current_quota["requests_today"] >= 1
            assert current_quota["daily_tokens"] >= 5000

            # Verify usage logging
            usage_summary = usage_logger.get_usage_summary()
            assert usage_summary["total_requests"] >= 1
            assert usage_summary["total_tokens"] >= 5000

    @patch("subprocess.run")
    def test_error_recovery_workflow(self, mock_run, tmp_path) -> None:
        quota_tracker = GeminiQuotaTracker()

        # Simulate quota exhaustion
        with patch.object(quota_tracker, "get_quota_status") as mock_status:
            mock_status.return_value = (
                "[CRITICAL] Daily Quota Exhausted",
                ["Daily quota nearly exhausted! Large tasks may fail."],
            )

            status, warnings = quota_tracker.get_quota_status()
            assert "[CRITICAL]" in status
            assert len(warnings) > 0

            # Test that workflow would be blocked
            with patch.object(quota_tracker, "can_handle_task") as mock_can_handle:
                mock_can_handle.return_value = (
                    False,
                    ["Daily token quota would be exceeded - wait for reset"],
                )

                can_handle, issues = quota_tracker.can_handle_task(
                    estimated_tokens=50000,
                )
                assert can_handle is False
                assert "quota" in issues[0].lower()

    def test_multiple_service_delegation_workflow(self, tmp_path) -> None:

    def test_large_file_token_estimation_performance(self, tmp_path) -> None:
        # Setup mock
        mock_encoder_instance = MagicMock()
        mock_encoder_instance.encode.return_value = list(range(100))  # 100 tokens each
        mock_encoder.return_value = mock_encoder_instance

        # Create multiple test files
        files = []
        for i in range(50):  # 50 files
            test_file = tmp_path / f"file_{i}.py"
            test_file.write_text(f"def function_{i}():\n    return {i}\n")
            files.append(test_file)

        usage_file = tmp_path / "usage.json"

        with patch.object(GeminiQuotaTracker, "usage_file", usage_file):
            tracker = GeminiQuotaTracker()

            # Test batch token estimation
            start_time = time.time()
            estimated_tokens = tracker.estimate_task_tokens(
                [str(f) for f in files],
                prompt_length=200,
            )
            duration = time.time() - start_time

            # Should handle batch processing efficiently
            assert duration < 1.0  # Should complete quickly
            assert estimated_tokens > 5000  # Should account for all files + prompt

    def test_usage_log_performance_with_many_entries(self, tmp_path) -> None:
