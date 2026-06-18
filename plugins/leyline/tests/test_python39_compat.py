"""Python 3.9 compatibility guard for leyline hook-import-chain modules.

leyline is imported transitively by hook scripts that run under the
system Python 3.9. Two concrete chains:

- abstract's hook tests import ``leyline`` via ``post_learnings``
  -> ``leyline.git_platform`` -> ``leyline/__init__.py``
- every per-plugin ``scripts/deferred_capture.py`` (imbue, egregore,
  attune, pensive, abstract, sanctum) imports ``leyline.deferred_capture``

``datetime.UTC`` is a 3.11+ alias. Importing it on 3.9 raises
``ImportError`` and breaks the entire hook import chain. The
established convention (see ``quota_tracker.py``) is
``from datetime import timezone`` with ``datetime.now(timezone.utc)``.

This test source-scans every module under leyline's src tree so a
future reintroduction of ``datetime.UTC`` fails here in CI, not at
runtime inside a 3.9 hook.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

_LEYLINE_SRC = Path(__file__).resolve().parent.parent / "src" / "leyline"


def _utc_violations(path: Path) -> list[str]:
    """Return descriptions of ``datetime.UTC`` usage found in ``path``.

    AST-based so docstrings and comments mentioning "UTC" (e.g. the
    "UTC timestamp" prose in deferred_capture) are not flagged.
    """
    tree = ast.parse(path.read_text(), filename=str(path))
    hits: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module == "datetime" and any(
                alias.name == "UTC" for alias in node.names
            ):
                hits.append(f"line {node.lineno}: `from datetime import UTC`")
        elif isinstance(node, ast.Attribute):
            if (
                node.attr == "UTC"
                and isinstance(node.value, ast.Name)
                and node.value.id == "datetime"
            ):
                hits.append(f"line {node.lineno}: `datetime.UTC`")
    return hits


@pytest.mark.unit
class TestLeylinePython39Compat:
    """leyline modules must not use the 3.11+ ``datetime.UTC`` alias."""

    def test_no_datetime_utc_alias_in_leyline_src(self) -> None:
        files = sorted(_LEYLINE_SRC.rglob("*.py"))
        assert files, "leyline src tree not found"
        violations: dict[str, list[str]] = {}
        for path in files:
            hits = _utc_violations(path)
            if hits:
                violations[str(path.relative_to(_LEYLINE_SRC))] = hits
        assert not violations, (
            "leyline uses datetime.UTC (3.11+), which breaks the 3.9 "
            f"hook import chain:\n{violations}\n"
            "Use `from datetime import timezone` and `timezone.utc`."
        )
