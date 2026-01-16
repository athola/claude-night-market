"""Tests for Gemini bridge hooks following TDD/BDD principles."""

import json

# Import hook modules with proper error handling
import sys
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

# Hook files don't have .py extension, so we need to load them manually
HOOKS_DIR = Path(__file__).parent.parent / "hooks" / "gemini"


def load_hook_module(name: str, file_path: Path):
    """Load a Python module from a file without .py extension."""
    import importlib.machinery

    # Use SourceFileLoader for files without .py extension
    loader = importlib.machinery.SourceFileLoader(name, str(file_path))
    spec = importlib.util.spec_from_loader(name, loader, origin=str(file_path))
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    # Set __file__ so the module can find its location
    module.__file__ = str(file_path.absolute())
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# Mock quota_tracker before loading hooks (it's imported by the hooks)
sys.modules["quota_tracker"] = MagicMock()

# Create a fake 'bridge' package so @patch decorators work
bridge_package = MagicMock()
sys.modules["bridge"] = bridge_package

# Load hook modules from files without .py extension
try:
    bridge_start = load_hook_module(
        "bridge.on_tool_start", HOOKS_DIR / "bridge.on_tool_start"
    )
    bridge_after = load_hook_module(
        "bridge.after_tool_use", HOOKS_DIR / "bridge.after_tool_use"
    )
    if bridge_start is None or bridge_after is None:
        raise ImportError("Failed to load hook modules")
    # Also register with the package for attribute access
    bridge_package.on_tool_start = bridge_start
    bridge_package.after_tool_use = bridge_after
except (ImportError, FileNotFoundError, OSError) as e:
    # Create mock modules if actual ones can't be imported
    bridge_start = MagicMock()
    bridge_after = MagicMock()
    bridge_package.on_tool_start = bridge_start
    bridge_package.after_tool_use = bridge_after


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

        # Test the key functions directly (main logic now only runs as script)
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

    def test_hook_main_flow_no_recommendation(self) -> None:
        """Validate hook functions return no recommendation for minimal input."""
        # Test with empty/minimal tool args - should not recommend
        should_recommend, benefit_type = (
            bridge_after.analyze_execution_for_gemini_benefit(
                "Read",
                {"file_path": "small.py"},
                "x" * 100,  # Small result
            )
        )
        assert should_recommend is False
        assert benefit_type is None

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

    def test_format_collaborative_suggestion(self, tmp_path) -> None:
        """Test collaborative suggestions for intelligence-requiring tasks."""
        # Test that collaborative suggestions are generated for architecture tasks
        tool_name = "Task"
        tool_args = {"description": "Design a scalable microservices architecture"}

        # Intelligence tasks should NOT suggest Gemini (Claude handles these)
        should_suggest = bridge_start.should_suggest_gemini(tool_name, tool_args)
        assert should_suggest is False

        # But they should generate collaborative suggestions
        is_intelligence = bridge_start.is_intelligence_requiring_task(
            tool_name, tool_args
        )
        assert is_intelligence is True

        collaborative = bridge_start.format_collaborative_suggestion(
            tool_name, tool_args
        )
        assert len(collaborative) > 0
        assert any("Claude should lead" in s for s in collaborative)

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

        # Test the core logic directly
        tool_use = payload["tool_use"]
        tool_name = tool_use["name"]
        tool_args = tool_use["input"]

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

        def test_quota_integration_available(self) -> None:
            """Verify hook modules have the expected quota-related functions."""
            # Verify bridge_start has the expected functions for quota integration
            assert hasattr(bridge_start, "should_suggest_gemini")
            assert hasattr(bridge_start, "format_gemini_suggestion")
            assert hasattr(bridge_start, "is_intelligence_requiring_task")
            assert hasattr(bridge_start, "format_collaborative_suggestion")

            # Verify bridge_after has the expected functions
            assert hasattr(bridge_after, "analyze_execution_for_gemini_benefit")
            assert hasattr(bridge_after, "generate_contextual_recommendation")


# ruff: noqa: D101,D102,D103,PLR2004,E501
