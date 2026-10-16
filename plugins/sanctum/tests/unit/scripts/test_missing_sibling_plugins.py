# ruff: noqa: D101,D102,D103,S603
"""Sanctum scripts that reach into a sibling plugin, and what they do without it.

ADR-0001 asks a cross-plugin import to degrade with a message instead of a
traceback. Each test copies a script into a plugin tree that has no
siblings and runs it with ``python -S``, which drops the site-packages
where the development environment installs leyline and abstract.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import _vendored_leyline_sibling_plugins as locator

SCRIPTS = Path(__file__).resolve().parents[3] / "scripts"
VENDORED = SCRIPTS / "_vendored_leyline_sibling_plugins.py"


def _isolated_copy(tmp_path: Path, script: str) -> Path:
    """Place ``script`` in a lone plugin, beside the vendored locator."""
    plugin = tmp_path / "plugins" / "sanctum"
    (plugin / ".claude-plugin").mkdir(parents=True)
    scripts = plugin / "scripts"
    scripts.mkdir()
    shutil.copy(SCRIPTS / script, scripts / script)
    shutil.copy(VENDORED, scripts / VENDORED.name)
    return scripts / script


def _run(*args: str, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-S", *args],
        capture_output=True,
        text=True,
        check=False,
        cwd=cwd,
    )


def test_deferred_capture_exits_1_and_names_leyline_when_it_is_missing(
    tmp_path: Path,
) -> None:
    """GIVEN no leyline plugin beside sanctum and none installed
    WHEN deferred_capture.py runs
    THEN it exits 1 with a one-line reason instead of a traceback
    """
    script = _isolated_copy(tmp_path, "deferred_capture.py")

    result = _run(str(script), "--title", "x", "--dry-run", cwd=tmp_path)

    assert result.returncode == 1
    assert result.stderr == (
        "ERROR: leyline not found. Install leyline for deferred capture support.\n"
    )


def test_tasks_manager_reports_tasks_unavailable_without_abstract(
    tmp_path: Path,
) -> None:
    """GIVEN no abstract plugin beside sanctum and none installed
    WHEN tasks_manager is imported and used
    THEN it warns once, reports tasks unavailable, and refuses to build a manager
    """
    script = _isolated_copy(tmp_path, "tasks_manager.py")
    probe = (
        "import tasks_manager as tm\n"
        "print(tm.is_tasks_available(), tm.get_claude_code_version())\n"
        "try:\n"
        "    tm.TasksManager()\n"
        "except RuntimeError as exc:\n"
        "    print(exc)\n"
    )

    result = _run("-c", probe, cwd=script.parent)

    assert result.returncode == 0, result.stderr
    assert result.stderr == (
        "Warning: abstract plugin not found. Task management features disabled.\n"
    )
    assert result.stdout.splitlines() == [
        "False unknown",
        "Task management requires the abstract plugin",
    ]


class TestVendoredSiblingLocator:
    """The vendored locator finds siblings in both install layouts."""

    @staticmethod
    def _plugin(path: Path) -> Path:
        (path / ".claude-plugin").mkdir(parents=True)
        return path

    def test_newest_cached_version_wins(self, tmp_path: Path) -> None:
        """GIVEN the cache layout with two leyline versions
        WHEN sanctum looks for leyline
        THEN 1.10.0 is chosen over 1.9.21
        """
        market = tmp_path / "cache" / "market"
        sanctum = self._plugin(market / "sanctum" / "1.10.0")
        self._plugin(market / "leyline" / "1.9.21")
        newest = self._plugin(market / "leyline" / "1.10.0")

        assert locator.sibling_plugin_dir(sanctum / "x.py", "leyline") == newest

    def test_a_file_outside_any_plugin_has_no_siblings(self, tmp_path: Path) -> None:
        assert locator.sibling_plugin_dir(tmp_path / "loose.py", "leyline") is None

    def test_a_non_numeric_version_sorts_before_numeric_ones(
        self, tmp_path: Path
    ) -> None:
        market = tmp_path / "cache" / "market"
        sanctum = self._plugin(market / "sanctum" / "1.0.0")
        self._plugin(market / "leyline" / "dev")
        release = self._plugin(market / "leyline" / "0.1.0")

        assert locator.sibling_plugin_dir(sanctum, "leyline") == release
