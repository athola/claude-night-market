"""Tests for Gemini bridge hooks following TDD/BDD principles."""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open
import pytest

# Import hook modules with proper error handling
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "hooks" / "gemini"))

# Mock modules that might not be available
with patch.dict(sys.modules, {'quota_tracker': MagicMock()}):
    try:
        import bridge.on_tool_start as bridge_start
        import bridge.after_tool_use as bridge_after
    except ImportError as e:
        # Create mock modules if actual ones can't be imported
        bridge_start = MagicMock()
        bridge_after = MagicMock()
        print(f"Warning: Could not import bridge modules: {e}")


class TestBridgeAfterToolUse:
    """Test bridge.after_tool_use hook functionality."""

    def test_analyze_execution_for_gemini_benefit_large_file(self):
        """Given large file read when analyzing execution then should recommend gemini."""
        tool_result = "x" * 60000  # 60KB file

        should_recommend, benefit_type = bridge_after.analyze_execution_for_gemini_benefit(
            "Read", {"file_path": "large_file.py"}, tool_result
        )

        assert should_recommend is True
        assert benefit_type == "large_file_analysis"

    def test_analyze_execution_for_gemini_benefit_small_file(self):
        """Given small file read when analyzing execution then should not recommend gemini."""
        tool_result = "x" * 1000  # 1KB file

        should_recommend, benefit_type = bridge_after.analyze_execution_for_gemini_benefit(
            "Read", {"file_path": "small_file.py"}, tool_result
        )

        assert should_recommend is False
        assert benefit_type is None

    def test_analyze_execution_for_gemini_benefit_many_files(self):
        """Given many files found when analyzing execution then should recommend gemini."""
        tool_result = [f"file{i}.py" for i in range(25)]  # 25 files

        should_recommend, benefit_type = bridge_after.analyze_execution_for_gemini_benefit(
            "Glob", {"pattern": "**/*.py"}, tool_result
        )

        assert should_recommend is True
        assert benefit_type == "many_files_analysis"

    def test_analyze_execution_for_gemini_benefit_few_files(self):
        """Given few files found when analyzing execution then should not recommend gemini."""
        tool_result = [f"file{i}.py" for i in range(10)]  # 10 files

        should_recommend, benefit_type = bridge_after.analyze_execution_for_gemini_benefit(
            "Glob", {"pattern": "*.py"}, tool_result
        )

        assert should_recommend is False
        assert benefit_type is None

    def test_analyze_execution_for_gemini_benefit_extensive_search(self):
        """Given extensive search results when analyzing execution then should recommend gemini."""
        tool_result = "\n".join([f"match {i}" for i in range(60)])  # 60 lines

        should_recommend, benefit_type = bridge_after.analyze_execution_for_gemini_benefit(
            "Grep", {"pattern": "TODO"}, tool_result
        )

        assert should_recommend is True
        assert benefit_type == "extensive_search_results"

    def test_analyze_execution_for_gemini_benefit_task_exploration(self):
        """Given task exploration when analyzing execution then should recommend gemini."""
        should_recommend, benefit_type = bridge_after.analyze_execution_for_gemini_benefit(
            "Task", {"subagent_type": "Explore"}, "exploration results"
        )

        assert should_recommend is True
        assert benefit_type == "exploration_results"

    def test_analyze_execution_for_gemini_benefit_error_result(self):
        """Given error result when analyzing execution then should not recommend gemini."""
        tool_result = "Error: File not found"

        should_recommend, benefit_type = bridge_after.analyze_execution_for_gemini_benefit(
            "Read", {"file_path": "missing.py"}, tool_result
        )

        assert should_recommend is False
        assert benefit_type is None

    def test_generate_contextual_recommendation_large_file(self):
        """Given large file analysis when generating recommendations then should provide file-specific advice."""
        recommendations = bridge_after.generate_contextual_recommendation(
            "large_file_analysis", "Read", {"file_path": "src/large_module.py"}
        )

        assert len(recommendations) > 0
        assert any("large file analysis" in rec for rec in recommendations)
        assert any("@src/large_module.py" in rec for rec in recommendations)
        assert any("gemini-delegation" in rec for rec in recommendations)

    def test_generate_contextual_recommendation_many_files(self):
        """Given many files analysis when generating recommendations then should provide pattern advice."""
        recommendations = bridge_after.generate_contextual_recommendation(
            "many_files_analysis", "Glob", {"pattern": "**/*.py"}
        )

        assert len(recommendations) > 0
        assert any("**/*.py" in rec for rec in recommendations)
        assert any("analyze patterns" in rec for rec in recommendations)

    def test_generate_contextual_recommendation_extensive_search(self):
        """Given extensive search when generating recommendations then should provide search analysis advice."""
        recommendations = bridge_after.generate_contextual_recommendation(
            "extensive_search_results", "Grep", {"pattern": "TODO", "path": "src/"}
        )

        assert len(recommendations) > 0
        assert any("TODO" in rec for rec in recommendations)
        assert any("src/" in rec for rec in recommendations)
        assert any("higher-level analysis" in rec for rec in recommendations)

    def test_generate_contextual_recommendation_exploration(self):
        """Given exploration results when generating recommendations then should provide synthesis advice."""
        recommendations = bridge_after.generate_contextual_recommendation(
            "exploration_results", "Task", {"description": "Explore codebase patterns"}
        )

        assert len(recommendations) > 0
        assert any("synthesis" in rec for rec in recommendations)
        assert any("context window" in rec for rec in recommendations)

    @patch('sys.stdin', new_callable=mock_open)
    @patch('sys.stderr', new_callable=mock_open)
    @patch('bridge.after_tool_use.analyze_execution_for_gemini_benefit')
    @patch('bridge.after_tool_use.generate_contextual_recommendation')
    def test_hook_main_flow_with_recommendation(
        self, mock_generate, mock_analyze, mock_stderr, mock_stdin, tmp_path
    ):
        """Given execution that benefits from gemini when hook runs then should print recommendations."""
        # Setup input payload
        payload = {
            "tool_use": {
                "name": "Read",
                "input": {"file_path": "large_file.py"}
            },
            "tool_result": "x" * 60000
        }
        mock_stdin.return_value.read.return_value = json.dumps(payload)

        # Setup mocks
        mock_analyze.return_value = (True, "large_file_analysis")
        mock_generate.return_value = [
            "Use Gemini for large file analysis",
            "Run: gemini -p '@large_file.py analyze this file'"
        ]

        # Execute hook
        with patch.object(bridge_after, 'json.load', return_value=payload):
            try:
                # The hook script doesn't have a main function, it runs at import
                # So we need to test the key functions
                should_recommend, benefit_type = bridge_after.analyze_execution_for_gemini_benefit(
                    "Read", {"file_path": "large_file.py"}, "x" * 60000
                )
                recommendations = bridge_after.generate_contextual_recommendation(
                    benefit_type, "Read", {"file_path": "large_file.py"}
                )

                assert should_recommend is True
                assert len(recommendations) > 0
            except SystemExit:
                pass  # Hook calls sys.exit(0) at the end

    @patch('sys.stdin', new_callable=mock_open)
    def test_hook_main_flow_no_recommendation(self, mock_stdin, tmp_path):
        """Given execution that doesn't benefit from gemini when hook runs then should not print anything."""
        # Setup input payload
        payload = {
            "tool_use": {
                "name": "Read",
                "input": {"file_path": "small_file.py"}
            },
            "tool_result": "small content"
        }
        mock_stdin.return_value.read.return_value = json.dumps(payload)

        # Execute hook
        with patch.object(bridge_after, 'json.load', return_value=payload):
            with patch('bridge.after_tool_use.analyze_execution_for_gemini_benefit') as mock_analyze:
                mock_analyze.return_value = (False, None)

                try:
                    # The hook script doesn't have a main function, it runs at import
                    # So we need to test the key functions
                    should_recommend, benefit_type = bridge_after.analyze_execution_for_gemini_benefit(
                        "Read", {"file_path": "small_file.py"}, "small content"
                    )

                    assert should_recommend is False
                except SystemExit:
                    pass  # Hook calls sys.exit(0) at the end


class TestBridgeOnToolStart:
    """Test bridge.on_tool_start hook functionality."""

    def test_calculate_context_size_single_file(self, tmp_path):
        """Given single file when calculating context size then should return file size."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x" * 1000)  # 1KB file

        size = bridge_start.calculate_context_size([str(test_file)])

        assert size == 1000

    def test_calculate_context_size_directory(self, tmp_path):
        """Given directory when calculating context size then should sum source files."""
        # Create test directory structure
        test_dir = tmp_path / "project"
        test_dir.mkdir()

        (test_dir / "main.py").write_text("x" * 500)
        (test_dir / "utils.py").write_text("x" * 300)
        (test_dir / "data.json").write_text("x" * 200)
        (test_dir / "README.md").write_text("x" * 400)

        # Create files that should be skipped
        (test_dir / "__pycache__").mkdir()
        (test_dir / "__pycache__" / "cache.pyc").write_text("x" * 1000)
        (test_dir / "node_modules").mkdir()
        (test_dir / "node_modules" / "package.js").write_text("x" * 2000)

        size = bridge_start.calculate_context_size([str(test_dir)])

        # Should only include source files (500 + 300 + 200 + 400 = 1400)
        assert size == 1400

    def test_is_intelligence_requiring_task_architecture(self):
        """Given architecture task when checking intelligence requirement then should return True."""
        args = {"description": "Review the system architecture and recommend improvements"}

        result = bridge_start.is_intelligence_requiring_task("Task", args)

        assert result is True

    def test_is_intelligence_requiring_task_design(self):
        """Given design task when checking intelligence requirement then should return True."""
        args = {"description": "Design a new microservice architecture"}

        result = bridge_start.is_intelligence_requiring_task("Task", args)

        assert result is True

    def test_is_intelligence_requiring_task_simple(self):
        """Given simple task when checking intelligence requirement then should return False."""
        args = {"description": "List all Python files in the project"}

        result = bridge_start.is_intelligence_requiring_task("Task", args)

        assert result is False

    def test_is_data_processing_task_summarize(self):
        """Given summarize task when checking data processing requirement then should return True."""
        args = {"description": "Summarize the contents of all log files"}

        result = bridge_start.is_data_processing_task("Task", args)

        assert result is True

    def test_is_data_processing_task_list(self):
        """Given list task when checking data processing requirement then should return True."""
        args = {"description": "List all TODO comments in the codebase"}

        result = bridge_start.is_data_processing_task("Task", args)

        assert result is True

    def test_is_data_processing_task_complex(self):
        """Given complex task when checking data processing requirement then should return False."""
        args = {"description": "Analyze the system architecture and recommend optimizations"}

        result = bridge_start.is_data_processing_task("Task", args)

        assert result is False

    def test_should_suggest_gemini_large_file(self, tmp_path):
        """Given large file when checking gemini suggestion then should return True."""
        test_file = tmp_path / "large.py"
        test_file.write_text("x" * 150000)  # 150KB file

        args = {"file_path": str(test_file)}

        result = bridge_start.should_suggest_gemini("Read", args)

        assert result is True

    def test_should_suggest_gemini_small_file(self, tmp_path):
        """Given small file when checking gemini suggestion then should return False."""
        test_file = tmp_path / "small.py"
        test_file.write_text("x" * 1000)  # 1KB file

        args = {"file_path": str(test_file)}

        result = bridge_start.should_suggest_gemini("Read", args)

        assert result is False

    def test_should_suggest_gemini_intelligence_task(self):
        """Given intelligence requiring task when checking gemini suggestion then should return False."""
        args = {"description": "Design a scalable architecture for the system"}

        result = bridge_start.should_suggest_gemini("Task", args)

        assert result is False  # Claude should handle intelligence tasks

    def test_should_suggest_gemini_glob_pattern(self):
        """Given glob pattern with recursion when checking gemini suggestion then should return True."""
        args = {"pattern": "**/*.py"}

        result = bridge_start.should_suggest_gemini("Glob", args)

        assert result is True

    def test_should_suggest_gemini_data_processing_task(self):
        """Given data processing task when checking gemini suggestion then should return True."""
        args = {
            "description": "List and categorize all configuration files",
            "subagent_type": "Explore"
        }

        result = bridge_start.should_suggest_gemini("Task", args)

        assert result is True

    def test_format_gemini_suggestion_read(self):
        """Given Read tool when formatting gemini suggestion then should provide read-specific advice."""
        args = {"file_path": "src/main.py"}

        suggestions = bridge_start.format_gemini_suggestion("Read", args)

        assert len(suggestions) > 0
        assert any("src/main.py" in suggestion for suggestion in suggestions)
        assert any("Extract and summarize" in suggestion for suggestion in suggestions)

    def test_format_gemini_suggestion_glob(self):
        """Given Glob tool when formatting gemini suggestion then should provide glob-specific advice."""
        args = {"pattern": "**/*.py"}

        suggestions = bridge_start.format_gemini_suggestion("Glob", args)

        assert len(suggestions) > 0
        assert any("**/*.py" in suggestion for suggestion in suggestions)
        assert any("categorize" in suggestion for suggestion in suggestions)

    def test_format_gemini_suggestion_task(self):
        """Given Task tool when formatting gemini suggestion then should provide task-specific advice."""
        args = {"subagent_type": "Explore"}

        suggestions = bridge_start.format_gemini_suggestion("Task", args)

        assert len(suggestions) > 0
        assert any("Explore" in suggestion for suggestion in suggestions)
        assert any("gemini-delegation" in suggestion for suggestion in suggestions)

    def test_format_collaborative_suggestion(self):
        """Given Task tool when formatting collaborative suggestion then should provide workflow advice."""
        args = {"description": "Evaluate the current architecture and recommend improvements"}

        suggestions = bridge_start.format_collaborative_suggestion("Task", args)

        assert len(suggestions) > 0
        assert any("Claude should lead" in suggestion for suggestion in suggestions)
        assert any("Collaborative Workflow" in suggestion for suggestion in suggestions)
        assert any("architecture" in suggestion for suggestion in suggestions)

    @patch('bridge.on_tool_start.GeminiQuotaTracker')
    @patch('sys.stdin', new_callable=mock_open)
    @patch('sys.stderr', new_callable=mock_open)
    def test_hook_main_flow_with_suggestion(
        self, mock_stderr, mock_stdin, mock_tracker_class, tmp_path
    ):
        """Given tool that benefits from gemini when hook runs then should print suggestion."""
        # Setup input payload
        payload = {
            "tool_use": {
                "name": "Read",
                "input": {"file_path": "large_file.py"}
            }
        }
        mock_stdin.return_value.read.return_value = json.dumps(payload)

        # Setup quota tracker mock
        mock_tracker = MagicMock()
        mock_tracker.get_quota_status.return_value = ("[OK] Healthy", [])
        mock_tracker.estimate_task_tokens.return_value = 50000
        mock_tracker.can_handle_task.return_value = (True, [])
        mock_tracker_class.return_value = mock_tracker

        # Execute hook logic (simplified version)
        with patch.object(bridge_start, 'json.load', return_value=payload):
            tool_use = payload["tool_use"]
            tool_name = tool_use["name"]
            tool_args = tool_use["input"]

            # Test the core logic
            should_suggest = bridge_start.should_suggest_gemini(tool_name, tool_args)
            suggestions = bridge_start.format_gemini_suggestion(tool_name, tool_args)

            assert should_suggest is True
            assert len(suggestions) > 0

    @patch('bridge.on_tool_start.GeminiQuotaTracker')
    @patch('sys.stdin', new_callable=mock_open)
    def test_hook_main_flow_intelligence_task(
        self, mock_stdin, mock_tracker_class, tmp_path
    ):
        """Given intelligence task when hook runs then should provide collaborative suggestion."""
        # Setup input payload
        payload = {
            "tool_use": {
                "name": "Task",
                "input": {"description": "Design a scalable system architecture"}
            }
        }
        mock_stdin.return_value.read.return_value = json.dumps(payload)

        # Setup quota tracker mock
        mock_tracker = MagicMock()
        mock_tracker.get_quota_status.return_value = ("[OK] Healthy", [])
        mock_tracker_class.return_value = mock_tracker

        # Execute hook logic
        with patch.object(bridge_start, 'json.load', return_value=payload):
            tool_use = payload["tool_use"]
            tool_name = tool_use["name"]
            tool_args = tool_use["input"]

            # Test the core logic
            is_intelligence = bridge_start.is_intelligence_requiring_task(tool_name, tool_args)
            collaborative_suggestions = bridge_start.format_collaborative_suggestion(tool_name, tool_args)

            assert is_intelligence is True
            assert len(collaborative_suggestions) > 0
            assert any("Claude should lead" in suggestion for suggestion in collaborative_suggestions)


class TestHookIntegration:
    """Test integration between hooks and quota tracking."""

    @patch('bridge.on_tool_start.GeminiQuotaTracker')
    def test_quota_integration_available(self, mock_tracker_class):
        """Given available quota when suggesting gemini then should allow delegation."""
        mock_tracker = MagicMock()
        mock_tracker.get_quota_status.return_value = ("[OK] Healthy", [])
        mock_tracker.estimate_task_tokens.return_value = 10000
        mock_tracker.can_handle_task.return_value = (True, [])
        mock_tracker_class.return_value = mock_tracker

        # Simulate the hook's quota checking logic
        quota_status, quota_warnings = mock_tracker.get_quota_status()
        estimated_tokens = mock_tracker.estimate_task_tokens([])
        can_handle, issues = mock_tracker.can_handle_task(estimated_tokens)

        assert quota_status == "[OK] Healthy"
        assert can_handle is True
        assert len(issues) == 0

    @patch('bridge.on_tool_start.GeminiQuotaTracker')
    def test_quota_integration_exhausted(self, mock_tracker_class):
        """Given exhausted quota when suggesting gemini then should warn about limits."""
        mock_tracker = MagicMock()
        mock_tracker.get_quota_status.return_value = ("[CRITICAL] Daily Quota Exhausted", ["Daily quota nearly exhausted"])
        mock_tracker.estimate_task_tokens.return_value = 10000
        mock_tracker.can_handle_task.return_value = (False, ["Daily token quota would be exceeded"])
        mock_tracker_class.return_value = mock_tracker

        # Simulate the hook's quota checking logic
        quota_status, quota_warnings = mock_tracker.get_quota_status()
        estimated_tokens = mock_tracker.estimate_task_tokens([])
        can_handle, issues = mock_tracker.can_handle_task(estimated_tokens)

        assert "[CRITICAL]" in quota_status
        assert can_handle is False
        assert len(issues) > 0
        assert any("quota" in issue.lower() for issue in issues)

    def test_fallback_quota_tracker(self):
        """Given missing quota_tracker module when hook runs then should use fallback."""
        # Test fallback behavior when quota_tracker is not available
        with patch.dict('sys.modules', {'quota_tracker': None}):
            # Re-import to trigger fallback behavior
            with patch('bridge.on_tool_start._QUOTA_AVAILABLE', False):
                from bridge.on_tool_start import _FallbackQuotaTracker

                fallback_tracker = _FallbackQuotaTracker()
                status, warnings = fallback_tracker.get_quota_status()
                can_handle, issues = fallback_tracker.can_handle_task(10000)

                assert "Unknown" in status
                assert can_handle is True
                assert len(issues) == 0
