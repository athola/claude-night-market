"""attune task IDs must use the spec-kit ``T001`` form.

attune documented ``TASK-NNN`` while spec-kit writes ``T001``, and the
docs describe the two plugins as integrated (issue #980). A plan written
by one would carry IDs the other's docs never mention. The scan covers
every text file attune ships, tests included, since a fixture key is an
example a reader copies.
"""

from __future__ import annotations

import re
from pathlib import Path

_PLUGIN = Path(__file__).resolve().parents[1]
_OLD_ID = re.compile(r"TASK-(?:\d+|[NXYZ]{3})")
_SUFFIXES = {".md", ".py", ".json", ".yaml", ".yml", ".j2", ".template"}


def _shipped_text_files() -> list[Path]:
    return [
        path
        for path in _PLUGIN.rglob("*")
        if path.is_file()
        and path.suffix in _SUFFIXES
        and "__pycache__" not in path.parts
        and ".venv" not in path.parts
        and path.name != Path(__file__).name
    ]


def test_attune_files_carry_no_task_dash_ids() -> None:
    """No attune doc, template or fixture names a task as TASK-NNN."""
    offenders = [
        f"{path.relative_to(_PLUGIN)}:{lineno}"
        for path in _shipped_text_files()
        for lineno, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), start=1
        )
        if _OLD_ID.search(line)
    ]
    assert not offenders, f"TASK-NNN ids left, use T001: {offenders}"


def test_execute_command_documents_t001_ids() -> None:
    """The --task example a reader copies uses the T001 form."""
    execute_doc = (_PLUGIN / "commands/execute.md").read_text(encoding="utf-8")
    assert "--task T003" in execute_doc
