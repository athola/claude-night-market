"""Tasks Manager for Claude Code Tasks integration (spec-kit plugin).

Plugin-specific configuration for spec-kit's specification-driven workflows.
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
        "spec-kit requires the 'abstract' plugin to be installed. "
        "Install it from: plugins/abstract"
    ) from e

# Plugin-specific constants (preserved for backward compatibility)
PLUGIN_NAME = "spec-kit"
TASK_PREFIX = "SPECKIT"
DEFAULT_STATE_DIR = ".spec-kit"
DEFAULT_STATE_FILE = "implementation-state.json"
ENV_VAR_PREFIX = "CLAUDE_CODE_TASK_LIST_ID"

LARGE_SCOPE_TOKEN_THRESHOLD = int(
    os.environ.get("SPECKIT_LARGE_SCOPE_TOKEN_THRESHOLD", "5000")
)
LARGE_SCOPE_WORD_THRESHOLD = int(
    os.environ.get("SPECKIT_LARGE_SCOPE_WORD_THRESHOLD", "30")
)

# Cross-cutting concern keywords for spec-kit (specification-driven focus)
CROSS_CUTTING_KEYWORDS = [
    # Specification patterns
    "implement entire spec",
    "all requirements",
    "complete specification",
    "full implementation",
    # Phase-based patterns
    "all phases",
    "entire workflow",
    "end-to-end implementation",
    # Multi-component patterns
    "all modules",
    "all components",
    "entire system",
    "complete feature",
    # General scope indicators
    "throughout the codebase",
    "across the codebase",
    "across all",
    "everywhere in",
]

SPECKIT_CONFIG = TasksManagerConfig(
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
    "SPECKIT_CONFIG",
    "TasksManager",
    "TasksManagerConfig",
    "TaskState",
    "detect_ambiguity",
    "get_claude_code_version",
    "is_tasks_available",
]
