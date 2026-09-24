"""Every script with a CLI must be named by something that runs it.

``scripts/night_run.py`` shipped with an entry point and no caller: no
agent, skill, command or README told anyone to run it, and the only
mention was as an audit target. A script nothing names is a script
nothing runs.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
_PROSE_ROOTS = ("agents", "skills", "commands")


def _cli_scripts() -> list[Path]:
    return sorted(
        p
        for p in (PLUGIN_ROOT / "scripts").glob("*.py")
        if "\ndef main(" in p.read_text(encoding="utf-8")
    )


def _prose() -> str:
    chunks = [(PLUGIN_ROOT / "README.md").read_text(encoding="utf-8")]
    for root in _PROSE_ROOTS:
        chunks.extend(
            p.read_text(encoding="utf-8") for p in (PLUGIN_ROOT / root).rglob("*.md")
        )
    return "\n".join(chunks)


def _imported_by_a_sibling(script: Path) -> bool:
    """Return True when another shipped script or hook imports this one."""
    stem = script.stem
    siblings = [
        p
        for root in ("scripts", "hooks")
        for p in (PLUGIN_ROOT / root).glob("*.py")
        if p != script
    ]
    return any(
        f"import {stem}" in p.read_text(encoding="utf-8")
        or f'"{stem}"' in p.read_text(encoding="utf-8")
        for p in siblings
    )


@pytest.mark.parametrize("script", _cli_scripts(), ids=lambda p: p.name)
def test_a_script_with_a_main_is_named_by_an_agent_skill_command_or_readme(
    script: Path,
) -> None:
    assert script.name in _prose() or _imported_by_a_sibling(script), (
        f"scripts/{script.name} has a main() but no agent, skill, command, "
        "README or sibling script names it, so nothing runs it"
    )


def test_the_check_sees_the_scripts_it_guards() -> None:
    names = {p.name for p in _cli_scripts()}
    assert {"night_run.py", "learning.py"} <= names, names


def test_the_night_run_section_names_only_launchers_that_start_it() -> None:
    """The watchdog relaunches a ``claude -p`` session, not night_run.py.

    The summon skill once said the installed watchdog starts the night
    run, which sent an operator looking for a process that never ran.
    """
    watchdog = (PLUGIN_ROOT / "scripts" / "watchdog.sh").read_text(encoding="utf-8")
    skill = (PLUGIN_ROOT / "skills" / "summon" / "SKILL.md").read_text(encoding="utf-8")
    section = skill.split("### The unattended night run", 1)[1].split("\n## ", 1)[0]
    sentences = re.split(r"(?<=[.!?])\s+", " ".join(section.split()))
    claims = [s for s in sentences if "install-watchdog" in s]
    assert claims, "the section no longer mentions the watchdog"
    if "night_run" not in watchdog:
        for claim in claims:
            assert re.search(r"\b(not|neither|nor)\b", claim), claim
