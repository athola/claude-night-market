"""BDD-style tests for Claude Code Tasks integration.

Tests the lazy task creation pattern with user prompts on ambiguity.
Following TDD: Write failing tests first, then implement.
"""

import json
from unittest.mock import MagicMock, patch

import pytest

# Import from implementation module
from tasks_manager import (
    AmbiguityResult,
    AmbiguityType,
    TasksManager,
    detect_ambiguity,
    is_tasks_available,
)


class TestTasksAvailabilityDetection:
    """Feature: Detect whether Claude Code Tasks system is available."""

    @pytest.mark.bdd
    def test_tasks_available_when_claude_code_2116_or_higher(self):
        """Given Claude Code 2.1.16+, when checking availability, then Tasks is available."""
        # Arrange
        mock_version = "2.1.17"

        # Act
        with patch("tasks_manager.get_claude_code_version", return_value=mock_version):
            result = is_tasks_available()

        # Assert
        assert result is True

    @pytest.mark.bdd
    def test_tasks_not_available_when_older_version(self):
        """Given Claude Code < 2.1.16, when checking availability, then Tasks is not available."""
        # Arrange
        mock_version = "2.1.15"

        # Act
        with patch("tasks_manager.get_claude_code_version", return_value=mock_version):
            result = is_tasks_available()

        # Assert
        assert result is False

    @pytest.mark.bdd
    def test_tasks_not_available_when_not_in_claude_code(self):
        """Given not running in Claude Code, when checking availability, then Tasks is not available."""
        # Arrange - version returns None when not in Claude Code

        # Act
        with patch("tasks_manager.get_claude_code_version", return_value=None):
            result = is_tasks_available()

        # Assert
        assert result is False


class TestLazyTaskCreation:
    """Feature: Create tasks lazily as execution reaches them."""

    @pytest.fixture
    def tasks_manager(self, tmp_path):
        """Create TasksManager with mocked Claude Code tools."""
        manager = TasksManager(
            project_path=tmp_path,
            fallback_state_file=tmp_path / ".attune" / "execution-state.json",
            use_tasks=True,  # Enable Tasks mode for testing
        )
        # Mock the Claude Code task tools
        manager._task_create = MagicMock(
            return_value={"id": "task-001", "status": "pending"}
        )
        manager._task_list = MagicMock(return_value=[])
        manager._task_update = MagicMock(return_value=True)
        return manager

    @pytest.mark.bdd
    def test_task_created_when_execution_reaches_it(self, tasks_manager):
        """Given a task in the plan, when execution reaches it, then create the task."""
        # Arrange
        task_description = "Implement user authentication"

        # Act
        task_id = tasks_manager.ensure_task_exists(task_description)

        # Assert
        assert task_id == "task-001"
        tasks_manager._task_create.assert_called_once()

    @pytest.mark.bdd
    def test_existing_task_reused_not_recreated(self, tasks_manager):
        """Given a task already exists, when execution reaches it again, then reuse existing."""
        # Arrange
        task_description = "Implement user authentication"
        tasks_manager._task_list.return_value = [
            {
                "id": "task-existing",
                "description": "Implement user authentication",
                "status": "pending",
            }
        ]

        # Act
        task_id = tasks_manager.ensure_task_exists(task_description)

        # Assert
        assert task_id == "task-existing"
        tasks_manager._task_create.assert_not_called()

    @pytest.mark.bdd
    def test_tasks_not_created_upfront(self, tasks_manager):
        """Given a plan with 10 tasks, when starting execution, then no tasks created yet."""
        # Arrange
        plan_tasks = [f"Task {i}" for i in range(10)]

        # Act
        tasks_manager.load_plan(plan_tasks)

        # Assert
        tasks_manager._task_create.assert_not_called()
        assert tasks_manager.pending_count == 10
        assert tasks_manager.created_count == 0


class TestAmbiguityDetection:
    """Feature: Detect when task boundaries are ambiguous and need user input."""

    @pytest.mark.bdd
    def test_ambiguity_detected_for_multiple_components(self):
        """Given task touches multiple components, when checking ambiguity, then return True."""
        # Arrange
        task_description = "Implement authentication in auth service, user model, and session middleware"
        context = {
            "files_touched": ["src/auth/", "src/models/user.py", "src/middleware/"]
        }

        # Act
        result = detect_ambiguity(task_description, context)

        # Assert
        assert result.is_ambiguous is True
        assert result.ambiguity_type == AmbiguityType.MULTIPLE_COMPONENTS
        assert len(result.components) == 3

    @pytest.mark.bdd
    def test_ambiguity_detected_for_cross_cutting_concerns(self):
        """Given task involves cross-cutting concern, when checking ambiguity, then return True."""
        # Arrange
        task_description = "Add logging throughout the codebase"
        context = {}

        # Act
        result = detect_ambiguity(task_description, context)

        # Assert
        assert result.is_ambiguous is True
        assert result.ambiguity_type == AmbiguityType.CROSS_CUTTING

    @pytest.mark.bdd
    def test_ambiguity_detected_for_large_scope(self):
        """Given task has large estimated scope, when checking ambiguity, then return True."""
        # Arrange - use description without cross-cutting keywords
        task_description = "Refactor the entire payment processing module including gateway integration, transaction processing, receipt generation, refund logic, and database persistence"
        context = {"estimated_tokens": 8000}

        # Act
        result = detect_ambiguity(task_description, context)

        # Assert
        assert result.is_ambiguous is True
        assert result.ambiguity_type == AmbiguityType.LARGE_SCOPE

    @pytest.mark.bdd
    def test_no_ambiguity_for_simple_task(self):
        """Given simple focused task, when checking ambiguity, then return False."""
        # Arrange - simple task with no cross-cutting keywords
        task_description = "Add email format check to User model"
        context = {"files_touched": ["src/models/user.py"]}

        # Act
        result = detect_ambiguity(task_description, context)

        # Assert
        assert result.is_ambiguous is False

    @pytest.mark.bdd
    def test_ambiguity_detected_for_circular_dependency_risk(self):
        """Given task has circular dependency risk with existing tasks, then return True."""
        # Arrange
        task_description = "Implement AuthService that uses UserService"
        existing_tasks = [
            {
                "id": "task-001",
                "description": "Implement UserService that uses AuthService",
            }
        ]
        context = {"existing_tasks": existing_tasks}

        # Act
        result = detect_ambiguity(task_description, context)

        # Assert
        assert result.is_ambiguous is True
        assert result.ambiguity_type == AmbiguityType.CIRCULAR_DEPENDENCY


class TestUserPromptOnAmbiguity:
    """Feature: Prompt user for input when task boundaries are ambiguous."""

    @pytest.fixture
    def tasks_manager_with_prompt(self, tmp_path):
        """Create TasksManager with mocked user prompt."""
        manager = TasksManager(
            project_path=tmp_path,
            fallback_state_file=tmp_path / ".attune" / "execution-state.json",
            use_tasks=True,  # Enable Tasks mode for testing
        )
        manager._task_create = MagicMock(
            side_effect=lambda desc, **kw: {
                "id": f"task-{hash(desc) % 1000:03d}",
                "status": "pending",
            }
        )
        manager._task_list = MagicMock(return_value=[])
        manager._ask_user = MagicMock()
        return manager

    @pytest.mark.bdd
    def test_user_prompted_when_ambiguity_detected(self, tasks_manager_with_prompt):
        """Given ambiguous task, when creating task, then prompt user for decision."""
        # Arrange - use context with multiple components to trigger ambiguity
        task_description = "Implement authentication feature"
        # Provide context that triggers MULTIPLE_COMPONENTS ambiguity
        tasks_manager_with_prompt._task_list.return_value = []

        # Override detect_ambiguity to return ambiguous for this test
        with patch("tasks_manager.detect_ambiguity") as mock_detect:
            mock_detect.return_value = AmbiguityResult(
                is_ambiguous=True,
                ambiguity_type=AmbiguityType.MULTIPLE_COMPONENTS,
                components=["src/auth/", "src/models/", "src/middleware/"],
                message="Task touches 3 components",
            )
            tasks_manager_with_prompt._ask_user.return_value = (
                "1"  # Keep as single task
            )

            # Act
            tasks_manager_with_prompt.ensure_task_exists(task_description)

        # Assert
        tasks_manager_with_prompt._ask_user.assert_called_once()
        call_args = tasks_manager_with_prompt._ask_user.call_args[0][0]
        assert "Options:" in call_args or "options" in call_args.lower()

    @pytest.mark.bdd
    def test_user_choice_split_creates_multiple_tasks(self, tasks_manager_with_prompt):
        """Given user chooses to split, when creating task, then create subtasks."""
        # Arrange
        task_description = "Implement authentication feature"

        # Override detect_ambiguity to return ambiguous with components
        with patch("tasks_manager.detect_ambiguity") as mock_detect:
            mock_detect.return_value = AmbiguityResult(
                is_ambiguous=True,
                ambiguity_type=AmbiguityType.MULTIPLE_COMPONENTS,
                components=["src/auth/", "src/models/", "src/middleware/"],
                message="Task touches 3 components",
            )
            tasks_manager_with_prompt._ask_user.return_value = (
                "2"  # Split into subtasks
            )

            # Act
            task_ids = tasks_manager_with_prompt.ensure_task_exists(task_description)

        # Assert
        assert isinstance(task_ids, list)
        assert len(task_ids) >= 2  # At least 2 subtasks created

    @pytest.mark.bdd
    def test_user_choice_single_creates_one_task(self, tasks_manager_with_prompt):
        """Given user chooses single task, when creating task, then create one task."""
        # Arrange - non-ambiguous task (no prompt needed)
        task_description = "Add email field to User model"
        tasks_manager_with_prompt._ask_user.return_value = (
            "1"  # Would keep as single if asked
        )

        # Act
        task_id = tasks_manager_with_prompt.ensure_task_exists(task_description)

        # Assert
        assert isinstance(task_id, str)
        assert tasks_manager_with_prompt._task_create.call_count == 1

    @pytest.mark.bdd
    def test_default_behavior_when_user_no_response(self, tasks_manager_with_prompt):
        """Given user provides no response, when creating task, then use default (single)."""
        # Arrange - non-ambiguous task
        task_description = "Update database schema"
        tasks_manager_with_prompt._ask_user.return_value = ""  # No response

        # Act
        task_id = tasks_manager_with_prompt.ensure_task_exists(task_description)

        # Assert
        assert isinstance(task_id, str)  # Single task created (default)


class TestDualModeOperation:
    """Feature: Support both Tasks system and file-based fallback."""

    @pytest.fixture
    def fallback_state_file(self, tmp_path):
        """Create path for fallback state file."""
        state_dir = tmp_path / ".attune"
        state_dir.mkdir(parents=True)
        return state_dir / "execution-state.json"

    @pytest.mark.bdd
    def test_uses_tasks_when_available(self, tmp_path, fallback_state_file):
        """Given Tasks system available, when managing state, then use Tasks."""
        # Arrange
        manager = TasksManager(
            project_path=tmp_path,
            fallback_state_file=fallback_state_file,
            use_tasks=True,  # Explicitly enable Tasks mode
        )
        manager._task_create = MagicMock(return_value={"id": "task-001"})
        manager._task_list = MagicMock(return_value=[])

        # Act
        manager.ensure_task_exists("Test task")

        # Assert
        manager._task_create.assert_called_once()
        assert not fallback_state_file.exists()

    @pytest.mark.bdd
    def test_uses_file_fallback_when_tasks_unavailable(
        self, tmp_path, fallback_state_file
    ):
        """Given Tasks system unavailable, when managing state, then use file."""
        # Arrange
        manager = TasksManager(
            project_path=tmp_path,
            fallback_state_file=fallback_state_file,
            use_tasks=False,  # Explicitly disable Tasks mode
        )

        # Act
        manager.ensure_task_exists("Test task")

        # Assert
        assert fallback_state_file.exists()
        state = json.loads(fallback_state_file.read_text())
        assert "tasks" in state
        assert len(state["tasks"]) == 1

    @pytest.mark.bdd
    def test_file_state_compatible_with_existing_format(
        self, tmp_path, fallback_state_file
    ):
        """Given existing execution-state.json, when loading, then parse correctly."""
        # Arrange
        existing_state = {
            "tasks": {
                "TASK-001": {
                    "status": "complete",
                    "completed_at": "2026-01-23T10:00:00Z",
                },
                "TASK-002": {
                    "status": "in_progress",
                    "started_at": "2026-01-23T11:00:00Z",
                },
            },
            "metrics": {"tasks_complete": 1, "tasks_total": 2},
        }
        fallback_state_file.write_text(json.dumps(existing_state))

        manager = TasksManager(
            project_path=tmp_path,
            fallback_state_file=fallback_state_file,
            use_tasks=False,  # Explicitly disable Tasks mode
        )

        # Act
        state = manager.get_state()

        # Assert
        assert state.completed_count == 1
        assert state.total_count == 2
        assert "TASK-001" in state.completed_tasks


class TestResumeDetection:
    """Feature: Detect and resume from previous execution state."""

    @pytest.fixture
    def manager_with_existing_tasks(self, tmp_path):
        """Create manager with existing tasks."""
        manager = TasksManager(
            project_path=tmp_path,
            fallback_state_file=tmp_path / ".attune" / "execution-state.json",
            use_tasks=True,  # Enable Tasks mode for testing
        )
        manager._task_list = MagicMock(
            return_value=[
                {
                    "id": "task-001",
                    "description": "Setup database",
                    "status": "complete",
                },
                {
                    "id": "task-002",
                    "description": "Create models",
                    "status": "in_progress",
                },
                {
                    "id": "task-003",
                    "description": "Add API endpoints",
                    "status": "pending",
                },
            ]
        )
        return manager

    @pytest.mark.bdd
    def test_resume_detects_incomplete_tasks(self, manager_with_existing_tasks):
        """Given previous execution with incomplete tasks, when resuming, then find them."""
        # Act
        resume_state = manager_with_existing_tasks.detect_resume_state()

        # Assert
        assert resume_state.has_incomplete_tasks is True
        assert resume_state.next_task_id == "task-002"  # In-progress task
        assert len(resume_state.pending_tasks) == 1

    @pytest.mark.bdd
    def test_resume_preserves_completed_tasks(self, manager_with_existing_tasks):
        """Given previous execution, when resuming, then preserve completed tasks."""
        # Act
        resume_state = manager_with_existing_tasks.detect_resume_state()

        # Assert
        assert "task-001" in resume_state.completed_tasks
        assert resume_state.completed_count == 1

    @pytest.mark.bdd
    def test_resume_asks_user_to_continue(self, manager_with_existing_tasks):
        """Given incomplete execution, when detecting resume, then ask user."""
        # Arrange
        manager_with_existing_tasks._ask_user = MagicMock(return_value="y")

        # Act
        should_resume = manager_with_existing_tasks.prompt_for_resume()

        # Assert
        manager_with_existing_tasks._ask_user.assert_called_once()
        assert "resume" in manager_with_existing_tasks._ask_user.call_args[0][0].lower()
        assert should_resume is True


class TestDependencyTracking:
    """Feature: Track and enforce task dependencies."""

    @pytest.fixture
    def manager_with_dependencies(self, tmp_path):
        """Create manager with task dependencies."""
        manager = TasksManager(
            project_path=tmp_path,
            fallback_state_file=tmp_path / ".attune" / "execution-state.json",
            use_tasks=True,  # Enable Tasks mode for testing
        )
        manager._task_create = MagicMock(
            side_effect=lambda desc, **kw: {"id": f"task-{hash(desc) % 1000:03d}"}
        )
        manager._task_list = MagicMock(return_value=[])
        manager._task_update = MagicMock(return_value=True)
        return manager

    @pytest.mark.bdd
    def test_task_created_with_dependencies(self, manager_with_dependencies):
        """Given task with dependencies, when creating, then include dependencies."""
        # Arrange
        task_description = "Implement API endpoints"
        dependencies = ["task-001", "task-002"]  # Models and DB must complete first

        # Act
        manager_with_dependencies.ensure_task_exists(
            task_description,
            dependencies=dependencies,
        )

        # Assert
        call_kwargs = manager_with_dependencies._task_create.call_args[1]
        assert "dependencies" in call_kwargs
        assert call_kwargs["dependencies"] == dependencies

    @pytest.mark.bdd
    def test_blocked_task_cannot_start(self, manager_with_dependencies):
        """Given task with unmet dependencies, when trying to start, then block."""
        # Arrange
        manager_with_dependencies._task_list.return_value = [
            {"id": "task-001", "description": "Setup database", "status": "pending"},
            {
                "id": "task-002",
                "description": "Create models",
                "status": "pending",
                "dependencies": ["task-001"],
            },
        ]

        # Act
        can_start = manager_with_dependencies.can_start_task("task-002")

        # Assert
        assert can_start is False

    @pytest.mark.bdd
    def test_task_can_start_when_dependencies_met(self, manager_with_dependencies):
        """Given task with met dependencies, when checking, then allow start."""
        # Arrange
        manager_with_dependencies._task_list.return_value = [
            {"id": "task-001", "description": "Setup database", "status": "complete"},
            {
                "id": "task-002",
                "description": "Create models",
                "status": "pending",
                "dependencies": ["task-001"],
            },
        ]

        # Act
        can_start = manager_with_dependencies.can_start_task("task-002")

        # Assert
        assert can_start is True
