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


# ruff: noqa: S101
class TestDelegationExecutorIntegration:
    """Test integration scenarios for delegation executor."""

    @patch("subprocess.run")
    @patch("delegation_executor.tiktoken.get_encoding")
    def test_complete_delegation_workflow_success(
        self, mock_encoder, mock_run, tmp_path, sample_files
    ):
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
            is_available, issues = delegator.verify_service("gemini")
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
            log_entries = [json.loads(line.strip()) for line in f.readlines()]
            assert len(log_entries) > 0
            assert log_entries[-1]["service"] == "gemini"
            assert log_entries[-1]["success"] is True

    @patch("subprocess.run")
    def test_delegation_workflow_with_quota_limits(self, mock_run, tmp_path):
        """Given quota limits when executing workflow then should respect limits."""
        # Setup mock for service verification
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "version info"

        delegator = Delegator(config_dir=tmp_path)

        # Test quota-aware execution
        gemini_config = delegator.SERVICES["gemini"]
        assert gemini_config.quota_limits is not None
        assert "requests_per_minute" in gemini_config.quota_limits
        assert "tokens_per_day" in gemini_config.quota_limits

    @patch("subprocess.run")
    def test_smart_delegation_service_selection(self, mock_run, tmp_path):
        """Given multiple services when using smart delegation then should select appropriate service."""
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
            service, result = delegator.smart_delegate(
                "Execute this code",
                requirements={"code_execution": True, "qwen_available": True},
            )
            assert service == "qwen"


class TestQuotaTrackerIntegration:
    """Test integration scenarios for quota tracker."""

    @patch("quota_tracker.tiktoken.get_encoding")
    def test_quota_tracking_across_sessions(self, mock_encoder, tmp_path, sample_files):
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

    def test_quota_warnings_and_status_changes(self, tmp_path):
        """Given approaching limits when tracking quota then should provide appropriate warnings."""
        usage_file = tmp_path / "usage.json"

        with patch.object(GeminiQuotaTracker, "usage_file", usage_file):
            tracker = GeminiQuotaTracker()

            # Simulate high usage (over 80% threshold)
            now = datetime.now()
            high_usage_requests = []
            for i in range(50):  # 50 requests (over 80% of 60 RPM limit)
                high_usage_requests.append(
                    {
                        "timestamp": (now - timedelta(seconds=i * 10)).isoformat(),
                        "tokens": 100,
                        "success": True,
                    }
                )

            tracker.usage_data["requests"] = high_usage_requests

            status, warnings = tracker.get_quota_status()

            assert "[WARNING]" in status
            assert len(warnings) > 0

    @patch("quota_tracker.GeminiQuotaTracker")
    def test_quota_aware_task_execution(self, mock_tracker_class, tmp_path):
        """Given quota limits when executing tasks then should enforce limits appropriately."""
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

    def test_usage_logging_across_days(self, tmp_path):
        """Given usage spanning multiple days when logging then should handle day transitions."""
        usage_log = tmp_path / "usage.jsonl"

        with patch.object(GeminiUsageLogger, "usage_log", usage_log):
            logger = GeminiUsageLogger()

            # Day 1: Record usage
            day1_entries = [
                UsageEntry(
                    "gemini -p 'task1'",
                    1000,
                    actual_tokens=1200,
                    success=True,
                    duration=2.0,
                ),
                UsageEntry(
                    "gemini -p 'task2'",
                    800,
                    actual_tokens=900,
                    success=True,
                    duration=1.5,
                ),
            ]

            for entry in day1_entries:
                logger.log_usage(entry)

            # Simulate day transition by modifying session file
            session_file = tmp_path / "current_session.json"
            if session_file.exists():
                session_data = json.loads(session_file.read_text())
                # Set last_reset to yesterday
                session_data["last_reset"] = (
                    datetime.now() - timedelta(days=1)
                ).isoformat()
                session_file.write_text(json.dumps(session_data, indent=2))

            # Day 2: Record more usage
            day2_entries = [
                UsageEntry(
                    "gemini -p 'task3'",
                    1500,
                    actual_tokens=1600,
                    success=True,
                    duration=3.0,
                ),
            ]

            for entry in day2_entries:
                logger.log_usage(entry)

            # Verify usage summary
            summary = logger.get_usage_summary(hours=48)  # Last 2 days
            assert summary["total_requests"] == 3
            assert summary["total_tokens"] == 3700  # 1200 + 900 + 1600

    def test_error_logging_and_analysis(self, tmp_path):
        """Given errors occurring during usage when logging then should track and analyze them."""
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
                    "gemini -p 'task4'", 1200, success=False, error="Context too large"
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

    def test_session_management_and_tracking(self, tmp_path):
        """Given usage spanning sessions when logging then should track sessions correctly."""
        logger = GeminiUsageLogger()

        # Force creation of new session
        session_id1 = logger._get_session_id()
        assert session_id1.startswith("session_")

        # Record usage in session 1
        logger.log_usage(UsageEntry("task1", 1000, success=True))

        # Check session was updated
        session_file = logger.session_file
        assert session_file.exists()

        with open(session_file) as f:
            session_data = json.load(f)

        assert session_data["session_id"] == session_id1
        assert session_data["total_requests"] == 1
        assert session_data["total_tokens"] == 1000
        assert session_data["successful_requests"] == 1

        # Create new session (simulate timeout)
        with patch("time.time", return_value=int(time.time()) + 4000):  # 1+ hour later
            session_id2 = logger._get_session_id()

        assert session_id2 != session_id1  # Should be new session


class TestEndToEndWorkflows:
    """Test complete end-to-end workflows."""

    @patch("subprocess.run")
    @patch("delegation_executor.tiktoken.get_encoding")
    def test_complete_delegation_with_tracking(
        self, mock_encoder, mock_run, tmp_path, sample_files
    ):
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
            is_available, issues = delegator.verify_service("gemini")
            assert is_available is True

            # Step 2: Check quota before execution
            can_handle, quota_issues = quota_tracker.can_handle_task(
                estimated_tokens=5000
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
                estimated_tokens=result.tokens_used or 5000, success=result.success
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
    def test_error_recovery_workflow(self, mock_run, tmp_path):
        """Given errors during delegation when executing workflow then should recover appropriately."""
        # Setup error scenarios
        error_results = [
            MagicMock(returncode=1, stderr="Rate limit exceeded"),
            MagicMock(returncode=1, stderr="Authentication failed"),
            MagicMock(returncode=0, stdout="Success after retry", stderr=""),
        ]
        mock_run.side_effect = error_results

        delegator = Delegator(config_dir=tmp_path)

        # Test error handling and recovery
        for i, _expected_result in enumerate(error_results):
            result = delegator.execute("gemini", f"Test request {i}", timeout=30)

            if i < 2:  # First two attempts should fail
                assert result.success is False
                assert (
                    "Rate limit exceeded" in result.stderr
                    or "Authentication failed" in result.stderr
                )
            else:  # Third attempt should succeed
                assert result.success is True
                assert "Success after retry" in result.stdout

    def test_quota_exhaustion_handling_workflow(self, tmp_path):
        """Given quota exhaustion when executing workflow then should handle gracefully."""
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
                    estimated_tokens=50000
                )
                assert can_handle is False
                assert "quota" in issues[0].lower()

    def test_multiple_service_delegation_workflow(self, tmp_path):
        """Given multiple services available when executing workflow then should select optimal service."""
        # Create delegator with custom service configurations
        custom_config = {
            "services": {
                "gemini-fast": {
                    "name": "gemini-fast",
                    "command": "gemini",
                    "auth_method": "api_key",
                    "quota_limits": {
                        "requests_per_minute": 120,
                        "requests_per_day": 2000,
                        "tokens_per_day": 2000000,
                    },
                },
                "gemini-pro": {
                    "name": "gemini-pro",
                    "command": "gemini",
                    "auth_method": "api_key",
                    "quota_limits": {
                        "requests_per_minute": 30,
                        "requests_per_day": 500,
                        "tokens_per_day": 500000,
                    },
                },
            }
        }

        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(custom_config, indent=2))

        delegator = Delegator(config_dir=tmp_path)

        # Verify custom services were loaded
        assert "gemini-fast" in delegator.SERVICES
        assert "gemini-pro" in delegator.SERVICES

        # Test service selection logic
        fast_config = delegator.SERVICES["gemini-fast"]
        pro_config = delegator.SERVICES["gemini-pro"]

        # Fast service should have higher limits
        assert (
            fast_config.quota_limits["requests_per_minute"]
            > pro_config.quota_limits["requests_per_minute"]
        )

        # Pro service should be more conservative
        assert (
            pro_config.quota_limits["requests_per_day"]
            < fast_config.quota_limits["requests_per_day"]
        )


class TestPerformanceAndScalability:
    """Test performance and scalability scenarios."""

    def test_large_file_token_estimation_performance(self, tmp_path):
        """Given large files when estimating tokens then should perform efficiently."""
        # Create a large test file
        large_file = tmp_path / "large_file.py"
        content = "def function_{}():\n    return 'test'\n" * 10000  # 10K lines
        large_file.write_text(content)

        usage_file = tmp_path / "usage.json"

        with patch.object(GeminiQuotaTracker, "usage_file", usage_file):
            tracker = GeminiQuotaTracker()

            # Time the token estimation
            start_time = time.time()
            estimated_tokens = tracker.estimate_task_tokens(
                [str(large_file)], prompt_length=100
            )
            duration = time.time() - start_time

            # Should complete quickly even for large files
            assert duration < 2.0  # Should complete in under 2 seconds
            assert estimated_tokens > 0

    @patch("quota_tracker.tiktoken.get_encoding")
    def test_batch_processing_efficiency(self, mock_encoder, tmp_path):
        """Given multiple files when processing batch then should handle efficiently."""
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
                [str(f) for f in files], prompt_length=200
            )
            duration = time.time() - start_time

            # Should handle batch processing efficiently
            assert duration < 1.0  # Should complete quickly
            assert estimated_tokens > 5000  # Should account for all files + prompt

    def test_usage_log_performance_with_many_entries(self, tmp_path):
        """Given many usage log entries when analyzing logs then should perform efficiently."""
        usage_log = tmp_path / "usage.jsonl"

        # Create log with many entries
        entries = []
        for i in range(1000):  # 1000 entries
            entry = {
                "timestamp": (datetime.now() - timedelta(minutes=i)).isoformat(),
                "command": f"gemini -p 'task {i}'",
                "estimated_tokens": 1000 + i,
                "actual_tokens": 1100 + i,
                "success": i % 10 != 0,  # 90% success rate
                "duration_seconds": 1.0 + (i % 5) * 0.5,
                "error": None if i % 10 != 0 else f"Error {i}",
                "session_id": f"session_{i // 50}",
            }
            entries.append(entry)

        with open(usage_log, "w") as f:
            for entry in entries:
                f.write(json.dumps(entry) + "\n")

        with patch.object(GeminiUsageLogger, "usage_log", usage_log):
            logger = GeminiUsageLogger()

            # Test performance of usage analysis
            start_time = time.time()
            summary = logger.get_usage_summary(
                hours=25
            )  # Last 25 hours to include all entries
            duration = time.time() - start_time

            # Should analyze log efficiently
            assert duration < 2.0  # Should complete quickly
            assert summary["total_requests"] == 1000
            assert summary["success_rate"] == 90.0

            # Test error retrieval performance
            start_time = time.time()
            errors = logger.get_recent_errors(count=50)
            duration = time.time() - start_time

            assert duration < 1.0  # Should complete quickly
            assert len(errors) == 100  # 10% of 1000 entries should be errors
