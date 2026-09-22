"""Every module the research-quality metrics doc cites must exist.

`docs/metrics/tome-research-quality.md` marks each metric `exists`,
`wire-up` or `new`, and backs the first two with a module name and often
a line number. Those citations are the doc's whole claim to be a status
table rather than a wish list, and nothing checked them: commit
35d6c952 deleted `tome/src/tome/memory.py` and two rows kept pointing at
it, one of them still reading `exists`.

The check resolves a bare module name against the plugins tree, which is
how the doc writes them: several cited modules are memory-palace's, and
the doc says so in the status column.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_DOC = _REPO_ROOT / "docs" / "metrics" / "tome-research-quality.md"
_PLUGINS = _REPO_ROOT / "plugins"

#: A backticked module citation, with an optional `:line` suffix.
_CITATION = re.compile(r"`([A-Za-z_][A-Za-z0-9_]*\.py)(?::(\d+))?`")


def _citations() -> list[tuple[str, int | None]]:
    """Return every ``(module, line)`` citation in the doc."""
    return [
        (match.group(1), int(match.group(2)) if match.group(2) else None)
        for match in _CITATION.finditer(_DOC.read_text(encoding="utf-8"))
    ]


def _resolve(module: str) -> list[Path]:
    """Find files named *module* under any plugin's ``src/``.

    The scope is ``src/`` rather than the whole plugins tree for two
    reasons: every module this page cites lives there, and a bare
    `rglob` also walks `.venv` and `.uv-cache`, where an `anyio`
    `memory.py` made a deleted module look present (and took 17s).
    """
    return list(_PLUGINS.glob(f"*/src/**/{module}"))


def test_the_doc_exists_and_cites_modules() -> None:
    """Guard the guard: a doc that stopped citing anything passes vacuously."""
    assert _DOC.is_file()
    assert len(_citations()) >= 5


@pytest.mark.parametrize("module", sorted({module for module, _ in _citations()}))
def test_every_cited_module_exists(module: str) -> None:
    """A citation to a deleted module makes the status column a lie."""
    assert _resolve(module), (
        f"{_DOC.name} cites `{module}`, which is nowhere under plugins/. "
        "Either the module came back or the row needs restating."
    )


@pytest.mark.parametrize(
    "module,line",
    sorted({(module, line) for module, line in _citations() if line is not None}),
)
def test_every_cited_line_is_inside_its_file(module: str, line: int) -> None:
    """A line number past the end of the file cites nothing."""
    lengths = {
        path: len(path.read_text(encoding="utf-8").splitlines())
        for path in _resolve(module)
    }
    assert any(line <= total for total in lengths.values()), (
        f"{_DOC.name} cites `{module}:{line}`, past the end of every "
        f"file of that name: {sorted(lengths.values())}"
    )
