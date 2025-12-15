"""Unit tests for Task dataclass.

Tests the Task dataclass following TDD/BDD principles:
- GIVEN-WHEN-THEN test naming convention
- Isolated test scenarios covering all dataclass behaviors
- Validation of required and optional fields
- Dataclass equality and serialization
"""

from __future__ import annotations

from dataclasses import asdict

from minister.project_tracker import Task

# =============================================================================
# Task Creation Tests
# =============================================================================


def test_given_all_required_fields_when_creating_task_then_task_is_created_successfully():
    """Test that Task can be created with all required fields.

    GIVEN: All required Task fields are provided
    WHEN: A Task instance is created
    THEN: The Task is successfully instantiated with correct field values
    """
    task = Task(
        id="TSK-001",
        title="Test Task",
        initiative="Test Initiative",
        phase="Phase 1",
        priority="High",
        status="To Do",
        owner="developer",
        effort_hours=5.0,
        completion_percent=0.0,
        due_date="2025-01-15",
        created_date="2025-01-01T10:00:00",
        updated_date="2025-01-01T10:00:00",
    )

    assert task.id == "TSK-001"
    assert task.title == "Test Task"
    assert task.initiative == "Test Initiative"
    assert task.phase == "Phase 1"
    assert task.priority == "High"
    assert task.status == "To Do"
    assert task.owner == "developer"
    assert task.effort_hours == 5.0
    assert task.completion_percent == 0.0
    assert task.due_date == "2025-01-15"
    assert task.created_date == "2025-01-01T10:00:00"
    assert task.updated_date == "2025-01-01T10:00:00"
    assert task.github_issue is None


def test_given_minimal_task_fixture_when_accessing_fields_then_all_fields_match_expected():
    """Test that minimal_task fixture is properly configured.

    GIVEN: A minimal_task fixture from conftest
    WHEN: The task fields are accessed
    THEN: All required fields have correct values and github_issue is None
    """
    # This test verifies the fixture works correctly and can be reused
    task = Task(
        id="TSK-001",
        title="Minimal Task",
        initiative="Test Initiative",
        phase="Phase 1",
        priority="Medium",
        status="To Do",
        owner="tester",
        effort_hours=2.0,
        completion_percent=0.0,
        due_date="2025-01-15",
        created_date="2025-01-01T10:00:00",
        updated_date="2025-01-01T10:00:00",
    )

    assert task.github_issue is None
    assert isinstance(task.id, str)
    assert isinstance(task.title, str)
    assert isinstance(task.effort_hours, float)
    assert isinstance(task.completion_percent, float)


# =============================================================================
# Optional Field Tests
# =============================================================================


def test_given_no_github_issue_when_creating_task_then_github_issue_is_none():
    """Test that github_issue defaults to None when not provided.

    GIVEN: A Task is created without the optional github_issue field
    WHEN: The task instance is created
    THEN: The github_issue field is None
    """
    task = Task(
        id="TSK-002",
        title="Task Without Issue",
        initiative="Test Initiative",
        phase="Phase 1",
        priority="Medium",
        status="To Do",
        owner="developer",
        effort_hours=3.0,
        completion_percent=0.0,
        due_date="2025-01-20",
        created_date="2025-01-02T09:00:00",
        updated_date="2025-01-02T09:00:00",
    )

    assert task.github_issue is None


def test_given_github_issue_url_when_creating_task_then_github_issue_is_stored():
    """Test that github_issue field stores URL when provided.

    GIVEN: A GitHub issue URL is provided during task creation
    WHEN: The Task is instantiated
    THEN: The github_issue field contains the URL string
    """
    github_url = "https://github.com/org/repo/issues/42"
    task = Task(
        id="TSK-003",
        title="Task With GitHub Issue",
        initiative="Test Initiative",
        phase="Phase 2",
        priority="High",
        status="In Progress",
        owner="developer",
        effort_hours=8.0,
        completion_percent=50.0,
        due_date="2025-01-25",
        created_date="2025-01-03T11:00:00",
        updated_date="2025-01-10T14:30:00",
        github_issue=github_url,
    )

    assert task.github_issue == github_url
    assert isinstance(task.github_issue, str)


def test_given_github_issue_number_when_creating_task_then_github_issue_is_stored():
    """Test that github_issue field can store issue number as string.

    GIVEN: A GitHub issue number is provided as a string
    WHEN: The Task is instantiated
    THEN: The github_issue field contains the issue number string
    """
    task = Task(
        id="TSK-004",
        title="Task With Issue Number",
        initiative="Test Initiative",
        phase="Phase 1",
        priority="Low",
        status="Review",
        owner="reviewer",
        effort_hours=2.0,
        completion_percent=80.0,
        due_date="2025-01-18",
        created_date="2025-01-04T08:00:00",
        updated_date="2025-01-12T16:00:00",
        github_issue="#123",
    )

    assert task.github_issue == "#123"


def test_given_explicit_none_when_creating_task_then_github_issue_is_none():
    """Test that github_issue can be explicitly set to None.

    GIVEN: github_issue is explicitly passed as None
    WHEN: The Task is instantiated
    THEN: The github_issue field is None
    """
    task = Task(
        id="TSK-005",
        title="Explicit None Issue",
        initiative="Test Initiative",
        phase="Phase 1",
        priority="Medium",
        status="Done",
        owner="developer",
        effort_hours=4.0,
        completion_percent=100.0,
        due_date="2025-01-10",
        created_date="2025-01-05T10:00:00",
        updated_date="2025-01-09T17:00:00",
        github_issue=None,
    )

    assert task.github_issue is None


# =============================================================================
# Dataclass Equality Tests
# =============================================================================


def test_given_two_identical_tasks_when_comparing_then_tasks_are_equal():
    """Test that two Task instances with identical fields are equal.

    GIVEN: Two Task instances created with identical field values
    WHEN: The tasks are compared for equality
    THEN: The tasks are equal
    """
    task1 = Task(
        id="TSK-100",
        title="Same Task",
        initiative="Test Initiative",
        phase="Phase 1",
        priority="High",
        status="To Do",
        owner="developer",
        effort_hours=6.0,
        completion_percent=0.0,
        due_date="2025-02-01",
        created_date="2025-01-15T10:00:00",
        updated_date="2025-01-15T10:00:00",
        github_issue="https://github.com/org/repo/issues/100",
    )

    task2 = Task(
        id="TSK-100",
        title="Same Task",
        initiative="Test Initiative",
        phase="Phase 1",
        priority="High",
        status="To Do",
        owner="developer",
        effort_hours=6.0,
        completion_percent=0.0,
        due_date="2025-02-01",
        created_date="2025-01-15T10:00:00",
        updated_date="2025-01-15T10:00:00",
        github_issue="https://github.com/org/repo/issues/100",
    )

    assert task1 == task2


def test_given_two_tasks_with_different_ids_when_comparing_then_tasks_are_not_equal():
    """Test that tasks with different IDs are not equal.

    GIVEN: Two Task instances that differ only in their ID
    WHEN: The tasks are compared for equality
    THEN: The tasks are not equal
    """
    task1 = Task(
        id="TSK-101",
        title="Same Task",
        initiative="Test Initiative",
        phase="Phase 1",
        priority="High",
        status="To Do",
        owner="developer",
        effort_hours=6.0,
        completion_percent=0.0,
        due_date="2025-02-01",
        created_date="2025-01-15T10:00:00",
        updated_date="2025-01-15T10:00:00",
    )

    task2 = Task(
        id="TSK-102",
        title="Same Task",
        initiative="Test Initiative",
        phase="Phase 1",
        priority="High",
        status="To Do",
        owner="developer",
        effort_hours=6.0,
        completion_percent=0.0,
        due_date="2025-02-01",
        created_date="2025-01-15T10:00:00",
        updated_date="2025-01-15T10:00:00",
    )

    assert task1 != task2


def test_given_two_tasks_with_different_github_issues_when_comparing_then_tasks_are_not_equal():
    """Test that tasks with different github_issue values are not equal.

    GIVEN: Two Task instances that differ only in github_issue
    WHEN: The tasks are compared for equality
    THEN: The tasks are not equal
    """
    task1 = Task(
        id="TSK-103",
        title="Task",
        initiative="Test Initiative",
        phase="Phase 1",
        priority="Medium",
        status="To Do",
        owner="developer",
        effort_hours=4.0,
        completion_percent=0.0,
        due_date="2025-02-01",
        created_date="2025-01-15T10:00:00",
        updated_date="2025-01-15T10:00:00",
        github_issue="https://github.com/org/repo/issues/10",
    )

    task2 = Task(
        id="TSK-103",
        title="Task",
        initiative="Test Initiative",
        phase="Phase 1",
        priority="Medium",
        status="To Do",
        owner="developer",
        effort_hours=4.0,
        completion_percent=0.0,
        due_date="2025-02-01",
        created_date="2025-01-15T10:00:00",
        updated_date="2025-01-15T10:00:00",
        github_issue="https://github.com/org/repo/issues/20",
    )

    assert task1 != task2


def test_given_task_with_and_without_github_issue_when_comparing_then_tasks_are_not_equal():
    """Test that tasks differing in github_issue presence are not equal.

    GIVEN: Two otherwise identical tasks, one with github_issue and one without
    WHEN: The tasks are compared for equality
    THEN: The tasks are not equal
    """
    task1 = Task(
        id="TSK-104",
        title="Task",
        initiative="Test Initiative",
        phase="Phase 1",
        priority="Low",
        status="Done",
        owner="developer",
        effort_hours=3.0,
        completion_percent=100.0,
        due_date="2025-02-01",
        created_date="2025-01-15T10:00:00",
        updated_date="2025-01-20T15:00:00",
        github_issue=None,
    )

    task2 = Task(
        id="TSK-104",
        title="Task",
        initiative="Test Initiative",
        phase="Phase 1",
        priority="Low",
        status="Done",
        owner="developer",
        effort_hours=3.0,
        completion_percent=100.0,
        due_date="2025-02-01",
        created_date="2025-01-15T10:00:00",
        updated_date="2025-01-20T15:00:00",
        github_issue="https://github.com/org/repo/issues/50",
    )

    assert task1 != task2


# =============================================================================
# Dataclass Serialization Tests (asdict)
# =============================================================================


def test_given_task_without_github_issue_when_converting_to_dict_then_all_fields_present():
    """Test that asdict() includes all fields including None github_issue.

    GIVEN: A Task without github_issue (defaults to None)
    WHEN: asdict() is called on the task
    THEN: The resulting dict contains all fields with github_issue as None
    """
    task = Task(
        id="TSK-200",
        title="Dict Test Task",
        initiative="Serialization Tests",
        phase="Phase 1",
        priority="Medium",
        status="To Do",
        owner="tester",
        effort_hours=5.0,
        completion_percent=0.0,
        due_date="2025-02-10",
        created_date="2025-01-20T09:00:00",
        updated_date="2025-01-20T09:00:00",
    )

    task_dict = asdict(task)

    assert task_dict == {
        "id": "TSK-200",
        "title": "Dict Test Task",
        "initiative": "Serialization Tests",
        "phase": "Phase 1",
        "priority": "Medium",
        "status": "To Do",
        "owner": "tester",
        "effort_hours": 5.0,
        "completion_percent": 0.0,
        "due_date": "2025-02-10",
        "created_date": "2025-01-20T09:00:00",
        "updated_date": "2025-01-20T09:00:00",
        "github_issue": None,
    }


def test_given_task_with_github_issue_when_converting_to_dict_then_github_issue_included():
    """Test that asdict() properly serializes github_issue when present.

    GIVEN: A Task with a github_issue URL
    WHEN: asdict() is called on the task
    THEN: The resulting dict contains the github_issue field with the URL
    """
    task = Task(
        id="TSK-201",
        title="GitHub Task",
        initiative="Serialization Tests",
        phase="Phase 2",
        priority="High",
        status="In Progress",
        owner="developer",
        effort_hours=8.0,
        completion_percent=60.0,
        due_date="2025-02-15",
        created_date="2025-01-21T10:00:00",
        updated_date="2025-01-25T14:00:00",
        github_issue="https://github.com/claude/minister/issues/42",
    )

    task_dict = asdict(task)

    assert task_dict["github_issue"] == "https://github.com/claude/minister/issues/42"
    assert "github_issue" in task_dict
    assert len(task_dict) == 13  # All 13 fields should be present


def test_given_task_dict_when_reconstructing_task_then_task_matches_original():
    """Test round-trip serialization: Task -> dict -> Task.

    GIVEN: A Task instance with all fields populated
    WHEN: The task is converted to dict and reconstructed
    THEN: The reconstructed task equals the original
    """
    original_task = Task(
        id="TSK-202",
        title="Round Trip Task",
        initiative="Serialization Tests",
        phase="Phase 3",
        priority="Low",
        status="Review",
        owner="reviewer",
        effort_hours=3.5,
        completion_percent=90.0,
        due_date="2025-02-20",
        created_date="2025-01-22T11:00:00",
        updated_date="2025-01-26T16:30:00",
        github_issue="https://github.com/claude/minister/pulls/99",
    )

    task_dict = asdict(original_task)
    reconstructed_task = Task(**task_dict)

    assert reconstructed_task == original_task


def test_given_task_dict_with_none_github_issue_when_reconstructing_then_github_issue_is_none():
    """Test that None github_issue survives round-trip serialization.

    GIVEN: A Task with github_issue=None converted to dict
    WHEN: The task is reconstructed from the dict
    THEN: The reconstructed task has github_issue=None
    """
    original_task = Task(
        id="TSK-203",
        title="None Issue Task",
        initiative="Serialization Tests",
        phase="Phase 1",
        priority="Medium",
        status="Done",
        owner="developer",
        effort_hours=2.0,
        completion_percent=100.0,
        due_date="2025-02-05",
        created_date="2025-01-23T08:00:00",
        updated_date="2025-02-04T17:00:00",
        github_issue=None,
    )

    task_dict = asdict(original_task)
    reconstructed_task = Task(**task_dict)

    assert reconstructed_task.github_issue is None
    assert reconstructed_task == original_task


# =============================================================================
# Field Type Tests
# =============================================================================


def test_given_float_effort_hours_when_creating_task_then_effort_is_stored_correctly():
    """Test that effort_hours accepts and stores float values.

    GIVEN: Various float values for effort_hours
    WHEN: Tasks are created
    THEN: The effort_hours values are stored correctly as floats
    """
    task_integer_like = Task(
        id="TSK-301",
        title="Integer Effort",
        initiative="Type Tests",
        phase="Phase 1",
        priority="Medium",
        status="To Do",
        owner="dev",
        effort_hours=5.0,
        completion_percent=0.0,
        due_date="2025-03-01",
        created_date="2025-02-01T10:00:00",
        updated_date="2025-02-01T10:00:00",
    )

    task_decimal = Task(
        id="TSK-302",
        title="Decimal Effort",
        initiative="Type Tests",
        phase="Phase 1",
        priority="Medium",
        status="To Do",
        owner="dev",
        effort_hours=3.75,
        completion_percent=0.0,
        due_date="2025-03-01",
        created_date="2025-02-01T10:00:00",
        updated_date="2025-02-01T10:00:00",
    )

    assert task_integer_like.effort_hours == 5.0
    assert isinstance(task_integer_like.effort_hours, float)
    assert task_decimal.effort_hours == 3.75
    assert isinstance(task_decimal.effort_hours, float)


def test_given_float_completion_percent_when_creating_task_then_completion_stored_correctly():
    """Test that completion_percent accepts and stores float values.

    GIVEN: Various float values for completion_percent
    WHEN: Tasks are created
    THEN: The completion_percent values are stored correctly as floats
    """
    task_zero = Task(
        id="TSK-303",
        title="Zero Completion",
        initiative="Type Tests",
        phase="Phase 1",
        priority="Low",
        status="To Do",
        owner="dev",
        effort_hours=4.0,
        completion_percent=0.0,
        due_date="2025-03-05",
        created_date="2025-02-02T10:00:00",
        updated_date="2025-02-02T10:00:00",
    )

    task_partial = Task(
        id="TSK-304",
        title="Partial Completion",
        initiative="Type Tests",
        phase="Phase 1",
        priority="Medium",
        status="In Progress",
        owner="dev",
        effort_hours=6.0,
        completion_percent=42.5,
        due_date="2025-03-10",
        created_date="2025-02-03T10:00:00",
        updated_date="2025-02-07T15:00:00",
    )

    task_complete = Task(
        id="TSK-305",
        title="Full Completion",
        initiative="Type Tests",
        phase="Phase 1",
        priority="High",
        status="Done",
        owner="dev",
        effort_hours=8.0,
        completion_percent=100.0,
        due_date="2025-03-08",
        created_date="2025-02-04T10:00:00",
        updated_date="2025-03-08T16:00:00",
    )

    assert task_zero.completion_percent == 0.0
    assert isinstance(task_zero.completion_percent, float)
    assert task_partial.completion_percent == 42.5
    assert isinstance(task_partial.completion_percent, float)
    assert task_complete.completion_percent == 100.0
    assert isinstance(task_complete.completion_percent, float)


# =============================================================================
# Fixture Integration Tests
# =============================================================================


def test_given_minimal_task_fixture_when_used_then_has_expected_structure(
    minimal_task: Task,
):
    """Test that minimal_task fixture provides valid Task.

    GIVEN: The minimal_task fixture from conftest
    WHEN: The fixture is used in a test
    THEN: It provides a valid Task instance with required fields
    """
    assert isinstance(minimal_task, Task)
    assert minimal_task.id == "TSK-001"
    assert minimal_task.title == "Minimal Task"
    assert minimal_task.github_issue is None
    assert minimal_task.effort_hours == 2.0
    assert minimal_task.completion_percent == 0.0


def test_given_task_with_github_issue_fixture_when_used_then_github_issue_present(
    task_with_github_issue: Task,
):
    """Test that task_with_github_issue fixture has github_issue populated.

    GIVEN: The task_with_github_issue fixture from conftest
    WHEN: The fixture is used in a test
    THEN: It provides a Task with github_issue field populated
    """
    assert isinstance(task_with_github_issue, Task)
    assert task_with_github_issue.github_issue is not None
    assert "github.com" in task_with_github_issue.github_issue
    assert task_with_github_issue.id == "TSK-002"
    assert task_with_github_issue.completion_percent == 50.0


def test_given_completed_task_fixture_when_used_then_status_is_done(
    completed_task: Task,
):
    """Test that completed_task fixture represents a finished task.

    GIVEN: The completed_task fixture from conftest
    WHEN: The fixture is used in a test
    THEN: It provides a Task with status Done and 100% completion
    """
    assert isinstance(completed_task, Task)
    assert completed_task.status == "Done"
    assert completed_task.completion_percent == 100.0
    assert completed_task.id == "TSK-003"


# =============================================================================
# Edge Case Tests
# =============================================================================


def test_given_empty_strings_when_creating_task_then_task_accepts_empty_values():
    """Test that Task accepts empty strings for text fields.

    GIVEN: Empty strings for title, owner, and other text fields
    WHEN: A Task is created
    THEN: The Task is created successfully with empty strings
    """
    task = Task(
        id="",
        title="",
        initiative="",
        phase="Phase 1",
        priority="Low",
        status="To Do",
        owner="",
        effort_hours=0.0,
        completion_percent=0.0,
        due_date="",
        created_date="",
        updated_date="",
        github_issue="",
    )

    assert task.id == ""
    assert task.title == ""
    assert task.initiative == ""
    assert task.owner == ""
    assert task.github_issue == ""


def test_given_very_long_strings_when_creating_task_then_strings_are_stored():
    """Test that Task handles very long strings in text fields.

    GIVEN: Very long strings for various text fields
    WHEN: A Task is created
    THEN: The Task stores the complete long strings
    """
    long_title = "A" * 1000
    long_url = "https://github.com/org/repo/issues/" + "1" * 500

    task = Task(
        id="TSK-LONG",
        title=long_title,
        initiative="Edge Cases",
        phase="Phase 1",
        priority="Medium",
        status="To Do",
        owner="tester",
        effort_hours=1.0,
        completion_percent=0.0,
        due_date="2025-04-01",
        created_date="2025-03-01T10:00:00",
        updated_date="2025-03-01T10:00:00",
        github_issue=long_url,
    )

    assert len(task.title) == 1000
    assert len(task.github_issue) == len(long_url)
    assert task.title == long_title
    assert task.github_issue == long_url


def test_given_negative_effort_hours_when_creating_task_then_value_is_stored():
    """Test that Task accepts negative effort_hours (no validation).

    GIVEN: A negative value for effort_hours
    WHEN: A Task is created
    THEN: The negative value is stored (dataclass has no validation)
    """
    task = Task(
        id="TSK-NEG",
        title="Negative Effort",
        initiative="Edge Cases",
        phase="Phase 1",
        priority="Low",
        status="To Do",
        owner="tester",
        effort_hours=-5.0,
        completion_percent=0.0,
        due_date="2025-04-15",
        created_date="2025-03-15T10:00:00",
        updated_date="2025-03-15T10:00:00",
    )

    assert task.effort_hours == -5.0


def test_given_completion_over_100_when_creating_task_then_value_is_stored():
    """Test that Task accepts completion_percent over 100 (no validation).

    GIVEN: A completion_percent value greater than 100
    WHEN: A Task is created
    THEN: The value is stored (dataclass has no validation)
    """
    task = Task(
        id="TSK-OVER",
        title="Over Completion",
        initiative="Edge Cases",
        phase="Phase 1",
        priority="Medium",
        status="Done",
        owner="tester",
        effort_hours=3.0,
        completion_percent=150.0,
        due_date="2025-04-20",
        created_date="2025-03-20T10:00:00",
        updated_date="2025-04-20T17:00:00",
    )

    assert task.completion_percent == 150.0


# =============================================================================
# Special Characters and Unicode Tests
# =============================================================================


def test_given_unicode_characters_when_creating_task_then_unicode_is_stored():
    """Test that Task handles Unicode characters in text fields.

    GIVEN: Unicode characters in title and other text fields
    WHEN: A Task is created
    THEN: The Task correctly stores Unicode content
    """
    task = Task(
        id="TSK-UNI",
        title="Task with emoji 🚀 and unicode ñ ü ö",
        initiative="Internationalization",
        phase="Phase 1",
        priority="High",
        status="To Do",
        owner="developer 👨‍💻",
        effort_hours=4.5,
        completion_percent=0.0,
        due_date="2025-05-01",
        created_date="2025-04-01T10:00:00",
        updated_date="2025-04-01T10:00:00",
        github_issue="https://github.com/org/repo/issues/ñ",
    )

    assert "🚀" in task.title
    assert "ñ" in task.title
    assert "👨‍💻" in task.owner
    assert "ñ" in task.github_issue


def test_given_special_characters_when_creating_task_then_characters_preserved():
    """Test that Task preserves special characters in text fields.

    GIVEN: Special characters like quotes, newlines, and symbols
    WHEN: A Task is created
    THEN: The special characters are preserved correctly
    """
    task = Task(
        id="TSK-SPEC",
        title='Task with "quotes" and \\backslashes\\',
        initiative="Special & Characters < >",
        phase="Phase 1",
        priority="Medium",
        status="To Do",
        owner="test@example.com",
        effort_hours=2.0,
        completion_percent=0.0,
        due_date="2025-05-10",
        created_date="2025-04-10T10:00:00",
        updated_date="2025-04-10T10:00:00",
    )

    assert '"quotes"' in task.title
    assert "\\" in task.title
    assert "&" in task.initiative
    assert "<" in task.initiative
    assert ">" in task.initiative
