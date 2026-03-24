"""Tests for ProjectTracker initialization and data persistence.

Covers:
- TestProjectTrackerInitialization
- TestDataPersistence
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from minister.project_tracker import InitiativeTracker, ProjectTracker, Task


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


class TestDataPersistence:
    """Test save and load operations validate data integrity."""

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
        before_save = datetime.now(timezone.utc)

        # Act
        empty_tracker.add_task(task)

        # Assert
        with open(empty_tracker.data_file, encoding="utf-8") as f:
            data = json.load(f)
        last_updated = datetime.fromisoformat(data["last_updated"])
        assert last_updated >= before_save
