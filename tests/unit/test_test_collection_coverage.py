"""Every test file outside the plugins must sit in a collected path.

``prototypes/forced-eval/`` shipped in a tagged release with 20 passing
tests that no gate ran. ``testpaths = ["tests"]`` meant a ``pytest`` run
from the repo root never looked at it, so its README's "all green" claim
had nothing checking it and could rot silently for as long as the
prototype lived.

Plugin suites are deliberately excluded: they carry their own
``conftest.py`` files that collide when collected together, so
``make test`` runs each plugin from inside its own directory. That
exclusion is the reason ``norecursedirs`` lists ``plugins/*``, and it is
honored here.

What is left is everything else at the repo root, and there the rule is
simple: a test file that exists must be in a path pytest collects. A new
prototype gets one either way, and this test is what says so at the time
it is added rather than a release later.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import tomllib

REPO = Path(__file__).resolve().parents[2]

# Directories whose suites run from inside themselves, not from the root.
# plugins/* each carry a conftest.py that collides on a shared collection;
# the rest are caches and scratch trees.
SELF_CONTAINED = {"plugins", ".venv", ".uv-cache", ".worktrees", ".claude"}


def _testpaths() -> list[str]:
    config = tomllib.loads((REPO / "pyproject.toml").read_text())
    return config["tool"]["pytest"]["ini_options"]["testpaths"]


def _root_test_files() -> list[Path]:
    """Every test_*.py at the repo root outside the self-contained trees."""
    found = []
    for path in REPO.rglob("test_*.py"):
        relative = path.relative_to(REPO)
        if relative.parts[0] in SELF_CONTAINED:
            continue
        if any(part.startswith(".") for part in relative.parts):
            continue
        if "__pycache__" in relative.parts:
            continue
        found.append(relative)
    return sorted(found)


class TestScanIsNotVacuous:
    """A scan that finds nothing proves nothing."""

    @pytest.mark.unit
    def test_root_test_files_are_found(self) -> None:
        """
        GIVEN the repository root
        WHEN scanning for test files outside the self-contained trees
        THEN several are found
        """
        assert len(_root_test_files()) > 5, "the collection scan found almost nothing"

    @pytest.mark.unit
    def test_testpaths_is_declared(self) -> None:
        """
        GIVEN pyproject.toml
        WHEN reading the pytest configuration
        THEN testpaths is a non-empty list
        """
        assert _testpaths(), "testpaths must be declared for this gate to mean anything"


class TestEveryTestFileIsCollected:
    """Scenario: no test file may sit outside every collected path."""

    @pytest.mark.unit
    def test_no_test_file_falls_outside_testpaths(self) -> None:
        """
        GIVEN a test file at the repo root, outside the plugin trees
        WHEN pytest runs with the declared testpaths
        THEN that file is inside one of them

        A test nothing runs is worse than no test: it reads as coverage
        on the page and asserts nothing at the gate.
        """
        roots = tuple(_testpaths())
        orphans = [
            str(relative)
            for relative in _root_test_files()
            if not str(relative).startswith(roots)
        ]
        assert not orphans, (
            "these test files are in no collected path; add their directory "
            "to testpaths in pyproject.toml:\n  " + "\n  ".join(orphans)
        )
