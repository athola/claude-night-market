"""Resolve the active Claude session JSONL file.

Used by multiple conserve hooks (`tool_output_summarizer`,
`pre_compact_preserve`); previously inlined in each (D-05).
"""

from __future__ import annotations

import os
import re
from pathlib import Path

__all__ = ["project_dir_name", "resolve_session_file"]


def project_dir_name(cwd: Path) -> str:
    """Return the ``~/.claude/projects`` directory name Claude Code uses.

    Claude Code maps every non-alphanumeric character to "-", not just
    path separators: "/Users/a.b/my_repo" is "-Users-a-b-my-repo".
    """
    name = re.sub(r"[^A-Za-z0-9]", "-", str(cwd))
    return name if name.startswith("-") else "-" + name


def resolve_session_file() -> Path | None:
    """Find the current session's JSONL file."""
    claude_dir = Path(os.environ.get("CLAUDE_HOME", str(Path.home() / ".claude")))
    claude_projects = claude_dir / "projects"

    if not claude_projects.exists():
        return None

    # Try to find project directory from CWD
    cwd = Path.cwd()
    project_dir = claude_projects / project_dir_name(cwd)
    if not project_dir.exists():
        # Fallback: list all project dirs and use most recent
        project_dirs = sorted(
            claude_projects.iterdir(),
            key=lambda p: p.stat().st_mtime if p.is_dir() else 0,
            reverse=True,
        )
        if project_dirs:
            project_dir = project_dirs[0]
        else:
            return None

    # Find the current session file
    session_id = os.environ.get("CLAUDE_SESSION_ID", "")
    jsonl_files = list(project_dir.glob("*.jsonl"))

    if not jsonl_files:
        return None

    if session_id:
        for f in jsonl_files:
            if f.stem == session_id:
                return f

    # Fallback to most recent
    return max(jsonl_files, key=lambda f: f.stat().st_mtime)
