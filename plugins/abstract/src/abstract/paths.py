"""Resolve the directories and files this plugin reads and writes.

These helpers lived in ``utils``, which imports PyYAML and the
frontmatter processor to do its own work. That made pure path
lookups unreachable from a hook: hooks run under whatever ``python3``
the operator's PATH resolves, which carries the standard library and
nothing else, so ``pre_skill_execution`` and ``skill_execution_logger``
raised ``ModuleNotFoundError`` before reading their payload.

Nothing here imports outside the standard library, and nothing should.
``utils`` re-exports every one, so each existing caller is unchanged.
``tests/test_hooks_import_without_project_deps.py`` at the repository
root holds the invariant.
"""

from __future__ import annotations

import os
from pathlib import Path

__all__ = [
    "get_config_dir",
    "get_learnings_path",
    "get_log_directory",
    "get_observability_dir",
]


def _claude_home() -> Path:
    """Return the Claude Code home, honoring CLAUDE_HOME (D-04)."""
    return Path(os.environ.get("CLAUDE_HOME", Path.home() / ".claude"))


def get_log_directory(*, create: bool = False) -> Path:
    """Get the skill execution log directory.

    Respects CLAUDE_HOME env var for non-standard installations.

    Args:
        create: If True, create the directory if it doesn't exist.

    Returns:
        Path to ~/.claude/skills/logs/ (or $CLAUDE_HOME/skills/logs/).

    """
    log_base = _claude_home() / "skills" / "logs"
    if create:
        log_base.mkdir(parents=True, exist_ok=True)
    return log_base


def get_config_dir(*, create: bool = False) -> Path:
    """Get the discussions config directory.

    Args:
        create: If True, create the directory if it doesn't exist.

    Returns:
        Path to ~/.claude/skills/discussions/.

    """
    config_dir = Path.home() / ".claude" / "skills" / "discussions"
    if create:
        config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_observability_dir(*, create: bool = False) -> Path:
    """Get the skill observability state directory.

    Respects CLAUDE_HOME like the other dir helpers (D-04).

    Args:
        create: If True, create the directory if it doesn't exist.

    Returns:
        Path to ~/.claude/skills/observability/ (or
        ``$CLAUDE_HOME/skills/observability/``).

    """
    state_dir = _claude_home() / "skills" / "observability"
    if create:
        state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir


def get_learnings_path() -> Path:
    """Get the path to the LEARNINGS.md file.

    Respects CLAUDE_HOME the same way :func:`get_log_directory` does, so
    a non-standard installation keeps its logs and its learnings under
    one root.

    Returns:
        Path to ~/.claude/skills/LEARNINGS.md (or under $CLAUDE_HOME).

    """
    return _claude_home() / "skills" / "LEARNINGS.md"
