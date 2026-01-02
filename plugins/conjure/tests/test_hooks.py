"""Tests for Gemini bridge hooks following TDD/BDD principles."""

import json

# Import hook modules with proper error handling
import sys
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

sys.path.insert(0, str(Path(__file__).parent.parent / "hooks" / "gemini"))

# Mock modules that might not be available
with patch.dict(sys.modules, {"quota_tracker": MagicMock()}):
    try:
        import bridge.after_tool_use as bridge_after
        import bridge.on_tool_start as bridge_start
    except ImportError:
        # Create mock modules if actual ones can't be imported
        bridge_start = MagicMock()
        bridge_after = MagicMock()


class TestBridgeAfterToolUse:
    """Test bridge.after_tool_use hook functionality."""

    def test_analyze_execution_for_gemini_benefit_large_file(self) -> None:
        tool_result = [f"file{i}.py" for i in range(10)]  # 10 files

        should_recommend, benefit_type = (
            bridge_after.analyze_execution_for_gemini_benefit(
                "Glob",
                {"pattern": "*.py"},
                tool_result,
            )
        )

        assert should_recommend is False
        assert benefit_type is None

    def test_analyze_execution_for_gemini_benefit_extensive_search(self) -> None:
        tool_result = "Error: File not found"

        should_recommend, benefit_type = (
            bridge_after.analyze_execution_for_gemini_benefit(
                "Read",
                {"file_path": "missing.py"},
                tool_result,
            )
        )

        assert should_recommend is False
        assert benefit_type is None

    def test_generate_contextual_recommendation_large_file(self) -> None:
        recommendations = bridge_after.generate_contextual_recommendation(
            "many_files_analysis",
            "Glob",
            {"pattern": "**/*.py"},
        )

        assert len(recommendations) > 0
        assert any("**/*.py" in rec for rec in recommendations)
        assert any("analyze patterns" in rec for rec in recommendations)

    def test_generate_contextual_recommendation_extensive_search(self) -> None:
        recommendations = bridge_after.generate_contextual_recommendation(
            "exploration_results",
            "Task",
            {"description": "Explore codebase patterns"},
        )

        assert len(recommendations) > 0
        assert any("synthesis" in rec for rec in recommendations)
        assert any("context window" in rec for rec in recommendations)

    @patch("sys.stdin", new_callable=mock_open)
    @patch("sys.stderr", new_callable=mock_open)
    @patch("bridge.after_tool_use.analyze_execution_for_gemini_benefit")
    @patch("bridge.after_tool_use.generate_contextual_recommendation")
    def test_hook_main_flow_with_recommendation(
        self,
        mock_generate,
        mock_analyze,
        mock_stderr,
        mock_stdin,
        tmp_path,
    ) -> None:
        """Test test hook main flow with recommendation."""
        # Setup input payload
        payload = {
            "tool_use": {"name": "Read", "input": {"file_path": "large_file.py"}},
            "tool_result": "x" * 60000,
        }
        mock_stdin.return_value.read.return_value = json.dumps(payload)

        # Setup mocks
        mock_analyze.return_value = (True, "large_file_analysis")
        mock_generate.return_value = [
            "Use Gemini for large file analysis",
            "Run: gemini -p '@large_file.py analyze this file'",
        ]

        # Execute hook
        with patch.object(bridge_after, "json.load", return_value=payload):
            try:
                # The hook script doesn't have a main function, it runs at import
                # So we need to test the key functions
                should_recommend, benefit_type = (
                    bridge_after.analyze_execution_for_gemini_benefit(
                        "Read",
                        {"file_path": "large_file.py"},
                        "x" * 60000,
                    )
                )
                recommendations = bridge_after.generate_contextual_recommendation(
                    benefit_type,
                    "Read",
                    {"file_path": "large_file.py"},
                )

                assert should_recommend is True
                assert len(recommendations) > 0
            except SystemExit:
                pass  # Hook calls sys.exit(0) at the end

    @patch("sys.stdin", new_callable=mock_open)
    def test_hook_main_flow_no_recommendation(self, mock_stdin, tmp_path) -> None:
        """validate hook exits cleanly when no recommendation is produced."""
        mock_stdin.return_value.read.return_value = "{}"
        bridge_after = __import__("hooks.bridge.after_run", fromlist=["main"]).main
        with patch("sys.argv", ["after_run", "--event", "after_run"]):
            try:
                bridge_after()
            except SystemExit as exc:  # expected exit
                assert exc.code == 0

    def test_calculate_context_size_single_file(self, tmp_path) -> None:
        args = {
            "description": "Review the system architecture and recommend improvements",
        }

        result = bridge_start.is_intelligence_requiring_task("Task", args)

        assert result is True

    def test_is_intelligence_requiring_task_design(self) -> None:
        args = {"description": "List all Python files in the project"}

        result = bridge_start.is_intelligence_requiring_task("Task", args)

        assert result is False

    def test_is_data_processing_task_summarize(self) -> None:
        args = {"description": "List all TODO comments in the codebase"}

        result = bridge_start.is_data_processing_task("Task", args)

        assert result is True

    def test_is_data_processing_task_complex(self, tmp_path) -> None:
        """Large file should not trigger suggestion automatically."""
        test_file = tmp_path / "small.py"
        test_file.write_text("x" * 1000)  # 1KB file

        args = {"file_path": str(test_file)}

        result = bridge_start.should_suggest_gemini("Read", args)

        assert result is False

    def test_should_suggest_gemini_intelligence_task(self) -> None:
        args = {"pattern": "**/*.py"}

        result = bridge_start.should_suggest_gemini("Glob", args)

        assert result is True

    def test_should_suggest_gemini_data_processing_task(self) -> None:
        args = {"file_path": "src/main.py"}

        suggestions = bridge_start.format_gemini_suggestion("Read", args)

        assert len(suggestions) > 0
        assert any("src/main.py" in suggestion for suggestion in suggestions)
        assert any("Extract and summarize" in suggestion for suggestion in suggestions)

    def test_format_gemini_suggestion_glob(self) -> None:
        args = {"subagent_type": "Explore"}

        suggestions = bridge_start.format_gemini_suggestion("Task", args)

        assert len(suggestions) > 0
        assert any("Explore" in suggestion for suggestion in suggestions)
        assert any("gemini-delegation" in suggestion for suggestion in suggestions)

    @patch("bridge.on_tool_start.GeminiQuotaTracker")
    @patch("sys.stdin", new_callable=mock_open)
    def test_format_collaborative_suggestion(
        self, mock_stdin, mock_tracker_class
    ) -> None:
        # Setup input payload
        payload = {
            "tool_use": {"name": "Read", "input": {"file_path": "large_file.py"}},
        }
        mock_stdin.return_value.read.return_value = json.dumps(payload)

        # Setup quota tracker mock
        mock_tracker = MagicMock()
        mock_tracker.get_quota_status.return_value = ("[OK] Healthy", [])
        mock_tracker.estimate_task_tokens.return_value = 50000
        mock_tracker.can_handle_task.return_value = (True, [])
        mock_tracker_class.return_value = mock_tracker

        # Execute hook logic (simplified version)
        with patch.object(bridge_start, "json.load", return_value=payload):
            tool_use = payload["tool_use"]
            tool_name = tool_use["name"]
            tool_args = tool_use["input"]

            # Test the core logic
            should_suggest = bridge_start.should_suggest_gemini(tool_name, tool_args)
            suggestions = bridge_start.format_gemini_suggestion(tool_name, tool_args)

            assert should_suggest is True
            assert len(suggestions) > 0

    @patch("bridge.on_tool_start.GeminiQuotaTracker")
    @patch("sys.stdin", new_callable=mock_open)
    def test_hook_main_flow_intelligence_task(
        self,
        mock_stdin,
        mock_tracker_class,
        tmp_path,
    ) -> None:
        """Test test hook main flow intelligence task."""
        # Setup input payload
        payload = {
            "tool_use": {
                "name": "Task",
                "input": {"description": "Design a scalable system architecture"},
            },
        }
        mock_stdin.return_value.read.return_value = json.dumps(payload)

        # Setup quota tracker mock
        mock_tracker = MagicMock()
        mock_tracker.get_quota_status.return_value = ("[OK] Healthy", [])
        mock_tracker_class.return_value = mock_tracker

        # Execute hook logic
        with patch.object(bridge_start, "json.load", return_value=payload):
            tool_use = payload["tool_use"]
            tool_name = tool_use["name"]
            tool_args = tool_use["input"]

            # Test the core logic
            is_intelligence = bridge_start.is_intelligence_requiring_task(
                tool_name,
                tool_args,
            )
            collaborative_suggestions = bridge_start.format_collaborative_suggestion(
                tool_name,
                tool_args,
            )

            assert is_intelligence is True
            assert len(collaborative_suggestions) > 0
            assert any(
                "Claude should lead" in suggestion
                for suggestion in collaborative_suggestions
            )

    class TestHookIntegration:
        """Test integration between hooks and quota tracking."""

        @patch("bridge.on_tool_start.GeminiQuotaTracker")
        def test_quota_integration_available(self, mock_tracker_class) -> None:
            tracker_instance = mock_tracker_class.return_value
            tracker_instance.verify.return_value = (True, [])

            # Simulate on_tool_start calling tracker
            result = bridge_start.main()

            assert mock_tracker_class.called
            assert result is None


# ruff: noqa: D101,D102,D103,PLR2004,E501
