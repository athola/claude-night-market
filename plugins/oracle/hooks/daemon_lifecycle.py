#!/usr/bin/env python3
"""Oracle daemon lifecycle hook.

Handles SessionStart and SessionEnd events to start and stop the
ONNX inference daemon. Stop fires after every assistant turn, so it
would kill the daemon the session started after its first reply.
The daemon only runs when the opt-in sentinel file
``${CLAUDE_PLUGIN_DATA}/.oracle-enabled`` is present, making
activation explicit rather than automatic.

Designed for the 5-second hook timeout budget: the start path
checks the sentinel and, if set, launches the daemon as a detached
subprocess.  The stop path sends SIGTERM if the daemon is running.
"""

from __future__ import annotations

import json
import logging
import os
import signal
import subprocess
import sys
import time
from contextlib import AbstractContextManager
from pathlib import Path

from _vendored_leyline_atomic_file import file_lock

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


def _read_payload() -> dict:
    try:
        payload = json.load(sys.stdin)
    except (ValueError, OSError):
        # ValueError covers JSONDecodeError and UnicodeDecodeError.
        return {}
    return payload if isinstance(payload, dict) else {}


# What the daemon's command line must contain for a PID to count as ours.
# The full launched path, because a bare "daemon.py" also matches pytest
# running test_daemon.py or an editor with some other daemon.py open.
_DAEMON_SCRIPT = str(PLUGIN_ROOT / "src" / "oracle" / "daemon.py")
_PS_TIMEOUT_SECONDS = 2


def _pid_is_daemon(pid: int) -> bool:
    """Return True only if ``pid`` is alive and running the daemon script.

    PIDs are reused. After a crash, a reboot, or any exit that skipped the
    pid-file cleanup, the number in daemon.pid can belong to an unrelated
    process of the same user, and ``os.kill(pid, 0)`` says only that
    something is there. The signal-0 probe is kept as the cheap first
    step. The command line is what keeps the SessionEnd hook from killing that
    something.

    ``-ww`` is required on Linux: procps cuts the command column to 80
    characters when stdout is not a terminal, and the venv interpreter
    path alone can push the script path past the cut.
    """
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    try:
        listing = subprocess.run(
            ["ps", "-ww", "-o", "command=", "-p", str(pid)],
            capture_output=True,
            text=True,
            timeout=_PS_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return listing.returncode == 0 and _DAEMON_SCRIPT in listing.stdout


def _is_daemon_running(pid_file: Path) -> bool:
    """Check if the daemon process is still alive."""
    try:
        pid = int(pid_file.read_text().strip())
    except (OSError, ValueError):
        return False
    return _pid_is_daemon(pid)


def _start_daemon() -> None:
    """Launch the daemon as a detached subprocess."""
    venv = get_venv_path()
    python = str(get_python_path(venv))
    daemon_script = _DAEMON_SCRIPT
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

    # The daemon refuses to start without its models, so launching it
    # would write a pid for a process that is already gone.
    if not models_dir.is_dir():
        # No models ship, so this repeats every session: write it once.
        # Bytes throughout: a non-ASCII path is longer in bytes than in
        # characters, and a short seek never finds the line it wrote.
        line = f"oracle: not starting, models directory missing: {models_dir}\n"
        encoded = line.encode()
        log_path = data_dir / "daemon.log"
        tail = b""
        if log_path.is_file():
            with open(log_path, "rb") as log:
                log.seek(max(0, log_path.stat().st_size - len(encoded) - 1))
                tail = log.read()
        if not tail.endswith(encoded):
            with open(log_path, "ab") as log:
                log.write(encoded)
        return

    log_fh = open(str(data_dir / "daemon.log"), "a")  # noqa: SIM115 - fd duped into subprocess, closed on the parent side after Popen returns
    try:
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
            return
    finally:
        # Popen dup'd the fd into the subprocess. Close the parent-side
        # handle so it doesn't leak.
        log_fh.close()

    pid_file.write_text(str(proc.pid))


def _stop_daemon() -> None:
    """Send SIGTERM to the daemon if it is running."""
    pid_file = _get_pid_file()
    port_file = _get_port_file()

    try:
        pid = int(pid_file.read_text().strip())
    except ValueError:
        logging.getLogger(__name__).debug(
            "PID file corrupt, skipping SIGTERM: %s", pid_file
        )
        pid = None
    except OSError:
        pid = None

    if pid is not None and _pid_is_daemon(pid):
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError:
            pass
    elif pid is not None:
        logging.getLogger(__name__).debug(
            "PID %s is not the oracle daemon; leaving it alone", pid
        )

    for f in (pid_file, port_file):
        try:
            f.unlink()
        except OSError:
            pass


#: A marker holds the pid of its session's process, and counts while that
#: process lives. A marker with no readable pid counts for this long, as
#: does every marker on Windows, where signal 0 is CTRL_C_EVENT and
#: ``os.kill(pid, 0)`` is not a liveness probe.
_SESSION_MARKER_TTL_SECONDS = 24 * 60 * 60

# Claude Code may run the hook command through a shell that exits with the
# hook. Its pid would read as a crashed session at once.
_SHELLS = frozenset({"sh", "bash", "zsh", "dash", "ksh", "fish"})
_MAX_SHELL_HOPS = 4


def _sessions_dir() -> Path:
    return get_oracle_data_dir() / "sessions"


def _marker(session_id: str) -> Path | None:
    """Return the session's marker path, or None for an unusable id."""
    safe = "".join(c for c in session_id if c.isalnum() or c in "-_")[:128]
    return _sessions_dir() / safe if safe else None


def _session_pid() -> int:
    """Return the pid of the first ancestor of this hook that is not a shell."""
    pid = os.getppid()
    for _ in range(_MAX_SHELL_HOPS):
        try:
            listing = subprocess.run(
                ["ps", "-o", "ppid=", "-o", "comm=", "-p", str(pid)],
                capture_output=True,
                text=True,
                timeout=_PS_TIMEOUT_SECONDS,
                check=False,
            )
        except (OSError, subprocess.SubprocessError):
            return pid
        fields = listing.stdout.split(None, 1)
        if len(fields) != 2 or not fields[0].isdigit():
            return pid
        command = fields[1].strip().rsplit("/", 1)[-1].lstrip("-")
        if command not in _SHELLS:
            return pid
        pid = int(fields[0])
    return pid


def _register_session(session_id: str) -> None:
    marker = _marker(session_id)
    if marker is not None:
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text(str(_session_pid()))


def _marker_is_live(marker: Path, cutoff: float) -> bool:
    """Whether the marker's session process lives, or, with no pid, is fresh."""
    try:
        text = marker.read_bytes().strip()
    except FileNotFoundError:
        raise
    except OSError:
        text = b""  # unreadable: judged by its age below
    if text.isdigit() and os.name != "nt":
        try:
            os.kill(int(text), 0)
        except ProcessLookupError:
            return False
        except PermissionError:
            return True  # alive, owned by another user
        return True
    return marker.stat().st_mtime > cutoff


def _other_sessions_live(session_id: str) -> bool:
    """Drop this session's marker; report whether a live one remains.

    One daemon serves every session, so a session ending must not stop it
    while another session still uses it.
    """
    own = _marker(session_id)
    if own is not None:
        own.unlink(missing_ok=True)
    directory = _sessions_dir()
    if not directory.is_dir():
        return False
    cutoff = time.time() - _SESSION_MARKER_TTL_SECONDS
    for marker in directory.iterdir():
        try:
            if _marker_is_live(marker, cutoff):
                return True
        except FileNotFoundError:
            continue  # another session ended between iterdir and stat
    return False


def _start_lock() -> AbstractContextManager[None]:
    """Lock ``daemon.start.lock``, the file every oracle hook version uses."""
    return file_lock(get_oracle_data_dir() / "daemon.start")


def main() -> None:
    """Dispatch on SessionStart / SessionEnd events."""
    payload = _read_payload()
    event = str(payload.get("hook_event_name", ""))
    sentinel = _get_sentinel()
    venv = get_venv_path()

    if event == "SessionStart":
        if not sentinel.exists():
            return
        if not is_provisioned(venv):
            return
        _register_session(str(payload.get("session_id", "")))
        # Held across the running check and the spawn inside _start_daemon,
        # so two sessions starting together launch one daemon, not two.
        with _start_lock():
            _start_daemon()

    elif event == "SessionEnd":
        # The same lock: a stop between another session's running check and
        # its return would kill the daemon that session just confirmed.
        with _start_lock():
            live = _other_sessions_live(str(payload.get("session_id", "")))
            # /clear ends this id and starts another in the same process; the
            # stop runs async and could kill the daemon the next session keeps.
            if not live and payload.get("reason") != "clear":
                _stop_daemon()


if __name__ == "__main__":
    main()
