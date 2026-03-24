"""Tests for ProjectTracker status reports, GitHub comment formatting,
CSV export, and edge cases.

Covers:
- TestGetStatusReport
- TestFormatGitHubComment
- TestExportCSV
- TestEdgeCases
"""

from __future__ import annotations

import csv
from pathlib import Path

from minister.project_tracker import ProjectTracker, Task


class TestGetStatusReport:
    """Test detailed status report generation."""

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
        assert "### Initiative Pulse" in comment
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
        assert "### Overall Metrics" in comment
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
        assert "### Initiative Pulse" in comment
        assert "### Overall Metrics" in comment
        assert "Total tasks: 0" in comment


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
