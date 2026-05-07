"""BDD-style scenario tests for minister plugin workflows.

These tests follow the Behavior-Driven Development pattern with explicit
GIVEN-WHEN-THEN structure to document complete user workflows from a
business perspective.

Each scenario tests end-to-end functionality as experienced by actual users:

- Team leads managing initiatives
- Developers updating task progress
- Stakeholders reviewing status reports
- External systems integrating via CSV exports
"""

from __future__ import annotations

import csv
from datetime import UTC, datetime
from pathlib import Path

import pytest

from minister.project_tracker import ProjectTracker, Task

# ── Shared task-creation helpers ────────────────────────


def _make_task(
    task_id: str,
    title: str,
    initiative: str,
    *,
    phase: str = "Phase 1",
    priority: str = "Medium",
    status: str = "To Do",
    owner: str = "dev",
    effort_hours: float = 4.0,
    completion_percent: float = 0.0,
    due_date: str = "2025-01-15",
    github_issue: str | None = None,
) -> Task:
    """Build a Task with sensible defaults for BDD tests."""
    now = datetime.now(UTC).isoformat()
    return Task(
        id=task_id,
        title=title,
        initiative=initiative,
        phase=phase,
        priority=priority,
        status=status,
        owner=owner,
        effort_hours=effort_hours,
        completion_percent=completion_percent,
        due_date=due_date,
        created_date=now,
        updated_date=now,
        github_issue=github_issue,
    )


# ── Fixtures ────────────────────────────────────────────


@pytest.fixture
def kickoff_tasks() -> list[Task]:
    """Five tasks across three initiatives for kickoff scenarios."""
    return [
        _make_task(
            "GHYG-001",
            "Configure project board",
            "GitHub Projects Hygiene",
            priority="High",
            owner="tech-lead",
            effort_hours=3.0,
        ),
        _make_task(
            "GHYG-002",
            "Create label taxonomy",
            "GitHub Projects Hygiene",
            owner="admin",
            effort_hours=2.0,
            due_date="2025-01-18",
        ),
        _make_task(
            "PR-001",
            "Define PR template",
            "Pull Request Readiness",
            phase="Phase 2",
            priority="High",
            owner="senior-dev",
            effort_hours=4.0,
            due_date="2025-01-20",
        ),
        _make_task(
            "PR-002",
            "Set up CI checks",
            "Pull Request Readiness",
            phase="Phase 2",
            priority="High",
            owner="devops",
            effort_hours=6.0,
            due_date="2025-01-22",
        ),
        _make_task(
            "DOC-001",
            "Write onboarding guide",
            "Docs & Enablement",
            owner="tech-writer",
            effort_hours=8.0,
            due_date="2025-01-25",
        ),
    ]


@pytest.fixture
def three_initiative_tasks() -> list[Task]:
    """Tasks for initiative-completion tracking (A, B, C)."""
    return [
        _make_task(
            "A-001", "Task A1", "Initiative Alpha", priority="High", effort_hours=5.0
        ),
        _make_task(
            "A-002",
            "Task A2",
            "Initiative Alpha",
            effort_hours=3.0,
            due_date="2025-01-16",
        ),
        _make_task(
            "B-001",
            "Task B1",
            "Initiative Beta",
            phase="Phase 2",
            priority="High",
            effort_hours=4.0,
            due_date="2025-01-18",
        ),
        _make_task(
            "B-002",
            "Task B2",
            "Initiative Beta",
            phase="Phase 2",
            effort_hours=6.0,
            due_date="2025-01-20",
        ),
        _make_task(
            "C-001",
            "Task C1",
            "Initiative Charlie",
            phase="Phase 3",
            priority="Low",
            effort_hours=8.0,
            due_date="2025-01-25",
        ),
    ]


@pytest.fixture
def github_linked_tasks() -> list[Task]:
    """Tasks with GitHub issue links for report-formatting scenarios."""
    return [
        _make_task(
            "GHYG-001",
            "Configure project board",
            "GitHub Projects Hygiene",
            priority="High",
            status="Done",
            owner="admin",
            effort_hours=3.0,
            completion_percent=100.0,
            due_date="2025-01-10",
            github_issue="https://github.com/org/repo/issues/42",
        ),
        _make_task(
            "GHYG-002",
            "Create labels",
            "GitHub Projects Hygiene",
            status="In Progress",
            owner="admin",
            effort_hours=2.0,
            completion_percent=50.0,
            due_date="2025-01-12",
            github_issue="https://github.com/org/repo/issues/43",
        ),
        _make_task(
            "PR-001",
            "PR template",
            "Pull Request Readiness",
            phase="Phase 2",
            priority="High",
            owner="tech-lead",
            due_date="2025-01-15",
            github_issue="#44",
        ),
    ]


def _add_tasks(tracker: ProjectTracker, tasks: list[Task]) -> None:
    """Bulk-add tasks to a tracker."""
    for task in tasks:
        tracker.add_task(task)


# ── Scenario 1: Project Kickoff ─────────────────────────


class TestNewProjectKickoff:
    """Scenario 1: Team lead initializes a new project with multiple initiatives."""

    def test_kickoff_shows_all_initiatives(
        self,
        empty_tracker: ProjectTracker,
        kickoff_tasks: list[Task],
    ) -> None:
        """GIVEN a fresh tracker with no tasks.

        WHEN the team lead adds multiple tasks across initiatives
        THEN the status report shows all initiatives with correct counts.
        """
        assert len(empty_tracker.data.tasks) == 0

        _add_tasks(empty_tracker, kickoff_tasks)

        report = empty_tracker.get_status_report()
        initiatives = report["initiatives"]

        ghyg = initiatives["GitHub Projects Hygiene"]
        assert ghyg["total_tasks"] == 2
        assert ghyg["completed_tasks"] == 0
        assert ghyg["in_progress_tasks"] == 0

        pr = initiatives["Pull Request Readiness"]
        assert pr["total_tasks"] == 2

        doc = initiatives["Docs & Enablement"]
        assert doc["total_tasks"] == 1
        assert doc["total_effort"] == 8.0

        overall = report["overall_metrics"]
        assert overall["total_tasks"] == 5
        assert overall["overall_completion"] == 0.0


# ── Scenario 2: Sprint Progress ─────────────────────────


class TestSprintProgressUpdate:
    """Scenario 2: Development team updates task progress during a sprint."""

    def test_sprint_progress_reflected_in_metrics(
        self,
        populated_tracker: ProjectTracker,
    ) -> None:
        """GIVEN a tracker with existing tasks.

        WHEN team members update statuses through a sprint
        THEN metrics reflect accurate completion percentages.
        """
        initial_completion = populated_tracker.get_status_report()["overall_metrics"][
            "overall_completion"
        ]

        populated_tracker.update_task(
            "GHYG-002",
            {"status": "In Progress", "completion_percent": 25.0},
        )
        populated_tracker.update_task(
            "GHYG-002",
            {"completion_percent": 50.0},
        )
        populated_tracker.update_task(
            "PR-001",
            {"status": "In Progress", "completion_percent": 30.0},
        )
        populated_tracker.update_task(
            "GHYG-002",
            {"status": "Review", "completion_percent": 90.0},
        )
        populated_tracker.update_task(
            "GHYG-002",
            {"status": "Done", "completion_percent": 100.0},
        )
        populated_tracker.update_task(
            "PR-001",
            {"completion_percent": 60.0},
        )

        final = populated_tracker.get_status_report()
        ghyg = final["initiatives"]["GitHub Projects Hygiene"]
        assert ghyg["completed_tasks"] == 2
        assert ghyg["completion_percentage"] == 100.0

        pr = final["initiatives"]["Pull Request Readiness"]
        assert pr["in_progress_tasks"] == 1

        assert final["overall_metrics"]["overall_completion"] > initial_completion


# ── Scenario 3: Initiative Completion ────────────────────


class TestInitiativeCompletionTracking:
    """Scenario 3: Tracking completion across multiple initiatives."""

    def test_one_initiative_fully_completes(
        self,
        empty_tracker: ProjectTracker,
        three_initiative_tasks: list[Task],
    ) -> None:
        """GIVEN tasks across three initiatives.

        WHEN one initiative completes all tasks
        THEN it shows 100% while others remain partial.
        """
        _add_tasks(empty_tracker, three_initiative_tasks)

        empty_tracker.update_task(
            "A-001",
            {"status": "Done", "completion_percent": 100.0},
        )
        empty_tracker.update_task(
            "A-002",
            {"status": "Done", "completion_percent": 100.0},
        )
        empty_tracker.update_task(
            "B-001",
            {"status": "Done", "completion_percent": 100.0},
        )
        empty_tracker.update_task(
            "C-001",
            {"status": "In Progress", "completion_percent": 25.0},
        )

        report = empty_tracker.get_status_report()
        initiatives = report["initiatives"]

        alpha = initiatives["Initiative Alpha"]
        assert alpha["completion_percentage"] == 100.0
        assert alpha["average_task_completion"] == 100.0

        beta = initiatives["Initiative Beta"]
        assert beta["completion_percentage"] == 50.0

        charlie = initiatives["Initiative Charlie"]
        assert charlie["completed_tasks"] == 0
        assert charlie["average_task_completion"] == 25.0


# ── Scenario 4: GitHub Report Formatting ─────────────────


class TestGitHubIntegrationWorkflow:
    """Scenario 4: Generating GitHub-formatted status reports."""

    def test_valid_markdown_with_metrics(
        self,
        empty_tracker: ProjectTracker,
        github_linked_tasks: list[Task],
    ) -> None:
        """GIVEN tasks linked to GitHub issues.

        WHEN generating a GitHub-comment report
        THEN output is valid markdown with correct metrics.
        """
        _add_tasks(empty_tracker, github_linked_tasks)

        report = empty_tracker.get_status_report()
        comment = empty_tracker.format_github_comment(report)
        lines = comment.split("\n")

        assert lines[0] == "### Initiative Pulse"
        assert "Last updated:" in lines[1]
        assert (
            "| Initiative | Done | In Progress | Completion | Avg Task % |" in comment
        )

        ghyg_row = [line for line in lines if "GitHub Projects Hygiene" in line][0]
        assert "1/2" in ghyg_row
        assert "50.0%" in ghyg_row

        assert "### Overall Metrics" in comment
        assert "- Total tasks: 3" in comment

        table_rows = [
            line
            for line in lines
            if line.startswith("|") and "Initiative" not in line and "---" not in line
        ]
        for row in table_rows:
            assert row.count("|") == 6


# ── Scenario 5: Data Persistence ─────────────────────────


class TestDataPersistenceAcrossSessions:
    """Scenario 5: Data persistence and session continuity."""

    def test_data_preserved_across_sessions(
        self,
        seeded_data_file: Path,
        sample_tasks: list[Task],
    ) -> None:
        """GIVEN a tracker saved to disk.

        WHEN a new instance loads the same file
        THEN all tasks and metrics are preserved exactly.
        """
        session_1 = ProjectTracker(data_file=seeded_data_file)
        initial_count = len(session_1.data.tasks)

        session_1.add_task(
            _make_task(
                "PERSIST-001",
                "Persistence Test Task",
                "Testing",
                priority="High",
                effort_hours=2.0,
            )
        )
        session_1.update_task(
            "GHYG-001",
            {"status": "Review", "completion_percent": 95.0},
        )
        report_1 = session_1.get_status_report()

        session_2 = ProjectTracker(data_file=seeded_data_file)
        assert len(session_2.data.tasks) == initial_count + 1

        persist = next(
            (t for t in session_2.data.tasks if t.id == "PERSIST-001"),
            None,
        )
        assert persist is not None
        assert persist.title == "Persistence Test Task"

        ghyg = next(t for t in session_2.data.tasks if t.id == "GHYG-001")
        assert ghyg.status == "Review"
        assert ghyg.completion_percent == 95.0

        report_2 = session_2.get_status_report()
        assert (
            report_2["overall_metrics"]["total_tasks"]
            == report_1["overall_metrics"]["total_tasks"]
        )

        ids_2 = {t.id for t in session_2.data.tasks}
        for original in sample_tasks:
            assert original.id in ids_2


# ── Scenario 6: CSV Export ───────────────────────────────


class TestCSVExportForStakeholders:
    """Scenario 6: Exporting data for external stakeholder analysis."""

    def test_csv_contains_all_data_in_expected_format(
        self,
        populated_tracker: ProjectTracker,
        temp_data_dir: Path,
    ) -> None:
        """GIVEN a populated tracker.

        WHEN exporting to CSV
        THEN the file contains all task data with correct headers.
        """
        expected_count = len(populated_tracker.data.tasks)
        csv_file = temp_data_dir / "export.csv"
        populated_tracker.export_csv(csv_file)

        assert csv_file.exists()
        with open(csv_file, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == expected_count

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
        assert reader.fieldnames == expected_headers

        ghyg_001 = next(r for r in rows if r["id"] == "GHYG-001")
        assert ghyg_001["initiative"] == "GitHub Projects Hygiene"
        assert ghyg_001["status"] == "Done"
        assert float(ghyg_001["completion_percent"]) == 100.0

        for row in rows:
            assert float(row["effort_hours"]) >= 0
            assert 0 <= float(row["completion_percent"]) <= 100


# ── Scenario 7: Full Lifecycle ───────────────────────────


class TestCrossScenarioWorkflow:
    """Bonus: Complete project lifecycle from kickoff to stakeholder report."""

    def test_complete_project_lifecycle_workflow(
        self,
        empty_tracker: ProjectTracker,
        temp_data_dir: Path,
    ) -> None:
        """GIVEN a fresh project.

        WHEN executing kickoff, sprint, and reporting phases
        THEN all operations succeed and produce consistent results.
        """
        # Phase 1: kickoff
        tasks = [
            _make_task(
                f"INIT-{i:03d}",
                f"Initiative Setup Task {i}",
                f"Initiative {chr(65 + i // 3)}",
                priority=["High", "Medium", "Low"][i % 3],
                owner=f"team-member-{i % 5}",
                effort_hours=float(2 + i),
                due_date=f"2025-01-{15 + i:02d}",
                github_issue=f"#100{i}" if i % 2 == 0 else None,
            )
            for i in range(9)
        ]
        _add_tasks(empty_tracker, tasks)
        assert empty_tracker.get_status_report()["overall_metrics"]["total_tasks"] == 9

        # Phase 2: sprint execution
        for i in range(3):
            empty_tracker.update_task(
                f"INIT-{i:03d}",
                {"status": "Done", "completion_percent": 100.0},
            )
        empty_tracker.update_task(
            "INIT-003",
            {"status": "Done", "completion_percent": 100.0},
        )
        empty_tracker.update_task(
            "INIT-004",
            {"status": "In Progress", "completion_percent": 60.0},
        )
        empty_tracker.update_task(
            "INIT-006",
            {"status": "In Progress", "completion_percent": 20.0},
        )

        # Phase 3: mid-sprint check
        mid = empty_tracker.get_status_report()
        assert mid["initiatives"]["Initiative A"]["completion_percentage"] == 100.0
        assert mid["initiatives"]["Initiative B"]["completed_tasks"] == 1

        # Phase 4: GitHub comment
        comment = empty_tracker.format_github_comment(mid)
        assert "Initiative A" in comment
        assert "100.0%" in comment

        # Phase 5: CSV export
        csv_file = temp_data_dir / "stakeholder_report.csv"
        empty_tracker.export_csv(csv_file)
        with open(csv_file, encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        assert len(rows) == 9
        assert len([r for r in rows if r["status"] == "Done"]) == 4

        # Phase 6: persistence
        new_tracker = ProjectTracker(data_file=empty_tracker.data_file)
        assert (
            new_tracker.get_status_report()["overall_metrics"]["total_tasks"]
            == mid["overall_metrics"]["total_tasks"]
        )
