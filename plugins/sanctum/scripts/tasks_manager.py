"""Tasks Manager for Claude Code Tasks integration (sanctum plugin).

Plugin-specific configuration for sanctum's git and PR fix workflows.
Delegates all shared logic to abstract.tasks_manager_base.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Add abstract src to path for cross-plugin import (ADR-0001: guarded)
_ABSTRACT_SRC = Path(__file__).resolve().parents[2] / "abstract" / "src"
if str(_ABSTRACT_SRC) not in sys.path:
    sys.path.insert(0, str(_ABSTRACT_SRC))

try:
    from abstract.tasks_manager_base import (
        AmbiguityResult,
        AmbiguityType,
        ResumeState,
        TasksManager,
        TasksManagerConfig,
        TaskState,
        detect_ambiguity,
        get_claude_code_version,
        is_tasks_available,
    )
except ImportError:
    import sys

    sys.stderr.write(
        "Warning: abstract plugin not found. Task management features disabled.\n"
    )

    # Provide a stub that reports unavailability
    class TasksManagerBase:
        """Stub base when abstract plugin is unavailable."""

        def __init__(self, *args: object, **kwargs: object) -> None:
            """Initialize stub."""
            raise RuntimeError("Task management requires the abstract plugin")

    # Stubs so downstream references don't break at import time
    class AmbiguityResult:
        """Stub for AmbiguityResult."""

    class AmbiguityType:
        """Stub for AmbiguityType."""

    class ResumeState:
        """Stub for ResumeState."""

    TasksManager = TasksManagerBase

    class TasksManagerConfig:
        """Stub for TasksManagerConfig."""

        def __init__(self, *args: object, **kwargs: object) -> None:
            """Initialize stub."""

    class TaskState:
        """Stub for TaskState."""

    def detect_ambiguity(*args: object, **kwargs: object) -> None:
        """Stub for detect_ambiguity."""
        return None

    def get_claude_code_version(*args: object, **kwargs: object) -> str:
        """Stub for get_claude_code_version."""
        return "unknown"

    def is_tasks_available(*args: object, **kwargs: object) -> bool:
        """Stub for is_tasks_available."""
        return False


# Plugin-specific constants (preserved for backward compatibility)
PLUGIN_NAME = "sanctum"
TASK_PREFIX = "SANCTUM"
DEFAULT_STATE_DIR = ".sanctum"
DEFAULT_STATE_FILE = "pr-workflow-state.json"
ENV_VAR_PREFIX = "CLAUDE_CODE_TASK_LIST_ID"

LARGE_SCOPE_TOKEN_THRESHOLD = int(
    os.environ.get("SANCTUM_LARGE_SCOPE_TOKEN_THRESHOLD", "5000")
)
LARGE_SCOPE_WORD_THRESHOLD = int(
    os.environ.get("SANCTUM_LARGE_SCOPE_WORD_THRESHOLD", "30")
)

# Cross-cutting concern keywords for sanctum (git/PR workflow focus)
CROSS_CUTTING_KEYWORDS = [
    # PR review patterns
    "fix all review comments",
    "address all feedback",
    "update all tests",
    "fix all linting",
    # Git workflow patterns
    "rebase all commits",
    "squash all",
    "update all branches",
    "merge all",
    # Documentation patterns
    "update all docs",
    "fix all docstrings",
    # General scope indicators
    "throughout the codebase",
    "across the codebase",
    "across all files",
    "everywhere in",
]

SANCTUM_CONFIG = TasksManagerConfig(
    plugin_name=PLUGIN_NAME,
    task_prefix=TASK_PREFIX,
    default_state_dir=DEFAULT_STATE_DIR,
    default_state_file=DEFAULT_STATE_FILE,
    env_var_prefix=ENV_VAR_PREFIX,
    large_scope_token_threshold=LARGE_SCOPE_TOKEN_THRESHOLD,
    large_scope_word_threshold=LARGE_SCOPE_WORD_THRESHOLD,
    cross_cutting_keywords=CROSS_CUTTING_KEYWORDS,
)

__all__ = [
    "AmbiguityResult",
    "AmbiguityType",
    "CROSS_CUTTING_KEYWORDS",
    "ResumeState",
    "SANCTUM_CONFIG",
    "TasksManager",
    "TasksManagerConfig",
    "TaskState",
    "detect_ambiguity",
    "get_claude_code_version",
    "is_tasks_available",
]
