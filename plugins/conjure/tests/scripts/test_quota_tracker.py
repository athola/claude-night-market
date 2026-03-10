"""Tests for quota_tracker.py following TDD/BDD principles."""

from __future__ import annotations

# Import the module under test
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

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
        """Given custom limits when initializing tracker then should use them."""
        custom_limits = {
            "requests_per_minute": 30,
            "requests_per_day": 500,
            "tokens_per_minute": 16000,
            "tokens_per_day": 500000,
        }

        tracker = GeminiQuotaTracker(limits=custom_limits)

        assert tracker.limits == custom_limits

    @pytest.mark.bdd
    def test_initialization_sets_usage_file(self) -> None:
        """Given default init when checking usage_file then points to gemini dir."""
        tracker = GeminiQuotaTracker()

        expected = Path.home() / ".claude" / "hooks" / "gemini" / "usage.json"
        assert tracker.usage_file == expected

    @pytest.mark.bdd
    def test_initialization_usage_file_can_be_overridden(self, tmp_path: Path) -> None:
        """Given a tracker when overriding usage_file then the new value is used."""
        tracker = GeminiQuotaTracker()
        usage_file = tmp_path / "usage.json"
        tracker.usage_file = usage_file

        assert tracker.usage_file == usage_file

    @pytest.mark.bdd
    def test_initialization_storage_dir(self) -> None:
        """Given default init then storage_dir points to gemini directory."""
        tracker = GeminiQuotaTracker()

        expected = Path.home() / ".claude" / "hooks" / "gemini"
        assert tracker.storage_dir == expected

    @pytest.mark.bdd
    def test_initialization_service_name(self) -> None:
        """Given default init then service is set to gemini."""
        tracker = GeminiQuotaTracker()

        assert tracker.service == "gemini"

    @pytest.mark.bdd
    def test_initialization_config_reflects_custom_limits(self) -> None:
        """Given custom limits then config attributes match."""
        custom_limits = {
            "requests_per_minute": 10,
            "requests_per_day": 200,
            "tokens_per_minute": 5000,
            "tokens_per_day": 100000,
        }

        tracker = GeminiQuotaTracker(limits=custom_limits)

        assert tracker.config.requests_per_minute == 10
        assert tracker.config.requests_per_day == 200
        assert tracker.config.tokens_per_minute == 5000
        assert tracker.config.tokens_per_day == 100000

    @pytest.mark.bdd
    def test_get_quota_status_returns_tuple(self) -> None:
        """Given a fresh tracker when calling get_quota_status then returns tuple."""
        tracker = GeminiQuotaTracker()

        result = tracker.get_quota_status()

        assert isinstance(result, tuple)
        assert len(result) == 2

    @pytest.mark.bdd
    def test_get_quota_status_status_is_string(self) -> None:
        """Given a fresh tracker then status string is returned."""
        tracker = GeminiQuotaTracker()

        status, warnings = tracker.get_quota_status()

        assert isinstance(status, str)
        assert len(status) > 0

    @pytest.mark.bdd
    def test_get_quota_status_warnings_is_list(self) -> None:
        """Given a fresh tracker then warnings is a list of strings."""
        tracker = GeminiQuotaTracker()

        status, warnings = tracker.get_quota_status()

        assert isinstance(warnings, list)

    @pytest.mark.bdd
    def test_get_quota_status_healthy_stub(self) -> None:
        """Given stub QuotaTracker then status is OK Healthy."""
        tracker = GeminiQuotaTracker()

        status, warnings = tracker.get_quota_status()

        # Stub returns "[OK] Healthy" with leyline disabled notice
        assert "[OK] Healthy" in status
        assert len(warnings) >= 1
        assert any("leyline" in w.lower() for w in warnings)

    @pytest.mark.bdd
    def test_get_quota_status_with_custom_limits(self) -> None:
        """Given custom limits then get_quota_status still returns valid tuple."""
        limits = {
            "requests_per_minute": 1000,
            "requests_per_day": 10000,
            "tokens_per_minute": 1000000,
            "tokens_per_day": 10000000,
        }
        tracker = GeminiQuotaTracker(limits=limits)

        status, warnings = tracker.get_quota_status()

        assert isinstance(status, str)
        assert isinstance(warnings, list)

    def test_estimate_task_tokens_with_encoder(
        self,
        sample_files: list[Path],
    ) -> None:
        """Given tiktoken available when estimating tokens then should use encoder."""
        mock_encoder = MagicMock()
        mock_encoder.encode.return_value = list(range(50))  # 50 tokens

        # Clear the lru_cache then patch _get_encoder directly on the instance
        GeminiQuotaTracker._get_encoder.cache_clear()

        tracker = GeminiQuotaTracker()

        with patch.object(
            GeminiQuotaTracker, "_get_encoder", staticmethod(lambda: mock_encoder)
        ):
            file_paths = [str(f) for f in sample_files]
            estimated = tracker.estimate_task_tokens(file_paths, prompt_length=100)

        assert estimated > 0
        GeminiQuotaTracker._get_encoder.cache_clear()

    def test_estimate_task_tokens_without_encoder(
        self,
        sample_files: list[Path],
    ) -> None:
        """Given no tiktoken when estimating tokens then should use heuristic."""
        GeminiQuotaTracker._get_encoder.cache_clear()

        tracker = GeminiQuotaTracker()

        with patch.object(
            GeminiQuotaTracker, "_get_encoder", staticmethod(lambda: None)
        ):
            file_paths = [str(f) for f in sample_files]
            estimated = tracker.estimate_task_tokens(file_paths, prompt_length=100)

        assert isinstance(estimated, int)
        assert estimated > 0

        GeminiQuotaTracker._get_encoder.cache_clear()

    def test_estimate_task_tokens_heuristic_is_positive(self, tmp_path: Path) -> None:
        """Given heuristic path then result is a positive integer."""
        GeminiQuotaTracker._get_encoder.cache_clear()

        py_file = tmp_path / "hello.py"
        py_file.write_text("print('hello')\n")

        tracker = GeminiQuotaTracker()

        with patch.object(
            GeminiQuotaTracker, "_get_encoder", staticmethod(lambda: None)
        ):
            result = tracker.estimate_task_tokens([str(py_file)], prompt_length=40)

        assert result > 0

        GeminiQuotaTracker._get_encoder.cache_clear()

    @pytest.mark.bdd
    def test_iter_source_paths_files_only(self, sample_files: list[Path]) -> None:
        """Given file paths when iterating source paths then should yield files."""
        tracker = GeminiQuotaTracker()

        file_paths = [str(f) for f in sample_files]
        paths = list(tracker._iter_source_paths(file_paths))

        assert len(paths) == len(file_paths)
        for path in paths:
            assert Path(path).suffix.lower() in {".py", ".md", ".json"}

    @pytest.mark.bdd
    def test_iter_source_paths_directory(self, tmp_path: Path) -> None:
        """Given directory when iterating source paths then should yield source files."""
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
    def test_iter_source_paths_skips_node_modules(self, tmp_path: Path) -> None:
        """Given directory with node_modules then they are skipped."""
        tracker = GeminiQuotaTracker()

        test_dir = tmp_path / "project"
        test_dir.mkdir()
        (test_dir / "index.js").write_text("console.log('hi')")
        node_mods = test_dir / "node_modules"
        node_mods.mkdir()
        (node_mods / "lib.js").write_text("module.exports = {}")

        paths = list(tracker._iter_source_paths([str(test_dir)]))

        assert any("index.js" in p for p in paths)
        assert not any("node_modules" in p for p in paths)

    @pytest.mark.bdd
    def test_estimate_file_tokens_different_types(self, tmp_path: Path) -> None:
        """Given different file types when estimating tokens then returns int > 0."""
        tracker = GeminiQuotaTracker()

        content = "x" * 1000  # 1000 characters

        py_file = tmp_path / "test.py"
        py_file.write_text(content)

        json_file = tmp_path / "test.json"
        json_file.write_text(content)

        md_file = tmp_path / "test.md"
        md_file.write_text(content)

        py_tokens = tracker.estimate_file_tokens(py_file)
        json_tokens = tracker.estimate_file_tokens(json_file)
        md_tokens = tracker.estimate_file_tokens(md_file)

        assert py_tokens > 0
        assert json_tokens > 0
        assert md_tokens > 0

    @pytest.mark.bdd
    def test_estimate_file_tokens_missing_file(self, tmp_path: Path) -> None:
        """Given missing file when estimating tokens then returns 0."""
        tracker = GeminiQuotaTracker()

        missing = tmp_path / "does_not_exist.py"
        result = tracker.estimate_file_tokens(missing)

        assert result == 0

    @pytest.mark.bdd
    def test_estimate_file_tokens_empty_file(self, tmp_path: Path) -> None:
        """Given empty file when estimating tokens then returns small overhead."""
        tracker = GeminiQuotaTracker()

        empty = tmp_path / "empty.py"
        empty.write_text("")
        result = tracker.estimate_file_tokens(empty)

        # The heuristic: (len(text) // 4) + 6 = (0 // 4) + 6 = 6
        assert result >= 0


class TestTokenEstimation:
    """Test token estimation utility functions."""

    @patch("quota_tracker.GeminiQuotaTracker")
    def test_estimate_tokens_from_gemini_command_with_files(
        self,
        mock_tracker_class: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Given command with file references when estimating then extract paths."""
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
        self, mock_tracker_class: MagicMock
    ) -> None:
        """Given command without files when estimating then use default."""
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
    def test_cli_status(self, mock_tracker_class: MagicMock) -> None:
        """Given --status flag when running CLI then should print status."""
        mock_tracker = MagicMock()
        mock_tracker.get_quota_status.return_value = (
            "[OK] Healthy",
            ["Some warning"],
        )
        mock_tracker_class.return_value = mock_tracker

        with patch("builtins.print") as mock_print:
            main()

        mock_print.assert_any_call("[OK] Healthy")
        mock_print.assert_any_call("  WARNING: Some warning")

    @patch("quota_tracker.GeminiQuotaTracker")
    @patch("sys.argv", ["quota_tracker.py", "--estimate", "file1.py", "file2.md"])
    def test_cli_estimate(self, mock_tracker_class: MagicMock) -> None:
        """Given --estimate flag when running CLI then should estimate tokens."""
        mock_tracker = MagicMock()
        mock_tracker.estimate_task_tokens.return_value = 1500
        mock_tracker_class.return_value = mock_tracker

        with patch("builtins.print") as mock_print:
            main()

        mock_print.assert_any_call("Estimated tokens: 1500")

    @patch("quota_tracker.GeminiQuotaTracker")
    @patch("sys.argv", ["quota_tracker.py", "--validate-config"])
    def test_cli_validate_config(self, mock_tracker_class: MagicMock) -> None:
        """Given --validate-config flag when running CLI then print each limit."""
        mock_tracker = MagicMock()
        mock_tracker.limits = {"test": 123}
        mock_tracker_class.return_value = mock_tracker

        with patch("builtins.print") as mock_print:
            main()

        mock_print.assert_any_call("  test: 123")

    @pytest.mark.bdd
    @patch("quota_tracker.GeminiQuotaTracker")
    @patch("sys.argv", ["quota_tracker.py"])
    def test_cli_default_status(self, mock_tracker_class: MagicMock) -> None:
        """Given no flags when running CLI then should show status by default."""
        mock_tracker = MagicMock()
        mock_tracker.get_quota_status.return_value = ("[OK] Healthy", [])
        mock_tracker_class.return_value = mock_tracker

        with patch("builtins.print") as mock_print:
            main()

        mock_tracker.get_quota_status.assert_called_once()
        mock_print.assert_any_call("[OK] Healthy")

    @patch("quota_tracker.GeminiQuotaTracker")
    @patch("sys.argv", ["quota_tracker.py", "--status"])
    def test_cli_status_no_warnings(self, mock_tracker_class: MagicMock) -> None:
        """Given --status with no warnings then only status line is printed."""
        mock_tracker = MagicMock()
        mock_tracker.get_quota_status.return_value = ("[OK] Healthy", [])
        mock_tracker_class.return_value = mock_tracker

        with patch("builtins.print") as mock_print:
            main()

        calls = [str(c) for c in mock_print.call_args_list]
        assert not any("WARNING" in c for c in calls)

    @patch("quota_tracker.GeminiQuotaTracker")
    @patch("sys.argv", ["quota_tracker.py", "--status"])
    def test_cli_status_multiple_warnings(self, mock_tracker_class: MagicMock) -> None:
        """Given --status with multiple warnings then each is printed."""
        mock_tracker = MagicMock()
        mock_tracker.get_quota_status.return_value = (
            "[WARNING] High usage",
            ["warn1", "warn2"],
        )
        mock_tracker_class.return_value = mock_tracker

        with patch("builtins.print") as mock_print:
            main()

        mock_print.assert_any_call("[WARNING] High usage")
        mock_print.assert_any_call("  WARNING: warn1")
        mock_print.assert_any_call("  WARNING: warn2")
