"""Unit tests for InitiativeTracker dataclass.

Tests cover:
- Creation with empty and populated task lists
- Timestamp handling and validation
- Dataclass mutability and modification behavior
- Data integrity and type safety
"""

from __future__ import annotations

from datetime import datetime

from minister.project_tracker import InitiativeTracker, Task

# =============================================================================
# Creation Tests: Empty and Populated Initialization
# =============================================================================


def test_create_initiative_tracker_with_empty_tasks_list() -> None:
    """Test InitiativeTracker creation with an empty tasks list.

    Verifies that:
    - Tracker can be initialized with no tasks
    - Empty list is properly stored
    - Timestamp is set correctly
    """
    timestamp = datetime.now().isoformat()
    tracker = InitiativeTracker(tasks=[], last_updated=timestamp)

    assert tracker.tasks == []
    assert tracker.last_updated == timestamp
    assert isinstance(tracker.tasks, list)
    assert len(tracker.tasks) == 0


def test_create_initiative_tracker_with_populated_tasks_list(
    sample_tasks: list[Task],
) -> None:
    """Test InitiativeTracker creation with pre-populated tasks.

    Verifies that:
    - Tracker correctly stores multiple tasks
    - Task list length matches input
    - All tasks are accessible
    - Task order is preserved
    """
    timestamp = "2025-01-10T12:00:00"
    tracker = InitiativeTracker(tasks=sample_tasks, last_updated=timestamp)

    assert len(tracker.tasks) == len(sample_tasks)
    assert tracker.tasks == sample_tasks
    assert tracker.last_updated == timestamp

    # Verify tasks are accessible and order is preserved
    assert tracker.tasks[0].id == "GHYG-001"
    assert tracker.tasks[-1].id == "DOC-002"


def test_create_initiative_tracker_with_single_task(minimal_task: Task) -> None:
    """Test InitiativeTracker creation with a single task.

    Verifies that:
    - Single-task lists work correctly
    - Task properties are accessible
    """
    timestamp = "2025-01-01T10:00:00"
    tracker = InitiativeTracker(tasks=[minimal_task], last_updated=timestamp)

    assert len(tracker.tasks) == 1
    assert tracker.tasks[0] == minimal_task
    assert tracker.tasks[0].id == "TSK-001"
    assert tracker.last_updated == timestamp


# =============================================================================
# Timestamp Handling Tests
# =============================================================================


def test_last_updated_timestamp_formats() -> None:
    """Test InitiativeTracker handles various timestamp formats.

    Verifies that:
    - ISO format timestamps are stored correctly
    - Different timestamp precisions work
    - Timestamp is stored as-is without modification
    """
    # ISO format with seconds
    timestamp_seconds = "2025-01-10T15:30:45"
    tracker1 = InitiativeTracker(tasks=[], last_updated=timestamp_seconds)
    assert tracker1.last_updated == timestamp_seconds

    # ISO format with microseconds
    timestamp_micro = "2025-01-10T15:30:45.123456"
    tracker2 = InitiativeTracker(tasks=[], last_updated=timestamp_micro)
    assert tracker2.last_updated == timestamp_micro

    # ISO format with timezone
    timestamp_tz = "2025-01-10T15:30:45+00:00"
    tracker3 = InitiativeTracker(tasks=[], last_updated=timestamp_tz)
    assert tracker3.last_updated == timestamp_tz


def test_last_updated_timestamp_preservation() -> None:
    """Test that last_updated timestamp is preserved exactly.

    Verifies that:
    - Timestamp string is not parsed or modified
    - Original format is maintained
    """
    original_timestamp = "2025-12-13T08:15:30.500000"
    tracker = InitiativeTracker(tasks=[], last_updated=original_timestamp)

    assert tracker.last_updated == original_timestamp
    assert isinstance(tracker.last_updated, str)


def test_last_updated_can_be_current_time() -> None:
    """Test InitiativeTracker with current timestamp.

    Verifies that:
    - Current timestamp can be used
    - Timestamp is set correctly at creation time
    """
    before = datetime.now().isoformat()
    tracker = InitiativeTracker(tasks=[], last_updated=before)

    assert tracker.last_updated == before
    # Ensure timestamp is parseable as valid datetime
    parsed = datetime.fromisoformat(tracker.last_updated)
    assert isinstance(parsed, datetime)


# =============================================================================
# Mutability Tests: Dataclass Modification Behavior
# =============================================================================


def test_tasks_list_is_mutable_can_append(minimal_task: Task) -> None:
    """Test that tasks list can be modified by appending.

    Verifies that:
    - Tasks list allows append operations
    - New tasks are added correctly
    - List length increases appropriately
    """
    tracker = InitiativeTracker(tasks=[], last_updated="2025-01-01T10:00:00")
    assert len(tracker.tasks) == 0

    tracker.tasks.append(minimal_task)

    assert len(tracker.tasks) == 1
    assert tracker.tasks[0] == minimal_task


def test_tasks_list_is_mutable_can_extend(
    minimal_task: Task,
    completed_task: Task,
) -> None:
    """Test that tasks list can be modified by extending.

    Verifies that:
    - Tasks list allows extend operations
    - Multiple tasks can be added at once
    - Original and new tasks are all present
    """
    tracker = InitiativeTracker(
        tasks=[minimal_task], last_updated="2025-01-01T10:00:00"
    )
    assert len(tracker.tasks) == 1

    new_tasks = [completed_task]
    tracker.tasks.extend(new_tasks)

    assert len(tracker.tasks) == 2
    assert tracker.tasks[0] == minimal_task
    assert tracker.tasks[1] == completed_task


def test_tasks_list_is_mutable_can_remove(sample_tasks: list[Task]) -> None:
    """Test that tasks list supports removal operations.

    Verifies that:
    - Tasks can be removed from the list
    - Removal affects list length
    - Correct task is removed
    """
    tracker = InitiativeTracker(
        tasks=sample_tasks.copy(),
        last_updated="2025-01-01T10:00:00",
    )
    original_length = len(tracker.tasks)
    first_task = tracker.tasks[0]

    tracker.tasks.remove(first_task)

    assert len(tracker.tasks) == original_length - 1
    assert first_task not in tracker.tasks


def test_tasks_list_is_mutable_can_clear(sample_tasks: list[Task]) -> None:
    """Test that tasks list can be cleared.

    Verifies that:
    - Tasks list supports clear operation
    - All tasks are removed
    - List becomes empty
    """
    tracker = InitiativeTracker(
        tasks=sample_tasks.copy(),
        last_updated="2025-01-01T10:00:00",
    )
    assert len(tracker.tasks) > 0

    tracker.tasks.clear()

    assert len(tracker.tasks) == 0
    assert tracker.tasks == []


def test_tasks_list_supports_indexing_and_slicing(sample_tasks: list[Task]) -> None:
    """Test that tasks list supports standard list operations.

    Verifies that:
    - Individual tasks can be accessed by index
    - Slicing operations work correctly
    - Negative indexing works
    """
    tracker = InitiativeTracker(
        tasks=sample_tasks.copy(),
        last_updated="2025-01-01T10:00:00",
    )

    # Index access
    first_task = tracker.tasks[0]
    assert first_task.id == "GHYG-001"

    # Negative indexing
    last_task = tracker.tasks[-1]
    assert last_task.id == "DOC-002"

    # Slicing
    first_two = tracker.tasks[:2]
    assert len(first_two) == 2
    assert first_two[0].id == "GHYG-001"
    assert first_two[1].id == "GHYG-002"


def test_last_updated_field_is_mutable() -> None:
    """Test that last_updated timestamp can be modified.

    Verifies that:
    - Timestamp can be updated after creation
    - New timestamp replaces old value
    """
    original_timestamp = "2025-01-01T10:00:00"
    tracker = InitiativeTracker(tasks=[], last_updated=original_timestamp)
    assert tracker.last_updated == original_timestamp

    new_timestamp = "2025-01-10T15:30:00"
    tracker.last_updated = new_timestamp

    assert tracker.last_updated == new_timestamp
    assert tracker.last_updated != original_timestamp


# =============================================================================
# Data Integrity Tests
# =============================================================================


def test_tasks_list_reference_behavior(minimal_task: Task) -> None:
    """Test that tasks list maintains proper references.

    Verifies that:
    - Tasks list stores actual Task objects
    - Modifications to tasks affect the tracker
    - Reference semantics work correctly
    """
    tracker = InitiativeTracker(
        tasks=[minimal_task], last_updated="2025-01-01T10:00:00"
    )

    # Modify task through tracker's list
    tracker.tasks[0].status = "In Progress"

    # Verify modification is reflected
    assert tracker.tasks[0].status == "In Progress"
    assert minimal_task.status == "In Progress"


def test_tasks_list_copy_independence(sample_tasks: list[Task]) -> None:
    """Test that copied tasks lists are independent.

    Verifies that:
    - Passing a copy of tasks list creates independence
    - Modifications to original don't affect tracker
    """
    original_tasks = sample_tasks.copy()
    tracker = InitiativeTracker(
        tasks=original_tasks.copy(),
        last_updated="2025-01-01T10:00:00",
    )

    # Modify original list
    original_tasks.clear()

    # Tracker's list should be unaffected
    assert len(tracker.tasks) == len(sample_tasks)


def test_initiative_tracker_type_annotations() -> None:
    """Test that InitiativeTracker enforces type expectations.

    Verifies that:
    - Correct types can be assigned
    - Type annotations are present
    """
    tracker = InitiativeTracker(tasks=[], last_updated="2025-01-01T10:00:00")

    # These should work without type errors
    assert isinstance(tracker.tasks, list)
    assert isinstance(tracker.last_updated, str)


# =============================================================================
# Edge Cases and Special Scenarios
# =============================================================================


def test_initiative_tracker_with_duplicate_tasks(minimal_task: Task) -> None:
    """Test InitiativeTracker with duplicate task references.

    Verifies that:
    - Same task can appear multiple times
    - List allows duplicates
    """
    tracker = InitiativeTracker(
        tasks=[minimal_task, minimal_task],
        last_updated="2025-01-01T10:00:00",
    )

    assert len(tracker.tasks) == 2
    assert tracker.tasks[0] is tracker.tasks[1]
    assert tracker.tasks[0].id == tracker.tasks[1].id


def test_initiative_tracker_with_mixed_task_types(
    minimal_task: Task,
    completed_task: Task,
    task_with_github_issue: Task,
) -> None:
    """Test InitiativeTracker with various task configurations.

    Verifies that:
    - Different task types can coexist
    - All tasks are properly stored
    - Different field values are preserved
    """
    mixed_tasks = [minimal_task, completed_task, task_with_github_issue]
    tracker = InitiativeTracker(tasks=mixed_tasks, last_updated="2025-01-01T10:00:00")

    assert len(tracker.tasks) == 3
    assert tracker.tasks[0].github_issue is None
    assert tracker.tasks[1].status == "Done"
    assert tracker.tasks[2].github_issue == "https://github.com/org/repo/issues/123"


def test_initiative_tracker_empty_timestamp_string() -> None:
    """Test InitiativeTracker with empty timestamp string.

    Verifies that:
    - Empty string timestamps are accepted
    - No validation is performed on timestamp format
    """
    tracker = InitiativeTracker(tasks=[], last_updated="")

    assert tracker.last_updated == ""
    assert isinstance(tracker.last_updated, str)


def test_initiative_tracker_dataclass_equality(sample_tasks: list[Task]) -> None:
    """Test equality comparison between InitiativeTracker instances.

    Verifies that:
    - Two trackers with same data are equal
    - Dataclass equality works correctly
    """
    timestamp = "2025-01-10T12:00:00"
    tracker1 = InitiativeTracker(tasks=sample_tasks, last_updated=timestamp)
    tracker2 = InitiativeTracker(tasks=sample_tasks, last_updated=timestamp)

    assert tracker1 == tracker2


def test_initiative_tracker_dataclass_inequality() -> None:
    """Test inequality between different InitiativeTracker instances.

    Verifies that:
    - Trackers with different timestamps are not equal
    - Trackers with different tasks are not equal
    """
    timestamp1 = "2025-01-10T12:00:00"
    timestamp2 = "2025-01-11T12:00:00"

    tracker1 = InitiativeTracker(tasks=[], last_updated=timestamp1)
    tracker2 = InitiativeTracker(tasks=[], last_updated=timestamp2)

    assert tracker1 != tracker2


# =============================================================================
# Integration with sample_tasks Fixture
# =============================================================================


def test_sample_tasks_fixture_provides_multiple_initiatives(
    sample_tasks: list[Task],
) -> None:
    """Test that sample_tasks fixture works with InitiativeTracker.

    Verifies that:
    - Fixture integration works correctly
    - Multiple initiatives are present
    - All expected tasks are accessible
    """
    tracker = InitiativeTracker(tasks=sample_tasks, last_updated="2025-01-01T10:00:00")

    initiatives = {task.initiative for task in tracker.tasks}

    assert len(initiatives) >= 3
    assert "GitHub Projects Hygiene" in initiatives
    assert "Pull Request Readiness" in initiatives
    assert "Docs & Enablement" in initiatives


def test_sample_tasks_fixture_various_statuses(sample_tasks: list[Task]) -> None:
    """Test that sample_tasks includes various task statuses.

    Verifies that:
    - Sample tasks have diverse statuses
    - InitiativeTracker preserves status information
    """
    tracker = InitiativeTracker(tasks=sample_tasks, last_updated="2025-01-01T10:00:00")

    statuses = {task.status for task in tracker.tasks}

    assert "Done" in statuses
    assert "In Progress" in statuses
    assert "To Do" in statuses
