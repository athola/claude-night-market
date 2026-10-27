"""Tests for scripts/tasks_manager.py, the spec-kit binding to abstract.

The module configures itself at import time from the environment and from
whether the abstract plugin can be found, so each scenario imports it in a
fresh interpreter.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

_SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
_SIBLING_ABSTRACT = Path(__file__).resolve().parents[2] / "abstract" / "src"

_REPORT = (
    "import json, tasks_manager as tm; "
    "c = tm.SPECKIT_CONFIG; "
    "print(json.dumps({"
    "'stub': type(c).__module__ == 'tasks_manager', "
    "'plugin_name': getattr(c, 'plugin_name', None), "
    "'task_prefix': getattr(c, 'task_prefix', None), "
    "'words': getattr(c, 'large_scope_word_threshold', None), "
    "'tokens': getattr(c, 'large_scope_token_threshold', None), "
    "'available': tm.is_tasks_available()}))"
)


def _import_report(
    scripts_dir: Path, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-c", _REPORT],
        cwd=scripts_dir,
        capture_output=True,
        text=True,
        timeout=30,
        env={"PATH": "/usr/bin:/bin", **(env or {})},
        check=False,
    )


@pytest.mark.skipif(
    not _SIBLING_ABSTRACT.is_dir(),
    reason="needs the abstract plugin checked out beside spec-kit",
)
def test_repo_layout_binds_to_abstract_with_speckit_identity() -> None:
    """In the checkout, abstract is found beside spec-kit and configured."""
    result = _import_report(_SCRIPTS_DIR)

    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["stub"] is False
    assert report["plugin_name"] == "spec-kit"
    assert report["task_prefix"] == "SPECKIT"
    assert (report["words"], report["tokens"]) == (30, 5000)


def test_scope_thresholds_are_read_from_the_environment() -> None:
    result = _import_report(
        _SCRIPTS_DIR,
        {
            "SPECKIT_LARGE_SCOPE_WORD_THRESHOLD": "7",
            "SPECKIT_LARGE_SCOPE_TOKEN_THRESHOLD": "900",
        },
    )

    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert (report["words"], report["tokens"]) == (7, 900)


def test_non_integer_threshold_fails_the_import_loudly() -> None:
    """A typo in the env var stops the import instead of using a default."""
    result = _import_report(
        _SCRIPTS_DIR, {"SPECKIT_LARGE_SCOPE_WORD_THRESHOLD": "thirty"}
    )

    assert result.returncode != 0
    assert "ValueError" in result.stderr


def test_without_abstract_the_stubs_report_tasks_unavailable(
    tmp_path: Path,
) -> None:
    """A copy with no abstract sibling warns and disables task management."""
    isolated = tmp_path / "plugins" / "spec-kit" / "scripts"
    shutil.copytree(
        _SCRIPTS_DIR, isolated, ignore=shutil.ignore_patterns("__pycache__")
    )

    result = _import_report(isolated)

    assert result.returncode == 0, result.stderr
    assert "abstract plugin not found" in result.stderr
    report = json.loads(result.stdout)
    assert report["stub"] is True
    assert report["available"] is False


def test_without_abstract_constructing_a_manager_raises(tmp_path: Path) -> None:
    isolated = tmp_path / "plugins" / "spec-kit" / "scripts"
    shutil.copytree(
        _SCRIPTS_DIR, isolated, ignore=shutil.ignore_patterns("__pycache__")
    )

    result = subprocess.run(
        [sys.executable, "-c", "import tasks_manager as tm; tm.TasksManager()"],
        cwd=isolated,
        capture_output=True,
        text=True,
        timeout=30,
        env={"PATH": "/usr/bin:/bin"},
        check=False,
    )

    assert result.returncode != 0
    assert "Task management requires the abstract plugin" in result.stderr
