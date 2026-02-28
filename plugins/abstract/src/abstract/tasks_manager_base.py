"""Shared Tasks Manager base for Claude Code Tasks integration.

Provides lazy task creation with user prompts on ambiguity,
supporting both Claude Code Tasks system and file-based fallback.

Plugins configure this via TasksManagerConfig with plugin-specific
constants and cross-cutting keywords.
"""

from __future__ import annotations

import json
import re
import subprocess
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


@dataclass
class TasksManagerConfig:
    """Plugin-specific configuration for TasksManager."""

    plugin_name: str
    task_prefix: str
    default_state_dir: str
    default_state_file: str
    env_var_prefix: str
    large_scope_token_threshold: int = 5000
    large_scope_word_threshold: int = 30
    cross_cutting_keywords: list[str] = field(default_factory=list)


class AmbiguityType(Enum):
    """Types of task ambiguity that require user input."""

    NONE = "none"
    MULTIPLE_COMPONENTS = "multiple_components"
    CROSS_CUTTING = "cross_cutting"
    LARGE_SCOPE = "large_scope"
    CIRCULAR_DEPENDENCY = "circular_dependency"


@dataclass
class AmbiguityResult:
    """Result of ambiguity detection."""

    is_ambiguous: bool
    ambiguity_type: AmbiguityType = AmbiguityType.NONE
    components: list[str] = field(default_factory=list)
    message: str = ""


@dataclass
class TaskState:
    """Current state of task execution."""

    completed_tasks: list[str] = field(default_factory=list)
    pending_tasks: list[str] = field(default_factory=list)
    completed_count: int = 0
    total_count: int = 0

    @property
    def in_progress_tasks(self) -> list[str]:
        """Tasks currently in progress."""
        return [t for t in self.pending_tasks if t not in self.completed_tasks]


@dataclass
class ResumeState:
    """State for resuming previous execution."""

    has_incomplete_tasks: bool = False
    next_task_id: str | None = None
    pending_tasks: list[str] = field(default_factory=list)
    completed_tasks: list[str] = field(default_factory=list)
    completed_count: int = 0


def get_claude_code_version() -> str | None:
    """Get the current Claude Code version, or None if not in Claude Code."""
    try:
        result = subprocess.run(
            ["claude", "--version"],  # noqa: S607
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if result.returncode == 0:
            # Parse version from output like "2.1.17 (Claude Code)"
            match = re.search(r"(\d+\.\d+\.\d+)", result.stdout)
            if match:
                return match.group(1)
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    return None


def is_tasks_available() -> bool:
    """Check if Claude Code Tasks system is available (2.1.16+)."""
    version = get_claude_code_version()
    if version is None:
        return False

    try:
        parts = [int(p) for p in version.split(".")]
        # Version 2.1.16 or higher
        if parts[0] > 2:
            return True
        if parts[0] == 2 and parts[1] > 1:
            return True
        if parts[0] == 2 and parts[1] == 1 and parts[2] >= 16:
            return True
    except (ValueError, IndexError):
        pass

    return False


_MULTI_COMPONENT_THRESHOLD = 2


def detect_ambiguity(
    task_description: str,
    context: dict[str, Any] | None = None,
    *,
    cross_cutting_keywords: list[str] | None = None,
    large_scope_token_threshold: int = 5000,
    large_scope_word_threshold: int = 30,
) -> AmbiguityResult:
    """Detect if task boundaries are ambiguous and need user input.

    Args:
        task_description: The task description to analyze
        context: Optional context with files_touched, existing_tasks, estimated_tokens
        cross_cutting_keywords: Plugin-specific keywords indicating broad scope
        large_scope_token_threshold: Token count above which scope is "large"
        large_scope_word_threshold: Word count above which scope is "large"

    Returns:
        AmbiguityResult with is_ambiguous flag and type

    """
    context = context or {}
    keywords = cross_cutting_keywords or []

    # Check for multiple components
    files_touched = context.get("files_touched", [])
    if len(files_touched) > _MULTI_COMPONENT_THRESHOLD:
        return AmbiguityResult(
            is_ambiguous=True,
            ambiguity_type=AmbiguityType.MULTIPLE_COMPONENTS,
            components=files_touched,
            message=f"Task touches {len(files_touched)} components",
        )

    # Check for cross-cutting concerns
    description_lower = task_description.lower()
    for keyword in keywords:
        if keyword in description_lower:
            return AmbiguityResult(
                is_ambiguous=True,
                ambiguity_type=AmbiguityType.CROSS_CUTTING,
                message=f"Cross-cutting concern detected: {keyword}",
            )

    # Check for large scope
    estimated_tokens = context.get("estimated_tokens", 0)
    if estimated_tokens > large_scope_token_threshold:
        return AmbiguityResult(
            is_ambiguous=True,
            ambiguity_type=AmbiguityType.LARGE_SCOPE,
            message=f"Large scope: {estimated_tokens} estimated tokens",
        )

    # Estimate tokens from description length if not provided
    if estimated_tokens == 0:
        word_count = len(task_description.split())
        if word_count > large_scope_word_threshold:
            return AmbiguityResult(
                is_ambiguous=True,
                ambiguity_type=AmbiguityType.LARGE_SCOPE,
                message=f"Large scope: {word_count} words in description",
            )

    # Check for circular dependency risk
    existing_tasks = context.get("existing_tasks", [])
    for existing in existing_tasks:
        existing_desc = existing.get("description", "").lower()
        task_lower = task_description.lower()

        task_services = set(
            re.findall(r"\b(\w+(?:service|manager|handler))\b", task_lower, re.I)
        )
        existing_services = set(
            re.findall(r"\b(\w+(?:service|manager|handler))\b", existing_desc, re.I)
        )

        if task_services and existing_services:
            for service in task_services:
                if service.lower() in existing_desc and "uses" in task_lower:
                    for other_service in existing_services:
                        if (
                            other_service.lower() in task_lower
                            and "uses" in existing_desc
                        ):
                            return AmbiguityResult(
                                is_ambiguous=True,
                                ambiguity_type=AmbiguityType.CIRCULAR_DEPENDENCY,
                                message="Potential circular dependency detected",
                            )

    return AmbiguityResult(is_ambiguous=False)


class TasksManager:
    """Manages task state with lazy creation and user prompts.

    Supports dual-mode operation:
    - Claude Code Tasks system (2.1.16+)
    - File-based fallback for older versions or non-Claude environments
    """

    def __init__(
        self,
        project_path: Path,
        fallback_state_file: Path,
        config: TasksManagerConfig,
        ask_user_fn: Callable[[str], str] | None = None,
        use_tasks: bool | None = None,
    ):
        """Initialize TasksManager.

        Args:
            project_path: Root path of the project
            fallback_state_file: Path to fallback state JSON file
            config: Plugin-specific configuration
            ask_user_fn: Optional function to prompt user for input
            use_tasks: Override tasks availability (None = auto-detect)

        """
        self.project_path = project_path
        self.fallback_state_file = fallback_state_file
        self.config = config
        self._ask_user = ask_user_fn or self._default_ask_user
        self._use_tasks = use_tasks if use_tasks is not None else is_tasks_available()

        # Plan tasks (not yet created in Tasks system)
        self._plan_tasks: list[str] = []

        # Mock methods for Claude Code task tools (will be overridden in tests)
        self._task_create: Callable[..., dict] | None = None
        self._task_list: Callable[[], list[dict]] | None = None
        self._task_update: Callable[..., bool] | None = None
        self._task_get: Callable[[str], dict | None] | None = None

    def _default_ask_user(self, prompt: str) -> str:
        """Default user prompt using input()."""
        try:
            return input(prompt)
        except (EOFError, KeyboardInterrupt):
            return ""

    @property
    def pending_count(self) -> int:
        """Number of tasks in the plan not yet created."""
        return len(self._plan_tasks)

    @property
    def created_count(self) -> int:
        """Number of tasks created in the Tasks system."""
        if self._task_list:
            return len(self._task_list())
        return 0

    def load_plan(self, tasks: list[str]) -> None:
        """Load a plan of tasks without creating them yet (lazy loading).

        Args:
            tasks: List of task descriptions from the implementation plan

        """
        self._plan_tasks = tasks.copy()

    def ensure_task_exists(
        self,
        task_description: str,
        dependencies: list[str] | None = None,
    ) -> str | list[str]:
        """Ensure a task exists, creating it lazily if needed.

        If ambiguity is detected, prompts user for decision.

        Args:
            task_description: Description of the task
            dependencies: Optional list of task IDs this task depends on

        Returns:
            Task ID (str) or list of task IDs if split into subtasks

        """
        dependencies = dependencies or []

        if self._use_tasks and self._task_list and self._task_create:
            # Check for existing similar task
            existing_tasks = self._task_list()
            for task in existing_tasks:
                if task.get("description") == task_description:
                    return str(task["id"])

            # Check for ambiguity
            context = {"existing_tasks": existing_tasks}
            ambiguity = detect_ambiguity(
                task_description,
                context,
                cross_cutting_keywords=self.config.cross_cutting_keywords,
                large_scope_token_threshold=self.config.large_scope_token_threshold,
                large_scope_word_threshold=self.config.large_scope_word_threshold,
            )

            if ambiguity.is_ambiguous:
                user_choice = self._ask_user(
                    f"\nAmbiguity detected: {ambiguity.message}\n"
                    f"Task: {task_description}\n\n"
                    f"Options:\n"
                    f"  1. Create as single task\n"
                    f"  2. Split into subtasks\n"
                    f"  3. Let me specify the split\n\n"
                    f"Choice [1/2/3]: "
                )

                if user_choice == "2":
                    return self._create_subtasks(
                        task_description, ambiguity, dependencies
                    )

            # Create single task
            result = self._task_create(task_description, dependencies=dependencies)
            return str(result["id"])
        else:
            # File-based fallback
            return self._ensure_task_in_file(task_description, dependencies)

    def _create_subtasks(
        self,
        task_description: str,
        ambiguity: AmbiguityResult,
        dependencies: list[str],
    ) -> list[str]:
        """Create multiple subtasks from an ambiguous task.

        Args:
            task_description: Original task description
            ambiguity: Ambiguity detection result
            dependencies: Dependencies for the first subtask

        Returns:
            List of created task IDs

        """
        task_ids: list[str] = []

        if ambiguity.components:
            for i, component in enumerate(ambiguity.components):
                subtask_desc = f"{task_description} - {component}"
                deps = dependencies if i == 0 else [task_ids[-1]]
                if self._task_create:
                    result = self._task_create(subtask_desc, dependencies=deps)
                    task_ids.append(str(result["id"]))
        else:
            for i, suffix in enumerate(["Part 1", "Part 2"]):
                subtask_desc = f"{task_description} - {suffix}"
                deps = dependencies if i == 0 else [task_ids[-1]]
                if self._task_create:
                    result = self._task_create(subtask_desc, dependencies=deps)
                    task_ids.append(str(result["id"]))

        return task_ids

    def _ensure_task_in_file(
        self,
        task_description: str,
        dependencies: list[str],
    ) -> str:
        """Create or find task in file-based state.

        Args:
            task_description: Description of the task
            dependencies: Task dependencies

        Returns:
            Task ID

        """
        self.fallback_state_file.parent.mkdir(parents=True, exist_ok=True)

        if self.fallback_state_file.exists():
            state = json.loads(self.fallback_state_file.read_text())
        else:
            state = {"tasks": {}, "metrics": {"tasks_complete": 0, "tasks_total": 0}}

        task_id = f"{self.config.task_prefix}-{len(state['tasks']) + 1:03d}"

        state["tasks"][task_id] = {
            "description": task_description,
            "status": "pending",
            "dependencies": dependencies,
        }
        state["metrics"]["tasks_total"] = len(state["tasks"])

        self.fallback_state_file.write_text(json.dumps(state, indent=2))

        return task_id

    def get_state(self) -> TaskState:
        """Get current task state.

        Returns:
            TaskState with completed and pending tasks

        """
        if self._use_tasks and self._task_list:
            tasks = self._task_list()
            completed = [t["id"] for t in tasks if t.get("status") == "complete"]
            pending = [t["id"] for t in tasks if t.get("status") != "complete"]
            return TaskState(
                completed_tasks=completed,
                pending_tasks=pending,
                completed_count=len(completed),
                total_count=len(tasks),
            )
        else:
            if not self.fallback_state_file.exists():
                return TaskState()

            state = json.loads(self.fallback_state_file.read_text())
            tasks_dict: dict[str, dict[str, Any]] = state.get("tasks", {})
            completed = [
                tid for tid, t in tasks_dict.items() if t.get("status") == "complete"
            ]
            pending = [
                tid for tid, t in tasks_dict.items() if t.get("status") != "complete"
            ]

            return TaskState(
                completed_tasks=completed,
                pending_tasks=pending,
                completed_count=len(completed),
                total_count=len(tasks_dict),
            )

    def detect_resume_state(self) -> ResumeState:
        """Detect if there's a previous execution to resume.

        Returns:
            ResumeState with information about incomplete tasks

        """
        if self._use_tasks and self._task_list:
            tasks = self._task_list()
        else:
            if not self.fallback_state_file.exists():
                return ResumeState()
            state = json.loads(self.fallback_state_file.read_text())
            tasks = [
                {"id": tid, **tdata} for tid, tdata in state.get("tasks", {}).items()
            ]

        completed = [t["id"] for t in tasks if t.get("status") == "complete"]
        in_progress = [t["id"] for t in tasks if t.get("status") == "in_progress"]
        pending = [t["id"] for t in tasks if t.get("status") == "pending"]

        has_incomplete = len(in_progress) > 0 or len(pending) > 0
        next_task = in_progress[0] if in_progress else (pending[0] if pending else None)

        return ResumeState(
            has_incomplete_tasks=has_incomplete,
            next_task_id=next_task,
            pending_tasks=pending,
            completed_tasks=completed,
            completed_count=len(completed),
        )

    def prompt_for_resume(self) -> bool:
        """Ask user if they want to resume previous execution.

        Returns:
            True if user wants to resume, False otherwise

        """
        resume_state = self.detect_resume_state()
        if not resume_state.has_incomplete_tasks:
            return False

        response = self._ask_user(
            f"\nFound incomplete execution:\n"
            f"  Completed: {resume_state.completed_count} tasks\n"
            f"  Pending: {len(resume_state.pending_tasks)} tasks\n"
            f"  Next: {resume_state.next_task_id}\n\n"
            f"Would you like to resume? [Y/n]: "
        )

        return response.lower() in ("", "y", "yes")

    def can_start_task(self, task_id: str) -> bool:
        """Check if a task can start (dependencies met).

        Args:
            task_id: ID of the task to check

        Returns:
            True if task can start, False if blocked by dependencies

        """
        if self._use_tasks and self._task_list:
            tasks = self._task_list()
        else:
            if not self.fallback_state_file.exists():
                return True
            state = json.loads(self.fallback_state_file.read_text())
            tasks = [
                {"id": tid, **tdata} for tid, tdata in state.get("tasks", {}).items()
            ]

        task = next((t for t in tasks if t["id"] == task_id), None)
        if not task:
            return True

        dependencies = task.get("dependencies", [])
        if not dependencies:
            return True

        completed_ids = {t["id"] for t in tasks if t.get("status") == "complete"}
        return all(dep in completed_ids for dep in dependencies)

    def update_task_status(
        self,
        task_id: str,
        status: str,
        **kwargs: Any,
    ) -> bool:
        """Update task status.

        Args:
            task_id: ID of the task to update
            status: New status (pending, in_progress, complete, blocked)
            **kwargs: Additional fields to update

        Returns:
            True if update successful

        """
        if self._use_tasks and self._task_update:
            return self._task_update(task_id, status=status, **kwargs)
        else:
            if not self.fallback_state_file.exists():
                return False

            state = json.loads(self.fallback_state_file.read_text())
            if task_id not in state.get("tasks", {}):
                return False

            state["tasks"][task_id]["status"] = status
            state["tasks"][task_id].update(kwargs)

            if status == "complete":
                state["metrics"]["tasks_complete"] = len(
                    [
                        t
                        for t in state["tasks"].values()
                        if t.get("status") == "complete"
                    ]
                )

            self.fallback_state_file.write_text(json.dumps(state, indent=2))
            return True
