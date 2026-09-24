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
    """Find files named *module*, tome's own before any other plugin's.

    The scope is ``src/`` rather than the whole plugins tree for two
    reasons: every module this page cites lives there, and a bare
    `rglob` also walks `.venv` and `.uv-cache`, where an `anyio`
    `memory.py` made a deleted module look present (and took 17s).
    Tome comes first because a bare `quality.py` also names pensive's,
    and a line that fits the wrong file proves nothing.
    """
    return list(_PLUGINS.glob(f"tome/src/**/{module}")) or list(
        _PLUGINS.glob(f"*/src/**/{module}")
    )


def _row_citations() -> list[tuple[str, int, tuple[str, ...]]]:
    """Return ``(module, line, identifiers)`` for each line-numbered citation.

    The identifiers are the words inside the row's other backticked
    spans: what the row claims sits at that line.
    """
    rows = []
    for text in _DOC.read_text(encoding="utf-8").splitlines():
        cited = [m for m in _CITATION.finditer(text) if m.group(2)]
        if not cited:
            continue
        spans = [
            span
            for span in re.findall(r"`([^`]+)`", text)
            if not _CITATION.fullmatch(f"`{span}`")
        ]
        words = tuple(
            word
            for span in spans
            for word in re.findall(r"[A-Za-z_][A-Za-z0-9_]{3,}", span)
        )
        rows.extend((m.group(1), int(m.group(2)), words) for m in cited)
    return rows


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


@pytest.mark.parametrize(
    "module,line,identifiers",
    _row_citations(),
    ids=lambda v: v if isinstance(v, str) else None,
)
def test_every_cited_line_is_where_its_row_says(
    module: str, line: int, identifiers: tuple[str, ...]
) -> None:
    """A line number that fits the file but not the code cites the wrong thing.

    `quality.py:96` stayed green for months while the Herfindahl sum
    sat near line 327, because the only check was the file length.
    """
    assert identifiers, f"`{module}:{line}` has no backticked identifier to anchor"
    source = _resolve(module)[0].read_text(encoding="utf-8").splitlines()
    window = "\n".join(source[max(0, line - 6) : line + 5])
    assert any(word in window for word in identifiers), (
        f"{_DOC.name} cites `{module}:{line}` for {identifiers}, "
        "none of which is within 5 lines of it"
    )
