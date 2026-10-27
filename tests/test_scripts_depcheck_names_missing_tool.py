"""Every script's depcheck must stop it and say which tool is missing.

The shell rules require a depcheck() for non-POSIX tools, and most
scripts on this branch gained one. Line tracing showed the missing-tool
branch ran under no test, so a depcheck that returned 0 regardless would
have passed review. This runs each script with its first required tool
removed from PATH.
"""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
_DEPS = re.compile(r'REQUIRED_DEPENDENCIES="([^"]+)"')

#: Scripts that reach depcheck only after a guard that is correct to hit
#: first. Each reason must still hold, or the entry should go.
SKIPPED = {
    "plugins/egregore/scripts/watchdog.sh": (
        "a timer with no manifest exits 0 before checking tools, by design"
    ),
    "plugins/leyline/scripts/interactive_auth.sh": (
        "refuses bash below 4 first, and main never calls depcheck"
    ),
}

#: Scripts whose depcheck reports the platform rather than the tool.
PLATFORM_MESSAGE = {
    "plugins/egregore/scripts/install_launchd.sh": "macOS only",
    "plugins/egregore/scripts/install_systemd.sh": "systemd host",
}


def _scripts() -> list[str]:
    tracked = subprocess.run(
        ["git", "ls-files", "*.sh"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    return sorted(
        rel
        for rel in tracked
        if "depcheck" in (text := (REPO_ROOT / rel).read_text(errors="replace"))
        and _DEPS.search(text)
    )


def _path_without(tool: str, root: Path) -> str:
    """A PATH directory linking every executable on PATH except ``tool``."""
    farm = root / "bin"
    farm.mkdir()
    for directory in os.environ.get("PATH", "").split(os.pathsep):
        if not os.path.isdir(directory):
            continue
        for name in os.listdir(directory):
            source = Path(directory) / name
            link = farm / name
            # os.path.isfile, not Path.is_file: an unreadable entry such
            # as /usr/sbin/weakpass_edit makes the latter raise on 3.12.
            if name == tool or link.exists() or not os.path.isfile(source):
                continue
            if os.access(source, os.X_OK):
                link.symlink_to(source)
    return str(farm)


def test_every_skip_names_a_script_that_still_has_a_depcheck() -> None:
    """A stale skip would hide a script that later gains the check."""
    assert set(SKIPPED) <= set(_scripts())


@pytest.mark.parametrize(
    "rel", [s for s in _scripts() if s not in SKIPPED], ids=lambda s: s
)
def test_a_missing_required_tool_stops_the_script_by_name(
    rel: str, tmp_path: Path
) -> None:
    """GIVEN a script whose first required tool is absent from PATH
    WHEN it runs with no arguments
    THEN it exits nonzero
    AND its output names the missing tool, or the platform it needs
    """
    tool = _DEPS.search((REPO_ROOT / rel).read_text()).group(1).split()[0]
    env = {**os.environ, "PATH": _path_without(tool, tmp_path)}

    run = subprocess.run(
        ["/bin/bash", rel],
        cwd=REPO_ROOT,
        env=env,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )

    output = run.stdout + run.stderr
    assert run.returncode != 0, output
    assert PLATFORM_MESSAGE.get(rel, tool) in output, output
