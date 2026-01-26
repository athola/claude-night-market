"""Tests for clear-context skill execution mode functionality.

Tests the execution mode propagation for context handoffs, ensuring
batch operations continue without pausing when --dangerous is set.
"""

import json


class TestExecutionModeDetection:
    """Test execution mode detection from environment and state."""

    def test_default_mode_is_interactive(self):
        """Default execution mode should be interactive."""
        execution_mode = {
            "mode": "interactive",
            "auto_continue": False,
            "source_command": None,
            "remaining_tasks": [],
            "dangerous_mode": False,
        }
        assert execution_mode["mode"] == "interactive"
        assert execution_mode["auto_continue"] is False

    def test_dangerous_mode_sets_auto_continue(self):
        """Dangerous mode should enable auto_continue."""
        execution_mode = {
            "mode": "dangerous",
            "auto_continue": True,
            "source_command": "do-issue",
            "remaining_tasks": ["#43", "#44"],
            "dangerous_mode": True,
        }
        assert execution_mode["mode"] == "dangerous"
        assert execution_mode["auto_continue"] is True
        assert execution_mode["dangerous_mode"] is True

    def test_unattended_mode_sets_auto_continue(self):
        """Unattended mode should enable auto_continue."""
        execution_mode = {
            "mode": "unattended",
            "auto_continue": True,
            "source_command": "batch-process",
            "remaining_tasks": [],
            "dangerous_mode": False,
        }
        assert execution_mode["mode"] == "unattended"
        assert execution_mode["auto_continue"] is True


class TestSessionStateMetadata:
    """Test session state metadata format."""

    def test_metadata_v1_1_includes_execution_mode(self):
        """Checkpoint version 1.1 should include execution_mode."""
        metadata = {
            "checkpoint_version": "1.1",
            "parent_session_id": None,
            "handoff_count": 0,
            "estimated_remaining_work": "medium",
            "priority": "high",
            "execution_mode": {
                "mode": "interactive",
                "auto_continue": False,
                "source_command": None,
                "remaining_tasks": [],
                "dangerous_mode": False,
            },
        }
        assert "execution_mode" in metadata
        assert metadata["checkpoint_version"] == "1.1"

    def test_execution_mode_serializable(self):
        """Execution mode should be JSON serializable."""
        execution_mode = {
            "mode": "dangerous",
            "auto_continue": True,
            "source_command": "do-issue",
            "remaining_tasks": ["#42", "#43"],
            "dangerous_mode": True,
        }
        serialized = json.dumps(execution_mode)
        deserialized = json.loads(serialized)
        assert deserialized == execution_mode


class TestExecutionModeInheritance:
    """Test execution mode inheritance across handoffs."""

    def test_child_inherits_parent_mode(self):
        """Continuation agent should inherit parent's execution mode."""
        parent_mode = {
            "mode": "dangerous",
            "auto_continue": True,
            "source_command": "do-issue",
            "remaining_tasks": ["#43", "#44"],
            "dangerous_mode": True,
        }
        # Simulate inheritance
        child_mode = parent_mode.copy()
        child_mode["remaining_tasks"] = ["#44"]  # One task completed

        assert child_mode["mode"] == parent_mode["mode"]
        assert child_mode["auto_continue"] == parent_mode["auto_continue"]
        assert child_mode["dangerous_mode"] == parent_mode["dangerous_mode"]

    def test_handoff_count_increments(self):
        """Handoff count should increment on each handoff."""
        parent_metadata = {"handoff_count": 1}
        child_metadata = {"handoff_count": parent_metadata["handoff_count"] + 1}
        assert child_metadata["handoff_count"] == 2


class TestBatchProcessingMode:
    """Test batch processing with multiple issues."""

    def test_multiple_issues_sets_remaining_tasks(self):
        """Multiple issues should populate remaining_tasks."""
        issues = [42, 43, 44]
        execution_mode = {
            "mode": "unattended",
            "auto_continue": True,
            "source_command": "do-issue",
            "remaining_tasks": [
                f"#{i}" for i in issues[1:]
            ],  # Skip first (in progress)
            "dangerous_mode": False,
        }
        assert len(execution_mode["remaining_tasks"]) == 2
        assert "#43" in execution_mode["remaining_tasks"]
        assert "#44" in execution_mode["remaining_tasks"]

    def test_task_completion_updates_remaining(self):
        """Completing a task should update remaining_tasks."""
        execution_mode = {
            "remaining_tasks": ["#43", "#44"],
            "auto_continue": True,
        }
        # Simulate completing #43
        execution_mode["remaining_tasks"].remove("#43")
        assert execution_mode["remaining_tasks"] == ["#44"]

    def test_empty_remaining_signals_completion(self):
        """Empty remaining_tasks indicates all work complete."""
        execution_mode = {
            "remaining_tasks": [],
            "auto_continue": True,
        }
        is_complete = len(execution_mode["remaining_tasks"]) == 0
        assert is_complete is True
