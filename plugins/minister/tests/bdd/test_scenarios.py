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
from datetime import datetime
from pathlib import Path

from minister.project_tracker import ProjectTracker, Task


class TestNewProjectKickoff:
    """Scenario 1: Team lead initializes a new project with multiple initiatives.

    Business Context:
    A team lead starts a new quarter and needs to organize work across
    multiple initiatives. They create tasks for each workstream and want
    immediate visibility into the initiative breakdown.
    """

    def test_given_fresh_tracker_when_adding_tasks_then_status_shows_all_initiatives(
        self,
        empty_tracker: ProjectTracker,
    ) -> None:
        """GIVEN a fresh tracker with no tasks.

        WHEN the team lead adds multiple tasks across initiatives
        THEN the status report shows all initiatives with correct task counts.
        """
        # GIVEN: Fresh tracker (provided by fixture)
        assert len(empty_tracker.data.tasks) == 0

        # WHEN: Team lead adds tasks across three initiatives
        tasks_to_add = [
            Task(
                id="GHYG-001",
                title="Configure project board",
                initiative="GitHub Projects Hygiene",
                phase="Phase 1",
                priority="High",
                status="To Do",
                owner="tech-lead",
                effort_hours=3.0,
                completion_percent=0.0,
                due_date="2025-01-15",
                created_date=datetime.now().isoformat(),
                updated_date=datetime.now().isoformat(),
            ),
            Task(
                id="GHYG-002",
                title="Create label taxonomy",
                initiative="GitHub Projects Hygiene",
                phase="Phase 1",
                priority="Medium",
                status="To Do",
                owner="admin",
                effort_hours=2.0,
                completion_percent=0.0,
                due_date="2025-01-18",
                created_date=datetime.now().isoformat(),
                updated_date=datetime.now().isoformat(),
            ),
            Task(
                id="PR-001",
                title="Define PR template",
                initiative="Pull Request Readiness",
                phase="Phase 2",
                priority="High",
                status="To Do",
                owner="senior-dev",
                effort_hours=4.0,
                completion_percent=0.0,
                due_date="2025-01-20",
                created_date=datetime.now().isoformat(),
                updated_date=datetime.now().isoformat(),
            ),
            Task(
                id="PR-002",
                title="Set up CI checks",
                initiative="Pull Request Readiness",
                phase="Phase 2",
                priority="High",
                status="To Do",
                owner="devops",
                effort_hours=6.0,
                completion_percent=0.0,
                due_date="2025-01-22",
                created_date=datetime.now().isoformat(),
                updated_date=datetime.now().isoformat(),
            ),
            Task(
                id="DOC-001",
                title="Write onboarding guide",
                initiative="Docs & Enablement",
                phase="Phase 1",
                priority="Medium",
                status="To Do",
                owner="tech-writer",
                effort_hours=8.0,
                completion_percent=0.0,
                due_date="2025-01-25",
                created_date=datetime.now().isoformat(),
                updated_date=datetime.now().isoformat(),
            ),
        ]

        for task in tasks_to_add:
            empty_tracker.add_task(task)

        # THEN: Status report reflects all initiatives with accurate counts
        status_report = empty_tracker.get_status_report()

        assert "initiatives" in status_report
        initiatives = status_report["initiatives"]

        # Verify GitHub Projects Hygiene initiative
        assert "GitHub Projects Hygiene" in initiatives
        ghyg_metrics = initiatives["GitHub Projects Hygiene"]
        assert ghyg_metrics["total_tasks"] == 2
        assert ghyg_metrics["completed_tasks"] == 0
        assert ghyg_metrics["in_progress_tasks"] == 0
        assert ghyg_metrics["completion_percentage"] == 0.0

        # Verify Pull Request Readiness initiative
        assert "Pull Request Readiness" in initiatives
        pr_metrics = initiatives["Pull Request Readiness"]
        assert pr_metrics["total_tasks"] == 2
        assert pr_metrics["completed_tasks"] == 0

        # Verify Docs & Enablement initiative
        assert "Docs & Enablement" in initiatives
        doc_metrics = initiatives["Docs & Enablement"]
        assert doc_metrics["total_tasks"] == 1
        assert doc_metrics["total_effort"] == 8.0

        # Verify overall metrics
        overall = status_report["overall_metrics"]
        assert overall["total_tasks"] == 5
        assert overall["overall_completion"] == 0.0


class TestSprintProgressUpdate:
    """Scenario 2: Development team updates task progress during a sprint.

    Business Context:
    During a 2-week sprint, team members work on tasks and update their
    status as they progress. The project manager needs real-time metrics
    to track sprint velocity and identify blockers.
    """

    def test_given_existing_tasks_when_updating_through_sprint_then_metrics_reflect_progress(
        self,
        populated_tracker: ProjectTracker,
    ) -> None:
        """GIVEN a tracker with existing tasks.

        WHEN team members update task statuses through a sprint
        THEN metrics reflect accurate completion percentages.
        """
        # GIVEN: Tracker with sample tasks (provided by fixture)
        initial_report = populated_tracker.get_status_report()
        initial_completion = initial_report["overall_metrics"]["overall_completion"]

        # WHEN: Team members update tasks during sprint
        # Day 1: Developer starts work on GHYG-002
        populated_tracker.update_task(
            "GHYG-002",
            {"status": "In Progress", "completion_percent": 25.0},
        )

        # Day 3: Developer continues GHYG-002
        populated_tracker.update_task(
            "GHYG-002",
            {"completion_percent": 50.0},
        )

        # Day 5: Tech lead starts PR-001
        populated_tracker.update_task(
            "PR-001",
            {"status": "In Progress", "completion_percent": 30.0},
        )

        # Day 7: GHYG-002 moves to review
        populated_tracker.update_task(
            "GHYG-002",
            {"status": "Review", "completion_percent": 90.0},
        )

        # Day 10: GHYG-002 completed, PR-001 progresses
        populated_tracker.update_task(
            "GHYG-002",
            {"status": "Done", "completion_percent": 100.0},
        )
        populated_tracker.update_task(
            "PR-001",
            {"completion_percent": 60.0},
        )

        # THEN: Metrics accurately reflect sprint progress
        final_report = populated_tracker.get_status_report()
        ghyg_metrics = final_report["initiatives"]["GitHub Projects Hygiene"]
        pr_metrics = final_report["initiatives"]["Pull Request Readiness"]
        overall = final_report["overall_metrics"]

        # GHYG-002 is now complete (added to existing completed task GHYG-001)
        assert ghyg_metrics["completed_tasks"] == 2
        assert ghyg_metrics["completion_percentage"] == 100.0

        # PR-001 is in progress
        assert pr_metrics["in_progress_tasks"] == 1

        # Overall completion improved
        assert overall["overall_completion"] > initial_completion

        # Verify specific task states
        ghyg_002 = next(
            task for task in populated_tracker.data.tasks if task.id == "GHYG-002"
        )
        assert ghyg_002.status == "Done"
        assert ghyg_002.completion_percent == 100.0

        pr_001 = next(
            task for task in populated_tracker.data.tasks if task.id == "PR-001"
        )
        assert pr_001.status == "In Progress"
        assert pr_001.completion_percent == 60.0


class TestInitiativeCompletionTracking:
    """Scenario 3: Tracking completion across multiple initiatives.

    Business Context:
    A program manager oversees three parallel initiatives. They need to
    identify which initiatives are on track vs. at risk, and celebrate
    completed initiatives while focusing resources on lagging ones.
    """

    def test_given_tasks_when_one_initiative_completes_then_shows_100_percent(
        self,
        empty_tracker: ProjectTracker,
    ) -> None:
        """GIVEN tasks spread across multiple initiatives.

        WHEN one initiative completes all tasks
        THEN that initiative shows 100% completion while others remain partial.
        """
        # GIVEN: Tasks distributed across three initiatives
        tasks = [
            # Initiative A: Will be completed
            Task(
                id="A-001",
                title="Task A1",
                initiative="Initiative Alpha",
                phase="Phase 1",
                priority="High",
                status="To Do",
                owner="dev1",
                effort_hours=5.0,
                completion_percent=0.0,
                due_date="2025-01-15",
                created_date=datetime.now().isoformat(),
                updated_date=datetime.now().isoformat(),
            ),
            Task(
                id="A-002",
                title="Task A2",
                initiative="Initiative Alpha",
                phase="Phase 1",
                priority="Medium",
                status="To Do",
                owner="dev2",
                effort_hours=3.0,
                completion_percent=0.0,
                due_date="2025-01-16",
                created_date=datetime.now().isoformat(),
                updated_date=datetime.now().isoformat(),
            ),
            # Initiative B: Will be partially complete
            Task(
                id="B-001",
                title="Task B1",
                initiative="Initiative Beta",
                phase="Phase 2",
                priority="High",
                status="To Do",
                owner="dev3",
                effort_hours=4.0,
                completion_percent=0.0,
                due_date="2025-01-18",
                created_date=datetime.now().isoformat(),
                updated_date=datetime.now().isoformat(),
            ),
            Task(
                id="B-002",
                title="Task B2",
                initiative="Initiative Beta",
                phase="Phase 2",
                priority="Medium",
                status="To Do",
                owner="dev4",
                effort_hours=6.0,
                completion_percent=0.0,
                due_date="2025-01-20",
                created_date=datetime.now().isoformat(),
                updated_date=datetime.now().isoformat(),
            ),
            # Initiative C: Will have minimal progress
            Task(
                id="C-001",
                title="Task C1",
                initiative="Initiative Charlie",
                phase="Phase 3",
                priority="Low",
                status="To Do",
                owner="dev5",
                effort_hours=8.0,
                completion_percent=0.0,
                due_date="2025-01-25",
                created_date=datetime.now().isoformat(),
                updated_date=datetime.now().isoformat(),
            ),
        ]

        for task in tasks:
            empty_tracker.add_task(task)

        # WHEN: Initiative Alpha completes all tasks
        empty_tracker.update_task(
            "A-001",
            {"status": "Done", "completion_percent": 100.0},
        )
        empty_tracker.update_task(
            "A-002",
            {"status": "Done", "completion_percent": 100.0},
        )

        # Initiative Beta completes one task
        empty_tracker.update_task(
            "B-001",
            {"status": "Done", "completion_percent": 100.0},
        )

        # Initiative Charlie has one task in progress
        empty_tracker.update_task(
            "C-001",
            {"status": "In Progress", "completion_percent": 25.0},
        )

        # THEN: Metrics show different completion states
        report = empty_tracker.get_status_report()
        initiatives = report["initiatives"]

        # Initiative Alpha: 100% complete
        alpha = initiatives["Initiative Alpha"]
        assert alpha["total_tasks"] == 2
        assert alpha["completed_tasks"] == 2
        assert alpha["completion_percentage"] == 100.0
        assert alpha["average_task_completion"] == 100.0

        # Initiative Beta: 50% complete (1 of 2 tasks)
        beta = initiatives["Initiative Beta"]
        assert beta["total_tasks"] == 2
        assert beta["completed_tasks"] == 1
        assert beta["completion_percentage"] == 50.0

        # Initiative Charlie: 0% complete (0 of 1 tasks)
        charlie = initiatives["Initiative Charlie"]
        assert charlie["total_tasks"] == 1
        assert charlie["completed_tasks"] == 0
        assert charlie["completion_percentage"] == 0.0
        assert charlie["average_task_completion"] == 25.0  # Task is 25% done


class TestGitHubIntegrationWorkflow:
    """Scenario 4: Generating GitHub-formatted status reports.

    Business Context:
    The team uses GitHub issues and PRs for all work. The project manager
    needs to post weekly status updates to a tracking issue, formatted
    as markdown tables that render nicely on GitHub.
    """

    def test_given_tasks_with_github_issues_when_generating_report_then_valid_markdown_with_metrics(
        self,
        empty_tracker: ProjectTracker,
    ) -> None:
        """GIVEN tasks linked to GitHub issues.

        WHEN generating a status report for GitHub
        THEN the formatted output is valid markdown with correct metrics.
        """
        # GIVEN: Tasks with GitHub issue links
        tasks = [
            Task(
                id="GHYG-001",
                title="Configure project board",
                initiative="GitHub Projects Hygiene",
                phase="Phase 1",
                priority="High",
                status="Done",
                owner="admin",
                effort_hours=3.0,
                completion_percent=100.0,
                due_date="2025-01-10",
                created_date=datetime.now().isoformat(),
                updated_date=datetime.now().isoformat(),
                github_issue="https://github.com/org/repo/issues/42",
            ),
            Task(
                id="GHYG-002",
                title="Create labels",
                initiative="GitHub Projects Hygiene",
                phase="Phase 1",
                priority="Medium",
                status="In Progress",
                owner="admin",
                effort_hours=2.0,
                completion_percent=50.0,
                due_date="2025-01-12",
                created_date=datetime.now().isoformat(),
                updated_date=datetime.now().isoformat(),
                github_issue="https://github.com/org/repo/issues/43",
            ),
            Task(
                id="PR-001",
                title="PR template",
                initiative="Pull Request Readiness",
                phase="Phase 2",
                priority="High",
                status="To Do",
                owner="tech-lead",
                effort_hours=4.0,
                completion_percent=0.0,
                due_date="2025-01-15",
                created_date=datetime.now().isoformat(),
                updated_date=datetime.now().isoformat(),
                github_issue="#44",
            ),
        ]

        for task in tasks:
            empty_tracker.add_task(task)

        # WHEN: Generating GitHub comment format
        report = empty_tracker.get_status_report()
        github_comment = empty_tracker.format_github_comment(report)

        # THEN: Output is valid markdown with correct structure
        lines = github_comment.split("\n")

        # Verify header
        assert lines[0] == "### Initiative Pulse"
        assert "Last updated:" in lines[1]

        # Verify table headers present
        assert (
            "| Initiative | Done | In Progress | Completion | Avg Task % |"
            in github_comment
        )
        assert (
            "|------------|------|-------------|------------|-------------|"
            in github_comment
        )

        # Verify initiative rows contain correct data
        ghyg_row = [line for line in lines if "GitHub Projects Hygiene" in line][0]
        assert "1/2" in ghyg_row  # 1 of 2 tasks done
        assert "1 |" in ghyg_row  # 1 in progress
        assert "50.0%" in ghyg_row  # 50% completion

        pr_row = [line for line in lines if "Pull Request Readiness" in line][0]
        assert "0/1" in pr_row  # 0 of 1 tasks done
        assert "0 |" in pr_row  # 0 in progress

        # Verify overall metrics section
        assert "### Overall Metrics" in github_comment
        assert "- Total tasks: 3" in github_comment
        assert "- Completion:" in github_comment
        assert "- Total effort:" in github_comment
        assert "- Burn rate:" in github_comment

        # Verify markdown table structure is valid (correct number of columns)
        table_rows = [
            line
            for line in lines
            if line.startswith("|") and "Initiative" not in line and "---" not in line
        ]
        for row in table_rows:
            # Each row should have 6 pipes (5 columns)
            assert row.count("|") == 6


class TestDataPersistenceAcrossSessions:
    """Scenario 5: Data persistence and session continuity.

    Business Context:
    Team members access the tracker throughout the day from different
    contexts (CLI, scripts, manual edits). All changes must persist
    correctly and be available to subsequent tracker instances.
    """

    def test_given_tracker_saved_to_disk_when_loading_new_instance_then_all_data_preserved(
        self,
        seeded_data_file: Path,
        sample_tasks: list[Task],
    ) -> None:
        """GIVEN a tracker with tasks saved to disk.

        WHEN a new tracker instance loads the same data file
        THEN all tasks and metrics are preserved exactly.
        """
        # GIVEN: Data file seeded with tasks (provided by fixture)
        assert seeded_data_file.exists()

        # WHEN: First tracker instance makes changes
        tracker_session_1 = ProjectTracker(data_file=seeded_data_file)
        initial_task_count = len(tracker_session_1.data.tasks)

        # Add a new task in session 1
        new_task = Task(
            id="PERSIST-001",
            title="Persistence Test Task",
            initiative="Testing",
            phase="Phase 1",
            priority="High",
            status="To Do",
            owner="tester",
            effort_hours=2.0,
            completion_percent=0.0,
            due_date="2025-01-20",
            created_date=datetime.now().isoformat(),
            updated_date=datetime.now().isoformat(),
        )
        tracker_session_1.add_task(new_task)

        # Update an existing task in session 1
        tracker_session_1.update_task(
            "GHYG-001",
            {"status": "Review", "completion_percent": 95.0},
        )

        # Get metrics from session 1
        report_session_1 = tracker_session_1.get_status_report()

        # WHEN: New tracker instance loads the same file (simulating new session)
        tracker_session_2 = ProjectTracker(data_file=seeded_data_file)

        # THEN: All data is preserved exactly
        assert len(tracker_session_2.data.tasks) == initial_task_count + 1

        # Verify new task exists
        persist_task = next(
            (task for task in tracker_session_2.data.tasks if task.id == "PERSIST-001"),
            None,
        )
        assert persist_task is not None
        assert persist_task.title == "Persistence Test Task"
        assert persist_task.initiative == "Testing"

        # Verify updated task reflects changes
        ghyg_task = next(
            task for task in tracker_session_2.data.tasks if task.id == "GHYG-001"
        )
        assert ghyg_task.status == "Review"
        assert ghyg_task.completion_percent == 95.0

        # Verify metrics are identical
        report_session_2 = tracker_session_2.get_status_report()
        assert (
            report_session_2["overall_metrics"]["total_tasks"]
            == report_session_1["overall_metrics"]["total_tasks"]
        )

        # Verify all original sample tasks are present
        task_ids_session_2 = {task.id for task in tracker_session_2.data.tasks}
        for original_task in sample_tasks:
            assert original_task.id in task_ids_session_2


class TestCSVExportForStakeholders:
    """Scenario 6: Exporting data for external stakeholder analysis.

    Business Context:
    Executive leadership and external stakeholders need to analyze project
    data in Excel or other tools. The system must export complete, accurate
    CSV files with all relevant task attributes.
    """

    def test_given_populated_tracker_when_exporting_csv_then_contains_all_data_in_expected_format(
        self,
        populated_tracker: ProjectTracker,
        temp_data_dir: Path,
    ) -> None:
        """GIVEN a populated tracker with diverse tasks.

        WHEN exporting to CSV
        THEN the CSV contains all task data in the expected format.
        """
        # GIVEN: Tracker with sample tasks (provided by fixture)
        expected_task_count = len(populated_tracker.data.tasks)
        assert expected_task_count > 0

        # WHEN: Exporting to CSV
        csv_output_file = temp_data_dir / "export.csv"
        populated_tracker.export_csv(csv_output_file)

        # THEN: CSV file exists and contains correct data
        assert csv_output_file.exists()

        with open(csv_output_file, encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            rows = list(reader)

            # Verify row count matches task count
            assert len(rows) == expected_task_count

            # Verify headers match expected fields
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

            # Verify data integrity for specific tasks
            ghyg_001_row = next(row for row in rows if row["id"] == "GHYG-001")
            assert ghyg_001_row["title"] == "Set up project board"
            assert ghyg_001_row["initiative"] == "GitHub Projects Hygiene"
            assert ghyg_001_row["status"] == "Done"
            assert ghyg_001_row["priority"] == "High"
            assert float(ghyg_001_row["effort_hours"]) == 2.0
            assert float(ghyg_001_row["completion_percent"]) == 100.0

            # Verify task with GitHub issue
            ghyg_002_row = next(row for row in rows if row["id"] == "GHYG-002")
            assert ghyg_002_row["status"] == "In Progress"
            assert float(ghyg_002_row["completion_percent"]) == 75.0

            # Verify tasks without GitHub issues have empty string
            pr_001_row = next(row for row in rows if row["id"] == "PR-001")
            assert pr_001_row["github_issue"] == ""

            # Verify numeric fields are properly formatted
            for row in rows:
                # Effort hours should be valid numbers
                effort = float(row["effort_hours"])
                assert effort >= 0

                # Completion percent should be 0-100
                completion = float(row["completion_percent"])
                assert 0 <= completion <= 100

            # Verify all initiatives are represented
            initiatives_in_csv = {row["initiative"] for row in rows}
            expected_initiatives = {
                "GitHub Projects Hygiene",
                "Pull Request Readiness",
                "Docs & Enablement",
            }
            assert initiatives_in_csv == expected_initiatives


class TestCrossScenarioWorkflow:
    """Bonus Scenario: Complete project lifecycle from kickoff to stakeholder report.

    Business Context:
    A realistic end-to-end workflow combining multiple scenarios: project
    kickoff, sprint updates, initiative completion, and stakeholder reporting.
    This tests the full value chain of the minister plugin.
    """

    def test_complete_project_lifecycle_workflow(
        self,
        empty_tracker: ProjectTracker,
        temp_data_dir: Path,
    ) -> None:
        """GIVEN a fresh project.

        WHEN executing a complete workflow from kickoff to reporting
        THEN all operations succeed and produce consistent results.
        """
        # PHASE 1: Project Kickoff
        # -------------------------
        kickoff_tasks = [
            Task(
                id=f"INIT-{i:03d}",
                title=f"Initiative Setup Task {i}",
                initiative=f"Initiative {chr(65 + i // 3)}",  # A, B, C
                phase="Phase 1",
                priority=["High", "Medium", "Low"][i % 3],
                status="To Do",
                owner=f"team-member-{i % 5}",
                effort_hours=float(2 + i),
                completion_percent=0.0,
                due_date=f"2025-01-{15 + i:02d}",
                created_date=datetime.now().isoformat(),
                updated_date=datetime.now().isoformat(),
                github_issue=f"#100{i}" if i % 2 == 0 else None,
            )
            for i in range(9)  # 3 tasks per initiative
        ]

        for task in kickoff_tasks:
            empty_tracker.add_task(task)

        kickoff_report = empty_tracker.get_status_report()
        assert kickoff_report["overall_metrics"]["total_tasks"] == 9

        # PHASE 2: Sprint Execution
        # --------------------------
        # Complete Initiative A tasks
        for i in range(3):
            empty_tracker.update_task(
                f"INIT-{i:03d}",
                {"status": "Done", "completion_percent": 100.0},
            )

        # Partially complete Initiative B
        empty_tracker.update_task(
            "INIT-003",
            {"status": "Done", "completion_percent": 100.0},
        )
        empty_tracker.update_task(
            "INIT-004",
            {"status": "In Progress", "completion_percent": 60.0},
        )

        # Start Initiative C
        empty_tracker.update_task(
            "INIT-006",
            {"status": "In Progress", "completion_percent": 20.0},
        )

        # PHASE 3: Mid-Sprint Status Check
        # ----------------------------------
        mid_sprint_report = empty_tracker.get_status_report()

        # Initiative A should be 100% complete
        init_a_metrics = mid_sprint_report["initiatives"]["Initiative A"]
        assert init_a_metrics["completion_percentage"] == 100.0
        assert init_a_metrics["completed_tasks"] == 3

        # Initiative B should be partial
        init_b_metrics = mid_sprint_report["initiatives"]["Initiative B"]
        assert init_b_metrics["completed_tasks"] == 1
        assert init_b_metrics["in_progress_tasks"] == 1

        # PHASE 4: GitHub Status Update
        # -------------------------------
        github_comment = empty_tracker.format_github_comment(mid_sprint_report)
        assert "Initiative A" in github_comment
        assert "100.0%" in github_comment
        assert "### Overall Metrics" in github_comment

        # PHASE 5: Stakeholder CSV Export
        # ---------------------------------
        csv_file = temp_data_dir / "stakeholder_report.csv"
        empty_tracker.export_csv(csv_file)

        with open(csv_file, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            csv_rows = list(reader)
            assert len(csv_rows) == 9

            # Verify completed tasks in CSV
            completed_in_csv = [row for row in csv_rows if row["status"] == "Done"]
            assert len(completed_in_csv) == 4

        # PHASE 6: Data Persistence Check
        # ---------------------------------
        # Simulate new session
        new_tracker = ProjectTracker(data_file=empty_tracker.data_file)
        persistence_report = new_tracker.get_status_report()

        # All data should match
        assert (
            persistence_report["overall_metrics"]["total_tasks"]
            == mid_sprint_report["overall_metrics"]["total_tasks"]
        )
        assert (
            persistence_report["initiatives"]["Initiative A"]["completion_percentage"]
            == 100.0
        )
