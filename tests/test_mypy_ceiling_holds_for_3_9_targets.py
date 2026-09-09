"""The mypy ``<2`` ceiling is what keeps the Python 3.9 target checked.

mypy 2.x refuses ``python_version = "3.9"``. Given a config that sets it, mypy
2.3.1 prints a note and then checks the file against 3.10+ semantics, so code
that cannot run on the interpreter the hooks actually use passes the gate::

    $ uv run python -m mypy probe.py            # mypy 1.20.2
    probe.py:1: error: X | Y syntax for unions requires Python 3.10  [syntax]

    $ uv run --with mypy==2.3.1 python -m mypy probe.py
    pyproject.toml: [mypy]: python_version: Python 3.9 is not supported
      (must be 3.10 or higher)
    Success: no issues found in 1 source file

where ``probe.py`` is ``def f(x: int | None) -> None: ...`` and the config is
plugins/leyline's. Both runs exit 0, so nothing downstream notices.

The hooks run on the system interpreter, which is 3.9.6 on macOS. A plugin that
targets 3.9 therefore pins mypy below 2 until it stops targeting 3.9.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover - the repo itself runs 3.12
    import tomli as tomllib

REPO_ROOT = Path(__file__).resolve().parent.parent

# ``mypy>=1.11.0,<2`` and friends: capture whatever follows the name.
_MYPY_SPEC = re.compile(r"^mypy\s*(?P<spec>[<>=!~].*)$")


def _pyprojects() -> list[Path]:
    paths = [REPO_ROOT / "pyproject.toml"]
    paths.extend(sorted((REPO_ROOT / "plugins").glob("*/pyproject.toml")))
    return [p for p in paths if p.is_file()]


def _mypy_specs(data: dict) -> list[str]:
    """Every mypy requirement string in a parsed pyproject, from any table."""
    found: list[str] = []
    project = data.get("project", {})
    groups: list[list[str]] = [project.get("dependencies", [])]
    groups.extend(project.get("optional-dependencies", {}).values())
    groups.extend(data.get("dependency-groups", {}).values())
    for group in groups:
        for raw in group:
            if not isinstance(raw, str):
                continue
            match = _MYPY_SPEC.match(raw.strip())
            if match:
                found.append(match.group("spec"))
    return found


@pytest.mark.parametrize("pyproject", _pyprojects(), ids=lambda p: p.parent.name)
def test_a_3_9_target_pins_mypy_below_2(pyproject: Path) -> None:
    data = tomllib.loads(pyproject.read_text())
    target = data.get("tool", {}).get("mypy", {}).get("python_version")
    specs = _mypy_specs(data)

    if target != "3.9":
        pytest.skip(f"targets {target!r}, not 3.9")

    assert specs, (
        f"{pyproject.relative_to(REPO_ROOT)} sets python_version = '3.9' but "
        "declares no mypy requirement, so nothing pins the checker that "
        "enforces the target."
    )
    unbounded = [spec for spec in specs if "<2" not in spec]
    assert not unbounded, (
        f"{pyproject.relative_to(REPO_ROOT)} targets Python 3.9 with mypy "
        f"{unbounded}, which allows mypy 2.x. mypy 2 refuses "
        "python_version = '3.9', reports success anyway, and stops catching "
        "3.10-only syntax in code the 3.9 hooks run. Drop the 3.9 target "
        "first, then the ceiling."
    )


def test_at_least_one_plugin_still_targets_3_9() -> None:
    """Guard the guard: if nothing targets 3.9, every case above skips."""
    targets = [
        tomllib.loads(p.read_text())
        .get("tool", {})
        .get("mypy", {})
        .get("python_version")
        for p in _pyprojects()
    ]
    assert "3.9" in targets, (
        "No pyproject targets Python 3.9 any more, so the ceiling assertion "
        "skips everywhere and cannot go red. Retire this test with the target."
    )


@pytest.mark.parametrize(
    "pyproject",
    [p for p in _pyprojects() if p.parent.name != "claude-night-market"],
    ids=lambda p: p.parent.name,
)
def test_every_plugin_still_declares_python_3_9(pyproject: Path) -> None:
    """The floor the hooks actually run on, declared where uv reads it.

    The system interpreter is 3.9.6. A plugin that raises this floor stops
    installing on it, and the mypy target above stops meaning anything.
    """
    if pyproject.parent == REPO_ROOT:
        pytest.skip("the repo's own tooling targets 3.12")
    requires = (
        tomllib.loads(pyproject.read_text()).get("project", {}).get("requires-python")
    )
    assert requires is not None, (
        f"{pyproject.relative_to(REPO_ROOT)} declares no requires-python, so "
        "nothing stops a resolve from picking a 3.10-only dependency set."
    )
    assert requires.startswith(">=3.9"), (
        f"{pyproject.relative_to(REPO_ROOT)} requires {requires!r}. The hooks "
        "run on the system interpreter, which is 3.9.6, so the floor stays "
        "at 3.9 until that changes."
    )
