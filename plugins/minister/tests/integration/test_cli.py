"""Integration tests for Minister CLI commands.

Tests the full CLI workflow end-to-end including:
- Command parsing and validation
- Data persistence across CLI calls
- Output generation and formatting
- Error handling for invalid inputs
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from minister.project_tracker import (
    ProjectTracker,
    build_cli_parser,
    run_cli,
)

# =============================================================================
# CLI Parser Tests: Argument validation and command structure
# =============================================================================


def test_cli_parser_add_command_with_all_required_arguments() -> None:
    """Test that add command parses successfully with all required arguments."""
    parser = build_cli_parser()
    args = parser.parse_args(
        [
            "add",
            "--id",
            "TSK-001",
            "--title",
            "Test Task",
            "--initiative",
            "Test Initiative",
            "--phase",
            "Phase 1",
            "--priority",
            "High",
            "--owner",
            "tester",
            "--effort",
            "5.0",
            "--due",
            "2025-01-15",
        ],
    )

    assert args.command == "add"
    assert args.id == "TSK-001"
    assert args.title == "Test Task"
    assert args.initiative == "Test Initiative"
    assert args.phase == "Phase 1"
    assert args.priority == "High"
    assert args.owner == "tester"
    assert args.effort == 5.0
    assert args.due == "2025-01-15"
    assert args.github_issue is None


def test_cli_parser_add_command_with_github_issue() -> None:
    """Test that add command accepts optional github-issue argument."""
    parser = build_cli_parser()
    args = parser.parse_args(
        [
            "add",
            "--id",
            "TSK-002",
            "--title",
            "GitHub Task",
            "--initiative",
            "GitHub Projects Hygiene",
            "--phase",
            "Phase 2",
            "--priority",
            "Medium",
            "--owner",
            "dev",
            "--effort",
            "3.5",
            "--due",
            "2025-01-20",
            "--github-issue",
            "https://github.com/org/repo/issues/42",
        ],
    )

    assert args.command == "add"
    assert args.github_issue == "https://github.com/org/repo/issues/42"


def test_cli_parser_add_command_rejects_missing_required_argument() -> None:
    """Test that add command fails when required arguments are missing."""
    parser = build_cli_parser()

    with pytest.raises(SystemExit):
        parser.parse_args(
            [
                "add",
                "--id",
                "TSK-001",
                "--title",
                "Incomplete Task",
                # Missing --initiative, --phase, --priority, --owner, --effort, --due
            ],
        )


def test_cli_parser_add_command_rejects_invalid_phase() -> None:
    """Test that add command rejects invalid phase values."""
    parser = build_cli_parser()

    with pytest.raises(SystemExit):
        parser.parse_args(
            [
                "add",
                "--id",
                "TSK-001",
                "--title",
                "Bad Phase",
                "--initiative",
                "Test",
                "--phase",
                "Invalid Phase",  # Not in choices
                "--priority",
                "High",
                "--owner",
                "tester",
                "--effort",
                "2.0",
                "--due",
                "2025-01-15",
            ],
        )


def test_cli_parser_add_command_rejects_invalid_priority() -> None:
    """Test that add command rejects invalid priority values."""
    parser = build_cli_parser()

    with pytest.raises(SystemExit):
        parser.parse_args(
            [
                "add",
                "--id",
                "TSK-001",
                "--title",
                "Bad Priority",
                "--initiative",
                "Test",
                "--phase",
                "Phase 1",
                "--priority",
                "Critical",  # Not in choices
                "--owner",
                "tester",
                "--effort",
                "2.0",
                "--due",
                "2025-01-15",
            ],
        )


def test_cli_parser_update_command_with_status() -> None:
    """Test that update command parses status change correctly."""
    parser = build_cli_parser()
    args = parser.parse_args(
        [
            "update",
            "--id",
            "TSK-001",
            "--status",
            "In Progress",
        ],
    )

    assert args.command == "update"
    assert args.id == "TSK-001"
    assert args.status == "In Progress"
    assert args.completion is None
    assert args.github_issue is None


def test_cli_parser_update_command_with_completion() -> None:
    """Test that update command parses completion percentage correctly."""
    parser = build_cli_parser()
    args = parser.parse_args(
        [
            "update",
            "--id",
            "TSK-002",
            "--completion",
            "75.5",
        ],
    )

    assert args.command == "update"
    assert args.id == "TSK-002"
    assert args.completion == 75.5
    assert args.status is None


def test_cli_parser_update_command_with_multiple_fields() -> None:
    """Test that update command can update multiple fields simultaneously."""
    parser = build_cli_parser()
    args = parser.parse_args(
        [
            "update",
            "--id",
            "TSK-003",
            "--status",
            "Done",
            "--completion",
            "100.0",
            "--github-issue",
            "https://github.com/org/repo/pull/123",
        ],
    )

    assert args.command == "update"
    assert args.id == "TSK-003"
    assert args.status == "Done"
    assert args.completion == 100.0
    assert args.github_issue == "https://github.com/org/repo/pull/123"


def test_cli_parser_update_command_requires_task_id() -> None:
    """Test that update command fails without task ID."""
    parser = build_cli_parser()

    with pytest.raises(SystemExit):
        parser.parse_args(
            [
                "update",
                "--status",
                "Done",
            ],
        )


def test_cli_parser_update_command_rejects_invalid_status() -> None:
    """Test that update command rejects invalid status values."""
    parser = build_cli_parser()

    with pytest.raises(SystemExit):
        parser.parse_args(
            [
                "update",
                "--id",
                "TSK-001",
                "--status",
                "Pending",  # Not in choices
            ],
        )


def test_cli_parser_status_command_without_flags() -> None:
    """Test that status command parses without optional flags."""
    parser = build_cli_parser()
    args = parser.parse_args(["status"])

    assert args.command == "status"
    assert args.github_comment is False


def test_cli_parser_status_command_with_github_comment_flag() -> None:
    """Test that status command accepts github-comment flag."""
    parser = build_cli_parser()
    args = parser.parse_args(["status", "--github-comment"])

    assert args.command == "status"
    assert args.github_comment is True


def test_cli_parser_export_command_with_output_path() -> None:
    """Test that export command parses output path correctly."""
    parser = build_cli_parser()
    args = parser.parse_args(
        [
            "export",
            "--output",
            "tasks.csv",
        ],
    )

    assert args.command == "export"
    assert args.output == "tasks.csv"


def test_cli_parser_export_command_requires_output_path() -> None:
    """Test that export command fails without output path."""
    parser = build_cli_parser()

    with pytest.raises(SystemExit):
        parser.parse_args(["export"])


def test_cli_parser_no_command_shows_help() -> None:
    """Test that parser without command returns None for command."""
    parser = build_cli_parser()
    args = parser.parse_args([])

    assert args.command is None


def test_cli_parser_invalid_command_rejected() -> None:
    """Test that parser rejects invalid commands."""
    parser = build_cli_parser()

    with pytest.raises(SystemExit):
        parser.parse_args(["invalid-command"])


# =============================================================================
# CLI Integration Tests: End-to-end workflow with data persistence
# =============================================================================


@pytest.fixture
def cli_with_temp_data(temp_data_file: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Fixture that patches ProjectTracker to use temp_data_file for CLI tests."""
    original_init = ProjectTracker.__init__

    def patched_init(self, data_file=None, initiatives=None):
        original_init(self, data_file=temp_data_file, initiatives=initiatives)

    monkeypatch.setattr(ProjectTracker, "__init__", patched_init)
    return temp_data_file


@pytest.fixture
def cli_with_seeded_data(
    seeded_data_file: Path, monkeypatch: pytest.MonkeyPatch
) -> Path:
    """Fixture that patches ProjectTracker to use seeded_data_file for CLI tests."""
    original_init = ProjectTracker.__init__

    def patched_init(self, data_file=None, initiatives=None):
        original_init(self, data_file=seeded_data_file, initiatives=initiatives)

    monkeypatch.setattr(ProjectTracker, "__init__", patched_init)
    return seeded_data_file


def test_cli_add_command_creates_task_and_persists_to_file(
    cli_with_temp_data: Path,
) -> None:
    """Test that add command creates a task and saves it to the data file."""
    temp_data_file = cli_with_temp_data

    # Run CLI add command
    result = run_cli(
        [
            "add",
            "--id",
            "CLI-001",
            "--title",
            "CLI Test Task",
            "--initiative",
            "Test Initiative",
            "--phase",
            "Phase 1",
            "--priority",
            "High",
            "--owner",
            "cli-tester",
            "--effort",
            "4.5",
            "--due",
            "2025-01-20",
        ],
    )

    assert result == 0

    # Verify task was persisted to file
    assert temp_data_file.exists()
    with open(temp_data_file, encoding="utf-8") as f:
        data = json.load(f)

    assert len(data["tasks"]) == 1
    task = data["tasks"][0]
    assert task["id"] == "CLI-001"
    assert task["title"] == "CLI Test Task"
    assert task["initiative"] == "Test Initiative"
    assert task["phase"] == "Phase 1"
    assert task["priority"] == "High"
    assert task["status"] == "To Do"
    assert task["owner"] == "cli-tester"
    assert task["effort_hours"] == 4.5
    assert task["completion_percent"] == 0.0
    assert task["due_date"] == "2025-01-20"
    assert task["github_issue"] is None


def test_cli_add_command_with_github_issue_persists_correctly(
    cli_with_temp_data: Path,
) -> None:
    """Test that add command with GitHub issue saves the URL correctly."""
    temp_data_file = cli_with_temp_data

    result = run_cli(
        [
            "add",
            "--id",
            "CLI-002",
            "--title",
            "GitHub Task",
            "--initiative",
            "GitHub Projects Hygiene",
            "--phase",
            "Phase 2",
            "--priority",
            "Medium",
            "--owner",
            "dev",
            "--effort",
            "6.0",
            "--due",
            "2025-01-25",
            "--github-issue",
            "https://github.com/test/repo/issues/99",
        ],
    )

    assert result == 0

    with open(temp_data_file, encoding="utf-8") as f:
        data = json.load(f)

    task = data["tasks"][0]
    assert task["github_issue"] == "https://github.com/test/repo/issues/99"


def test_cli_add_multiple_tasks_accumulates_in_data_file(
    cli_with_temp_data: Path,
) -> None:
    """Test that adding multiple tasks via CLI accumulates them in the data file."""
    temp_data_file = cli_with_temp_data

    # Add first task
    run_cli(
        [
            "add",
            "--id",
            "MULTI-001",
            "--title",
            "First Task",
            "--initiative",
            "Test",
            "--phase",
            "Phase 1",
            "--priority",
            "High",
            "--owner",
            "user1",
            "--effort",
            "2.0",
            "--due",
            "2025-01-15",
        ],
    )

    # Add second task
    run_cli(
        [
            "add",
            "--id",
            "MULTI-002",
            "--title",
            "Second Task",
            "--initiative",
            "Test",
            "--phase",
            "Phase 2",
            "--priority",
            "Low",
            "--owner",
            "user2",
            "--effort",
            "3.0",
            "--due",
            "2025-01-20",
        ],
    )

    # Add third task
    run_cli(
        [
            "add",
            "--id",
            "MULTI-003",
            "--title",
            "Third Task",
            "--initiative",
            "Different Initiative",
            "--phase",
            "Phase 1",
            "--priority",
            "Medium",
            "--owner",
            "user3",
            "--effort",
            "1.5",
            "--due",
            "2025-01-18",
        ],
    )

    # Verify all tasks are in file
    with open(temp_data_file, encoding="utf-8") as f:
        data = json.load(f)

    assert len(data["tasks"]) == 3
    task_ids = {task["id"] for task in data["tasks"]}
    assert task_ids == {"MULTI-001", "MULTI-002", "MULTI-003"}


def test_cli_update_command_modifies_task_status(cli_with_seeded_data: Path) -> None:
    """Test that update command changes task status and persists to file."""
    seeded_data_file = cli_with_seeded_data

    # Update the first task's status
    result = run_cli(
        [
            "update",
            "--id",
            "GHYG-001",
            "--status",
            "In Progress",
        ],
    )

    assert result == 0

    # Verify update was persisted
    with open(seeded_data_file, encoding="utf-8") as f:
        data = json.load(f)

    task = next(t for t in data["tasks"] if t["id"] == "GHYG-001")
    assert task["status"] == "In Progress"
    # Original task was Done, so this is a real change
    assert task["updated_date"] != task["created_date"]


def test_cli_update_command_modifies_task_completion(
    cli_with_seeded_data: Path,
) -> None:
    """Test that update command changes task completion percentage."""
    seeded_data_file = cli_with_seeded_data

    result = run_cli(
        [
            "update",
            "--id",
            "PR-001",
            "--completion",
            "45.5",
        ],
    )

    assert result == 0

    with open(seeded_data_file, encoding="utf-8") as f:
        data = json.load(f)

    task = next(t for t in data["tasks"] if t["id"] == "PR-001")
    assert task["completion_percent"] == 45.5


def test_cli_update_command_adds_github_issue_to_existing_task(
    cli_with_seeded_data: Path,
) -> None:
    """Test that update command can add GitHub issue URL to existing task."""
    seeded_data_file = cli_with_seeded_data

    result = run_cli(
        [
            "update",
            "--id",
            "DOC-002",
            "--github-issue",
            "https://github.com/org/repo/pull/789",
        ],
    )

    assert result == 0

    with open(seeded_data_file, encoding="utf-8") as f:
        data = json.load(f)

    task = next(t for t in data["tasks"] if t["id"] == "DOC-002")
    assert task["github_issue"] == "https://github.com/org/repo/pull/789"


def test_cli_update_command_with_multiple_fields_updates_all(
    cli_with_seeded_data: Path,
) -> None:
    """Test that update command can modify multiple fields simultaneously."""
    seeded_data_file = cli_with_seeded_data

    result = run_cli(
        [
            "update",
            "--id",
            "GHYG-002",
            "--status",
            "Done",
            "--completion",
            "100.0",
            "--github-issue",
            "https://github.com/org/repo/issues/456",
        ],
    )

    assert result == 0

    with open(seeded_data_file, encoding="utf-8") as f:
        data = json.load(f)

    task = next(t for t in data["tasks"] if t["id"] == "GHYG-002")
    assert task["status"] == "Done"
    assert task["completion_percent"] == 100.0
    assert task["github_issue"] == "https://github.com/org/repo/issues/456"


def test_cli_update_nonexistent_task_completes_without_error(
    cli_with_seeded_data: Path,
) -> None:
    """Test that updating a nonexistent task completes successfully without changes."""
    seeded_data_file = cli_with_seeded_data

    result = run_cli(
        [
            "update",
            "--id",
            "NONEXISTENT-999",
            "--status",
            "Done",
        ],
    )

    assert result == 0

    # Data should be unchanged (except timestamp)
    with open(seeded_data_file, encoding="utf-8") as f:
        data = json.load(f)

    # No task with this ID exists
    assert not any(t["id"] == "NONEXISTENT-999" for t in data["tasks"])


def test_cli_status_command_executes_successfully(cli_with_seeded_data: Path) -> None:
    """Test that status command runs without errors on populated data."""
    result = run_cli(["status"])

    assert result == 0


def test_cli_status_command_with_github_comment_flag_executes(
    cli_with_seeded_data: Path,
) -> None:
    """Test that status command with --github-comment flag runs successfully."""
    result = run_cli(["status", "--github-comment"])

    assert result == 0


def test_cli_export_command_creates_csv_file(
    cli_with_seeded_data: Path,
    temp_data_dir: Path,
) -> None:
    """Test that export command creates a CSV file with task data."""
    output_csv = temp_data_dir / "export.csv"

    result = run_cli(
        [
            "export",
            "--output",
            str(output_csv),
        ],
    )

    assert result == 0
    assert output_csv.exists()


def test_cli_export_command_csv_has_correct_headers(
    cli_with_seeded_data: Path,
    temp_data_dir: Path,
) -> None:
    """Test that exported CSV has the correct column headers."""
    output_csv = temp_data_dir / "export_headers.csv"

    run_cli(
        [
            "export",
            "--output",
            str(output_csv),
        ],
    )

    with open(output_csv, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames

    expected_headers = [
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
    assert headers == expected_headers


def test_cli_export_command_csv_contains_all_tasks(
    cli_with_seeded_data: Path,
    temp_data_dir: Path,
) -> None:
    """Test that exported CSV contains all tasks from the data file."""
    output_csv = temp_data_dir / "export_all.csv"

    run_cli(
        [
            "export",
            "--output",
            str(output_csv),
        ],
    )

    with open(output_csv, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # seeded_data_file fixture has 5 sample_tasks
    assert len(rows) == 5

    task_ids = {row["id"] for row in rows}
    expected_ids = {"GHYG-001", "GHYG-002", "PR-001", "DOC-001", "DOC-002"}
    assert task_ids == expected_ids


def test_cli_export_command_csv_task_data_matches_source(
    cli_with_seeded_data: Path,
    temp_data_dir: Path,
) -> None:
    """Test that CSV export contains accurate task data matching the source."""
    seeded_data_file = cli_with_seeded_data
    output_csv = temp_data_dir / "export_accuracy.csv"

    run_cli(
        [
            "export",
            "--output",
            str(output_csv),
        ],
    )

    # Load original data
    with open(seeded_data_file, encoding="utf-8") as f:
        original_data = json.load(f)

    # Load exported CSV
    with open(output_csv, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        csv_tasks = {row["id"]: row for row in reader}

    # Verify a specific task's data
    original_task = next(t for t in original_data["tasks"] if t["id"] == "DOC-001")
    csv_task = csv_tasks["DOC-001"]

    assert csv_task["title"] == original_task["title"]
    assert csv_task["initiative"] == original_task["initiative"]
    assert csv_task["phase"] == original_task["phase"]
    assert csv_task["priority"] == original_task["priority"]
    assert csv_task["status"] == original_task["status"]
    assert csv_task["owner"] == original_task["owner"]
    assert float(csv_task["effort_hours"]) == original_task["effort_hours"]
    assert float(csv_task["completion_percent"]) == original_task["completion_percent"]
    assert csv_task["due_date"] == original_task["due_date"]


def test_cli_no_command_returns_success(cli_with_temp_data: Path) -> None:
    """Test that running CLI without command returns success (prints help)."""
    result = run_cli([])

    assert result == 0


# =============================================================================
# Cross-command Integration Tests: Workflows spanning multiple CLI calls
# =============================================================================


def test_full_task_lifecycle_via_cli(
    cli_with_temp_data: Path, temp_data_dir: Path
) -> None:
    """Test complete task lifecycle: add, update status, update completion, export."""
    temp_data_file = cli_with_temp_data

    # Step 1: Add a new task
    run_cli(
        [
            "add",
            "--id",
            "LIFE-001",
            "--title",
            "Lifecycle Task",
            "--initiative",
            "Full Test",
            "--phase",
            "Phase 1",
            "--priority",
            "High",
            "--owner",
            "lifecycle-tester",
            "--effort",
            "8.0",
            "--due",
            "2025-02-01",
        ],
    )

    # Verify task was created
    tracker = ProjectTracker(data_file=temp_data_file)
    assert len(tracker.data.tasks) == 1
    task = tracker.data.tasks[0]
    assert task.id == "LIFE-001"
    assert task.status == "To Do"
    assert task.completion_percent == 0.0

    # Step 2: Start working on the task
    run_cli(
        [
            "update",
            "--id",
            "LIFE-001",
            "--status",
            "In Progress",
            "--completion",
            "25.0",
        ],
    )

    # Reload and verify update
    tracker = ProjectTracker(data_file=temp_data_file)
    task = tracker.data.tasks[0]
    assert task.status == "In Progress"
    assert task.completion_percent == 25.0

    # Step 3: Move to review
    run_cli(
        [
            "update",
            "--id",
            "LIFE-001",
            "--status",
            "Review",
            "--completion",
            "90.0",
            "--github-issue",
            "https://github.com/test/repo/pull/100",
        ],
    )

    # Verify review state
    tracker = ProjectTracker(data_file=temp_data_file)
    task = tracker.data.tasks[0]
    assert task.status == "Review"
    assert task.completion_percent == 90.0
    assert task.github_issue == "https://github.com/test/repo/pull/100"

    # Step 4: Complete the task
    run_cli(
        [
            "update",
            "--id",
            "LIFE-001",
            "--status",
            "Done",
            "--completion",
            "100.0",
        ],
    )

    # Verify completion
    tracker = ProjectTracker(data_file=temp_data_file)
    task = tracker.data.tasks[0]
    assert task.status == "Done"
    assert task.completion_percent == 100.0

    # Step 5: Export to CSV
    output_csv = temp_data_dir / "lifecycle.csv"
    run_cli(["export", "--output", str(output_csv)])

    # Verify export
    with open(output_csv, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 1
    assert rows[0]["id"] == "LIFE-001"
    assert rows[0]["status"] == "Done"
    assert float(rows[0]["completion_percent"]) == 100.0


def test_multiple_initiatives_workflow(
    cli_with_temp_data: Path, temp_data_dir: Path
) -> None:
    """Test workflow with tasks across multiple initiatives."""
    temp_data_file = cli_with_temp_data

    # Add tasks to different initiatives
    initiatives = [
        "GitHub Projects Hygiene",
        "Pull Request Readiness",
        "Docs & Enablement",
    ]

    for i, initiative in enumerate(initiatives, start=1):
        run_cli(
            [
                "add",
                "--id",
                f"INIT-{i:03d}",
                "--title",
                f"Task for {initiative}",
                "--initiative",
                initiative,
                "--phase",
                "Phase 1",
                "--priority",
                "Medium",
                "--owner",
                f"owner{i}",
                "--effort",
                str(float(i * 2)),
                "--due",
                f"2025-01-{15 + i:02d}",
            ],
        )

    # Verify all tasks exist
    tracker = ProjectTracker(data_file=temp_data_file)
    assert len(tracker.data.tasks) == 3

    task_initiatives = {task.initiative for task in tracker.data.tasks}
    assert task_initiatives == set(initiatives)

    # Run status command
    result = run_cli(["status"])
    assert result == 0

    # Export to CSV
    output_csv = temp_data_dir / "multi_init.csv"
    run_cli(["export", "--output", str(output_csv)])

    # Verify CSV contains all initiatives
    with open(output_csv, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    csv_initiatives = {row["initiative"] for row in rows}
    assert csv_initiatives == set(initiatives)


def test_empty_tracker_status_and_export(
    cli_with_temp_data: Path, temp_data_dir: Path
) -> None:
    """Test that status and export commands work on empty tracker."""
    # Run status on empty tracker
    result = run_cli(["status"])
    assert result == 0

    # Export empty tracker to CSV
    output_csv = temp_data_dir / "empty.csv"
    result = run_cli(["export", "--output", str(output_csv)])
    assert result == 0

    # Verify CSV exists with only headers
    with open(output_csv, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 0  # No data rows, just headers


# =============================================================================
# Edge Cases and Error Conditions
# =============================================================================


def test_cli_update_with_no_fields_specified_completes_successfully(
    seeded_data_file: Path,
) -> None:
    """Test that update command with only ID (no fields to update) completes without error."""
    result = run_cli(
        [
            "update",
            "--id",
            "GHYG-001",
        ],
    )

    # Should complete successfully even though no updates are applied
    assert result == 0


def test_cli_add_task_with_fractional_effort_hours(cli_with_temp_data: Path) -> None:
    """Test that add command correctly handles fractional effort hours."""
    temp_data_file = cli_with_temp_data

    result = run_cli(
        [
            "add",
            "--id",
            "FRAC-001",
            "--title",
            "Fractional Effort",
            "--initiative",
            "Test",
            "--phase",
            "Phase 1",
            "--priority",
            "Low",
            "--owner",
            "tester",
            "--effort",
            "0.5",
            "--due",
            "2025-01-30",
        ],
    )

    assert result == 0

    with open(temp_data_file, encoding="utf-8") as f:
        data = json.load(f)

    task = data["tasks"][0]
    assert task["effort_hours"] == 0.5


def test_cli_update_task_completion_with_decimal(cli_with_seeded_data: Path) -> None:
    """Test that update command handles decimal completion percentages."""
    seeded_data_file = cli_with_seeded_data

    result = run_cli(
        [
            "update",
            "--id",
            "PR-001",
            "--completion",
            "33.33",
        ],
    )

    assert result == 0

    with open(seeded_data_file, encoding="utf-8") as f:
        data = json.load(f)

    task = next(t for t in data["tasks"] if t["id"] == "PR-001")
    assert task["completion_percent"] == 33.33


def test_cli_export_overwrites_existing_csv_file(
    cli_with_seeded_data: Path,
    temp_data_dir: Path,
) -> None:
    """Test that export command overwrites existing CSV file."""
    output_csv = temp_data_dir / "overwrite.csv"

    # Create initial CSV
    output_csv.write_text("old,data\n1,2\n")

    # Export should overwrite
    result = run_cli(["export", "--output", str(output_csv)])
    assert result == 0

    # Verify new content
    with open(output_csv, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames

    # Should have proper task headers, not old data
    assert "id" in headers
    assert "title" in headers
    assert "old" not in headers
