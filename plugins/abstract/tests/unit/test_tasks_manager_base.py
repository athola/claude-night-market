"""Tests for shared tasks_manager_base module.

Validates that the extracted base module provides identical behavior
to the original per-plugin tasks_manager.py files.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from abstract.tasks_manager_base import (
    AmbiguityResult,
    AmbiguityType,
    TasksManager,
    TasksManagerConfig,
    TaskState,
    detect_ambiguity,
    get_claude_code_version,
    is_tasks_available,
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
def config() -> TasksManagerConfig:
    """Given a minimal TasksManagerConfig for testing."""
    return TasksManagerConfig(
        plugin_name="test",
        task_prefix="TEST",
        default_state_dir=".test",
        default_state_file="state.json",
        env_var_prefix="TEST_VAR",
        cross_cutting_keywords=["update everything", "all files"],
        large_scope_token_threshold=5000,
        large_scope_word_threshold=10,
    )


@pytest.fixture
def sanctum_manager(tmp_path, sanctum_config):
    """TasksManager with file-based fallback using sanctum config."""
    state_file = tmp_path / ".sanctum" / "pr-workflow-state.json"
    return TasksManager(
        project_path=tmp_path,
        fallback_state_file=state_file,
        config=sanctum_config,
        use_tasks=False,
    )


@pytest.fixture
def manager(tmp_path: Path, config: TasksManagerConfig) -> TasksManager:
    """Given a file-based TasksManager."""
    state_file = tmp_path / "state.json"
    return TasksManager(
        project_path=tmp_path,
        fallback_state_file=state_file,
        config=config,
        use_tasks=False,
    )


@pytest.fixture
def tasks_manager(tmp_path: Path, config: TasksManagerConfig) -> TasksManager:
    """Given a Tasks-mode manager with mocked task functions."""
    state_file = tmp_path / "state.json"
    mgr = TasksManager(
        project_path=tmp_path,
        fallback_state_file=state_file,
        config=config,
        use_tasks=True,
    )

    # Provide mock task functions
    _tasks: list[dict] = []
    _next_id = [1]

    def _create(description: str, dependencies: list = None) -> dict:
        task = {
            "id": str(_next_id[0]),
            "description": description,
            "status": "pending",
            "dependencies": dependencies or [],
        }
        _tasks.append(task)
        _next_id[0] += 1
        return task

    def _list() -> list[dict]:
        return list(_tasks)

    def _update(task_id: str, **kwargs) -> bool:
        for t in _tasks:
            if t["id"] == task_id:
                t.update(kwargs)
                return True
        return False

    def _get(task_id: str):
        return next((t for t in _tasks if t["id"] == task_id), None)

    mgr._task_create = _create
    mgr._task_list = _list
    mgr._task_update = _update
    mgr._task_get = _get
    return mgr


# ---------------------------------------------------------------------------
# Tests: TasksManagerConfig
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Tests: AmbiguityResult dataclass
# ---------------------------------------------------------------------------


class TestAmbiguityResult:
    """Feature: AmbiguityResult defaults."""

    @pytest.mark.unit
    def test_defaults_are_not_ambiguous(self) -> None:
        """Scenario: Default AmbiguityResult is not ambiguous."""
        result = AmbiguityResult(is_ambiguous=False)
        assert result.is_ambiguous is False
        assert result.ambiguity_type == AmbiguityType.NONE
        assert result.components == []
        assert result.message == ""


# ---------------------------------------------------------------------------
# Tests: TaskState
# ---------------------------------------------------------------------------


class TestTaskState:
    """Feature: TaskState in_progress_tasks property."""

    @pytest.mark.unit
    def test_in_progress_excludes_completed(self) -> None:
        """Scenario: in_progress_tasks does not include completed tasks."""
        state = TaskState(
            completed_tasks=["t1"],
            pending_tasks=["t1", "t2"],
        )
        assert "t1" not in state.in_progress_tasks
        assert "t2" in state.in_progress_tasks


# ---------------------------------------------------------------------------
# Tests: get_claude_code_version / is_tasks_available
# ---------------------------------------------------------------------------


class TestGetClaudeCodeVersion:
    """Feature: get_claude_code_version handles errors gracefully."""

    @pytest.mark.unit
    def test_returns_string_or_none(self) -> None:
        """Scenario: Function always returns str or None without crashing."""
        result = get_claude_code_version()
        assert result is None or isinstance(result, str)


class TestIsTasksAvailable:
    """Feature: is_tasks_available checks version requirement."""

    @pytest.mark.unit
    def test_returns_bool(self) -> None:
        """Scenario: Function always returns a boolean."""
        result = is_tasks_available()
        assert isinstance(result, bool)


# ---------------------------------------------------------------------------
# Tests: detect_ambiguity
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Tests: detect_ambiguity edge cases
# ---------------------------------------------------------------------------


class TestDetectAmbiguityEdgeCases:
    """Feature: detect_ambiguity handles edge cases."""

    @pytest.mark.unit
    def test_large_scope_by_word_count(self) -> None:
        """Scenario: Long description with no token context triggers LARGE_SCOPE."""
        # 11 words > default word threshold of 10
        description = "one two three four five six seven eight nine ten eleven"
        result = detect_ambiguity(
            description,
            large_scope_word_threshold=10,
        )
        assert result.is_ambiguous
        assert result.ambiguity_type == AmbiguityType.LARGE_SCOPE

    @pytest.mark.unit
    def test_no_ambiguity_below_word_threshold(self) -> None:
        """Scenario: Short description is not flagged as large scope."""
        description = "Short task"
        result = detect_ambiguity(description, large_scope_word_threshold=50)
        assert not result.is_ambiguous

    @pytest.mark.unit
    def test_exact_file_count_threshold_not_ambiguous(self) -> None:
        """Scenario: Exactly 2 files touched is not ambiguous (threshold is >2)."""
        result = detect_ambiguity(
            "Update imports",
            context={"files_touched": ["a.py", "b.py"]},
        )
        # _MULTI_COMPONENT_THRESHOLD = 2, condition is > 2, so 2 is not ambiguous
        assert not result.is_ambiguous

    @pytest.mark.unit
    def test_circular_dependency_not_triggered_without_uses(self) -> None:
        """Scenario: services without 'uses' keyword don't trigger circular dep."""
        result = detect_ambiguity(
            "Update authmanager",
            context={"existing_tasks": [{"description": "Update paymentmanager"}]},
        )
        # No 'uses' keyword, so no circular dependency
        assert (
            not result.is_ambiguous
            or result.ambiguity_type != AmbiguityType.CIRCULAR_DEPENDENCY
        )

    @pytest.mark.unit
    def test_cross_cutting_case_insensitive(self) -> None:
        """Scenario: Cross-cutting keyword match is case-insensitive."""
        result = detect_ambiguity(
            "UPDATE EVERYTHING in the repo",
            cross_cutting_keywords=["update everything"],
        )
        assert result.is_ambiguous
        assert result.ambiguity_type == AmbiguityType.CROSS_CUTTING

    @pytest.mark.unit
    def test_estimated_tokens_zero_skips_token_check(self) -> None:
        """Scenario: estimated_tokens=0 falls through to word count check."""
        result = detect_ambiguity(
            "short",
            context={"estimated_tokens": 0},
            large_scope_word_threshold=50,
        )
        assert not result.is_ambiguous


# ---------------------------------------------------------------------------
# Tests: TasksManager file-based fallback (sanctum config)
# ---------------------------------------------------------------------------


class TestTasksManagerFileFallback:
    """File-based fallback creates tasks with plugin prefix."""

    @pytest.mark.unit
    def test_ensure_task_creates_file(self, sanctum_manager):
        """Given file fallback mode, task is persisted to JSON."""
        task_id = sanctum_manager.ensure_task_exists("Fix the bug")
        assert task_id == "SANCTUM-001"
        assert sanctum_manager.fallback_state_file.exists()

    @pytest.mark.unit
    def test_task_prefix_matches_config(self, sanctum_manager):
        """Given sanctum config, task IDs use SANCTUM prefix."""
        t1 = sanctum_manager.ensure_task_exists("Task one")
        t2 = sanctum_manager.ensure_task_exists("Task two")
        assert t1.startswith("SANCTUM-")
        assert t2.startswith("SANCTUM-")

    @pytest.mark.unit
    def test_get_state_empty(self, sanctum_manager):
        """Given no tasks, state is empty."""
        state = sanctum_manager.get_state()
        assert state.total_count == 0
        assert state.completed_tasks == []

    @pytest.mark.unit
    def test_update_task_status(self, sanctum_manager):
        """Given a pending task, status can be updated to complete."""
        task_id = sanctum_manager.ensure_task_exists("Do thing")
        result = sanctum_manager.update_task_status(task_id, "complete")
        assert result is True

        state = sanctum_manager.get_state()
        assert task_id in state.completed_tasks

    @pytest.mark.unit
    def test_detect_resume_state(self, sanctum_manager):
        """Given pending tasks, resume state reports them."""
        sanctum_manager.ensure_task_exists("Task A")
        sanctum_manager.ensure_task_exists("Task B")

        resume = sanctum_manager.detect_resume_state()
        assert resume.has_incomplete_tasks
        assert len(resume.pending_tasks) == 2

    @pytest.mark.unit
    def test_can_start_task_no_deps(self, sanctum_manager):
        """Given task with no dependencies, it can start."""
        task_id = sanctum_manager.ensure_task_exists("Independent task")
        assert sanctum_manager.can_start_task(task_id) is True


# ---------------------------------------------------------------------------
# Tests: TasksManager file-based (extended)
# ---------------------------------------------------------------------------


class TestTasksManagerFileBasedExtended:
    """Feature: TasksManager file-based fallback extended tests."""

    @pytest.mark.unit
    def test_pending_count_property(self, manager: TasksManager) -> None:
        """Scenario: pending_count reflects plan tasks count."""
        manager.load_plan(["Task A", "Task B"])
        assert manager.pending_count == 2

    @pytest.mark.unit
    def test_created_count_property_file_mode(self, manager: TasksManager) -> None:
        """Scenario: created_count is 0 in file mode (no task_list)."""
        assert manager.created_count == 0

    @pytest.mark.unit
    def test_load_plan_copies_list(self, manager: TasksManager) -> None:
        """Scenario: load_plan makes a copy so mutations don't affect manager."""
        tasks = ["Task A", "Task B"]
        manager.load_plan(tasks)
        tasks.append("Task C")
        assert manager.pending_count == 2

    @pytest.mark.unit
    def test_ensure_task_with_dependencies(self, manager: TasksManager) -> None:
        """Scenario: Dependencies are stored in the state file."""
        t1 = manager.ensure_task_exists("First task")
        t2 = manager.ensure_task_exists("Second task", dependencies=[str(t1)])
        assert t2 == "TEST-002"

    @pytest.mark.unit
    def test_update_nonexistent_task_returns_false(self, manager: TasksManager) -> None:
        """Scenario: Updating a task that doesn't exist returns False."""
        manager.ensure_task_exists("Some task")
        result = manager.update_task_status("NONEXISTENT-999", "complete")
        assert result is False

    @pytest.mark.unit
    def test_update_task_status_no_state_file(
        self, tmp_path: Path, config: TasksManagerConfig
    ) -> None:
        """Scenario: Updating without a state file returns False."""
        state_file = tmp_path / "nonexistent.json"
        mgr = TasksManager(
            project_path=tmp_path,
            fallback_state_file=state_file,
            config=config,
            use_tasks=False,
        )
        result = mgr.update_task_status("TEST-001", "complete")
        assert result is False

    @pytest.mark.unit
    def test_can_start_task_with_completed_dependency(
        self, manager: TasksManager
    ) -> None:
        """Scenario: Task can start when its dependency is complete."""
        t1 = manager.ensure_task_exists("Dep task")
        t2 = manager.ensure_task_exists("Blocked task", dependencies=[str(t1)])
        manager.update_task_status(str(t1), "complete")
        assert manager.can_start_task(str(t2)) is True

    @pytest.mark.unit
    def test_can_start_task_blocked_by_pending_dependency(
        self, manager: TasksManager
    ) -> None:
        """Scenario: Task cannot start when dependency is still pending."""
        t1 = manager.ensure_task_exists("Dep task")
        t2 = manager.ensure_task_exists("Blocked task", dependencies=[str(t1)])
        assert manager.can_start_task(str(t2)) is False

    @pytest.mark.unit
    def test_can_start_nonexistent_task_returns_true(
        self, manager: TasksManager
    ) -> None:
        """Scenario: can_start_task for unknown task_id returns True."""
        assert manager.can_start_task("NONEXISTENT-999") is True

    @pytest.mark.unit
    def test_can_start_task_no_state_file(
        self, tmp_path: Path, config: TasksManagerConfig
    ) -> None:
        """Scenario: can_start_task with no state file returns True."""
        state_file = tmp_path / "missing.json"
        mgr = TasksManager(
            project_path=tmp_path,
            fallback_state_file=state_file,
            config=config,
            use_tasks=False,
        )
        assert mgr.can_start_task("TEST-001") is True

    @pytest.mark.unit
    def test_detect_resume_no_state_file(
        self, tmp_path: Path, config: TasksManagerConfig
    ) -> None:
        """Scenario: detect_resume_state with no state file returns empty state."""
        state_file = tmp_path / "missing.json"
        mgr = TasksManager(
            project_path=tmp_path,
            fallback_state_file=state_file,
            config=config,
            use_tasks=False,
        )
        resume = mgr.detect_resume_state()
        assert not resume.has_incomplete_tasks

    @pytest.mark.unit
    def test_detect_resume_in_progress_tasks(self, manager: TasksManager) -> None:
        """Scenario: In-progress tasks appear in resume state."""
        t1 = manager.ensure_task_exists("Task A")
        manager.update_task_status(str(t1), "in_progress")
        resume = manager.detect_resume_state()
        assert resume.has_incomplete_tasks
        assert resume.next_task_id == str(t1)

    @pytest.mark.unit
    def test_detect_resume_all_complete(self, manager: TasksManager) -> None:
        """Scenario: All complete tasks produce empty resume state."""
        t1 = manager.ensure_task_exists("Task A")
        manager.update_task_status(str(t1), "complete")
        resume = manager.detect_resume_state()
        assert not resume.has_incomplete_tasks

    @pytest.mark.unit
    def test_prompt_for_resume_no_incomplete(self, manager: TasksManager) -> None:
        """Scenario: prompt_for_resume returns False when no incomplete tasks."""
        result = manager.prompt_for_resume()
        assert result is False

    @pytest.mark.unit
    def test_prompt_for_resume_yes_response(self, manager: TasksManager) -> None:
        """Scenario: User responding 'y' to resume prompt returns True."""
        manager.ensure_task_exists("Task A")

        # Provide 'y' answer via ask_user_fn
        def answer_yes(prompt: str) -> str:
            return "y"

        manager._ask_user = answer_yes
        result = manager.prompt_for_resume()
        assert result is True

    @pytest.mark.unit
    def test_prompt_for_resume_no_response(self, manager: TasksManager) -> None:
        """Scenario: User responding 'n' to resume prompt returns False."""
        manager.ensure_task_exists("Task A")

        def answer_no(prompt: str) -> str:
            return "n"

        manager._ask_user = answer_no
        result = manager.prompt_for_resume()
        assert result is False

    @pytest.mark.unit
    def test_get_state_with_tasks(self, manager: TasksManager) -> None:
        """Scenario: get_state reflects created and completed tasks."""
        t1 = manager.ensure_task_exists("Task A")
        t2 = manager.ensure_task_exists("Task B")
        manager.update_task_status(str(t1), "complete")

        state = manager.get_state()
        assert state.total_count == 2
        assert str(t1) in state.completed_tasks
        assert str(t2) in state.pending_tasks

    @pytest.mark.unit
    def test_get_state_no_state_file(
        self, tmp_path: Path, config: TasksManagerConfig
    ) -> None:
        """Scenario: get_state with no state file returns empty TaskState."""
        state_file = tmp_path / "missing.json"
        mgr = TasksManager(
            project_path=tmp_path,
            fallback_state_file=state_file,
            config=config,
            use_tasks=False,
        )
        state = mgr.get_state()
        assert state.total_count == 0

    @pytest.mark.unit
    def test_update_task_status_extra_kwargs(self, manager: TasksManager) -> None:
        """Scenario: update_task_status stores extra kwargs in state."""
        import json  # noqa: PLC0415

        t1 = manager.ensure_task_exists("Task")
        manager.update_task_status(str(t1), "in_progress", note="working on it")
        state_data = json.loads(manager.fallback_state_file.read_text())
        assert state_data["tasks"][str(t1)]["note"] == "working on it"

    @pytest.mark.unit
    def test_update_complete_updates_metrics(self, manager: TasksManager) -> None:
        """Scenario: Completing a task updates the tasks_complete metric."""
        import json  # noqa: PLC0415

        t1 = manager.ensure_task_exists("Task A")
        manager.ensure_task_exists("Task B")
        manager.update_task_status(str(t1), "complete")
        state_data = json.loads(manager.fallback_state_file.read_text())
        assert state_data["metrics"]["tasks_complete"] == 1


# ---------------------------------------------------------------------------
# Tests: TasksManager Tasks-mode
# ---------------------------------------------------------------------------


class TestTasksManagerTasksMode:
    """Feature: TasksManager Claude Code Tasks system mode."""

    @pytest.mark.unit
    def test_ensure_task_creates_in_tasks_system(
        self, tasks_manager: TasksManager
    ) -> None:
        """Scenario: Task is created via _task_create in Tasks mode."""
        task_id = tasks_manager.ensure_task_exists("Fix the bug")
        assert task_id is not None
        assert isinstance(task_id, str)

    @pytest.mark.unit
    def test_ensure_task_returns_existing_task(
        self, tasks_manager: TasksManager
    ) -> None:
        """Scenario: Creating the same task twice returns the existing ID."""
        t1 = tasks_manager.ensure_task_exists("Unique task")
        t2 = tasks_manager.ensure_task_exists("Unique task")
        assert t1 == t2

    @pytest.mark.unit
    def test_get_state_tasks_mode(self, tasks_manager: TasksManager) -> None:
        """Scenario: get_state in Tasks mode reads from _task_list."""
        tasks_manager.ensure_task_exists("Task A")
        state = tasks_manager.get_state()
        assert state.total_count == 1

    @pytest.mark.unit
    def test_created_count_property(self, tasks_manager: TasksManager) -> None:
        """Scenario: created_count reflects number of tasks in system."""
        tasks_manager.ensure_task_exists("Task A")
        tasks_manager.ensure_task_exists("Task B")
        assert tasks_manager.created_count == 2

    @pytest.mark.unit
    def test_get_state_with_complete_task(self, tasks_manager: TasksManager) -> None:
        """Scenario: Completed tasks appear in completed list."""
        task_id = tasks_manager.ensure_task_exists("Task")
        tasks_manager.update_task_status(task_id, "complete")
        state = tasks_manager.get_state()
        assert task_id in state.completed_tasks

    @pytest.mark.unit
    def test_can_start_task_tasks_mode(self, tasks_manager: TasksManager) -> None:
        """Scenario: Task with no dependencies can start in Tasks mode."""
        task_id = tasks_manager.ensure_task_exists("Independent")
        assert tasks_manager.can_start_task(task_id) is True

    @pytest.mark.unit
    def test_detect_resume_tasks_mode(self, tasks_manager: TasksManager) -> None:
        """Scenario: detect_resume_state reads from _task_list in Tasks mode."""
        tasks_manager.ensure_task_exists("Task A")
        resume = tasks_manager.detect_resume_state()
        assert resume.has_incomplete_tasks

    @pytest.mark.unit
    def test_ensure_task_splits_on_user_choice_2(
        self, tasks_manager: TasksManager
    ) -> None:
        """Scenario: User choice '2' splits an ambiguous task into subtasks."""

        def choose_split(prompt: str) -> str:
            return "2"

        tasks_manager._ask_user = choose_split

        # Create a task with many file touches to trigger ambiguity
        class FakeList:
            _inner = []

            def __call__(self):
                return self._inner

        fake_list = FakeList()
        tasks_manager._task_list = fake_list

        # Directly test _create_subtasks
        ambiguity = AmbiguityResult(
            is_ambiguous=True,
            ambiguity_type=AmbiguityType.MULTIPLE_COMPONENTS,
            components=["component_a", "component_b"],
        )
        task_ids = tasks_manager._create_subtasks("Update components", ambiguity, [])
        assert len(task_ids) == 2

    @pytest.mark.unit
    def test_create_subtasks_no_components_creates_parts(
        self, tasks_manager: TasksManager
    ) -> None:
        """Scenario: Ambiguity with no components creates Part 1 / Part 2."""
        ambiguity = AmbiguityResult(
            is_ambiguous=True,
            ambiguity_type=AmbiguityType.CROSS_CUTTING,
            components=[],
        )
        task_ids = tasks_manager._create_subtasks("Cross-cutting change", ambiguity, [])
        assert len(task_ids) == 2

    @pytest.mark.unit
    def test_update_task_status_tasks_mode(self, tasks_manager: TasksManager) -> None:
        """Scenario: update_task_status calls _task_update in Tasks mode."""
        task_id = tasks_manager.ensure_task_exists("Task")
        result = tasks_manager.update_task_status(task_id, "complete")
        assert result is True


# ---------------------------------------------------------------------------
# Tests: Default ask_user
# ---------------------------------------------------------------------------


class TestDefaultAskUser:
    """Feature: Default ask_user_fn handles EOF gracefully."""

    @pytest.mark.unit
    def test_default_ask_user_on_eof(
        self, tmp_path: Path, config: TasksManagerConfig
    ) -> None:
        """Scenario: EOFError from input() returns empty string."""
        state_file = tmp_path / "state.json"
        mgr = TasksManager(
            project_path=tmp_path,
            fallback_state_file=state_file,
            config=config,
            use_tasks=False,
        )

        import io  # noqa: PLC0415
        import sys  # noqa: PLC0415

        old_stdin = sys.stdin
        sys.stdin = io.StringIO("")  # EOF immediately
        try:
            result = mgr._default_ask_user("Enter something: ")
            assert result == ""
        finally:
            sys.stdin = old_stdin
