"""Tests for ProjectTracker task add and update operations.

Covers:
- TestAddTask
- TestUpdateTask
"""

from __future__ import annotations

from datetime import datetime, timezone

from minister.project_tracker import ProjectTracker, Task


class TestAddTask:
    """Test task addition functionality."""

    def test_add_single_task_increases_task_count(
        self, empty_tracker: ProjectTracker, minimal_task: Task
    ) -> None:
        """GIVEN empty tracker.

        WHEN single task is added
        THEN task count increases by one.
        """
        # Arrange
        initial_count = len(empty_tracker.data.tasks)

        # Act
        empty_tracker.add_task(minimal_task)

        # Assert
        assert len(empty_tracker.data.tasks) == initial_count + 1

    def test_add_task_stores_task_with_all_fields(
        self, empty_tracker: ProjectTracker
    ) -> None:
        """GIVEN tracker and task with all fields.

        WHEN task is added
        THEN all fields are stored correctly.
        """
        # Arrange
        task = Task(
            id="FULL-001",
            title="Full Featured Task",
            initiative="Test Initiative",
            phase="Phase 2",
            priority="High",
            status="In Progress",
            owner="developer",
            effort_hours=8.0,
            completion_percent=45.5,
            due_date="2025-02-01",
            created_date="2025-01-01T10:00:00",
            updated_date="2025-01-15T14:30:00",
            github_issue="https://github.com/org/repo/issues/456",
        )

        # Act
        empty_tracker.add_task(task)

        # Assert
        stored_task = empty_tracker.data.tasks[0]
        assert stored_task.id == "FULL-001"
        assert stored_task.title == "Full Featured Task"
        assert stored_task.initiative == "Test Initiative"
        assert stored_task.phase == "Phase 2"
        assert stored_task.priority == "High"
        assert stored_task.status == "In Progress"
        assert stored_task.owner == "developer"
        assert stored_task.effort_hours == 8.0
        assert stored_task.completion_percent == 45.5
        assert stored_task.due_date == "2025-02-01"
        assert stored_task.github_issue == "https://github.com/org/repo/issues/456"

    def test_add_multiple_tasks_preserves_order(
        self, empty_tracker: ProjectTracker, sample_tasks: list[Task]
    ) -> None:
        """GIVEN empty tracker and multiple tasks.

        WHEN tasks are added sequentially
        THEN tasks are stored in addition order.
        """
        # Act
        for task in sample_tasks:
            empty_tracker.add_task(task)

        # Assert
        for i, task in enumerate(sample_tasks):
            assert empty_tracker.data.tasks[i].id == task.id

    def test_add_task_persists_to_file(
        self, empty_tracker: ProjectTracker, minimal_task: Task
    ) -> None:
        """GIVEN empty tracker.

        WHEN task is added
        THEN task is persisted to data file.
        """
        # Act
        empty_tracker.add_task(minimal_task)

        # Assert
        reloaded_tracker = ProjectTracker(data_file=empty_tracker.data_file)
        assert len(reloaded_tracker.data.tasks) == 1
        assert reloaded_tracker.data.tasks[0].id == minimal_task.id


class TestUpdateTask:
    """Test task update functionality."""

    def test_update_task_status(self, populated_tracker: ProjectTracker) -> None:
        """GIVEN tracker with existing task.

        WHEN task status is updated
        THEN status changes and file is saved.
        """
        # Arrange
        task_id = populated_tracker.data.tasks[0].id

        # Act
        populated_tracker.update_task(task_id, {"status": "In Progress"})

        # Assert
        updated_task = next(t for t in populated_tracker.data.tasks if t.id == task_id)
        assert updated_task.status == "In Progress"

    def test_update_task_completion_percent(
        self, populated_tracker: ProjectTracker
    ) -> None:
        """GIVEN tracker with task.

        WHEN completion percentage is updated
        THEN value is changed correctly.
        """
        # Arrange
        task_id = populated_tracker.data.tasks[0].id

        # Act
        populated_tracker.update_task(task_id, {"completion_percent": 75.0})

        # Assert
        updated_task = next(t for t in populated_tracker.data.tasks if t.id == task_id)
        assert updated_task.completion_percent == 75.0

    def test_update_task_multiple_fields(
        self, populated_tracker: ProjectTracker
    ) -> None:
        """GIVEN tracker with task.

        WHEN multiple fields are updated
        THEN all fields are changed.
        """
        # Arrange
        task_id = populated_tracker.data.tasks[0].id
        updates = {
            "status": "Review",
            "completion_percent": 90.0,
            "github_issue": "https://github.com/org/repo/pull/789",
        }

        # Act
        populated_tracker.update_task(task_id, updates)

        # Assert
        updated_task = next(t for t in populated_tracker.data.tasks if t.id == task_id)
        assert updated_task.status == "Review"
        assert updated_task.completion_percent == 90.0
        assert updated_task.github_issue == "https://github.com/org/repo/pull/789"

    def test_update_task_sets_updated_date(
        self, populated_tracker: ProjectTracker
    ) -> None:
        """GIVEN tracker with task.

        WHEN task is updated
        THEN updated_date is set to current time.
        """
        # Arrange
        task_id = populated_tracker.data.tasks[0].id
        original_date = populated_tracker.data.tasks[0].updated_date
        before_update = datetime.now(timezone.utc)

        # Act
        populated_tracker.update_task(task_id, {"status": "Done"})

        # Assert
        updated_task = next(t for t in populated_tracker.data.tasks if t.id == task_id)
        updated_date = datetime.fromisoformat(updated_task.updated_date)
        assert updated_date >= before_update
        assert updated_task.updated_date != original_date

    def test_update_task_persists_changes(
        self, populated_tracker: ProjectTracker
    ) -> None:
        """GIVEN tracker with task.

        WHEN task is updated
        THEN changes are persisted to file.
        """
        # Arrange
        task_id = populated_tracker.data.tasks[0].id

        # Act
        populated_tracker.update_task(task_id, {"status": "Done"})

        # Assert
        reloaded_tracker = ProjectTracker(data_file=populated_tracker.data_file)
        reloaded_task = next(t for t in reloaded_tracker.data.tasks if t.id == task_id)
        assert reloaded_task.status == "Done"

    def test_update_nonexistent_task_does_nothing(
        self, populated_tracker: ProjectTracker
    ) -> None:
        """GIVEN tracker with tasks.

        WHEN update is called with nonexistent task ID
        THEN no tasks are modified.
        """
        # Arrange
        original_tasks = [t.status for t in populated_tracker.data.tasks]

        # Act
        populated_tracker.update_task("NONEXISTENT-999", {"status": "Done"})

        # Assert
        updated_tasks = [t.status for t in populated_tracker.data.tasks]
        assert original_tasks == updated_tasks
