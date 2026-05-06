"""Resolve the active Claude session JSONL file.

Used by multiple conserve hooks (`tool_output_summarizer`,
`pre_compact_preserve`); previously inlined in each (D-05).
"""

from __future__ import annotations

import os
from pathlib import Path

__all__ = ["resolve_session_file"]


def resolve_session_file() -> Path | None:
    """Find the current session's JSONL file."""
    claude_dir = Path(os.environ.get("CLAUDE_HOME", str(Path.home() / ".claude")))
    claude_projects = claude_dir / "projects"

    if not claude_projects.exists():
        return None

    # Try to find project directory from CWD
    cwd = Path.cwd()
    project_dir_name = str(cwd).replace(os.sep, "-")
    if not project_dir_name.startswith("-"):
        project_dir_name = "-" + project_dir_name

    project_dir = claude_projects / project_dir_name
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
