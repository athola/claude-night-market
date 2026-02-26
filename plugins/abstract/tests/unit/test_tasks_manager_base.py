"""Tests for shared tasks_manager_base module.

Validates that the extracted base module provides identical behavior
to the original per-plugin tasks_manager.py files.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from abstract.tasks_manager_base import (
    AmbiguityResult,
    AmbiguityType,
    ResumeState,
    TasksManager,
    TasksManagerConfig,
    TaskState,
    detect_ambiguity,
)


@pytest.fixture
def sanctum_config():
    """Sanctum plugin config matching original tasks_manager.py."""
    return TasksManagerConfig(
        plugin_name="sanctum",
        task_prefix="SANCTUM",
        default_state_dir=".sanctum",
        default_state_file="pr-workflow-state.json",
        env_var_prefix="CLAUDE_CODE_TASK_LIST_ID",
        cross_cutting_keywords=[
            "fix all review comments",
            "address all feedback",
            "throughout the codebase",
        ],
    )


@pytest.fixture
def manager(tmp_path, sanctum_config):
    """TasksManager with file-based fallback."""
    state_file = tmp_path / ".sanctum" / "pr-workflow-state.json"
    return TasksManager(
        project_path=tmp_path,
        fallback_state_file=state_file,
        config=sanctum_config,
        use_tasks=False,
    )


class TestTasksManagerConfig:
    """Config dataclass holds plugin-specific settings."""

    @pytest.mark.unit
    def test_config_stores_plugin_identity(self, sanctum_config):
        """Given a sanctum config, plugin name and prefix are correct."""
        assert sanctum_config.plugin_name == "sanctum"
        assert sanctum_config.task_prefix == "SANCTUM"

    @pytest.mark.unit
    def test_config_defaults(self):
        """Given minimal config, thresholds default to sensible values."""
        cfg = TasksManagerConfig(
            plugin_name="test",
            task_prefix="TEST",
            default_state_dir=".test",
            default_state_file="state.json",
            env_var_prefix="TEST_VAR",
        )
        assert cfg.large_scope_token_threshold == 5000
        assert cfg.large_scope_word_threshold == 30
        assert cfg.cross_cutting_keywords == []


class TestDetectAmbiguity:
    """Ambiguity detection uses plugin-specific keywords."""

    @pytest.mark.unit
    def test_no_ambiguity_for_simple_task(self):
        """Given a simple task, no ambiguity is detected."""
        result = detect_ambiguity("Fix typo in README")
        assert not result.is_ambiguous

    @pytest.mark.unit
    def test_cross_cutting_detected_with_keywords(self):
        """Given sanctum keywords, PR patterns trigger cross-cutting."""
        result = detect_ambiguity(
            "fix all review comments in the PR",
            cross_cutting_keywords=["fix all review comments"],
        )
        assert result.is_ambiguous
        assert result.ambiguity_type == AmbiguityType.CROSS_CUTTING

    @pytest.mark.unit
    def test_no_cross_cutting_without_keywords(self):
        """Given no keywords, cross-cutting is not detected."""
        result = detect_ambiguity(
            "fix all review comments in the PR",
            cross_cutting_keywords=[],
        )
        assert not result.is_ambiguous

    @pytest.mark.unit
    def test_multiple_components(self):
        """Given many files touched, multiple components detected."""
        result = detect_ambiguity(
            "Update imports",
            context={"files_touched": ["a.py", "b.py", "c.py"]},
        )
        assert result.is_ambiguous
        assert result.ambiguity_type == AmbiguityType.MULTIPLE_COMPONENTS

    @pytest.mark.unit
    def test_large_scope_by_tokens(self):
        """Given high token count, large scope detected."""
        result = detect_ambiguity(
            "Refactor auth",
            context={"estimated_tokens": 10000},
            large_scope_token_threshold=5000,
        )
        assert result.is_ambiguous
        assert result.ambiguity_type == AmbiguityType.LARGE_SCOPE


class TestTasksManagerFileFallback:
    """File-based fallback creates tasks with plugin prefix."""

    @pytest.mark.unit
    def test_ensure_task_creates_file(self, manager):
        """Given file fallback mode, task is persisted to JSON."""
        task_id = manager.ensure_task_exists("Fix the bug")
        assert task_id == "SANCTUM-001"
        assert manager.fallback_state_file.exists()

    @pytest.mark.unit
    def test_task_prefix_matches_config(self, manager):
        """Given sanctum config, task IDs use SANCTUM prefix."""
        t1 = manager.ensure_task_exists("Task one")
        t2 = manager.ensure_task_exists("Task two")
        assert t1.startswith("SANCTUM-")
        assert t2.startswith("SANCTUM-")

    @pytest.mark.unit
    def test_get_state_empty(self, manager):
        """Given no tasks, state is empty."""
        state = manager.get_state()
        assert state.total_count == 0
        assert state.completed_tasks == []

    @pytest.mark.unit
    def test_update_task_status(self, manager):
        """Given a pending task, status can be updated to complete."""
        task_id = manager.ensure_task_exists("Do thing")
        result = manager.update_task_status(task_id, "complete")
        assert result is True

        state = manager.get_state()
        assert task_id in state.completed_tasks

    @pytest.mark.unit
    def test_detect_resume_state(self, manager):
        """Given pending tasks, resume state reports them."""
        manager.ensure_task_exists("Task A")
        manager.ensure_task_exists("Task B")

        resume = manager.detect_resume_state()
        assert resume.has_incomplete_tasks
        assert len(resume.pending_tasks) == 2

    @pytest.mark.unit
    def test_can_start_task_no_deps(self, manager):
        """Given task with no dependencies, it can start."""
        task_id = manager.ensure_task_exists("Independent task")
        assert manager.can_start_task(task_id) is True
