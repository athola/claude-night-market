"""Tasks Manager for Claude Code Tasks integration (attune plugin).

Plugin-specific configuration for attune's project execution workflows.
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
    from abstract.tasks_manager_base import (  # noqa: E402
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
except ImportError as e:
    raise ImportError(
        "attune requires the 'abstract' plugin to be installed. "
        "Install it from: plugins/abstract"
    ) from e

# Plugin-specific constants (preserved for backward compatibility)
PLUGIN_NAME = "attune"
TASK_PREFIX = "ATTUNE"
DEFAULT_STATE_DIR = ".attune"
DEFAULT_STATE_FILE = "execution-state.json"
ENV_VAR_PREFIX = "CLAUDE_CODE_TASK_LIST_ID"

LARGE_SCOPE_TOKEN_THRESHOLD = int(
    os.environ.get("ATTUNE_LARGE_SCOPE_TOKEN_THRESHOLD", "5000")
)
LARGE_SCOPE_WORD_THRESHOLD = int(
    os.environ.get("ATTUNE_LARGE_SCOPE_WORD_THRESHOLD", "30")
)

# Cross-cutting concern keywords for attune (project execution focus)
CROSS_CUTTING_KEYWORDS = [
    # General development patterns
    "logging throughout",
    "add logging",
    "error handling throughout",
    "validation throughout",
    "throughout the codebase",
    "across the codebase",
    "across all",
    "everywhere in",
    # Architecture-level concerns
    "authentication system",
    "authorization layer",
    "caching layer",
    "monitoring system",
    "tracing throughout",
    "security audit",
    # Project-wide refactoring
    "refactor all",
    "migrate all",
    "update all dependencies",
    "rename throughout",
]

ATTUNE_CONFIG = TasksManagerConfig(
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
    "ATTUNE_CONFIG",
    "CROSS_CUTTING_KEYWORDS",
    "ResumeState",
    "TasksManager",
    "TasksManagerConfig",
    "TaskState",
    "detect_ambiguity",
    "get_claude_code_version",
    "is_tasks_available",
]
