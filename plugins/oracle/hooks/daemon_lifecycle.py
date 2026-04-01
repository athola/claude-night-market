#!/usr/bin/env python3
"""Oracle daemon lifecycle hook.

Handles SessionStart and Stop events to start and stop the ONNX
inference daemon.  The daemon only runs when the opt-in sentinel
file ``${CLAUDE_PLUGIN_DATA}/.oracle-enabled`` is present, making
activation explicit rather than automatic.

Designed for the 5-second hook timeout budget: the start path
checks the sentinel and, if set, launches the daemon as a detached
subprocess.  The stop path sends a shutdown signal if the daemon
is running.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PLUGIN_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from oracle.provision import (  # noqa: E402 - sys.path must be extended before this import
    get_oracle_data_dir,
    get_venv_path,
    is_provisioned,
)


def _get_sentinel() -> Path:
    return get_oracle_data_dir() / ".oracle-enabled"


def _get_event() -> str:
    try:
        payload = json.load(sys.stdin)
        return str(payload.get("hook_event_name", ""))
    except (json.JSONDecodeError, OSError):
        return ""


def main() -> None:
    """Dispatch on SessionStart / Stop events."""
    event = _get_event()
    sentinel = _get_sentinel()
    venv = get_venv_path()

    if event == "SessionStart":
        if not sentinel.exists():
            return
        if not is_provisioned(venv):
            return
        # Daemon startup is deferred to a future task.
        # The hook exits cleanly so Claude Code is not blocked.

    elif event == "Stop":
        # Daemon shutdown is deferred to a future task.
        pass


if __name__ == "__main__":
    main()
