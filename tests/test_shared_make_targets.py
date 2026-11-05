"""The catch-all and ``debug-variables`` live once, in the shared includes.

Twenty-one plugin Makefiles each carried a copy of both. The catch-all
copies stayed byte-identical. The ``debug-variables`` copies drifted into
eight bodies, and nine of them echoed ``$(SHELLFLAGS)``, a variable no
file sets, so they reported an empty value for the flags every recipe
ran under. Six had been corrected to ``$(.SHELLFLAGS)``. A fix applied to
some copies and not others is the cost the copies carried.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGINS_DIR = REPO_ROOT / "plugins"
SHARED = re.compile(r"^\s*include\s+.*\b(common|markdown-only)\.mk", re.MULTILINE)


def _sharing_makefiles() -> list[Path]:
    return sorted(
        path
        for path in PLUGINS_DIR.glob("*/Makefile")
        if SHARED.search(path.read_text(encoding="utf-8"))
    )


def test_discovery_finds_the_plugins_that_share_the_includes() -> None:
    assert len(_sharing_makefiles()) >= 20


@pytest.mark.parametrize("makefile", _sharing_makefiles(), ids=lambda p: p.parent.name)
def test_plugin_makefile_carries_no_copy_of_a_shared_target(makefile: Path) -> None:
    text = makefile.read_text(encoding="utf-8")
    assert not re.search(r"^debug-variables:", text, re.MULTILINE)
    assert not re.search(r"^%::", text, re.MULTILINE)


@pytest.mark.skipif(shutil.which("make") is None, reason="needs make")
@pytest.mark.parametrize("plugin", ["abstract", "scribe"])
def test_debug_variables_reports_the_flags_recipes_run_under(plugin: str) -> None:
    result = subprocess.run(
        ["make", "-s", "-C", f"plugins/{plugin}", "debug-variables"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    line = next(x for x in result.stdout.splitlines() if x.startswith("SHELLFLAGS:"))
    assert "pipefail" in line


@pytest.mark.skipif(shutil.which("make") is None, reason="needs make")
@pytest.mark.parametrize("plugin", ["abstract", "scribe"])
def test_an_unknown_target_is_refused_by_the_shared_catch_all(plugin: str) -> None:
    result = subprocess.run(
        ["make", "-s", "-C", f"plugins/{plugin}", "no-such-target"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert result.returncode != 0
    assert "Unknown target 'no-such-target'" in result.stdout
