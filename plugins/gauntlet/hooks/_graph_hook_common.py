"""Launch and report helpers the two graph hooks share.

Both hooks run on the first python3 on PATH, so this module imports the
standard library only.
"""

from __future__ import annotations

import shlex
import subprocess
from pathlib import Path
from typing import Any

PLUGIN_ROOT = Path(__file__).resolve().parent.parent


def context(event_name: str, message: str) -> dict[str, Any]:
    """Build hook output that adds ``message`` to the session context."""
    return {
        "hookSpecificOutput": {
            "hookEventName": event_name,
            "additionalContext": message,
        }
    }


def graph_build_argv(uv: str, root: Path, *extra: str) -> list[str]:
    """Run graph_build.py in the plugin's environment, which has tree-sitter."""
    return [
        uv,
        "run",
        "--project",
        str(PLUGIN_ROOT),
        "python",
        str(PLUGIN_ROOT / "scripts" / "graph_build.py"),
        str(root),
        *extra,
    ]


def status_command(build: list[str], status: Path) -> str:
    """Shell line that runs ``build`` and writes its exit code to ``status``.

    The build is detached, so its exit code is otherwise lost and a failure
    reads the same as a build still running.
    """
    return f"{shlex.join(build)}; echo $? > {shlex.quote(str(status))}"


def last_run_failed(status: Path) -> bool:
    """Whether the last detached build wrote a nonzero exit code."""
    try:
        return status.read_text(encoding="ascii").strip() != "0"
    except FileNotFoundError:
        return False


def launch(argv: list[str], root: Path, log_path: Path) -> None:
    """Start ``argv`` detached, so it outlives the hook's timeout."""
    with open(log_path, "ab") as log:
        subprocess.Popen(
            argv,
            cwd=str(root),
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
