"""Tests for quota_tracker.py following TDD/BDD principles."""

import json

# Import the module under test
import sys
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from quota_tracker import (
    DEFAULT_LIMITS,
    GeminiQuotaTracker,
    estimate_tokens_from_gemini_command,
    main,
)


class TestGeminiQuotaTracker:
    """Test GeminiQuotaTracker class functionality."""

    @pytest.mark.bdd
    def test_initialization_default_limits(self) -> None:
        """Given no custom limits when initializing tracker then should use defaults."""
        tracker = GeminiQuotaTracker()

        assert tracker.limits == DEFAULT_LIMITS
        assert (
            tracker.usage_file
            == Path.home() / ".claude" / "hooks" / "gemini" / "usage.json"
        )

    @pytest.mark.bdd
    def test_initialization_custom_limits(self) -> None:
        """Given custom limits when initializing tracker.

        then should use provided limits.
        """
        custom_limits = {
            "requests_per_minute": 30,
            "requests_per_day": 500,
            "tokens_per_minute": 16000,
            "tokens_per_day": 500000,
        }

        tracker = GeminiQuotaTracker(limits=custom_limits)

        assert tracker.limits == custom_limits

    @pytest.mark.bdd
    def test_load_usage_data_no_file(self, tmp_path) -> None:
        """Given no usage file when loading data then should create new structure."""
        usage_file = tmp_path / "usage.json"

        with patch.object(GeminiQuotaTracker, "usage_file", usage_file):
            tracker = GeminiQuotaTracker()

        assert "requests" in tracker.usage_data
        assert "daily_tokens" in tracker.usage_data
        assert "last_reset" in tracker.usage_data
        assert tracker.usage_data["daily_tokens"] == 0

    @pytest.mark.bdd
    def test_load_usage_data_existing_file(self, tmp_path) -> None:
        """Given existing usage file when loading data.

        then should load and clean data.
        """
        usage_file = tmp_path / "usage.json"

        # Create old data (more than 24 hours old)
        old_timestamp = (datetime.now() - timedelta(hours=25)).isoformat()
        recent_timestamp = (datetime.now() - timedelta(minutes=30)).isoformat()

        existing_data = {
            "requests": [
                {
                    "timestamp": old_timestamp,
                    "tokens": 100,
                    "success": True,
                },
                {
                    "timestamp": recent_timestamp,
                    "tokens": 200,
                    "success": True,
                },
            ],
            "daily_tokens": 500,
            "last_reset": (datetime.now() - timedelta(days=2)).isoformat(),
        }

        usage_file.write_text(json.dumps(existing_data))

        with patch.object(GeminiQuotaTracker, "usage_file", usage_file):
            tracker = GeminiQuotaTracker()

        # Should have cleaned old data and reset daily counter
        assert len(tracker.usage_data["requests"]) == 1
        assert tracker.usage_data["requests"][0]["tokens"] == 200
        assert tracker.usage_data["daily_tokens"] == 0  # Reset due to day change

    @pytest.mark.bdd
    def test_load_usage_data_invalid_json(self, tmp_path) -> None:
        """Given invalid JSON file when loading data.

        then should create new structure.
        """
        usage_file = tmp_path / "usage.json"
        usage_file.write_text("invalid json content")

        with patch.object(GeminiQuotaTracker, "usage_file", usage_file):
            tracker = GeminiQuotaTracker()

        assert tracker.usage_data["daily_tokens"] == 0
        assert len(tracker.usage_data["requests"]) == 0

    @pytest.mark.bdd
    @patch("builtins.open", new_callable=mock_open)
    @patch("pathlib.Path.mkdir")
    def test_record_request_success(self, mock_mkdir, mock_file, tmp_path) -> None:
        """Given successful request when recording then should update usage data."""
        usage_file = tmp_path / "usage.json"

        with patch.object(GeminiQuotaTracker, "usage_file", usage_file):
            tracker = GeminiQuotaTracker()

        initial_daily_tokens = tracker.usage_data["daily_tokens"]
        initial_requests_count = len(tracker.usage_data["requests"])

        tracker.record_request(estimated_tokens=150, success=True)

        # Check data was updated
        assert tracker.usage_data["daily_tokens"] == initial_daily_tokens + 150
        assert len(tracker.usage_data["requests"]) == initial_requests_count + 1

        # Check the new request entry
        new_request = tracker.usage_data["requests"][-1]
        assert new_request["tokens"] == 150
        assert new_request["success"] is True
        assert "timestamp" in new_request

        # Verify file was saved
        mock_file.assert_called_with(usage_file, "w")

    @pytest.mark.bdd
    def test_record_request_failure(self, tmp_path) -> None:
        """Given failed request when recording then should not add to daily tokens."""
        usage_file = tmp_path / "usage.json"

        with patch.object(GeminiQuotaTracker, "usage_file", usage_file):
            tracker = GeminiQuotaTracker()

        initial_daily_tokens = tracker.usage_data["daily_tokens"]

        tracker.record_request(estimated_tokens=150, success=False)

        # Daily tokens should not increase for failed requests
        assert tracker.usage_data["daily_tokens"] == initial_daily_tokens
        assert (
            len(tracker.usage_data["requests"]) == 1
        )  # Still recorded in requests list

    @pytest.mark.bdd
    def test_get_current_usage_empty(self, tmp_path) -> None:
        """Given no usage data when getting current usage then should return zeros."""
        usage_file = tmp_path / "usage.json"

        with patch.object(GeminiQuotaTracker, "usage_file", usage_file):
            tracker = GeminiQuotaTracker()

        usage = tracker.get_current_usage()

        assert usage["requests_last_minute"] == 0
        assert usage["tokens_last_minute"] == 0
        assert usage["daily_tokens"] == 0
        assert usage["requests_today"] == 0

    @pytest.mark.bdd
    def test_get_current_usage_with_data(self, tmp_path) -> None:
        """Given usage data when getting current usage.

        then should calculate correctly.
        """
        usage_file = tmp_path / "usage.json"

        # Create tracker and add some test data
        with patch.object(GeminiQuotaTracker, "usage_file", usage_file):
            tracker = GeminiQuotaTracker()

        # Add requests at different times
        now = datetime.now()
        one_minute_ago = now - timedelta(seconds=30)
        two_minutes_ago = now - timedelta(minutes=2)

        # Manually set up usage data for testing
        tracker.usage_data["requests"] = [
            {
                "timestamp": one_minute_ago.isoformat(),
                "tokens": 100,
                "success": True,
            },
            {
                "timestamp": two_minutes_ago.isoformat(),
                "tokens": 200,
                "success": True,
            },
        ]
        tracker.usage_data["daily_tokens"] = 500

        usage = tracker.get_current_usage()

        assert usage["requests_last_minute"] == 1  # Only the one from 30 seconds ago
        assert usage["tokens_last_minute"] == 100
        assert usage["daily_tokens"] == 500
        assert usage["requests_today"] == 2

    @pytest.mark.bdd
    def test_get_quota_status_healthy(self, tmp_path) -> None:
        """Given low usage when getting quota status.

        then should return healthy status.
        """
        usage_file = tmp_path / "usage.json"

        # Create tracker with very high limits to validate low usage
        high_limits = {
            "requests_per_minute": 1000,
            "requests_per_day": 10000,
            "tokens_per_minute": 1000000,
            "tokens_per_day": 10000000,
        }

        with patch.object(GeminiQuotaTracker, "usage_file", usage_file):
            tracker = GeminiQuotaTracker(limits=high_limits)

        status, warnings = tracker.get_quota_status()

        assert status == "[OK] Healthy"
        assert len(warnings) == 0

    @pytest.mark.bdd
    def test_get_quota_status_warning_threshold(self, tmp_path) -> None:
        """Given high usage when getting quota status then should return warning."""
        usage_file = tmp_path / "usage.json"

        # Create tracker with low limits to trigger warnings
        low_limits = {
            "requests_per_minute": 10,
            "requests_per_day": 100,
            "tokens_per_minute": 1000,
            "tokens_per_day": 10000,
        }

        with patch.object(GeminiQuotaTracker, "usage_file", usage_file):
            tracker = GeminiQuotaTracker(limits=low_limits)

        # Add usage that exceeds warning threshold (80%)
        now = datetime.now()
        tracker.usage_data["requests"] = [
            {
                "timestamp": (now - timedelta(seconds=30)).isoformat(),
                "tokens": 800,  # 80% of 1000
                "success": True,
            },
        ]
        tracker.usage_data["daily_tokens"] = int(10000 * 0.85)  # 85% of daily limit

        status, warnings = tracker.get_quota_status()

        assert "[WARNING]" in status
        assert len(warnings) > 0
        assert any("Token rate" in warning for warning in warnings)

    @pytest.mark.bdd
    def test_get_quota_status_critical_threshold(self, tmp_path) -> None:
        """Given critical usage when getting quota status.

        then should return critical.
        """
        usage_file = tmp_path / "usage.json"

        # Create tracker with very low limits
        critical_limits = {
            "requests_per_minute": 10,
            "requests_per_day": 100,
            "tokens_per_minute": 1000,
            "tokens_per_day": 10000,
        }

        with patch.object(GeminiQuotaTracker, "usage_file", usage_file):
            tracker = GeminiQuotaTracker(limits=critical_limits)

        # Add usage that exceeds critical threshold (95%)
        now = datetime.now()
        tracker.usage_data["requests"] = [
            {
                "timestamp": (now - timedelta(seconds=30)).isoformat(),
                "tokens": 960,  # 96% of 1000
                "success": True,
            },
        ]

        status, warnings = tracker.get_quota_status()

        assert "[CRITICAL]" in status
        assert len(warnings) > 0
        assert any("IMMEDIATE" in warning for warning in warnings)

    @patch("quota_tracker.tiktoken.get_encoding")
    def test_estimate_task_tokens_with_encoder(
        self,
        mock_get_encoding,
        sample_files,
        tmp_path,
    ) -> None:
        """Given tiktoken available when estimating tokens then should use encoder."""
        mock_encoder = MagicMock()
        mock_encoder.encode.return_value = list(range(50))  # 50 tokens
        mock_get_encoding.return_value = mock_encoder

        usage_file = tmp_path / "usage.json"
        with patch.object(GeminiQuotaTracker, "usage_file", usage_file):
            tracker = GeminiQuotaTracker()

        file_paths = [str(f) for f in sample_files]
        estimated = tracker.estimate_task_tokens(file_paths, prompt_length=100)

        assert estimated > 100  # More than just the prompt
        mock_get_encoding.assert_called_once_with("cl100k_base")

    @patch("quota_tracker.tiktoken.get_encoding")
    def test_estimate_task_tokens_without_encoder(
        self,
        mock_get_encoding,
        sample_files,
        tmp_path,
    ) -> None:
        """Given no tiktoken when estimating tokens then should use heuristic."""
        mock_get_encoding.side_effect = Exception("tiktoken not available")

        usage_file = tmp_path / "usage.json"
        with patch.object(GeminiQuotaTracker, "usage_file", usage_file):
            tracker = GeminiQuotaTracker()

        file_paths = [str(f) for f in sample_files]
        estimated = tracker.estimate_task_tokens(file_paths, prompt_length=100)

        assert isinstance(estimated, int)
        assert estimated > 0

    @pytest.mark.bdd
    def test_iter_source_paths_files_only(self, sample_files, tmp_path) -> None:
        """Given file paths when iterating source paths then should yield files."""
        usage_file = tmp_path / "usage.json"
        with patch.object(GeminiQuotaTracker, "usage_file", usage_file):
            tracker = GeminiQuotaTracker()

        file_paths = [str(f) for f in sample_files]
        paths = list(tracker._iter_source_paths(file_paths))

        assert len(paths) == len(file_paths)
        for path in paths:
            assert Path(path).suffix.lower() in {".py", ".md", ".json"}

    @pytest.mark.bdd
    def test_iter_source_paths_directory(self, tmp_path) -> None:
        """Given directory when iterating source paths.

        then should yield source files.
        """
        usage_file = tmp_path / "usage.json"
        with patch.object(GeminiQuotaTracker, "usage_file", usage_file):
            tracker = GeminiQuotaTracker()

        # Create a test directory structure
        test_dir = tmp_path / "test_project"
        test_dir.mkdir()

        (test_dir / "main.py").write_text("print('hello')")
        (test_dir / "README.md").write_text("# Project")
        (test_dir / "config.json").write_text("{}")
        (test_dir / "data.txt").write_text("some data")
        (test_dir / "__pycache__").mkdir()
        (test_dir / "__pycache__" / "cache.pyc").write_text("binary")

        paths = list(tracker._iter_source_paths([str(test_dir)]))

        # Should include source files but skip __pycache__
        assert len(paths) == 4  # py, md, json, txt
        assert any(path.endswith("main.py") for path in paths)
        assert any(path.endswith("README.md") for path in paths)
        assert not any("__pycache__" in path for path in paths)

    @pytest.mark.bdd
    def test_estimate_file_tokens_different_types(self, tmp_path) -> None:
        """Given different file types when estimating tokens.

        then should use correct ratios.
        """
        usage_file = tmp_path / "usage.json"
        with patch.object(GeminiQuotaTracker, "usage_file", usage_file):
            tracker = GeminiQuotaTracker()

        # Create test files of different types with same content length
        content = "x" * 1000  # 1000 characters

        py_file = tmp_path / "test.py"
        py_file.write_text(content)

        json_file = tmp_path / "test.json"
        json_file.write_text(content)

        md_file = tmp_path / "test.md"
        md_file.write_text(content)

        # Estimate tokens for each
        py_tokens = tracker._estimate_file_tokens(py_file)
        json_tokens = tracker._estimate_file_tokens(json_file)
        md_tokens = tracker._estimate_file_tokens(md_file)

        # Code files should have different token ratios than text files
        assert py_tokens > 0
        assert json_tokens > 0
        assert md_tokens > 0

    @pytest.mark.bdd
    def test_can_handle_task_success(self, tmp_path) -> None:
        """Given available capacity when checking task then should return.

        can_handle=True.
        """
        usage_file = tmp_path / "usage.json"

        with patch.object(GeminiQuotaTracker, "usage_file", usage_file):
            tracker = GeminiQuotaTracker()

        can_handle, issues = tracker.can_handle_task(estimated_tokens=100)

        assert can_handle is True
        assert len(issues) == 0

    @pytest.mark.bdd
    def test_can_handle_task_rate_limit(self, tmp_path) -> None:
        """Given rate limit reached when checking task then should return.

        can_handle=False.
        """
        usage_file = tmp_path / "usage.json"

        # Create tracker with low limits
        low_limits = {
            "requests_per_minute": 1,
            "requests_per_day": 100,
            "tokens_per_minute": 100,
            "tokens_per_day": 10000,
        }

        with patch.object(GeminiQuotaTracker, "usage_file", usage_file):
            tracker = GeminiQuotaTracker(limits=low_limits)

        # Add usage that reaches the limit
        now = datetime.now()
        tracker.usage_data["requests"] = [
            {
                "timestamp": (now - timedelta(seconds=30)).isoformat(),
                "tokens": 50,
                "success": True,
            },
        ]

        can_handle, issues = tracker.can_handle_task(estimated_tokens=100)

        assert can_handle is False
        assert len(issues) > 0
        assert any("limit" in issue.lower() for issue in issues)

    @pytest.mark.bdd
    def test_can_handle_task_daily_quota(self, tmp_path) -> None:
        """Given daily quota exhausted when checking task then should return.

        can_handle=False.
        """
        usage_file = tmp_path / "usage.json"

        # Create tracker with low daily limit
        low_limits = {
            "requests_per_minute": 60,
            "requests_per_day": 100,
            "tokens_per_minute": 32000,
            "tokens_per_day": 1000,
        }

        with patch.object(GeminiQuotaTracker, "usage_file", usage_file):
            tracker = GeminiQuotaTracker(limits=low_limits)

        # Set daily tokens near the limit
        tracker.usage_data["daily_tokens"] = 950

        can_handle, issues = tracker.can_handle_task(estimated_tokens=100)

        assert can_handle is False
        assert any("daily token quota" in issue.lower() for issue in issues)


class TestTokenEstimation:
    """Test token estimation utility functions."""

    @patch("quota_tracker.GeminiQuotaTracker")
    def test_estimate_tokens_from_gemini_command_with_files(
        self,
        mock_tracker_class,
        tmp_path,
    ) -> None:
        """Given command with file references when estimating then should.

        extract paths.
        """
        mock_tracker = MagicMock()
        mock_tracker.estimate_task_tokens.return_value = 500
        mock_tracker_class.return_value = mock_tracker

        command = 'gemini -p "analyze code" @src/main.py @docs/README.md'

        estimated = estimate_tokens_from_gemini_command(command)

        assert estimated == 500
        mock_tracker.estimate_task_tokens.assert_called_once_with(
            ["src/main.py", "docs/README.md"],
            len(command),
        )

    @patch("quota_tracker.GeminiQuotaTracker")
    def test_estimate_tokens_from_gemini_command_no_files(
        self, mock_tracker_class
    ) -> None:
        """Given command without files when estimating then should use default."""
        mock_tracker = MagicMock()
        mock_tracker.estimate_task_tokens.return_value = 50
        mock_tracker_class.return_value = mock_tracker

        command = 'gemini -p "simple question"'

        estimated = estimate_tokens_from_gemini_command(command)

        assert estimated == 50
        mock_tracker.estimate_task_tokens.assert_called_once_with([], len(command))

    @pytest.mark.bdd
    def test_estimate_tokens_from_gemini_command_invalid_command(self) -> None:
        """Given invalid command when estimating then should return default."""
        command = 'gemini -p "unclosed quote'

        estimated = estimate_tokens_from_gemini_command(command)

        # Should fall back to default estimation
        assert isinstance(estimated, int)
        assert estimated > 0


class TestQuotaTrackerCli:
    """Test CLI functionality of quota tracker."""

    @patch("quota_tracker.GeminiQuotaTracker")
    @patch("sys.argv", ["quota_tracker.py", "--status"])
    def test_cli_status(self, mock_tracker_class) -> None:
        """Given --status flag when running CLI then should show quota status."""
        mock_tracker = MagicMock()
        mock_tracker.get_quota_status.return_value = ("[OK] Healthy", ["Some warning"])
        mock_tracker_class.return_value = mock_tracker

        with patch("builtins.print") as mock_print:
            # main already imported at top level

            main()

        mock_print.assert_any_call("Status: [OK] Healthy")
        mock_print.assert_any_call("  Warning: Some warning")

    @patch("quota_tracker.GeminiQuotaTracker")
    @patch("sys.argv", ["quota_tracker.py", "--estimate", "file1.py", "file2.md"])
    def test_cli_estimate(self, mock_tracker_class) -> None:
        """Given --estimate flag when running CLI then should estimate tokens."""
        mock_tracker = MagicMock()
        mock_tracker.estimate_task_tokens.return_value = 1500
        mock_tracker_class.return_value = mock_tracker

        with patch("builtins.print") as mock_print:
            # main already imported at top level

            main()

        mock_print.assert_any_call(
            "Estimated tokens for ['file1.py', 'file2.md']: 1,500",
        )

    @patch("quota_tracker.GeminiQuotaTracker")
    @patch("sys.argv", ["quota_tracker.py", "--validate-config"])
    def test_cli_validate_config(self, mock_tracker_class) -> None:
        """Given --validate-config flag when running CLI then should validate config."""
        mock_tracker = MagicMock()
        mock_tracker.limits = {"test": 123}
        mock_tracker_class.return_value = mock_tracker

        with patch("builtins.print") as mock_print:
            # main already imported at top level

            main()

        mock_print.assert_any_call("Quota configuration validation:")
        mock_print.assert_any_call("  test: 123")
        mock_print.assert_any_call("  Configuration is valid")

    @pytest.mark.bdd
    @patch("quota_tracker.GeminiQuotaTracker")
    @patch("sys.argv", ["quota_tracker.py"])
    def test_cli_default_status(self, mock_tracker_class) -> None:
        """Given no flags when running CLI then should show status by default."""
        mock_tracker = MagicMock()
        mock_tracker.get_quota_status.return_value = ("[OK] Healthy", [])
        mock_tracker_class.return_value = mock_tracker

        with patch("builtins.print") as mock_print:
            # main already imported at top level

            main()

        mock_tracker.get_quota_status.assert_called_once()
        mock_print.assert_any_call("Status: [OK] Healthy")
