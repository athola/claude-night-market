"""Tests for ProjectTracker query and metrics calculation.

Covers:
- TestGetTasksByInitiative
- TestCalculateInitiativeMetrics
- TestCalculateOverallMetrics
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from minister.project_tracker import ProjectTracker, Task


class TestGetTasksByInitiative:
    """Test task filtering by initiative."""

    def test_get_tasks_for_existing_initiative_returns_matching_tasks(
        self, populated_tracker: ProjectTracker
    ) -> None:
        """GIVEN tracker with tasks across initiatives.

        WHEN filtering by specific initiative
        THEN only tasks from that initiative are returned.
        """
        # Act
        tasks = populated_tracker.get_tasks_by_initiative("GitHub Projects Hygiene")

        # Assert
        assert len(tasks) == 2
        assert all(t.initiative == "GitHub Projects Hygiene" for t in tasks)

    def test_get_tasks_for_initiative_with_no_tasks_returns_empty_list(
        self, populated_tracker: ProjectTracker
    ) -> None:
        """GIVEN tracker with tasks.

        WHEN filtering by initiative with no tasks
        THEN empty list is returned.
        """
        # Act
        tasks = populated_tracker.get_tasks_by_initiative("Nonexistent Initiative")

        # Assert
        assert tasks == []

    def test_get_tasks_from_empty_tracker_returns_empty_list(
        self, empty_tracker: ProjectTracker
    ) -> None:
        """GIVEN empty tracker.

        WHEN filtering by any initiative
        THEN empty list is returned.
        """
        # Act
        tasks = empty_tracker.get_tasks_by_initiative("Any Initiative")

        # Assert
        assert tasks == []

    def test_get_tasks_preserves_task_order(
        self, populated_tracker: ProjectTracker
    ) -> None:
        """GIVEN tracker with multiple tasks in same initiative.

        WHEN filtering by initiative
        THEN tasks are returned in original order.
        """
        # Act
        tasks = populated_tracker.get_tasks_by_initiative("Docs & Enablement")

        # Assert
        assert len(tasks) == 2
        assert tasks[0].id == "DOC-001"
        assert tasks[1].id == "DOC-002"


class TestCalculateInitiativeMetrics:
    """Test initiative-level metrics calculation."""

    def test_calculate_metrics_for_empty_task_list(
        self, empty_tracker: ProjectTracker
    ) -> None:
        """GIVEN empty task list.

        WHEN metrics are calculated
        THEN all metrics are zero.
        """
        # Act
        metrics = empty_tracker._calculate_initiative_metrics([])

        # Assert
        assert metrics["total_tasks"] == 0
        assert metrics["completed_tasks"] == 0
        assert metrics["in_progress_tasks"] == 0
        assert metrics["total_effort"] == 0
        assert metrics["completed_effort"] == 0
        assert metrics["completion_percentage"] == 0
        assert metrics["average_task_completion"] == 0

    def test_calculate_metrics_for_single_completed_task(
        self, empty_tracker: ProjectTracker, completed_task: Task
    ) -> None:
        """GIVEN single completed task.

        WHEN metrics are calculated
        THEN completion is 100%.
        """
        # Act
        metrics = empty_tracker._calculate_initiative_metrics([completed_task])

        # Assert
        assert metrics["total_tasks"] == 1
        assert metrics["completed_tasks"] == 1
        assert metrics["in_progress_tasks"] == 0
        assert metrics["total_effort"] == 4.0
        assert metrics["completed_effort"] == 4.0
        assert metrics["completion_percentage"] == 100.0
        assert metrics["average_task_completion"] == 100.0

    def test_calculate_metrics_for_mixed_status_tasks(
        self, empty_tracker: ProjectTracker, single_initiative_tasks: list[Task]
    ) -> None:
        """GIVEN tasks with different statuses.

        WHEN metrics are calculated
        THEN metrics reflect mixed completion.
        """
        # Act
        metrics = empty_tracker._calculate_initiative_metrics(single_initiative_tasks)

        # Assert
        assert metrics["total_tasks"] == 3
        assert metrics["completed_tasks"] == 1
        assert metrics["in_progress_tasks"] == 1
        assert metrics["total_effort"] == 10.0  # 5 + 3 + 2
        assert metrics["completed_effort"] == 5.0
        assert metrics["completion_percentage"] == 33.3  # 1/3
        assert metrics["average_task_completion"] == 50.0  # (100 + 50 + 0) / 3

    def test_calculate_metrics_rounds_percentages_to_one_decimal(
        self, empty_tracker: ProjectTracker
    ) -> None:
        """GIVEN tasks that produce non-round percentages.

        WHEN metrics are calculated
        THEN percentages are rounded to one decimal place.
        """
        # Arrange
        tasks = [
            Task(
                id=f"TSK-{i}",
                title=f"Task {i}",
                initiative="Test",
                phase="Phase 1",
                priority="Medium",
                status="Done" if i < 2 else "To Do",
                owner="tester",
                effort_hours=1.0,
                completion_percent=100.0 if i < 2 else 0.0,
                due_date="2025-01-15",
                created_date="2025-01-01T10:00:00",
                updated_date="2025-01-01T10:00:00",
            )
            for i in range(7)
        ]

        # Act
        metrics = empty_tracker._calculate_initiative_metrics(tasks)

        # Assert - 2/7 = 28.571...
        assert metrics["completion_percentage"] == 28.6
        assert isinstance(metrics["completion_percentage"], float)

    def test_calculate_metrics_counts_only_done_tasks_as_completed(
        self, empty_tracker: ProjectTracker
    ) -> None:
        """GIVEN tasks with various statuses including Review.

        WHEN metrics are calculated
        THEN only 'Done' status counts as completed.
        """
        # Arrange
        tasks = [
            Task(
                id="TSK-1",
                title="Task 1",
                initiative="Test",
                phase="Phase 1",
                priority="Medium",
                status="Done",
                owner="tester",
                effort_hours=2.0,
                completion_percent=100.0,
                due_date="2025-01-15",
                created_date="2025-01-01T10:00:00",
                updated_date="2025-01-01T10:00:00",
            ),
            Task(
                id="TSK-2",
                title="Task 2",
                initiative="Test",
                phase="Phase 1",
                priority="Medium",
                status="Review",
                owner="tester",
                effort_hours=2.0,
                completion_percent=95.0,
                due_date="2025-01-15",
                created_date="2025-01-01T10:00:00",
                updated_date="2025-01-01T10:00:00",
            ),
        ]

        # Act
        metrics = empty_tracker._calculate_initiative_metrics(tasks)

        # Assert
        assert metrics["completed_tasks"] == 1
        assert metrics["completed_effort"] == 2.0


class TestCalculateOverallMetrics:
    """Test overall project metrics calculation."""

    def test_calculate_overall_metrics_for_empty_tracker(
        self, empty_tracker: ProjectTracker
    ) -> None:
        """GIVEN tracker with no tasks.

        WHEN overall metrics are calculated
        THEN all metrics are zero.
        """
        # Act
        metrics = empty_tracker._calculate_overall_metrics()

        # Assert
        assert metrics["total_tasks"] == 0
        assert metrics["overall_completion"] == 0
        assert metrics["total_effort"] == 0
        assert metrics["burn_rate"] == 0

    def test_calculate_overall_metrics_with_all_completed_tasks(
        self, empty_tracker: ProjectTracker
    ) -> None:
        """GIVEN tracker where all tasks are completed.

        WHEN overall metrics are calculated
        THEN completion is 100%.
        """
        # Arrange
        for i in range(3):
            task = Task(
                id=f"TSK-{i}",
                title=f"Task {i}",
                initiative="Test",
                phase="Phase 1",
                priority="Medium",
                status="Done",
                owner="tester",
                effort_hours=5.0,
                completion_percent=100.0,
                due_date="2025-01-15",
                created_date="2025-01-01T10:00:00",
                updated_date="2025-01-01T10:00:00",
            )
            empty_tracker.add_task(task)

        # Act
        metrics = empty_tracker._calculate_overall_metrics()

        # Assert
        assert metrics["total_tasks"] == 3
        assert metrics["overall_completion"] == 100.0
        assert metrics["total_effort"] == 15.0

    def test_calculate_overall_metrics_burn_rate(
        self, empty_tracker: ProjectTracker
    ) -> None:
        """GIVEN tasks created over time with some completed.

        WHEN overall metrics are calculated
        THEN burn rate reflects hours per week.
        """
        # Arrange - Create tasks 14 days ago, complete some
        base_date = datetime.now(timezone.utc) - timedelta(days=14)
        for i in range(4):
            task = Task(
                id=f"TSK-{i}",
                title=f"Task {i}",
                initiative="Test",
                phase="Phase 1",
                priority="Medium",
                status="Done" if i < 2 else "To Do",
                owner="tester",
                effort_hours=10.0,
                completion_percent=100.0 if i < 2 else 0.0,
                due_date="2025-01-15",
                created_date=base_date.isoformat(),
                updated_date=datetime.now(timezone.utc).isoformat(),
            )
            empty_tracker.add_task(task)

        # Act
        metrics = empty_tracker._calculate_overall_metrics()

        # Assert - 2 tasks @ 10h = 20h over 2 weeks = 10h/week
        assert metrics["burn_rate"] == 10.0

    def test_calculate_overall_metrics_rounds_to_one_decimal(
        self, empty_tracker: ProjectTracker
    ) -> None:
        """GIVEN tasks that produce non-round percentages.

        WHEN overall metrics are calculated
        THEN values are rounded to one decimal.
        """
        # Arrange
        base_date = datetime.now(timezone.utc) - timedelta(days=7)
        for i in range(7):
            task = Task(
                id=f"TSK-{i}",
                title=f"Task {i}",
                initiative="Test",
                phase="Phase 1",
                priority="Medium",
                status="Done" if i < 2 else "To Do",
                owner="tester",
                effort_hours=1.0,
                completion_percent=100.0 if i < 2 else 0.0,
                due_date="2025-01-15",
                created_date=base_date.isoformat(),
                updated_date=datetime.now(timezone.utc).isoformat(),
            )
            empty_tracker.add_task(task)

        # Act
        metrics = empty_tracker._calculate_overall_metrics()

        # Assert - 2/7 = 28.571...
        assert metrics["overall_completion"] == 28.6
