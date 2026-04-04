#!/usr/bin/env python3
"""PostToolUse hook: auto-update the code graph after git commits.

Runs an incremental graph update when a git commit succeeds.
Opt-in via .gauntlet/config.json: {"auto_update": true}
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any

_src_path = Path(__file__).parent.parent / "src"
if str(_src_path) not in sys.path:
    sys.path.insert(0, str(_src_path))


def _get_gauntlet_dir() -> Path | None:
    cwd = Path(os.getcwd())
    candidate = cwd / ".gauntlet"
    if candidate.is_dir():
        return candidate
    return None


def _is_auto_update_enabled(gauntlet_dir: Path) -> bool:
    """Check if auto_update is enabled in config."""
    for name in ("config.json", "config.yaml"):
        config_path = gauntlet_dir / name
        if config_path.exists():
            try:
                if name.endswith(".json"):
                    data = json.loads(config_path.read_text())
                else:
                    try:
                        from yaml import (
                            safe_load,
                        )

                        data = safe_load(config_path.read_text())
                    except ImportError:
                        continue
                return bool(data.get("auto_update", False))
            except (json.JSONDecodeError, OSError, TypeError):
                continue
    return False


def main(hook_input: dict[str, Any]) -> dict[str, Any] | None:
    """Process a PostToolUse hook event after git commit."""
    tool_name = hook_input.get("tool_name", "")
    tool_input = hook_input.get("tool_input", {})

    if tool_name != "Bash":
        return None

    command = tool_input.get("command", "")
    if not command.startswith("git commit"):
        return None

    # Check if the commit succeeded
    tool_result = hook_input.get("tool_result", {})
    stdout = tool_result.get("stdout", "")
    if "nothing to commit" in stdout or tool_result.get("exitCode", 1) != 0:
        return None

    gauntlet_dir = _get_gauntlet_dir()
    if gauntlet_dir is None:
        return None

    if not _is_auto_update_enabled(gauntlet_dir):
        return None

    db_path = gauntlet_dir / "graph.db"
    if not db_path.exists():
        return None

    try:
        from gauntlet.graph import (
            GraphStore,
        )
        from gauntlet.incremental import (
            incremental_update,
        )

        start = time.monotonic()
        graph = GraphStore(str(db_path))
        report = incremental_update(str(Path(os.getcwd())), graph, base_ref="HEAD~1")
        graph.close()
        duration = round(time.monotonic() - start, 2)

        files = report.get("files_parsed", 0)
        nodes = report.get("nodes_created", 0)
        msg = f"Graph updated: {files} files, {nodes} nodes in {duration}s"
        return {"additionalContext": msg}
    except Exception:
        return None


if __name__ == "__main__":
    try:
        hook_input = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, OSError):
        hook_input = {}

    output = main(hook_input)
    if output is not None:
        print(json.dumps(output))
