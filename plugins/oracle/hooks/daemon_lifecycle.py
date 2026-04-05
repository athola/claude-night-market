#!/usr/bin/env python3
"""Oracle daemon lifecycle hook.

Handles SessionStart and Stop events to start and stop the ONNX
inference daemon.  The daemon only runs when the opt-in sentinel
file ``${CLAUDE_PLUGIN_DATA}/.oracle-enabled`` is present, making
activation explicit rather than automatic.

Designed for the 5-second hook timeout budget: the start path
checks the sentinel and, if set, launches the daemon as a detached
subprocess.  The stop path sends SIGTERM if the daemon is running.
"""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PLUGIN_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from oracle.provision import (  # noqa: E402 - sys.path must be extended before this import
    get_oracle_data_dir,
    get_python_path,
    get_venv_path,
    is_provisioned,
)


def _get_sentinel() -> Path:
    return get_oracle_data_dir() / ".oracle-enabled"


def _get_pid_file() -> Path:
    return get_oracle_data_dir() / "daemon.pid"


def _get_port_file() -> Path:
    return get_oracle_data_dir() / "daemon.port"


def _get_models_dir() -> Path:
    return PLUGIN_ROOT / "models"


def _get_event() -> str:
    try:
        payload = json.load(sys.stdin)
        return str(payload.get("hook_event_name", ""))
    except (json.JSONDecodeError, OSError):
        return ""


def _is_daemon_running(pid_file: Path) -> bool:
    """Check if the daemon process is still alive."""
    try:
        pid = int(pid_file.read_text().strip())
        os.kill(pid, 0)
        return True
    except (OSError, ValueError):
        return False


def _start_daemon() -> None:
    """Launch the daemon as a detached subprocess."""
    venv = get_venv_path()
    python = str(get_python_path(venv))
    daemon_script = str(PLUGIN_ROOT / "src" / "oracle" / "daemon.py")
    data_dir = get_oracle_data_dir()
    port_file = _get_port_file()
    pid_file = _get_pid_file()
    models_dir = _get_models_dir()

    if _is_daemon_running(pid_file):
        return

    # Clean stale files from a previous run.
    for f in (port_file, pid_file):
        if f.exists():
            f.unlink()

    log_fh = open(str(data_dir / "daemon.log"), "a")  # noqa: SIM115 - fd passed to Popen, must outlive this scope
    try:
        proc = subprocess.Popen(
            [
                python,
                daemon_script,
                "--host",
                "127.0.0.1",
                "--port",
                "0",
                "--models-dir",
                str(models_dir),
                "--port-file",
                str(port_file),
            ],
            stdout=subprocess.DEVNULL,
            stderr=log_fh,
            start_new_session=True,
        )
    except OSError:
        log_fh.close()
        return

    pid_file.write_text(str(proc.pid))


def _stop_daemon() -> None:
    """Send SIGTERM to the daemon if it is running."""
    pid_file = _get_pid_file()
    port_file = _get_port_file()

    try:
        pid = int(pid_file.read_text().strip())
        os.kill(pid, signal.SIGTERM)
    except (OSError, ValueError):
        pass

    for f in (pid_file, port_file):
        try:
            f.unlink()
        except OSError:
            pass


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
        _start_daemon()

    elif event == "Stop":
        _stop_daemon()


if __name__ == "__main__":
    main()
