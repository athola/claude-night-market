"""A file claiming ``-euo pipefail`` must say when it does not get it.

``.SHELLFLAGS`` and ``.ONESHELL`` arrived in GNU make 3.82. Stock macOS
ships 3.81 from the Xcode command line tools, and that is what this
repository's own platform runs. 3.81 parses ``.SHELLFLAGS := -euo
pipefail -c`` and ignores it, so every recipe in the file runs under a
plain ``sh -c``: no errexit, no pipefail, and a failing stage of a
pipeline passes.

``plugins/abstract/config/make/common.mk`` pairs the assignment with a
``$(warning)`` so the gap is announced once per invocation. The root
``Makefile`` and ``plugins/phantom/Makefile`` copied the assignment
without the warning and include neither shared ``.mk``, so they claimed
the guarantee silently. The root file is where the masked ``cargo build``
of ``tests/test_skrills_build_propagates_failure.py`` lived.

The second assertion is about the guard's own arithmetic. Enumerating the
good versions (``3.82 4.%``) leaves GNU make 5.x falling through to a
warning that tells the user to install 3.82 or later, which they already
have. The versions that ignore ``.SHELLFLAGS`` are a closed set, so the
filter names those instead.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

SHELLFLAGS_ASSIGNMENT = re.compile(r"^\s*\.SHELLFLAGS\s*[:?+]?=", re.MULTILINE)
MAKE_VERSION_GUARD = re.compile(r"MAKE_VERSION")
SHARED_INCLUDE = re.compile(
    r"^\s*-?include\s+.*\b(common|markdown-only)\.mk", re.MULTILINE
)

# Versions that parse .SHELLFLAGS and ignore it. Everything from 3.82 on
# honors it, so the guard names the closed set rather than the open one.
KNOWN_BAD_FILTER = re.compile(r"\$\(filter\s+3\.7%\s+3\.80\s+3\.81\s*,")


def _make_files() -> list[Path]:
    found = [
        path
        for pattern in ("Makefile", "*.mk", "Makefile.template", "*/Makefile")
        for path in REPO_ROOT.glob(pattern)
    ]
    found += list((REPO_ROOT / "plugins").rglob("Makefile"))
    found += list((REPO_ROOT / "plugins").rglob("*.mk"))
    found += list((REPO_ROOT / "plugins").rglob("Makefile.template"))
    return sorted({p for p in found if p.is_file()})


def _files_setting_shellflags() -> list[Path]:
    return [
        path
        for path in _make_files()
        if SHELLFLAGS_ASSIGNMENT.search(path.read_text(encoding="utf-8"))
    ]


def test_discovery_finds_shellflags_users() -> None:
    """An empty parametrize list would make the guards below vacuous."""
    assert len(_files_setting_shellflags()) >= 5


@pytest.mark.parametrize(
    "path",
    _files_setting_shellflags(),
    ids=lambda p: str(p.relative_to(REPO_ROOT)),
)
def test_shellflags_assignment_announces_when_make_ignores_it(path: Path) -> None:
    """Either include a shared .mk that warns, or carry the warning."""
    text = path.read_text(encoding="utf-8")
    if SHARED_INCLUDE.search(text):
        return
    assert MAKE_VERSION_GUARD.search(text), (
        f"{path.relative_to(REPO_ROOT)} sets .SHELLFLAGS but neither includes "
        "a shared .mk nor checks MAKE_VERSION, so on GNU make 3.81 it claims "
        "errexit and pipefail and gets neither, with no diagnostic."
    )


@pytest.mark.parametrize(
    "path",
    [
        p
        for p in _files_setting_shellflags()
        if MAKE_VERSION_GUARD.search(p.read_text(encoding="utf-8"))
    ],
    ids=lambda p: str(p.relative_to(REPO_ROOT)),
)
def test_version_guard_names_the_versions_that_ignore_shellflags(path: Path) -> None:
    """The filter lists the known-bad versions, not the known-good ones."""
    text = path.read_text(encoding="utf-8")
    assert KNOWN_BAD_FILTER.search(text), (
        f"{path.relative_to(REPO_ROOT)} enumerates the versions that honor "
        ".SHELLFLAGS, so GNU make 5.x falls through and is told to install "
        "3.82 or later. Filter on 3.7% 3.80 3.81 instead."
    )
