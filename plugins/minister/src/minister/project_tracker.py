"""Provide core tracking utilities for Minister.

Returns (JSON):
    success (bool): Whether operation completed successfully
    data.command (str): The command that was executed
    data.result (dict): Command-specific result data
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import sys
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass
class Task:
    """Represent a task in the initiative."""

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
    """Track progress across initiatives."""

    tasks: list[Task]
    last_updated: str


class ProjectTracker:
    """Manage the project tracking system."""

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
            try:
                with open(self.data_file, encoding="utf-8") as file:
                    data = json.load(file)
            except (json.JSONDecodeError, OSError) as exc:
                logging.getLogger(__name__).warning(
                    "minister: corrupt data file %s: %s", self.data_file, exc
                )
                return InitiativeTracker([], datetime.now(UTC).isoformat())
            tasks = [Task(**task) for task in data.get("tasks", [])]
            return InitiativeTracker(
                tasks, data.get("last_updated", datetime.now(UTC).isoformat())
            )

        return InitiativeTracker([], datetime.now(UTC).isoformat())

    def _save_data(self) -> None:
        """Save tracking data to file."""
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "tasks": [asdict(task) for task in self.data.tasks],
            "last_updated": datetime.now(UTC).isoformat(),
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
                task.updated_date = datetime.now(UTC).isoformat()
                self._save_data()
                return

    def get_tasks_by_initiative(self, initiative: str) -> list[Task]:
        """Get all tasks for a specific initiative."""
        return [task for task in self.data.tasks if task.initiative == initiative]

    def get_status_report(self) -> dict[str, Any]:
        """Generate detailed status report."""
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

        total_effort = 0.0
        completed_effort = 0.0
        completed_count = 0
        earliest: str | None = None
        for task in all_tasks:
            total_effort += task.effort_hours
            if earliest is None or task.created_date < earliest:
                earliest = task.created_date
            if task.status == "Done":
                completed_count += 1
                completed_effort += task.effort_hours

        total_tasks = len(all_tasks)
        overall_completion = (completed_count / total_tasks) * 100

        if earliest is None or earliest == "":
            weeks_elapsed = 1.0
        else:
            start_date = datetime.fromisoformat(earliest)
            if start_date.tzinfo is None:
                start_date = start_date.replace(tzinfo=UTC)
            weeks_elapsed = max(1, (datetime.now(UTC) - start_date).days / 7)
        burn_rate = completed_effort / weeks_elapsed

        return {
            "total_tasks": total_tasks,
            "overall_completion": round(overall_completion, 1),
            "total_effort": total_effort,
            "burn_rate": round(burn_rate, 1),
        }

    def format_github_comment(self, report: dict[str, Any] | None = None) -> str:
        """Render a markdown summary for GitHub issues and pull requests."""
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
    parser.add_argument(
        "--output-json",
        action="store_true",
        help="Output results as JSON for programmatic use",
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


def _collect_updates(args: argparse.Namespace) -> dict[str, Any]:
    """Build the updates dict from CLI args for the update command."""
    updates: dict[str, Any] = {}
    if args.status:
        updates["status"] = args.status
    if args.completion is not None:
        updates["completion_percent"] = args.completion
    if args.github_issue is not None:
        updates["github_issue"] = args.github_issue
    return updates


def run_cli(argv: list[str] | None = None) -> int:
    """Execute the CLI entry point."""
    parser = build_cli_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 0

    try:
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
                created_date=datetime.now(UTC).isoformat(),
                updated_date=datetime.now(UTC).isoformat(),
                github_issue=args.github_issue,
            )
            tracker.add_task(task)
            add_result: dict[str, Any] = {
                "command": "add",
                "task_id": task.id,
                "title": task.title,
                "initiative": task.initiative,
            }
            _output_result(add_result, args)

        elif args.command == "update":
            updates = _collect_updates(args)
            if updates:
                tracker.update_task(args.id, updates)
                _output_result(
                    {"command": "update", "task_id": args.id, "updates": updates},
                    args,
                )
            else:
                _output_result(
                    {
                        "command": "update",
                        "task_id": args.id,
                        "message": "No updates specified",
                    },
                    args,
                )

        elif args.command == "status":
            report = tracker.get_status_report()
            if hasattr(args, "github_comment") and args.github_comment:
                print(tracker.format_github_comment(report))
            else:
                _output_result({"command": "status", "report": report}, args)

        elif args.command == "export":
            output_path = Path(args.output)
            tracker.export_csv(output_path)
            export_result: dict[str, Any] = {
                "command": "export",
                "output_file": str(output_path),
                "tasks_exported": len(tracker.data.tasks),
            }
            _output_result(export_result, args)

        return 0

    except Exception as e:
        _output_error(f"Error executing command: {e}", args)
        return 1


def _output_result(result: dict[str, Any], args: argparse.Namespace) -> None:
    """Print the result in the specified format."""
    if args.output_json:
        print(
            json.dumps(
                {
                    "success": True,
                    "data": result,
                },
                indent=2,
                default=str,
            )
        )
    else:
        # Human-readable format
        print(f"Command '{result['command']}' completed successfully")
        for key, value in result.items():
            if key != "command":
                print(f"  {key}: {value}")


def _output_error(message: str, args: argparse.Namespace) -> None:
    """Output error in requested format."""
    if args.output_json:
        print(
            json.dumps(
                {
                    "success": False,
                    "error": message,
                },
                indent=2,
            )
        )
    else:
        print(f"Error: {message}", file=sys.stderr)
