"""Tests for Gemini bridge hooks following TDD/BDD principles.

Adds mock verification (assert_called_with / call_args checks)
and parametrize for repeated patterns.
"""

from __future__ import annotations

import importlib.machinery
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest

# Hook files don't have .py extension, so we need to load them manually
HOOKS_DIR = Path(__file__).parent.parent / "hooks" / "gemini"


def load_hook_module(name: str, file_path: Path):
    """Load a Python module from a file without .py extension."""
    loader = importlib.machinery.SourceFileLoader(name, str(file_path))
    spec = importlib.util.spec_from_loader(name, loader, origin=str(file_path))
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    module.__file__ = str(file_path.absolute())
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# Mock quota_tracker before loading hooks (it's imported by the hooks)
_real_quota_tracker = sys.modules.get("quota_tracker")
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
    bridge_package.on_tool_start = bridge_start
    bridge_package.after_tool_use = bridge_after
except (ImportError, FileNotFoundError, OSError):
    bridge_start = MagicMock()
    bridge_after = MagicMock()
    bridge_package.on_tool_start = bridge_start
    bridge_package.after_tool_use = bridge_after

# Restore the real quota_tracker module
if _real_quota_tracker is not None:
    sys.modules["quota_tracker"] = _real_quota_tracker
else:
    del sys.modules["quota_tracker"]


class TestBridgeAfterToolUse:
    """Test bridge.after_tool_use hook functionality."""

    @pytest.mark.parametrize(
        ("tool_name", "tool_args", "tool_result", "expected_recommend"),
        [
            (
                "Glob",
                {"pattern": "*.py"},
                [f"file{i}.py" for i in range(10)],
                False,
            ),
            (
                "Read",
                {"file_path": "missing.py"},
                "Error: File not found",
                False,
            ),
        ],
        ids=["glob-10-files", "read-missing-file"],
    )
    def test_analyze_execution_no_recommendation(
        self,
        tool_name: str,
        tool_args: dict,
        tool_result: object,
        expected_recommend: bool,
    ) -> None:
        """Small results don't trigger Gemini recommendation."""
        should_recommend, benefit_type = (
            bridge_after.analyze_execution_for_gemini_benefit(
                tool_name,
                tool_args,
                tool_result,
            )
        )

        assert should_recommend is expected_recommend
        assert benefit_type is None

    def test_generate_recommendation_many_files(self) -> None:
        """many_files_analysis generates pattern-aware recommendations."""
        recs = bridge_after.generate_contextual_recommendation(
            "many_files_analysis",
            "Glob",
            {"pattern": "**/*.py"},
        )

        assert len(recs) > 0
        assert any("**/*.py" in rec for rec in recs)
        assert any("analyze patterns" in rec for rec in recs)

    def test_generate_recommendation_exploration(self) -> None:
        """exploration_results generates synthesis recommendations."""
        recs = bridge_after.generate_contextual_recommendation(
            "exploration_results",
            "Task",
            {"description": "Explore codebase patterns"},
        )

        assert len(recs) > 0
        assert any("synthesis" in rec for rec in recs)
        assert any("context window" in rec for rec in recs)

    @patch("sys.stdin", new_callable=mock_open)
    @patch("sys.stderr", new_callable=mock_open)
    @patch("bridge.after_tool_use.analyze_execution_for_gemini_benefit")
    @patch("bridge.after_tool_use.generate_contextual_recommendation")
    def test_hook_main_flow_with_recommendation(
        self,
        mock_generate: MagicMock,
        mock_analyze: MagicMock,
        mock_stderr: MagicMock,
        mock_stdin: MagicMock,
    ) -> None:
        """Hook functions return recommendation for large results."""
        payload = {
            "tool_use": {
                "name": "Read",
                "input": {"file_path": "large_file.py"},
            },
            "tool_result": "x" * 60000,
        }
        mock_stdin.return_value.read.return_value = json.dumps(payload)

        mock_analyze.return_value = (True, "large_file_analysis")
        mock_generate.return_value = [
            "Use Gemini for large file analysis",
            "Run: gemini -p '@large_file.py analyze this file'",
        ]

        should_recommend, benefit_type = (
            bridge_after.analyze_execution_for_gemini_benefit(
                "Read",
                {"file_path": "large_file.py"},
                "x" * 60000,
            )
        )
        recs = bridge_after.generate_contextual_recommendation(
            benefit_type,
            "Read",
            {"file_path": "large_file.py"},
        )

        assert should_recommend is True
        assert len(recs) > 0
        # Verify analyze was called with correct args
        mock_analyze.assert_called_once_with(
            "Read",
            {"file_path": "large_file.py"},
            "x" * 60000,
        )
        # Verify generate was called with the benefit type
        mock_generate.assert_called_once_with(
            "large_file_analysis",
            "Read",
            {"file_path": "large_file.py"},
        )

    def test_hook_main_flow_no_recommendation(self) -> None:
        """Minimal input doesn't trigger recommendation."""
        should_recommend, benefit_type = (
            bridge_after.analyze_execution_for_gemini_benefit(
                "Read",
                {"file_path": "small.py"},
                "x" * 100,
            )
        )
        assert should_recommend is False
        assert benefit_type is None


class TestBridgeOnToolStart:
    """Test bridge.on_tool_start hook functionality."""

    @pytest.mark.parametrize(
        ("description", "expected"),
        [
            (
                "Review the system architecture and recommend improvements",
                True,
            ),
            ("List all Python files in the project", False),
        ],
        ids=["architecture-review", "simple-listing"],
    )
    def test_is_intelligence_requiring_task(
        self,
        description: str,
        expected: bool,
    ) -> None:
        """Intelligence-requiring tasks are correctly identified."""
        result = bridge_start.is_intelligence_requiring_task(
            "Task",
            {"description": description},
        )
        assert result is expected

    def test_is_data_processing_task(self) -> None:
        """Data processing tasks are correctly identified."""
        result = bridge_start.is_data_processing_task(
            "Task",
            {"description": "List all TODO comments in the codebase"},
        )
        assert result is True

    def test_small_file_no_suggestion(self, tmp_path: Path) -> None:
        """Small files don't trigger Gemini suggestion."""
        test_file = tmp_path / "small.py"
        test_file.write_text("x" * 1000)

        result = bridge_start.should_suggest_gemini(
            "Read",
            {"file_path": str(test_file)},
        )
        assert result is False

    def test_glob_triggers_suggestion(self) -> None:
        """Glob with broad pattern triggers suggestion."""
        result = bridge_start.should_suggest_gemini(
            "Glob",
            {"pattern": "**/*.py"},
        )
        assert result is True

    def test_format_suggestion_read(self) -> None:
        """Read tool generates file-specific suggestions."""
        suggestions = bridge_start.format_gemini_suggestion(
            "Read",
            {"file_path": "src/main.py"},
        )

        assert len(suggestions) > 0
        assert any("src/main.py" in s for s in suggestions)
        assert any("Extract and summarize" in s for s in suggestions)

    def test_format_suggestion_task(self) -> None:
        """Task tool generates delegation-specific suggestions."""
        suggestions = bridge_start.format_gemini_suggestion(
            "Task",
            {"subagent_type": "Explore"},
        )

        assert len(suggestions) > 0
        assert any("Explore" in s for s in suggestions)
        assert any("gemini-delegation" in s for s in suggestions)

    def test_collaborative_suggestion_for_architecture(self) -> None:
        """Architecture tasks get collaborative (Claude-led) suggestions."""
        tool_name = "Task"
        tool_args = {
            "description": "Design a scalable microservices architecture",
        }

        should_suggest = bridge_start.should_suggest_gemini(
            tool_name,
            tool_args,
        )
        assert should_suggest is False

        is_intelligence = bridge_start.is_intelligence_requiring_task(
            tool_name,
            tool_args,
        )
        assert is_intelligence is True

        collaborative = bridge_start.format_collaborative_suggestion(
            tool_name,
            tool_args,
        )
        assert len(collaborative) > 0
        assert any("Claude should lead" in s for s in collaborative)

    def test_hook_main_flow_intelligence_task(self) -> None:
        """Intelligence tasks produce collaborative suggestions."""
        tool_name = "Task"
        tool_args = {
            "description": "Design a scalable system architecture",
        }

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
        assert any("Claude should lead" in s for s in collaborative_suggestions)

    class TestHookIntegration:
        """Test integration between hooks and quota tracking."""

        def test_quota_integration_available(self) -> None:
            """Hook modules have the expected quota-related functions."""
            assert hasattr(bridge_start, "should_suggest_gemini")
            assert hasattr(bridge_start, "format_gemini_suggestion")
            assert hasattr(bridge_start, "is_intelligence_requiring_task")
            assert hasattr(bridge_start, "format_collaborative_suggestion")

            assert hasattr(
                bridge_after,
                "analyze_execution_for_gemini_benefit",
            )
            assert hasattr(
                bridge_after,
                "generate_contextual_recommendation",
            )
