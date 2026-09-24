"""The inline parse_frontmatter fallback must agree with leyline (XPL-001).

`sanctum/validators/_frontmatter.py` routes through
`leyline.frontmatter.parse_frontmatter` and carries an inline copy for
systems where leyline is absent. Deleting the copy is not available:
`plugins/abstract/hooks/shared/hook_io.py:64` records the standing
constraint that "plugin isolation forbids a cross-plugin import, so the
copies must change together", and sanctum declares no hard dependency on
leyline. Two copies of one contract drift silently, and the fallback is
the copy nobody runs.

So the copy is pinned to the canonical by behavior over a fixture set
rather than deleted. Change either parser without changing the other and
these tests go red.
"""

from __future__ import annotations

import importlib
import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

_LEYLINE_SOURCE = (
    Path(__file__).resolve().parents[2]
    / "leyline"
    / "src"
    / "leyline"
    / "frontmatter.py"
)

#: One document per shape the two parsers could disagree about.
DOCUMENTS: dict[str, str] = {
    "plain": "---\nname: a\nvalue: 2\n---\n\nbody\n",
    "horizontal_rule_in_body": "---\nname: a\n---\n\nintro\n\n---\n\nmore\n",
    "leading_blank_lines": "\n\n---\nname: a\n---\n\nbody\n",
    "no_closing_delimiter": "---\nname: a\n\nbody without a close\n",
    "no_frontmatter": "# Just a heading\n\nbody\n",
    "empty_frontmatter": "---\n---\n\nbody\n",
    "closing_delimiter_at_eof": "---\nname: a\n---",
    "trailing_spaces_on_delimiters": "---  \nname: a\n---  \n\nbody\n",
    "malformed_yaml": "---\nname: [unclosed\n---\n\nbody\n",
    "nested_mapping": "---\nouter:\n  inner: 1\nlist:\n  - one\n  - two\n---\nbody\n",
    "empty_document": "",
}


def _load_canonical() -> ModuleType:
    """Load leyline's parser from its file, bypassing sys.modules."""
    spec = importlib.util.spec_from_file_location(
        "_canonical_frontmatter", _LEYLINE_SOURCE
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def inline_parser(monkeypatch: pytest.MonkeyPatch) -> Any:
    """Return the inline fallback, forced by making the leyline import fail.

    Setting the module to None in ``sys.modules`` makes ``from
    leyline.frontmatter import ...`` raise ImportError, which is the
    branch a machine without leyline takes.
    """
    monkeypatch.setitem(sys.modules, "leyline.frontmatter", None)
    module = importlib.import_module("sanctum.validators._frontmatter")
    reloaded = importlib.reload(module)
    parser = reloaded.parse_frontmatter
    yield parser
    # Restore the leyline-backed binding for every later test in the run.
    monkeypatch.undo()
    importlib.reload(reloaded)


def test_the_fixture_really_exercises_the_inline_copy(inline_parser: Any) -> None:
    """Without this, every comparison below could be leyline against itself."""
    assert inline_parser.__module__ == "sanctum.validators._frontmatter"


@pytest.mark.parametrize("name", sorted(DOCUMENTS))
def test_inline_fallback_matches_leyline(name: str, inline_parser: Any) -> None:
    """Both parsers return the same value for every fixture document."""
    document = DOCUMENTS[name]
    canonical = _load_canonical().parse_frontmatter(document)
    assert inline_parser(document) == canonical, name


def test_a_horizontal_rule_in_the_body_does_not_change_the_frontmatter(
    inline_parser: Any,
) -> None:
    """The shape the old string-splitting copy got wrong."""
    document = DOCUMENTS["horizontal_rule_in_body"]
    assert inline_parser(document) == {"name": "a"}


def test_leading_blank_lines_still_parse(inline_parser: Any) -> None:
    """leyline strips before splitting; the copy must do the same."""
    assert inline_parser(DOCUMENTS["leading_blank_lines"]) == {"name": "a"}
