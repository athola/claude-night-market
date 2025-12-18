"""Core tracking utilities for Minister."""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class Task:
    """Represents a task in the initiative."""

    id: str
    title: str
    initiative: str
    phase: str
    priority: str
    status: str
    owner: str
    effort_hours: float
    completion_percent: float
    due_date: str
    created_date: str
    updated_date: str
    github_issue: str | None = None


@dataclass
class InitiativeTracker:
    """Tracks progress across all initiatives."""

    tasks: list[Task]
    last_updated: str


class ProjectTracker:
    """Main project tracking system."""

    DEFAULT_INITIATIVES = [
        "GitHub Projects Hygiene",
        "Pull Request Readiness",
        "Docs & Enablement",
    ]

    def __init__(
        self, data_file: Path | None = None, initiatives: list[str] | None = None
    ) -> None:
        """Initialize the project tracker."""
        plugin_root = Path(__file__).resolve().parents[2]
        default_data = plugin_root / "data" / "project-data.json"
        self.data_file = data_file or default_data
        self.initiatives = initiatives or self.DEFAULT_INITIATIVES
        self.data = self._load_data()

    def _load_data(self) -> InitiativeTracker:
        """Load tracking data from file."""
        if self.data_file.exists():
            with open(self.data_file, encoding="utf-8") as file:
                data = json.load(file)
            tasks = [Task(**task) for task in data.get("tasks", [])]
            return InitiativeTracker(
                tasks, data.get("last_updated", datetime.now().isoformat())
            )

        return InitiativeTracker([], datetime.now().isoformat())

    def _save_data(self) -> None:
        """Save tracking data to file."""
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "tasks": [asdict(task) for task in self.data.tasks],
            "last_updated": datetime.now().isoformat(),
        }
        with open(self.data_file, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=2)

    def add_task(self, task: Task) -> None:
        """Add a new task to the tracker."""
        self.data.tasks.append(task)
        self._save_data()

    def update_task(self, task_id: str, updates: dict[str, Any]) -> None:
        """Update an existing task."""
        for task in self.data.tasks:
            if task.id == task_id:
                for key, value in updates.items():
                    setattr(task, key, value)
                task.updated_date = datetime.now().isoformat()
                self._save_data()
                return

    def get_tasks_by_initiative(self, initiative: str) -> list[Task]:
        """Get all tasks for a specific initiative."""
        return [task for task in self.data.tasks if task.initiative == initiative]

    def get_status_report(self) -> dict[str, Any]:
        """Generate comprehensive status report."""
        report: dict[str, Any] = {
            "last_updated": self.data.last_updated,
            "initiatives": {},
            "overall_metrics": self._calculate_overall_metrics(),
        }

        initiative_names = sorted(
            {task.initiative for task in self.data.tasks} | set(self.initiatives),
        )
        for initiative in initiative_names:
            tasks = self.get_tasks_by_initiative(initiative)
            report["initiatives"][initiative] = self._calculate_initiative_metrics(
                tasks
            )

        return report

    def _calculate_initiative_metrics(self, tasks: list[Task]) -> dict[str, Any]:
        """Calculate metrics for an initiative."""
        if not tasks:
            return {
                "total_tasks": 0,
                "completed_tasks": 0,
                "in_progress_tasks": 0,
                "total_effort": 0,
                "completed_effort": 0,
                "completion_percentage": 0,
                "average_task_completion": 0,
            }

        total_tasks = len(tasks)
        completed_tasks = len([task for task in tasks if task.status == "Done"])
        in_progress_tasks = len(
            [task for task in tasks if task.status == "In Progress"]
        )

        total_effort = sum(task.effort_hours for task in tasks)
        completed_effort = sum(
            task.effort_hours for task in tasks if task.status == "Done"
        )

        completion_percentage = (completed_tasks / total_tasks) * 100
        average_task_completion = (
            sum(task.completion_percent for task in tasks) / total_tasks
        )

        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "in_progress_tasks": in_progress_tasks,
            "total_effort": total_effort,
            "completed_effort": completed_effort,
            "completion_percentage": round(completion_percentage, 1),
            "average_task_completion": round(average_task_completion, 1),
        }

    def _calculate_overall_metrics(self) -> dict[str, Any]:
        """Calculate overall project metrics."""
        all_tasks = self.data.tasks
        if not all_tasks:
            return {
                "total_tasks": 0,
                "overall_completion": 0,
                "total_effort": 0,
                "burn_rate": 0,
            }

        total_tasks = len(all_tasks)
        completed_tasks = len([task for task in all_tasks if task.status == "Done"])
        overall_completion = (completed_tasks / total_tasks) * 100
        total_effort = sum(task.effort_hours for task in all_tasks)

        start_date = datetime.fromisoformat(
            min(task.created_date for task in all_tasks)
        )
        weeks_elapsed = max(1, (datetime.now() - start_date).days / 7)
        burn_rate = (
            sum(task.effort_hours for task in all_tasks if task.status == "Done")
            / weeks_elapsed
        )

        return {
            "total_tasks": total_tasks,
            "overall_completion": round(overall_completion, 1),
            "total_effort": total_effort,
            "burn_rate": round(burn_rate, 1),
        }

    def format_github_comment(self, report: dict[str, Any] | None = None) -> str:
        """Render a markdown snippet suitable for GitHub issues/PRs."""
        report = report or self.get_status_report()
        lines = [
            "### Initiative Pulse",
            f"Last updated: {report['last_updated']}",
            "",
            "| Initiative | Done | In Progress | Completion | Avg Task % |",
            "|------------|------|-------------|------------|-------------|",
        ]

        for initiative, metrics in report["initiatives"].items():
            lines.append(
                f"| {initiative} | "
                f"{metrics['completed_tasks']}/{metrics['total_tasks']} | "
                f"{metrics['in_progress_tasks']} | "
                f"{metrics['completion_percentage']}% | "
                f"{metrics['average_task_completion']}% |",
            )

        overall = report["overall_metrics"]
        lines.extend(
            [
                "",
                "### Overall Metrics",
                f"- Total tasks: {overall['total_tasks']}",
                f"- Completion: {overall['overall_completion']}%",
                f"- Total effort: {overall['total_effort']}h",
                f"- Burn rate: {overall['burn_rate']}h/week",
            ],
        )
        return "\n".join(lines)

    def export_csv(self, output_file: Path) -> None:
        """Export tasks to CSV file."""
        with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
            fieldnames = [
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
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for task in self.data.tasks:
                writer.writerow(
                    {
                        "id": task.id,
                        "title": task.title,
                        "initiative": task.initiative,
                        "phase": task.phase,
                        "priority": task.priority,
                        "status": task.status,
                        "owner": task.owner,
                        "effort_hours": task.effort_hours,
                        "completion_percent": task.completion_percent,
                        "due_date": task.due_date,
                        "github_issue": task.github_issue or "",
                    },
                )


def build_cli_parser() -> argparse.ArgumentParser:
    """Create the CLI parser shared by scripts and tests."""
    parser = argparse.ArgumentParser(
        description="GitHub-centric initiative tracker for Claude Night Market",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    add_parser = subparsers.add_parser("add", help="Add a new task")
    add_parser.add_argument("--id", required=True, help="Task ID")
    add_parser.add_argument("--title", required=True, help="Task title")
    add_parser.add_argument(
        "--initiative", required=True, help="Name of the initiative"
    )
    add_parser.add_argument(
        "--phase",
        required=True,
        choices=["Phase 1", "Phase 2", "Phase 3", "Planning/Ongoing"],
    )
    add_parser.add_argument(
        "--priority",
        required=True,
        choices=["High", "Medium", "Low"],
    )
    add_parser.add_argument("--owner", required=True, help="Task owner")
    add_parser.add_argument(
        "--effort",
        type=float,
        required=True,
        help="Effort in hours",
    )
    add_parser.add_argument("--due", required=True, help="Due date (YYYY-MM-DD)")
    add_parser.add_argument("--github-issue", help="GitHub issue or PR URL/number")

    update_parser = subparsers.add_parser("update", help="Update a task")
    update_parser.add_argument("--id", required=True, help="Task ID")
    update_parser.add_argument(
        "--status", choices=["To Do", "In Progress", "Review", "Done"]
    )
    update_parser.add_argument(
        "--completion", type=float, help="Completion percentage (0-100)"
    )
    update_parser.add_argument("--github-issue", help="GitHub issue or PR URL/number")

    status_parser = subparsers.add_parser("status", help="Show status report")
    status_parser.add_argument(
        "--github-comment",
        action="store_true",
        help="Output markdown summary for GitHub issues/PRs",
    )

    export_parser = subparsers.add_parser("export", help="Export tasks to CSV")
    export_parser.add_argument("--output", required=True, help="Output CSV file path")

    return parser


def run_cli(argv: list[str] | None = None) -> int:
    """Entry point used by scripts and tests."""
    parser = build_cli_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 0

    tracker = ProjectTracker()

    if args.command == "add":
        task = Task(
            id=args.id,
            title=args.title,
            initiative=args.initiative,
            phase=args.phase,
            priority=args.priority,
            status="To Do",
            owner=args.owner,
            effort_hours=args.effort,
            completion_percent=0,
            due_date=args.due,
            created_date=datetime.now().isoformat(),
            updated_date=datetime.now().isoformat(),
            github_issue=args.github_issue,
        )
        tracker.add_task(task)

    elif args.command == "update":
        updates: dict[str, Any] = {}
        if args.status:
            updates["status"] = args.status
        if args.completion is not None:
            updates["completion_percent"] = args.completion
        if args.github_issue is not None:
            updates["github_issue"] = args.github_issue

        if updates:
            tracker.update_task(args.id, updates)
        else:
            pass

    elif args.command == "status":
        tracker.get_status_report()
        if args.github_comment:
            pass
        else:
            pass

    elif args.command == "export":
        tracker.export_csv(Path(args.output))

    return 0
