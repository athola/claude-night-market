"""Recipes fail fast under the stock macOS make too (Makefile review).

The shared includes set ``.SHELLFLAGS := -euo pipefail -c``. GNU make
3.81, which macOS ships, ignores ``.SHELLFLAGS``. Every recipe on this
platform therefore ran without errexit or pipefail. The review reproduced
the result several times: ``make lint`` passing on a syntax error, a test
target passing when the tests failed, and a demo piped into ``head``
passing when the demo crashed. 3.81 does honor flags written into
``SHELL`` itself, so the includes set them there for the releases that
ignore ``.SHELLFLAGS``.

``.ONESHELL`` is gone from the includes as well. 3.81 ignores it, so every
recipe here was written and run one line per shell, and on 3.82+ the same
recipe ran as one shell. A mid-recipe ``exit`` then ended the recipe
early, and a ``cd`` leaked into later lines. One semantics now holds on
every make.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
INCLUDES = [
    ROOT / "plugins/abstract/config/make/common.mk",
    ROOT / "plugins/abstract/config/make/markdown-only.mk",
]
STANDALONE = [ROOT / "Makefile", ROOT / "plugins/phantom/Makefile"]

pytestmark = pytest.mark.skipif(shutil.which("make") is None, reason="needs make")


def _run(makefile: Path, target: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["make", "-s", "-f", str(makefile), target],
        cwd=makefile.parent,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )


@pytest.mark.parametrize("include", INCLUDES, ids=lambda p: p.name)
def test_a_failing_pipeline_stage_fails_the_recipe(
    include: Path, tmp_path: Path
) -> None:
    makefile = tmp_path / "Makefile"
    makefile.write_text(
        f"include {include}\nhelp:\n\t@true\nprobe:\n\t@false | cat; echo reached\n"
    )
    result = _run(makefile, "probe")
    assert result.returncode != 0
    assert "reached" not in result.stdout


@pytest.mark.parametrize("include", INCLUDES, ids=lambda p: p.name)
def test_the_include_no_longer_declares_oneshell(include: Path) -> None:
    lines = include.read_text().splitlines()
    assert not [x for x in lines if x.strip().startswith(".ONESHELL")]


@pytest.mark.parametrize("makefile", STANDALONE, ids=lambda p: str(p.relative_to(ROOT)))
def test_standalone_makefiles_set_the_flags_for_3_81(makefile: Path) -> None:
    """These two include neither shared .mk, so each carries the guard."""
    text = makefile.read_text()
    guard = text.index("ifneq ($(filter 3.7% 3.80 3.81")
    block = text[guard : text.index("endif", guard)]
    assert "SHELL := /bin/bash -euo pipefail" in block
