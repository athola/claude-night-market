"""Shared test fixtures for minister plugin tests.

Provides reusable fixtures following TDD/BDD best practices:
- Isolated test environments with temp directories
- Pre-configured Task and ProjectTracker instances
- Sample data generators for various test scenarios
"""

from __future__ import annotations

import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from minister.project_tracker import ProjectTracker, Task

# Seed RNG for deterministic test data generation
_test_rng = random.Random(42)  # noqa: S311

if TYPE_CHECKING:
    from collections.abc import Generator

# =============================================================================
# Base Fixtures: Isolation & Cleanup
# =============================================================================


@pytest.fixture
def temp_data_dir(tmp_path: Path) -> Path:
    """Provide an isolated temp directory for test data."""
    data_dir = tmp_path / "minister_data"
    data_dir.mkdir()
    return data_dir


@pytest.fixture
def temp_data_file(temp_data_dir: Path) -> Path:
    """Provide a path to a non-existent data file for fresh tracker tests."""
    return temp_data_dir / "project-data.json"


# =============================================================================
# Task Fixtures: Pre-built Task instances for testing
# =============================================================================


@pytest.fixture
def minimal_task() -> Task:
    """Provide a minimal valid Task with required fields only."""
    return Task(
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


@pytest.fixture
def task_with_github_issue() -> Task:
    """Provide a Task with a GitHub issue linked."""
    return Task(
        id="TSK-002",
        title="GitHub-Linked Task",
        initiative="GitHub Projects Hygiene",
        phase="Phase 2",
        priority="High",
        status="In Progress",
        owner="dev-lead",
        effort_hours=8.0,
        completion_percent=50.0,
        due_date="2025-01-20",
        created_date="2025-01-05T09:00:00",
        updated_date="2025-01-10T14:30:00",
        github_issue="https://github.com/org/repo/issues/123",
    )


@pytest.fixture
def completed_task() -> Task:
    """Provide a fully completed Task."""
    return Task(
        id="TSK-003",
        title="Completed Task",
        initiative="Docs & Enablement",
        phase="Phase 1",
        priority="Low",
        status="Done",
        owner="doc-writer",
        effort_hours=4.0,
        completion_percent=100.0,
        due_date="2025-01-10",
        created_date="2025-01-02T11:00:00",
        updated_date="2025-01-08T16:00:00",
    )


# =============================================================================
# Task Collection Fixtures: Multiple tasks for metrics testing
# =============================================================================


@pytest.fixture
def sample_tasks() -> list[Task]:
    """Provide a diverse set of tasks across initiatives and statuses."""
    base_date = datetime(2025, 1, 1, 10, 0, 0)
    return [
        Task(
            id="GHYG-001",
            title="Set up project board",
            initiative="GitHub Projects Hygiene",
            phase="Phase 1",
            priority="High",
            status="Done",
            owner="admin",
            effort_hours=2.0,
            completion_percent=100.0,
            due_date="2025-01-05",
            created_date=base_date.isoformat(),
            updated_date=(base_date + timedelta(days=4)).isoformat(),
        ),
        Task(
            id="GHYG-002",
            title="Create label taxonomy",
            initiative="GitHub Projects Hygiene",
            phase="Phase 1",
            priority="Medium",
            status="In Progress",
            owner="admin",
            effort_hours=4.0,
            completion_percent=75.0,
            due_date="2025-01-10",
            created_date=base_date.isoformat(),
            updated_date=(base_date + timedelta(days=7)).isoformat(),
        ),
        Task(
            id="PR-001",
            title="Define PR template",
            initiative="Pull Request Readiness",
            phase="Phase 2",
            priority="High",
            status="To Do",
            owner="tech-lead",
            effort_hours=3.0,
            completion_percent=0.0,
            due_date="2025-01-15",
            created_date=base_date.isoformat(),
            updated_date=base_date.isoformat(),
        ),
        Task(
            id="DOC-001",
            title="Write onboarding guide",
            initiative="Docs & Enablement",
            phase="Phase 1",
            priority="Medium",
            status="Done",
            owner="writer",
            effort_hours=6.0,
            completion_percent=100.0,
            due_date="2025-01-08",
            created_date=base_date.isoformat(),
            updated_date=(base_date + timedelta(days=6)).isoformat(),
        ),
        Task(
            id="DOC-002",
            title="Create video tutorial",
            initiative="Docs & Enablement",
            phase="Phase 2",
            priority="Low",
            status="To Do",
            owner="content",
            effort_hours=10.0,
            completion_percent=0.0,
            due_date="2025-01-25",
            created_date=base_date.isoformat(),
            updated_date=base_date.isoformat(),
        ),
    ]


@pytest.fixture
def single_initiative_tasks() -> list[Task]:
    """Provide tasks from a single initiative for focused testing."""
    base_date = datetime(2025, 1, 1, 10, 0, 0)
    return [
        Task(
            id="TEST-001",
            title="Task A",
            initiative="Single Initiative",
            phase="Phase 1",
            priority="High",
            status="Done",
            owner="tester",
            effort_hours=5.0,
            completion_percent=100.0,
            due_date="2025-01-05",
            created_date=base_date.isoformat(),
            updated_date=(base_date + timedelta(days=3)).isoformat(),
        ),
        Task(
            id="TEST-002",
            title="Task B",
            initiative="Single Initiative",
            phase="Phase 1",
            priority="Medium",
            status="In Progress",
            owner="tester",
            effort_hours=3.0,
            completion_percent=50.0,
            due_date="2025-01-10",
            created_date=base_date.isoformat(),
            updated_date=(base_date + timedelta(days=5)).isoformat(),
        ),
        Task(
            id="TEST-003",
            title="Task C",
            initiative="Single Initiative",
            phase="Phase 2",
            priority="Low",
            status="To Do",
            owner="tester",
            effort_hours=2.0,
            completion_percent=0.0,
            due_date="2025-01-15",
            created_date=base_date.isoformat(),
            updated_date=base_date.isoformat(),
        ),
    ]


# =============================================================================
# ProjectTracker Fixtures: Pre-configured tracker instances
# =============================================================================


@pytest.fixture
def empty_tracker(temp_data_file: Path) -> ProjectTracker:
    """Provide a fresh ProjectTracker with no tasks."""
    return ProjectTracker(data_file=temp_data_file)


@pytest.fixture
def populated_tracker(temp_data_file: Path, sample_tasks: list[Task]) -> ProjectTracker:
    """Provide a ProjectTracker pre-loaded with sample tasks."""
    tracker = ProjectTracker(data_file=temp_data_file)
    for task in sample_tasks:
        tracker.add_task(task)
    return tracker


@pytest.fixture
def seeded_data_file(temp_data_file: Path, sample_tasks: list[Task]) -> Path:
    """Provide a data file pre-seeded with sample tasks for load testing."""
    data = {
        "tasks": [
            {
                "id": t.id,
                "title": t.title,
                "initiative": t.initiative,
                "phase": t.phase,
                "priority": t.priority,
                "status": t.status,
                "owner": t.owner,
                "effort_hours": t.effort_hours,
                "completion_percent": t.completion_percent,
                "due_date": t.due_date,
                "created_date": t.created_date,
                "updated_date": t.updated_date,
                "github_issue": t.github_issue,
            }
            for t in sample_tasks
        ],
        "last_updated": datetime.now().isoformat(),
    }
    temp_data_file.parent.mkdir(parents=True, exist_ok=True)
    with open(temp_data_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return temp_data_file


# =============================================================================
# CLI Testing Fixtures
# =============================================================================


@pytest.fixture
def cli_env(temp_data_file: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Set up environment for CLI integration tests."""
    # CLI tests use the default data path, so we patch it
    return temp_data_file


# =============================================================================
# Generators: For parametrized and property-based testing
# =============================================================================


def generate_task_id(prefix: str, number: int) -> str:
    """Generate a task ID in the standard format."""
    return f"{prefix}-{number:03d}"


def generate_tasks_batch(
    count: int,
    initiative: str = "Test Initiative",
    status_distribution: dict[str, float] | None = None,
) -> Generator[Task, None, None]:
    """Generate a batch of tasks with configurable distribution.

    Args:
        count: Number of tasks to generate
        initiative: Initiative name for all tasks
        status_distribution: Optional dict mapping status to proportion
            e.g., {"Done": 0.5, "In Progress": 0.3, "To Do": 0.2}
    """
    statuses = ["To Do", "In Progress", "Review", "Done"]
    if status_distribution:
        weights = [status_distribution.get(s, 0.25) for s in statuses]
    else:
        weights = [0.25, 0.25, 0.25, 0.25]

    base_date = datetime(2025, 1, 1, 10, 0, 0)

    for i in range(1, count + 1):
        status = _test_rng.choices(statuses, weights=weights, k=1)[0]
        completion = 100.0 if status == "Done" else _test_rng.uniform(0, 99)

        yield Task(
            id=generate_task_id("GEN", i),
            title=f"Generated Task {i}",
            initiative=initiative,
            phase=_test_rng.choice(["Phase 1", "Phase 2", "Phase 3"]),
            priority=_test_rng.choice(["High", "Medium", "Low"]),
            status=status,
            owner=f"user{i % 5}",
            effort_hours=float(_test_rng.randint(1, 20)),
            completion_percent=round(completion, 1),
            due_date=(base_date + timedelta(days=i * 3)).strftime("%Y-%m-%d"),
            created_date=base_date.isoformat(),
            updated_date=(base_date + timedelta(days=i)).isoformat(),
        )
