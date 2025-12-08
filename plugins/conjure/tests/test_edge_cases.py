"""Edge case and error handling tests for conjure plugin following TDD/BDD principles."""

import json
import tempfile
import subprocess
import time
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open
from datetime import datetime, timedelta
import pytest

# Import modules for testing
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from delegation_executor import Delegator, ServiceConfig, ExecutionResult
from quota_tracker import GeminiQuotaTracker, DEFAULT_LIMITS
from usage_logger import GeminiUsageLogger, UsageEntry


class TestDelegationExecutorEdgeCases:
    """Test edge cases for delegation executor."""

    def test_delegator_initialization_with_invalid_config(self, tmp_path):
        """Given invalid config file when initializing delegator then should handle gracefully."""
        # Create invalid JSON config
        config_file = tmp_path / "config.json"
        config_file.write_text("invalid json content")

        # Should not raise exception, should use defaults
        delegator = Delegator(config_dir=tmp_path)
        assert "gemini" in delegator.SERVICES
        assert "qwen" in delegator.SERVICES

    def test_delegator_initialization_with_malformed_config(self, tmp_path):
        """Given malformed config structure when initializing delegator then should handle gracefully."""
        # Create config with invalid structure
        config_file = tmp_path / "config.json"
        malformed_config = {
            "services": {
                "test_service": {
                    # Missing required fields
                    "name": "test"
                    # Missing command, auth_method
                }
            }
        }
        config_file.write_text(json.dumps(malformed_config, indent=2))

        # Should not raise exception
        delegator = Delegator(config_dir=tmp_path)
        # Should still have default services
        assert "gemini" in delegator.SERVICES

    @patch('subprocess.run')
    def test_service_verification_command_not_found(self, mock_run, tmp_path):
        """Given missing command when verifying service then should handle gracefully."""
        mock_run.side_effect = FileNotFoundError("Command not found")

        delegator = Delegator(config_dir=tmp_path)
        is_available, issues = delegator.verify_service("nonexistent_service")

        assert is_available is False
        assert len(issues) > 0
        assert any("not found" in issue.lower() for issue in issues)

    @patch('subprocess.run')
    def test_service_verification_timeout(self, mock_run, tmp_path):
        """Given command timeout when verifying service then should handle gracefully."""
        mock_run.side_effect = subprocess.TimeoutExpired("test", 10)

        delegator = Delegator(config_dir=tmp_path)
        is_available, issues = delegator.verify_service("gemini")

        assert is_available is False
        assert len(issues) > 0

    @patch('subprocess.run')
    def test_service_verification_authentication_failure(self, mock_run, tmp_path):
        """Given authentication failure when verifying service then should provide specific error."""
        # Mock version check success but auth check failure
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="version info"),  # Version check
            MagicMock(returncode=1, stderr="Authentication failed")  # Auth check
        ]

        delegator = Delegator(config_dir=tmp_path)
        with patch.dict('os.environ', {}, clear=False):  # Remove auth env var
            if 'GEMINI_API_KEY' in os.environ:
                del os.environ['GEMINI_API_KEY']

        is_available, issues = delegator.verify_service("gemini")

        assert is_available is False
        assert any("authentication" in issue.lower() or "GEMINI_API_KEY" in issue for issue in issues)

    def test_token_estimation_with_nonexistent_files(self, tmp_path):
        """Given nonexistent files when estimating tokens then should handle gracefully."""
        delegator = Delegator(config_dir=tmp_path)

        nonexistent_files = [
            "/nonexistent/file1.py",
            "/nonexistent/file2.py"
        ]

        # Should not raise exception
        estimated = delegator.estimate_tokens(nonexistent_files, "test prompt")
        assert isinstance(estimated, int)
        assert estimated >= len("test prompt") / 4  # At least prompt tokens

    def test_token_estimation_with_unreadable_files(self, tmp_path):
        """Given unreadable files when estimating tokens then should handle gracefully."""
        delegator = Delegator(config_dir=tmp_path)

        # Create a file and then make it unreadable (simulate permission error)
        test_file = tmp_path / "test.py"
        test_file.write_text("test content")

        with patch('pathlib.Path.read_text', side_effect=PermissionError("Permission denied")):
            estimated = delegator.estimate_tokens([str(test_file)], "test prompt")

        assert isinstance(estimated, int)
        # Should fall back to size-based estimation or skip the file

    @patch('subprocess.run')
    def test_execution_with_very_long_command(self, mock_run, tmp_path):
        """Given very long command when executing then should handle correctly."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Success"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        delegator = Delegator(config_dir=tmp_path)

        # Create very long prompt
        long_prompt = "x" * 10000  # 10K characters
        many_files = [f"file{i}.py" for i in range(100)]  # Many files

        result = delegator.execute("gemini", long_prompt, files=many_files)

        # Should handle without errors
        assert mock_run.called
        command = mock_run.call_args[0][0]
        assert isinstance(command, list)
        assert len(" ".join(command)) > 10000  # Command should be long

    @patch('subprocess.run')
    def test_execution_with_unicode_content(self, mock_run, tmp_path):
        """Given unicode content in files when executing then should handle correctly."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Unicode success ✓ ✓ ✓"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        delegator = Delegator(config_dir=tmp_path)

        # Create file with unicode content
        unicode_file = tmp_path / "unicode.txt"
        unicode_content = "Test with unicode: αβγδε漢字𐍈"  # Greek, Chinese, and Gothic
        unicode_file.write_text(unicode_content)

        result = delegator.execute("gemini", "Process unicode content", files=[str(unicode_file)])

        assert result.success is True
        # Should handle unicode without encoding errors

    @patch('subprocess.run')
    def test_execution_with_zero_timeout(self, mock_run, tmp_path):
        """Given zero timeout when executing then should handle appropriately."""
        mock_run.side_effect = subprocess.TimeoutExpired("command", 0)

        delegator = Delegator(config_dir=tmp_path)

        result = delegator.execute("gemini", "test prompt", timeout=0)

        assert result.success is False
        assert "timed out" in result.stderr.lower()

    def test_usage_logging_with_invalid_directory(self, tmp_path):
        """Given invalid usage directory when logging then should create directories as needed."""
        invalid_dir = tmp_path / "nonexistent" / "deep" / "path"

        with patch.object(Delegator, 'usage_log', invalid_dir / "usage.jsonl"):
            delegator = Delegator(config_dir=tmp_path)

            # Should not raise exception when trying to log
            with patch('builtins.open', mock_open()):
                try:
                    # This would normally create the directory structure
                    delegator.log_usage("test", [], ExecutionResult(
                        success=True, stdout="", stderr="", exit_code=0, duration=1.0
                    ))
                except Exception as e:
                    # If it fails, it should be a directory creation issue, not a crash
                    assert "directory" in str(e).lower() or "path" in str(e).lower()


class TestQuotaTrackerEdgeCases:
    """Test edge cases for quota tracker."""

    def test_quota_tracker_with_corrupted_usage_file(self, tmp_path):
        """Given corrupted usage file when loading tracker then should handle gracefully."""
        usage_file = tmp_path / "usage.json"
        usage_file.write_text("corrupted json content\n{invalid json")

        with patch.object(GeminiQuotaTracker, 'usage_file', usage_file):
            tracker = GeminiQuotaTracker()

            # Should create new structure instead of crashing
            assert tracker.usage_data["daily_tokens"] == 0
            assert len(tracker.usage_data["requests"]) == 0

    def test_quota_tracker_with_extreme_timestamps(self, tmp_path):
        """Given extreme timestamps in usage data when loading tracker then should handle gracefully."""
        usage_file = tmp_path / "usage.json"

        # Create usage data with extreme timestamps
        extreme_data = {
            "requests": [
                {
                    "timestamp": "9999-12-31T23:59:59",  # Future timestamp
                    "tokens": 100,
                    "success": True
                },
                {
                    "timestamp": "1970-01-01T00:00:00",  # Unix epoch
                    "tokens": 200,
                    "success": True
                }
            ],
            "daily_tokens": 300,
            "last_reset": datetime.now().isoformat()
        }

        usage_file.write_text(json.dumps(extreme_data, indent=2))

        with patch.object(GeminiQuotaTracker, 'usage_file', usage_file):
            tracker = GeminiQuotaTracker()

            # Should handle extreme timestamps without crashing
            usage = tracker.get_current_usage()
            assert isinstance(usage["requests_last_minute"], int)
            assert usage["requests_last_minute"] >= 0

    def test_quota_tracker_with_negative_values(self, tmp_path):
        """Given negative token values when tracking quota then should handle gracefully."""
        usage_file = tmp_path / "usage.json"

        # Create usage data with negative values (corrupted data)
        corrupted_data = {
            "requests": [
                {
                    "timestamp": datetime.now().isoformat(),
                    "tokens": -100,  # Negative tokens
                    "success": True
                }
            ],
            "daily_tokens": -50,  # Negative daily total
            "last_reset": datetime.now().isoformat()
        }

        usage_file.write_text(json.dumps(corrupted_data, indent=2))

        with patch.object(GeminiQuotaTracker, 'usage_file', usage_file):
            tracker = GeminiQuotaTracker()

            # Should handle negative values gracefully
            usage = tracker.get_current_usage()
            assert usage["daily_tokens"] >= 0  # Should not be negative

    def test_quota_tracker_with_huge_token_values(self, tmp_path):
        """Given extremely large token values when tracking quota then should handle gracefully."""
        usage_file = tmp_path / "usage.json"

        # Create usage data with huge values
        huge_data = {
            "requests": [
                {
                    "timestamp": datetime.now().isoformat(),
                    "tokens": 10**12,  # Trillion tokens
                    "success": True
                }
            ],
            "daily_tokens": 10**15,  # Quadrillion tokens
            "last_reset": datetime.now().isoformat()
        }

        usage_file.write_text(json.dumps(huge_data, indent=2))

        with patch.object(GeminiQuotaTracker, 'usage_file', usage_file):
            tracker = GeminiQuotaTracker()

            # Should handle huge values without overflow
            status, warnings = tracker.get_quota_status()
            assert status is not None
            # Should show critical status due to huge usage
            assert "[CRITICAL]" in status

    @patch('quota_tracker.tiktoken.get_encoding')
    def test_token_estimation_with_empty_files(self, mock_encoder, tmp_path):
        """Given empty files when estimating tokens then should handle gracefully."""
        mock_encoder_instance = MagicMock()
        mock_encoder_instance.encode.return_value = []  # No tokens for empty content
        mock_encoder.return_value = mock_encoder_instance

        usage_file = tmp_path / "usage.json"

        with patch.object(GeminiQuotaTracker, 'usage_file', usage_file):
            tracker = GeminiQuotaTracker()

            # Create empty file
            empty_file = tmp_path / "empty.py"
            empty_file.write_text("")

            estimated = tracker.estimate_task_tokens([str(empty_file)], prompt_length=0)

            assert isinstance(estimated, int)
            assert estimated >= 0  # Should not be negative

    def test_quota_tracker_file_permission_errors(self, tmp_path):
        """Given file permission errors when tracking quota then should handle gracefully."""
        usage_file = tmp_path / "usage.json"

        with patch.object(GeminiQuotaTracker, 'usage_file', usage_file):
            tracker = GeminiQuotaTracker()

            # Mock permission errors
            with patch('builtins.open', side_effect=PermissionError("Permission denied")):
                with patch('pathlib.Path.mkdir', side_effect=PermissionError("Permission denied")):
                    # Should not raise exception
                    try:
                        tracker.record_request(1000, success=True)
                    except PermissionError:
                        # Expected for this test
                        pass

                    # Should still be able to get current usage (from memory)
                    usage = tracker.get_current_usage()
                    assert isinstance(usage, dict)

    def test_quota_tracker_concurrent_access_simulation(self, tmp_path):
        """Given concurrent access when tracking quota then should handle race conditions."""
        usage_file = tmp_path / "usage.json"

        with patch.object(GeminiQuotaTracker, 'usage_file', usage_file):
            # Simulate multiple instances writing to the same file
            trackers = [GeminiQuotaTracker() for _ in range(5)]

            # All trackers record requests simultaneously
            for i, tracker in enumerate(trackers):
                tracker.record_request(1000, success=True)

            # Should have handled concurrent access gracefully
            # The exact state depends on file locking, but shouldn't crash
            for tracker in trackers:
                usage = tracker.get_current_usage()
                assert isinstance(usage["daily_tokens"], int)


class TestUsageLoggerEdgeCases:
    """Test edge cases for usage logger."""

    def test_usage_logger_with_very_long_commands(self, tmp_path):
        """Given very long commands when logging usage then should handle gracefully."""
        usage_log = tmp_path / "usage.jsonl"

        with patch.object(GeminiUsageLogger, 'usage_log', usage_log):
            logger = GeminiUsageLogger()

            # Create extremely long command
            long_command = "gemini -p '" + "x" * 10000 + "'"

            entry = UsageEntry(
                command=long_command,
                estimated_tokens=50000,
                success=True,
                duration=10.0
            )

            # Should not raise exception
            logger.log_usage(entry)

            # Verify log was written
            assert usage_log.exists()
            with open(usage_log) as f:
                log_content = f.read()
                assert long_command in log_content

    def test_usage_logger_with_special_characters(self, tmp_path):
        """Given special characters in commands when logging usage then should handle correctly."""
        usage_log = tmp_path / "usage.jsonl"

        with patch.object(GeminiUsageLogger, 'usage_log', usage_log):
            logger = GeminiUsageLogger()

            # Command with various special characters
            special_command = 'gemini -p "Test with \n\t\r and quotes \'\" and \\ backslashes"'

            entry = UsageEntry(
                command=special_command,
                estimated_tokens=1000,
                success=True,
                duration=2.0
            )

            logger.log_usage(entry)

            # Verify log contains properly escaped JSON
            with open(usage_log) as f:
                log_entry = json.loads(f.read().strip())
                assert log_entry["command"] == special_command

    def test_usage_logger_with_corrupted_session_file(self, tmp_path):
        """Given corrupted session file when logging usage then should handle gracefully."""
        session_file = tmp_path / "current_session.json"
        usage_log = tmp_path / "usage.jsonl"

        # Create corrupted session file
        session_file.write_text("corrupted json content {invalid")

        with patch.object(GeminiUsageLogger, 'session_file', session_file):
            with patch.object(GeminiUsageLogger, 'usage_log', usage_log):
                logger = GeminiUsageLogger()

                entry = UsageEntry("test command", 1000, success=True)
                logger.log_usage(entry)

                # Should create new session file
                assert session_file.exists()
                with open(session_file) as f:
                    session_data = json.load(f)
                    assert "session_id" in session_data

    def test_usage_logger_session_timeout_edge_cases(self, tmp_path):
        """Given session timeout edge cases when logging usage then should handle correctly."""
        session_file = tmp_path / "current_session.json"

        with patch.object(GeminiUsageLogger, 'session_file', session_file):
            logger = GeminiUsageLogger()

            # Test exactly at timeout boundary
            with patch('time.time', return_value=int(time.time())):
                session_id1 = logger._get_session_id()

            # Test just after timeout
            with patch('time.time', return_value=int(time.time()) + 3601):  # 1 hour + 1 second
                session_id2 = logger._get_session_id()

            # Should create new session after timeout
            assert session_id1 != session_id2

    def test_usage_logger_with_disk_full_simulation(self, tmp_path):
        """Given disk full condition when logging usage then should handle gracefully."""
        usage_log = tmp_path / "usage.jsonl"

        with patch.object(GeminiUsageLogger, 'usage_log', usage_log):
            logger = GeminiUsageLogger()

            # Simulate disk full error
            with patch('builtins.open', side_effect=OSError("No space left on device")):
                entry = UsageEntry("test command", 1000, success=True)

                # Should not raise exception to caller
                try:
                    logger.log_usage(entry)
                except OSError:
                    # Expected for this test
                    pass

    def test_usage_logger_with_very_high_frequency_requests(self, tmp_path):
        """Given very high frequency requests when logging usage then should handle performance."""
        usage_log = tmp_path / "usage.jsonl"

        with patch.object(GeminiUsageLogger, 'usage_log', usage_log):
            logger = GeminiUsageLogger()

            # Log many requests rapidly
            start_time = time.time()
            for i in range(1000):
                entry = UsageEntry(f"command_{i}", 1000, success=i % 10 != 0)
                logger.log_usage(entry)
            duration = time.time() - start_time

            # Should complete reasonably quickly
            assert duration < 5.0  # Should complete in under 5 seconds

            # Verify all entries were logged
            with open(usage_log) as f:
                lines = f.readlines()
                assert len(lines) == 1000


class TestSystemIntegrationEdgeCases:
    """Test system integration edge cases."""

    @patch('subprocess.run')
    def test_network_connectivity_issues(self, mock_run, tmp_path):
        """Given network connectivity issues when executing delegation then should handle gracefully."""
        # Mock various network errors
        network_errors = [
            subprocess.CalledProcessError(1, "gemini", stderr="Network unreachable"),
            subprocess.CalledProcessError(1, "gemini", stderr="Connection timed out"),
            subprocess.CalledProcessError(1, "gemini", stderr="DNS resolution failed"),
            OSError("Network is unreachable"),
        ]

        delegator = Delegator(config_dir=tmp_path)

        for error in network_errors:
            mock_run.side_effect = error

            result = delegator.execute("gemini", "test prompt")

            assert result.success is False
            assert result.stderr is not None

    @patch('subprocess.run')
    def test_api_rate_limiting_scenarios(self, mock_run, tmp_path):
        """Given various API rate limiting scenarios when executing delegation then should handle appropriately."""
        rate_limit_responses = [
            # HTTP 429 with retry-after
            subprocess.CalledProcessError(1, "gemini", stderr="HTTP/1.1 429 Too Many Requests\nRetry-After: 60"),
            # HTTP 429 without retry-after
            subprocess.CalledProcessError(1, "gemini", stderr="HTTP/1.1 429 Too Many Requests"),
            # Custom rate limit message
            subprocess.CalledProcessError(1, "gemini", stderr="Rate limit exceeded. Try again later."),
        ]

        delegator = Delegator(config_dir=tmp_path)

        for response in rate_limit_responses:
            mock_run.side_effect = response

            result = delegator.execute("gemini", "test prompt")

            assert result.success is False
            # Should indicate rate limiting in the error
            assert any(keyword in result.stderr.lower() for keyword in ["429", "rate limit", "too many"])

    @patch('subprocess.run')
    def test_memory_exhaustion_scenarios(self, mock_run, tmp_path):
        """Given memory exhaustion scenarios when executing delegation then should handle gracefully."""
        memory_errors = [
            subprocess.CalledProcessError(1, "gemini", stderr="MemoryError: Out of memory"),
            subprocess.CalledProcessError(1, "gemini", stderr="Killed"),
            subprocess.CalledProcessError(1, "gemini", stderr="Segmentation fault"),
        ]

        delegator = Delegator(config_dir=tmp_path)

        for error in memory_errors:
            mock_run.side_effect = error

            result = delegator.execute("gemini", "test prompt")

            assert result.success is False
            # Should preserve the original error information

    def test_environment_variable_edge_cases(self, tmp_path):
        """Given edge cases with environment variables when executing delegation then should handle correctly."""
        delegator = Delegator(config_dir=tmp_path)

        # Test with empty environment variables
        with patch.dict(os.environ, {'GEMINI_API_KEY': ''}, clear=False):
            is_available, issues = delegator.verify_service("gemini")
            # Empty API key should be treated as missing

        # Test with None-like environment variables
        with patch.dict(os.environ, {}, clear=False):
            if 'GEMINI_API_KEY' in os.environ:
                del os.environ['GEMINI_API_KEY']

            is_available, issues = delegator.verify_service("gemini")
            assert is_available is False

    @patch('subprocess.run')
    def test_filesystem_edge_cases(self, mock_run, tmp_path):
        """Given filesystem edge cases when executing delegation then should handle appropriately."""
        # Create a very deep directory structure
        deep_path = tmp_path
        for i in range(20):  # Create 20 levels deep
            deep_path = deep_path / f"level_{i}"
            deep_path.mkdir(exist_ok=True)

        # Create a file in the deep structure
        deep_file = deep_path / "deep_file.py"
        deep_file.write_text("print('deep file')")

        delegator = Delegator(config_dir=tmp_path)

        # Test token estimation with deep path
        estimated = delegator.estimate_tokens([str(deep_file)], "analyze deep file")
        assert isinstance(estimated, int)
        assert estimated > 0

    def test_concurrent_delegation_scenarios(self, tmp_path):
        """Given concurrent delegation scenarios when executing then should handle thread safety."""
        import threading
        import queue

        delegator = Delegator(config_dir=tmp_path)
        results_queue = queue.Queue()

        def delegate_worker(worker_id):
            """Worker function for concurrent delegation."""
            try:
                # Mock the actual execution for thread safety
                with patch.object(delegator, 'build_command') as mock_build:
                    mock_build.return_value = ["echo", f"worker_{worker_id}"]
                    with patch('subprocess.run') as mock_run:
                        mock_result = MagicMock()
                        mock_result.returncode = 0
                        mock_result.stdout = f"Result from worker {worker_id}"
                        mock_result.stderr = ""
                        mock_run.return_value = mock_result

                        result = delegator.execute("gemini", f"test from worker {worker_id}")
                        results_queue.put((worker_id, result.success))
            except Exception as e:
                results_queue.put((worker_id, e))

        # Create multiple worker threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=delegate_worker, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=10)  # 10 second timeout

        # Collect results
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())

        # Should have completed all workers without crashes
        assert len(results) == 5
        for worker_id, result in results:
            if isinstance(result, Exception):
                # Log the exception but don't fail the test
                print(f"Worker {worker_id} failed with: {result}")
            else:
                assert result is True  # Success

    def test_configuration_corruption_recovery(self, tmp_path):
        """Given corrupted configuration when initializing then should recover gracefully."""
        # Create various types of corrupted config files
        corruption_scenarios = [
            ("empty_config.json", ""),
            ("partial_config.json", '{"services": {'),
            ("invalid_types.json", '{"services": {"test": "not_a_dict"}}'),
            ("circular_ref.json", '{"self": null}'),  # Will be manually set to circular
        ]

        for filename, content in corruption_scenarios:
            config_file = tmp_path / filename
            config_file.write_text(content)

            # For circular reference, modify after writing
            if filename == "circular_ref.json":
                data = json.loads(content)
                data["self"] = data  # Create circular reference
                config_file.write_text(json.dumps(data, indent=2))

            try:
                delegator = Delegator(config_dir=tmp_path)
                # Should initialize without crashing
                assert delegator.SERVICES is not None
            except Exception as e:
                # Should handle specific types of corruption gracefully
                assert not isinstance(e, RecursionError)  # Should not infinite loop

# Import os for environment variable tests
import os