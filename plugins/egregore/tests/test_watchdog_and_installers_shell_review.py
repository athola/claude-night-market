"""Watchdog and installer behavior on corrupt state and awkward paths.

A truncated budget.json
killed every watchdog tick before it logged anything, and a truncated
manifest was logged as "No active work items". The launchd plist broke
on a path containing "&", re-installing kept the old job loaded, and the
systemd unit split a path containing a space.
"""

from __future__ import annotations

import json
import os
import plistlib
import shutil
import subprocess
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"

needs_jq = pytest.mark.skipif(shutil.which("jq") is None, reason="needs jq")


def _tick(tmp_path: Path, manifest: str, budget: str | None = None):
    egregore_dir = tmp_path / ".egregore"
    egregore_dir.mkdir()
    (egregore_dir / "manifest.json").write_text(manifest)
    if budget is not None:
        (egregore_dir / "budget.json").write_text(budget)
    (egregore_dir / "pid").write_text(str(os.getpid()))
    result = subprocess.run(
        ["/bin/bash", str(SCRIPTS / "watchdog.sh")],
        env={**os.environ, "EGREGORE_DIR": str(egregore_dir)},
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    log = egregore_dir / "watchdog.log"
    return result, log.read_text() if log.exists() else ""


@needs_jq
def test_a_corrupt_manifest_is_an_error_not_completion(tmp_path: Path) -> None:
    result, log = _tick(tmp_path, '{"work_items": [')
    assert result.returncode != 0
    assert "No active work items" not in log
    assert "manifest" in log


@needs_jq
def test_a_corrupt_budget_is_logged(tmp_path: Path) -> None:
    active = json.dumps({"work_items": [{"status": "active"}]})
    result, log = _tick(tmp_path, active, budget='{"cooldown_until": ')
    assert result.returncode != 0
    assert "budget.json" in log


def _shims(tmp_path: Path, *names: str) -> tuple[Path, Path]:
    """PATH shims that record their argv to calls.log and succeed."""
    shim_dir = tmp_path / "shims"
    shim_dir.mkdir()
    calls = tmp_path / "calls.log"
    for name in names:
        shim = shim_dir / name
        shim.write_text(f'#!/bin/sh\nprintf "%s\\n" "{name} $*" >> "{calls}"\n')
        shim.chmod(0o755)
    return shim_dir, calls


def _install(
    tmp_path: Path, script: str, shim_dir: Path, workdir: Path, shell: str = "/bin/bash"
):
    home = tmp_path / "home"
    (home / "Library" / "LaunchAgents").mkdir(parents=True)
    return subprocess.run(
        [shell, str(SCRIPTS / script), "300", str(workdir)],
        env={
            **os.environ,
            "HOME": str(home),
            "PATH": f"{shim_dir}:{os.environ['PATH']}",
        },
        capture_output=True,
        text=True,
        check=False,
    ), home


SHELLS = sorted({"/bin/bash", shutil.which("bash") or "/bin/bash"})


@pytest.mark.parametrize("shell", SHELLS)
def test_launchd_plist_parses_with_an_ampersand_path(
    tmp_path: Path, shell: str
) -> None:
    """Bash 5.2 and 3.2 treat & and quotes in a replacement differently."""
    shim_dir, _calls = _shims(tmp_path, "launchctl")
    workdir = tmp_path / "R&D <repo>"
    workdir.mkdir()
    result, home = _install(tmp_path, "install_launchd.sh", shim_dir, workdir, shell)
    assert result.returncode == 0, result.stderr
    plist = home / "Library" / "LaunchAgents" / "com.egregore.watchdog.plist"
    parsed = plistlib.loads(plist.read_bytes())
    assert parsed["WorkingDirectory"] == str(workdir)


def test_launchd_reinstall_replaces_the_loaded_job(tmp_path: Path) -> None:
    """Bootstrap fails on a loaded label, so the old interval stayed."""
    shim_dir, calls = _shims(tmp_path, "launchctl")
    workdir = tmp_path / "w"
    workdir.mkdir()
    result, _home = _install(tmp_path, "install_launchd.sh", shim_dir, workdir)
    assert result.returncode == 0, result.stderr
    lines = calls.read_text().splitlines()
    assert lines[0].startswith("launchctl bootout ")
    assert lines[1].startswith("launchctl bootstrap ")


def test_systemd_unit_quotes_and_escapes_the_script_path(tmp_path: Path) -> None:
    shim_dir, _calls = _shims(tmp_path, "systemctl")
    workdir = tmp_path / "w"
    workdir.mkdir()
    result, home = _install(tmp_path, "install_systemd.sh", shim_dir, workdir)
    assert result.returncode == 0, result.stderr
    unit = (home / ".config/systemd/user/egregore-watchdog.service").read_text()
    exec_line = next(x for x in unit.splitlines() if x.startswith("ExecStart="))
    script = str(SCRIPTS / "watchdog.sh").replace("%", "%%")
    assert exec_line == f'ExecStart="{script}"'


def test_systemd_unit_escapes_percent_in_the_working_directory(
    tmp_path: Path,
) -> None:
    """The unit escapes % in WorkingDirectory, which systemd also expands."""
    shim_dir, _calls = _shims(tmp_path, "systemctl")
    workdir = tmp_path / "100% done"
    workdir.mkdir()
    result, home = _install(tmp_path, "install_systemd.sh", shim_dir, workdir)
    assert result.returncode == 0, result.stderr
    unit = (home / ".config/systemd/user/egregore-watchdog.service").read_text()
    work_line = next(x for x in unit.splitlines() if x.startswith("WorkingDirectory="))
    assert work_line == "WorkingDirectory=" + str(workdir).replace("%", "%%")


def test_launchd_job_leaves_the_relaunched_session_running(tmp_path: Path) -> None:
    """Launchd kills a job's process group when the job exits.

    The watchdog exits right after `nohup claude &`, so without
    AbandonProcessGroup the session it started died with it. The job's
    PATH is launchd's default, which has no ~/.local/bin, so the install
    records the PATH that found claude.
    """
    shim_dir, _calls = _shims(tmp_path, "launchctl", "claude")
    workdir = tmp_path / "w"
    workdir.mkdir()
    result, home = _install(tmp_path, "install_launchd.sh", shim_dir, workdir)
    assert result.returncode == 0, result.stderr
    plist = home / "Library" / "LaunchAgents" / "com.egregore.watchdog.plist"
    parsed = plistlib.loads(plist.read_bytes())
    assert parsed["AbandonProcessGroup"] is True
    assert str(shim_dir) in parsed["EnvironmentVariables"]["PATH"].split(":")


def test_systemd_unit_leaves_the_relaunched_session_running(tmp_path: Path) -> None:
    """A oneshot unit's default KillMode kills the session the tick started."""
    shim_dir, _calls = _shims(tmp_path, "systemctl", "claude")
    workdir = tmp_path / "w"
    workdir.mkdir()
    result, home = _install(tmp_path, "install_systemd.sh", shim_dir, workdir)
    assert result.returncode == 0, result.stderr
    unit = (home / ".config/systemd/user/egregore-watchdog.service").read_text()
    lines = unit.splitlines()
    assert "KillMode=process" in lines
    env_line = next(x for x in lines if x.startswith("Environment="))
    assert str(shim_dir) in env_line


@pytest.mark.parametrize(
    ("interval", "workdir_arg"), [("5m", None), ("300", "relative-dir")]
)
def test_launchd_install_rejects_a_bad_interval_or_relative_workdir(
    tmp_path: Path, interval: str, workdir_arg: str | None
) -> None:
    """A unit in the interval broke bootstrap; a relative dir ran elsewhere."""
    shim_dir, _calls = _shims(tmp_path, "launchctl")
    (tmp_path / "relative-dir").mkdir()
    home = tmp_path / "home"
    (home / "Library" / "LaunchAgents").mkdir(parents=True)
    result = subprocess.run(
        [
            "/bin/bash",
            str(SCRIPTS / "install_launchd.sh"),
            interval,
            workdir_arg or str(tmp_path),
        ],
        env={
            **os.environ,
            "HOME": str(home),
            "PATH": f"{shim_dir}:{os.environ['PATH']}",
        },
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    plist = home / "Library" / "LaunchAgents" / "com.egregore.watchdog.plist"
    if interval != "300":
        assert result.returncode != 0
        assert not plist.exists()
    else:
        assert result.returncode == 0, result.stderr
        parsed = plistlib.loads(plist.read_bytes())
        assert parsed["WorkingDirectory"] == str(tmp_path / "relative-dir")


@pytest.mark.parametrize(
    ("interval", "workdir_arg"), [("5m", None), ("5", "relative-dir")]
)
def test_systemd_install_rejects_a_bad_interval_and_resolves_the_workdir(
    tmp_path: Path, interval: str, workdir_arg: str | None
) -> None:
    """Systemd ignores a relative WorkingDirectory; "5m" became "5mmin"."""
    shim_dir, _calls = _shims(tmp_path, "systemctl")
    (tmp_path / "relative-dir").mkdir()
    home = tmp_path / "home"
    home.mkdir()
    result = subprocess.run(
        [
            "/bin/bash",
            str(SCRIPTS / "install_systemd.sh"),
            interval,
            workdir_arg or str(tmp_path),
        ],
        env={
            **os.environ,
            "HOME": str(home),
            "PATH": f"{shim_dir}:{os.environ['PATH']}",
        },
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    unit = home / ".config/systemd/user/egregore-watchdog.service"
    if interval != "5":
        assert result.returncode != 0
        assert not unit.exists()
    else:
        assert result.returncode == 0, result.stderr
        assert f"WorkingDirectory={tmp_path / 'relative-dir'}" in unit.read_text()


def test_launchd_install_creates_the_launch_agents_directory(tmp_path: Path) -> None:
    """A fresh account has no ~/Library/LaunchAgents yet."""
    shim_dir, _calls = _shims(tmp_path, "launchctl")
    home = tmp_path / "home"
    home.mkdir()
    result = subprocess.run(
        ["/bin/bash", str(SCRIPTS / "install_launchd.sh"), "300", str(tmp_path)],
        env={
            **os.environ,
            "HOME": str(home),
            "PATH": f"{shim_dir}:{os.environ['PATH']}",
        },
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert (home / "Library/LaunchAgents/com.egregore.watchdog.plist").exists()
