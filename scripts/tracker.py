#!/usr/bin/env python3
"""
Project Management Tracker

Simple CLI tool for tracking initiative progress and generating reports.
"""

import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass, asdict
import csv

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

@dataclass
class InitiativeTracker:
    """Tracks progress across all initiatives."""
    tasks: List[Task]
    last_updated: str

class ProjectTracker:
    """Main project tracking system."""

    def __init__(self, data_file: Path = Path("project-data.json")):
        self.data_file = data_file
        self.data = self._load_data()

    def _load_data(self) -> InitiativeTracker:
        """Load tracking data from file."""
        if self.data_file.exists():
            with open(self.data_file) as f:
                data = json.load(f)
                tasks = [Task(**task) for task in data['tasks']]
                return InitiativeTracker(tasks, data['last_updated'])
        else:
            return InitiativeTracker([], datetime.now().isoformat())

    def _save_data(self):
        """Save tracking data to file."""
        data = {
            'tasks': [asdict(task) for task in self.data.tasks],
            'last_updated': datetime.now().isoformat()
        }
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=2)

    def add_task(self, task: Task):
        """Add a new task to the tracker."""
        self.data.tasks.append(task)
        self._save_data()
        print(f"Added task: {task.title}")

    def update_task(self, task_id: str, updates: Dict[str, Any]):
        """Update an existing task."""
        for task in self.data.tasks:
            if task.id == task_id:
                for key, value in updates.items():
                    setattr(task, key, value)
                task.updated_date = datetime.now().isoformat()
                self._save_data()
                print(f"Updated task: {task.title}")
                return
        print(f"Task not found: {task_id}")

    def get_tasks_by_initiative(self, initiative: str) -> List[Task]:
        """Get all tasks for a specific initiative."""
        return [task for task in self.data.tasks if task.initiative == initiative]

    def get_status_report(self) -> Dict[str, Any]:
        """Generate comprehensive status report."""
        report = {
            'last_updated': self.data.last_updated,
            'initiatives': {},
            'overall_metrics': self._calculate_overall_metrics()
        }

        for initiative in ['Architecture Review', 'Test Infrastructure Modernization', 'Documentation Drive']:
            tasks = self.get_tasks_by_initiative(initiative)
            report['initiatives'][initiative] = self._calculate_initiative_metrics(tasks)

        return report

    def _calculate_initiative_metrics(self, tasks: List[Task]) -> Dict[str, Any]:
        """Calculate metrics for an initiative."""
        if not tasks:
            return {
                'total_tasks': 0,
                'completed_tasks': 0,
                'in_progress_tasks': 0,
                'total_effort': 0,
                'completed_effort': 0,
                'completion_percentage': 0,
                'average_task_completion': 0
            }

        total_tasks = len(tasks)
        completed_tasks = len([t for t in tasks if t.status == 'Done'])
        in_progress_tasks = len([t for t in tasks if t.status == 'In Progress'])

        total_effort = sum(t.effort_hours for t in tasks)
        completed_effort = sum(t.effort_hours for t in tasks if t.status == 'Done')

        completion_percentage = (completed_tasks / total_tasks) * 100
        average_task_completion = sum(t.completion_percent for t in tasks) / total_tasks

        return {
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'in_progress_tasks': in_progress_tasks,
            'total_effort': total_effort,
            'completed_effort': completed_effort,
            'completion_percentage': round(completion_percentage, 1),
            'average_task_completion': round(average_task_completion, 1)
        }

    def _calculate_overall_metrics(self) -> Dict[str, Any]:
        """Calculate overall project metrics."""
        all_tasks = self.data.tasks
        if not all_tasks:
            return {
                'total_tasks': 0,
                'overall_completion': 0,
                'total_effort': 0,
                'burn_rate': 0
            }

        total_tasks = len(all_tasks)
        completed_tasks = len([t for t in all_tasks if t.status == 'Done'])
        overall_completion = (completed_tasks / total_tasks) * 100
        total_effort = sum(t.effort_hours for t in all_tasks)

        # Simple burn rate calculation (effort completed per week)
        start_date = datetime.fromisoformat(min(t.created_date for t in all_tasks))
        weeks_elapsed = max(1, (datetime.now() - start_date).days / 7)
        burn_rate = sum(t.effort_hours for t in all_tasks if t.status == 'Done') / weeks_elapsed

        return {
            'total_tasks': total_tasks,
            'overall_completion': round(overall_completion, 1),
            'total_effort': total_effort,
            'burn_rate': round(burn_rate, 1)
        }

    def export_csv(self, output_file: Path):
        """Export tasks to CSV file."""
        with open(output_file, 'w', newline='') as csvfile:
            fieldnames = ['id', 'title', 'initiative', 'phase', 'priority', 'status',
                         'owner', 'effort_hours', 'completion_percent', 'due_date']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for task in self.data.tasks:
                writer.writerow({
                    'id': task.id,
                    'title': task.title,
                    'initiative': task.initiative,
                    'phase': task.phase,
                    'priority': task.priority,
                    'status': task.status,
                    'owner': task.owner,
                    'effort_hours': task.effort_hours,
                    'completion_percent': task.completion_percent,
                    'due_date': task.due_date
                })
        print(f"Exported {len(self.data.tasks)} tasks to {output_file}")

def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(description='Claude Night Market Initiative Tracker')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Add task command
    add_parser = subparsers.add_parser('add', help='Add a new task')
    add_parser.add_argument('--id', required=True, help='Task ID')
    add_parser.add_argument('--title', required=True, help='Task title')
    add_parser.add_argument('--initiative', required=True,
                           choices=['Architecture Review', 'Test Infrastructure Modernization', 'Documentation Drive'])
    add_parser.add_argument('--phase', required=True,
                           choices=['Phase 1', 'Phase 2', 'Phase 3', 'Planning/Ongoing'])
    add_parser.add_argument('--priority', required=True, choices=['High', 'Medium', 'Low'])
    add_parser.add_argument('--owner', required=True, help='Task owner')
    add_parser.add_argument('--effort', type=float, required=True, help='Effort in hours')
    add_parser.add_argument('--due', required=True, help='Due date (YYYY-MM-DD)')

    # Update task command
    update_parser = subparsers.add_parser('update', help='Update a task')
    update_parser.add_argument('--id', required=True, help='Task ID')
    update_parser.add_argument('--status', choices=['To Do', 'In Progress', 'Review', 'Done'])
    update_parser.add_argument('--completion', type=float, help='Completion percentage (0-100)')

    # Status command
    status_parser = subparsers.add_parser('status', help='Show status report')

    # Export command
    export_parser = subparsers.add_parser('export', help='Export tasks to CSV')
    export_parser.add_argument('--output', required=True, help='Output CSV file path')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    tracker = ProjectTracker()

    if args.command == 'add':
        task = Task(
            id=args.id,
            title=args.title,
            initiative=args.initiative,
            phase=args.phase,
            priority=args.priority,
            status='To Do',
            owner=args.owner,
            effort_hours=args.effort,
            completion_percent=0,
            due_date=args.due,
            created_date=datetime.now().isoformat(),
            updated_date=datetime.now().isoformat()
        )
        tracker.add_task(task)

    elif args.command == 'update':
        updates = {}
        if args.status:
            updates['status'] = args.status
        if args.completion is not None:
            updates['completion_percent'] = args.completion

        if updates:
            tracker.update_task(args.id, updates)
        else:
            print("No updates specified")

    elif args.command == 'status':
        report = tracker.get_status_report()
        print(json.dumps(report, indent=2))

    elif args.command == 'export':
        tracker.export_csv(Path(args.output))

if __name__ == '__main__':
    main()