"""Comprehensive unit tests for ProjectTracker class.

Tests follow TDD/BDD conventions with descriptive names and clear AAA pattern.
Each test focuses on a single behavior with explicit assertions.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime, timedelta
from pathlib import Path

from minister.project_tracker import InitiativeTracker, ProjectTracker, Task

# =============================================================================
# Initialization Tests
# =============================================================================


class TestProjectTrackerInitialization:
    """Test ProjectTracker initialization with various configurations."""

    def test_initialize_with_default_data_file_creates_empty_tracker(
        self, temp_data_file: Path
    ) -> None:
        """GIVEN no existing data file.

        WHEN tracker is initialized with default settings
        THEN it creates empty tracker with default initiatives.
        """
        # Arrange & Act
        tracker = ProjectTracker(data_file=temp_data_file)

        # Assert
        assert tracker.data_file == temp_data_file
        assert tracker.initiatives == ProjectTracker.DEFAULT_INITIATIVES
        assert len(tracker.data.tasks) == 0
        assert isinstance(tracker.data, InitiativeTracker)

    def test_initialize_with_custom_data_file_path(self, temp_data_dir: Path) -> None:
        """GIVEN custom data file path.

        WHEN tracker is initialized
        THEN it uses the specified path.
        """
        # Arrange
        custom_path = temp_data_dir / "custom" / "data.json"

        # Act
        tracker = ProjectTracker(data_file=custom_path)

        # Assert
        assert tracker.data_file == custom_path

    def test_initialize_with_custom_initiatives(self, temp_data_file: Path) -> None:
        """GIVEN custom initiative list.

        WHEN tracker is initialized
        THEN it uses custom initiatives instead of defaults.
        """
        # Arrange
        custom_initiatives = ["Initiative A", "Initiative B", "Initiative C"]

        # Act
        tracker = ProjectTracker(
            data_file=temp_data_file, initiatives=custom_initiatives
        )

        # Assert
        assert tracker.initiatives == custom_initiatives
        assert tracker.initiatives != ProjectTracker.DEFAULT_INITIATIVES

    def test_initialize_loads_existing_data_file(
        self, seeded_data_file: Path, sample_tasks: list[Task]
    ) -> None:
        """GIVEN existing data file with tasks.

        WHEN tracker is initialized
        THEN it loads tasks from file.
        """
        # Act
        tracker = ProjectTracker(data_file=seeded_data_file)

        # Assert
        assert len(tracker.data.tasks) == len(sample_tasks)
        assert tracker.data.tasks[0].id == sample_tasks[0].id
        assert tracker.data.tasks[0].title == sample_tasks[0].title

    def test_initialize_with_nonexistent_file_creates_empty_tracker(
        self, temp_data_dir: Path
    ) -> None:
        """GIVEN nonexistent data file path.

        WHEN tracker is initialized
        THEN it creates empty tracker without error.
        """
        # Arrange
        nonexistent_file = temp_data_dir / "does_not_exist.json"

        # Act
        tracker = ProjectTracker(data_file=nonexistent_file)

        # Assert
        assert len(tracker.data.tasks) == 0
        assert not nonexistent_file.exists()


# =============================================================================
# Data Persistence Tests
# =============================================================================


class TestDataPersistence:
    """Test save and load operations ensure data integrity."""

    def test_save_creates_data_file_with_correct_structure(
        self, empty_tracker: ProjectTracker
    ) -> None:
        """GIVEN empty tracker.

        WHEN task is added (triggering save)
        THEN data file is created with correct JSON structure.
        """
        # Arrange
        task = Task(
            id="TEST-001",
            title="Test Task",
            initiative="Test",
            phase="Phase 1",
            priority="High",
            status="To Do",
            owner="tester",
            effort_hours=2.0,
            completion_percent=0.0,
            due_date="2025-01-15",
            created_date="2025-01-01T10:00:00",
            updated_date="2025-01-01T10:00:00",
        )

        # Act
        empty_tracker.add_task(task)

        # Assert
        assert empty_tracker.data_file.exists()
        with open(empty_tracker.data_file, encoding="utf-8") as f:
            data = json.load(f)
        assert "tasks" in data
        assert "last_updated" in data
        assert len(data["tasks"]) == 1
        assert data["tasks"][0]["id"] == "TEST-001"

    def test_save_creates_parent_directories_if_needed(
        self, temp_data_dir: Path
    ) -> None:
        """GIVEN data file path with nonexistent parent directories.

        WHEN save is triggered
        THEN parent directories are created automatically.
        """
        # Arrange
        nested_path = temp_data_dir / "level1" / "level2" / "data.json"
        tracker = ProjectTracker(data_file=nested_path)
        task = Task(
            id="TEST-001",
            title="Test",
            initiative="Test",
            phase="Phase 1",
            priority="High",
            status="To Do",
            owner="tester",
            effort_hours=1.0,
            completion_percent=0.0,
            due_date="2025-01-15",
            created_date="2025-01-01T10:00:00",
            updated_date="2025-01-01T10:00:00",
        )

        # Act
        tracker.add_task(task)

        # Assert
        assert nested_path.exists()
        assert nested_path.parent.exists()

    def test_load_then_save_preserves_all_task_fields(
        self, seeded_data_file: Path, sample_tasks: list[Task]
    ) -> None:
        """GIVEN tracker loaded from file.

        WHEN data is saved back
        THEN all task fields are preserved correctly.
        """
        # Arrange
        tracker = ProjectTracker(data_file=seeded_data_file)
        original_task = tracker.data.tasks[0]

        # Act
        tracker._save_data()
        reloaded_tracker = ProjectTracker(data_file=seeded_data_file)
        reloaded_task = reloaded_tracker.data.tasks[0]

        # Assert
        assert reloaded_task.id == original_task.id
        assert reloaded_task.title == original_task.title
        assert reloaded_task.initiative == original_task.initiative
        assert reloaded_task.phase == original_task.phase
        assert reloaded_task.priority == original_task.priority
        assert reloaded_task.status == original_task.status
        assert reloaded_task.owner == original_task.owner
        assert reloaded_task.effort_hours == original_task.effort_hours
        assert reloaded_task.completion_percent == original_task.completion_percent
        assert reloaded_task.due_date == original_task.due_date
        assert reloaded_task.github_issue == original_task.github_issue

    def test_save_updates_last_updated_timestamp(
        self, empty_tracker: ProjectTracker
    ) -> None:
        """GIVEN tracker with tasks.

        WHEN save is called
        THEN last_updated timestamp is set to current time.
        """
        # Arrange
        task = Task(
            id="TEST-001",
            title="Test",
            initiative="Test",
            phase="Phase 1",
            priority="High",
            status="To Do",
            owner="tester",
            effort_hours=1.0,
            completion_percent=0.0,
            due_date="2025-01-15",
            created_date="2025-01-01T10:00:00",
            updated_date="2025-01-01T10:00:00",
        )
        before_save = datetime.now()

        # Act
        empty_tracker.add_task(task)

        # Assert
        with open(empty_tracker.data_file, encoding="utf-8") as f:
            data = json.load(f)
        last_updated = datetime.fromisoformat(data["last_updated"])
        assert last_updated >= before_save


# =============================================================================
# Task Management Tests
# =============================================================================


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
        before_update = datetime.now()

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


# =============================================================================
# Query and Filter Tests
# =============================================================================


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


# =============================================================================
# Metrics Calculation Tests
# =============================================================================


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
        base_date = datetime.now() - timedelta(days=14)
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
                updated_date=datetime.now().isoformat(),
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
        base_date = datetime.now() - timedelta(days=7)
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
                updated_date=datetime.now().isoformat(),
            )
            empty_tracker.add_task(task)

        # Act
        metrics = empty_tracker._calculate_overall_metrics()

        # Assert - 2/7 = 28.571...
        assert metrics["overall_completion"] == 28.6


# =============================================================================
# Status Report Tests
# =============================================================================


class TestGetStatusReport:
    """Test comprehensive status report generation."""

    def test_status_report_includes_all_sections(
        self, populated_tracker: ProjectTracker
    ) -> None:
        """GIVEN populated tracker.

        WHEN status report is generated
        THEN report contains all required sections.
        """
        # Act
        report = populated_tracker.get_status_report()

        # Assert
        assert "last_updated" in report
        assert "initiatives" in report
        assert "overall_metrics" in report

    def test_status_report_includes_all_initiatives(
        self, populated_tracker: ProjectTracker
    ) -> None:
        """GIVEN tracker with tasks in multiple initiatives.

        WHEN status report is generated
        THEN report includes all initiatives with tasks.
        """
        # Act
        report = populated_tracker.get_status_report()

        # Assert
        initiatives = report["initiatives"]
        assert "GitHub Projects Hygiene" in initiatives
        assert "Pull Request Readiness" in initiatives
        assert "Docs & Enablement" in initiatives

    def test_status_report_includes_initiatives_without_tasks(
        self, empty_tracker: ProjectTracker
    ) -> None:
        """GIVEN tracker with default initiatives but no tasks.

        WHEN status report is generated
        THEN report includes all default initiatives with zero metrics.
        """
        # Act
        report = empty_tracker.get_status_report()

        # Assert
        for initiative in ProjectTracker.DEFAULT_INITIATIVES:
            assert initiative in report["initiatives"]
            metrics = report["initiatives"][initiative]
            assert metrics["total_tasks"] == 0

    def test_status_report_sorts_initiatives_alphabetically(
        self, populated_tracker: ProjectTracker
    ) -> None:
        """GIVEN tracker with multiple initiatives.

        WHEN status report is generated
        THEN initiatives are sorted alphabetically.
        """
        # Act
        report = populated_tracker.get_status_report()

        # Assert
        initiative_names = list(report["initiatives"].keys())
        assert initiative_names == sorted(initiative_names)

    def test_status_report_overall_metrics_match_all_tasks(
        self, populated_tracker: ProjectTracker
    ) -> None:
        """GIVEN populated tracker.

        WHEN status report is generated
        THEN overall metrics aggregate all tasks correctly.
        """
        # Act
        report = populated_tracker.get_status_report()

        # Assert
        overall = report["overall_metrics"]
        assert overall["total_tasks"] == len(populated_tracker.data.tasks)


# =============================================================================
# GitHub Comment Formatting Tests
# =============================================================================


class TestFormatGitHubComment:
    """Test GitHub-flavored markdown output formatting."""

    def test_format_github_comment_includes_header(
        self, populated_tracker: ProjectTracker
    ) -> None:
        """GIVEN populated tracker.

        WHEN GitHub comment is formatted
        THEN output includes proper header.
        """
        # Act
        comment = populated_tracker.format_github_comment()

        # Assert
        assert "### 🗂️ Initiative Pulse" in comment
        assert "Last updated:" in comment

    def test_format_github_comment_includes_markdown_table(
        self, populated_tracker: ProjectTracker
    ) -> None:
        """GIVEN populated tracker.

        WHEN GitHub comment is formatted
        THEN output includes properly formatted markdown table.
        """
        # Act
        comment = populated_tracker.format_github_comment()

        # Assert
        assert (
            "| Initiative | Done | In Progress | Completion | Avg Task % |" in comment
        )
        assert (
            "|------------|------|-------------|------------|-------------|" in comment
        )

    def test_format_github_comment_includes_all_initiatives(
        self, populated_tracker: ProjectTracker
    ) -> None:
        """GIVEN tracker with multiple initiatives.

        WHEN GitHub comment is formatted
        THEN all initiatives appear in table.
        """
        # Act
        comment = populated_tracker.format_github_comment()

        # Assert
        assert "GitHub Projects Hygiene" in comment
        assert "Pull Request Readiness" in comment
        assert "Docs & Enablement" in comment

    def test_format_github_comment_includes_overall_metrics_section(
        self, populated_tracker: ProjectTracker
    ) -> None:
        """GIVEN populated tracker.

        WHEN GitHub comment is formatted
        THEN overall metrics section is included.
        """
        # Act
        comment = populated_tracker.format_github_comment()

        # Assert
        assert "### 📊 Overall Metrics" in comment
        assert "Total tasks:" in comment
        assert "Completion:" in comment
        assert "Total effort:" in comment
        assert "Burn rate:" in comment

    def test_format_github_comment_with_custom_report(
        self, empty_tracker: ProjectTracker
    ) -> None:
        """GIVEN custom report dict.

        WHEN formatting with explicit report
        THEN custom report is used instead of generating new one.
        """
        # Arrange
        custom_report = {
            "last_updated": "2025-01-01T12:00:00",
            "initiatives": {
                "Custom Initiative": {
                    "total_tasks": 5,
                    "completed_tasks": 3,
                    "in_progress_tasks": 1,
                    "completion_percentage": 60.0,
                    "average_task_completion": 70.0,
                }
            },
            "overall_metrics": {
                "total_tasks": 5,
                "overall_completion": 60.0,
                "total_effort": 20.0,
                "burn_rate": 5.0,
            },
        }

        # Act
        comment = empty_tracker.format_github_comment(report=custom_report)

        # Assert
        assert "Custom Initiative" in comment
        assert "3/5" in comment
        assert "60.0%" in comment

    def test_format_github_comment_for_empty_tracker(
        self, empty_tracker: ProjectTracker
    ) -> None:
        """GIVEN empty tracker.

        WHEN GitHub comment is formatted
        THEN output contains zero values but proper structure.
        """
        # Act
        comment = empty_tracker.format_github_comment()

        # Assert
        assert "### 🗂️ Initiative Pulse" in comment
        assert "### 📊 Overall Metrics" in comment
        assert "Total tasks: 0" in comment


# =============================================================================
# CSV Export Tests
# =============================================================================


class TestExportCSV:
    """Test CSV export functionality."""

    def test_export_csv_creates_file_with_header(
        self, empty_tracker: ProjectTracker, temp_data_dir: Path
    ) -> None:
        """GIVEN tracker with tasks.

        WHEN CSV export is called
        THEN file is created with proper header row.
        """
        # Arrange
        task = Task(
            id="TSK-001",
            title="Test Task",
            initiative="Test",
            phase="Phase 1",
            priority="High",
            status="To Do",
            owner="tester",
            effort_hours=2.0,
            completion_percent=0.0,
            due_date="2025-01-15",
            created_date="2025-01-01T10:00:00",
            updated_date="2025-01-01T10:00:00",
        )
        empty_tracker.add_task(task)
        output_file = temp_data_dir / "export.csv"

        # Act
        empty_tracker.export_csv(output_file)

        # Assert
        assert output_file.exists()
        with open(output_file, encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader)
        assert "id" in header
        assert "title" in header
        assert "initiative" in header
        assert "status" in header

    def test_export_csv_includes_all_tasks(
        self, populated_tracker: ProjectTracker, temp_data_dir: Path
    ) -> None:
        """GIVEN tracker with multiple tasks.

        WHEN CSV export is called
        THEN all tasks are exported.
        """
        # Arrange
        output_file = temp_data_dir / "export.csv"

        # Act
        populated_tracker.export_csv(output_file)

        # Assert
        with open(output_file, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) == len(populated_tracker.data.tasks)

    def test_export_csv_preserves_task_data(
        self, populated_tracker: ProjectTracker, temp_data_dir: Path
    ) -> None:
        """GIVEN tracker with tasks.

        WHEN CSV export is called
        THEN task data is accurately exported.
        """
        # Arrange
        output_file = temp_data_dir / "export.csv"
        first_task = populated_tracker.data.tasks[0]

        # Act
        populated_tracker.export_csv(output_file)

        # Assert
        with open(output_file, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            first_row = next(reader)
        assert first_row["id"] == first_task.id
        assert first_row["title"] == first_task.title
        assert first_row["initiative"] == first_task.initiative
        assert first_row["status"] == first_task.status
        assert first_row["effort_hours"] == str(first_task.effort_hours)

    def test_export_csv_handles_empty_tracker(
        self, empty_tracker: ProjectTracker, temp_data_dir: Path
    ) -> None:
        """GIVEN empty tracker.

        WHEN CSV export is called
        THEN file contains only header row.
        """
        # Arrange
        output_file = temp_data_dir / "export.csv"

        # Act
        empty_tracker.export_csv(output_file)

        # Assert
        with open(output_file, encoding="utf-8") as f:
            reader = csv.reader(f)
            rows = list(reader)
        assert len(rows) == 1  # Only header row

    def test_export_csv_handles_null_github_issue(
        self, empty_tracker: ProjectTracker, temp_data_dir: Path
    ) -> None:
        """GIVEN task with no GitHub issue.

        WHEN CSV export is called
        THEN github_issue field is empty string.
        """
        # Arrange
        task = Task(
            id="TSK-001",
            title="Task without issue",
            initiative="Test",
            phase="Phase 1",
            priority="Medium",
            status="To Do",
            owner="tester",
            effort_hours=1.0,
            completion_percent=0.0,
            due_date="2025-01-15",
            created_date="2025-01-01T10:00:00",
            updated_date="2025-01-01T10:00:00",
            github_issue=None,
        )
        empty_tracker.add_task(task)
        output_file = temp_data_dir / "export.csv"

        # Act
        empty_tracker.export_csv(output_file)

        # Assert
        with open(output_file, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            row = next(reader)
        assert row["github_issue"] == ""

    def test_export_csv_includes_expected_columns(
        self, populated_tracker: ProjectTracker, temp_data_dir: Path
    ) -> None:
        """GIVEN populated tracker.

        WHEN CSV export is called
        THEN exported CSV has all expected columns.
        """
        # Arrange
        output_file = temp_data_dir / "export.csv"
        expected_columns = [
            "id",
            "title",
            "initiative",
            "phase",
            "priority",
            "status",
            "owner",
            "effort_hours",
            "completion_percent",
            "due_date",
            "github_issue",
        ]

        # Act
        populated_tracker.export_csv(output_file)

        # Assert
        with open(output_file, encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader)
        assert header == expected_columns


# =============================================================================
# Edge Cases and Integration Tests
# =============================================================================


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_tracker_handles_very_large_task_count(
        self, empty_tracker: ProjectTracker
    ) -> None:
        """GIVEN tracker.

        WHEN many tasks are added
        THEN tracker handles large dataset efficiently.
        """
        # Arrange & Act
        for i in range(100):
            task = Task(
                id=f"TSK-{i:03d}",
                title=f"Task {i}",
                initiative="Test",
                phase="Phase 1",
                priority="Medium",
                status="To Do",
                owner="tester",
                effort_hours=1.0,
                completion_percent=0.0,
                due_date="2025-01-15",
                created_date="2025-01-01T10:00:00",
                updated_date="2025-01-01T10:00:00",
            )
            empty_tracker.add_task(task)

        # Assert
        assert len(empty_tracker.data.tasks) == 100
        report = empty_tracker.get_status_report()
        assert report["overall_metrics"]["total_tasks"] == 100

    def test_tracker_with_single_task_calculates_metrics_correctly(
        self, empty_tracker: ProjectTracker, minimal_task: Task
    ) -> None:
        """GIVEN tracker with exactly one task.

        WHEN metrics are calculated
        THEN percentages and averages are correct.
        """
        # Arrange
        empty_tracker.add_task(minimal_task)

        # Act
        report = empty_tracker.get_status_report()

        # Assert
        overall = report["overall_metrics"]
        assert overall["total_tasks"] == 1
        assert overall["overall_completion"] == 0.0  # Task is "To Do"

    def test_tracker_with_zero_effort_tasks(
        self, empty_tracker: ProjectTracker
    ) -> None:
        """GIVEN tasks with zero effort hours.

        WHEN metrics are calculated
        THEN no division by zero errors occur.
        """
        # Arrange
        task = Task(
            id="TSK-001",
            title="Zero effort task",
            initiative="Test",
            phase="Phase 1",
            priority="Low",
            status="Done",
            owner="tester",
            effort_hours=0.0,
            completion_percent=100.0,
            due_date="2025-01-15",
            created_date="2025-01-01T10:00:00",
            updated_date="2025-01-01T10:00:00",
        )
        empty_tracker.add_task(task)

        # Act
        report = empty_tracker.get_status_report()

        # Assert
        overall = report["overall_metrics"]
        assert overall["total_effort"] == 0.0
        assert overall["overall_completion"] == 100.0

    def test_complete_workflow_add_update_report_export(
        self, empty_tracker: ProjectTracker, temp_data_dir: Path
    ) -> None:
        """GIVEN empty tracker.

        WHEN complete workflow is executed (add, update, report, export)
        THEN all operations work together correctly.
        """
        # Arrange & Act - Add tasks
        task1 = Task(
            id="WF-001",
            title="First Task",
            initiative="Workflow Test",
            phase="Phase 1",
            priority="High",
            status="To Do",
            owner="user",
            effort_hours=5.0,
            completion_percent=0.0,
            due_date="2025-01-20",
            created_date="2025-01-01T10:00:00",
            updated_date="2025-01-01T10:00:00",
        )
        task2 = Task(
            id="WF-002",
            title="Second Task",
            initiative="Workflow Test",
            phase="Phase 1",
            priority="Medium",
            status="To Do",
            owner="user",
            effort_hours=3.0,
            completion_percent=0.0,
            due_date="2025-01-25",
            created_date="2025-01-01T10:00:00",
            updated_date="2025-01-01T10:00:00",
        )
        empty_tracker.add_task(task1)
        empty_tracker.add_task(task2)

        # Act - Update
        empty_tracker.update_task(
            "WF-001", {"status": "Done", "completion_percent": 100.0}
        )

        # Act - Report
        report = empty_tracker.get_status_report()
        comment = empty_tracker.format_github_comment(report)

        # Act - Export
        csv_file = temp_data_dir / "workflow.csv"
        empty_tracker.export_csv(csv_file)

        # Assert
        assert len(empty_tracker.data.tasks) == 2
        assert report["overall_metrics"]["overall_completion"] == 50.0
        assert "Workflow Test" in comment
        assert csv_file.exists()
        with open(csv_file, encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        assert len(rows) == 2
