"""Shared directory helpers for hooks.

Thin facade over ``abstract.utils.{get_log_directory,
get_config_dir, get_observability_dir}`` so PreToolUse and
PostToolUse hooks share one definition (D-04).

Hooks are invoked via ``${CLAUDE_PLUGIN_ROOT}/hooks/...``
without any guaranteed sys.path entry, so this module
inserts ``plugins/abstract/src`` once and delegates.
"""

from __future__ import annotations

import sys
from pathlib import Path

_src = Path(__file__).resolve().parent.parent.parent / "src"
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

from abstract.utils import (  # noqa: E402 - import after sys.path setup
    get_config_dir as _get_config_dir,
)
from abstract.utils import (
    get_log_directory as _get_log_directory,
)
from abstract.utils import (
    get_observability_dir as _get_observability_dir,
)


def get_observability_dir() -> Path:
    """Return ~/.claude/skills/observability/ (created)."""
    return _get_observability_dir(create=True)


def get_log_directory() -> Path:
    """Return ~/.claude/skills/logs/ (created)."""
    return _get_log_directory(create=True)


def get_config_dir() -> Path:
    """Return ~/.claude/skills/discussions/ (created)."""
    return _get_config_dir(create=True)
