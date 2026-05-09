"""Shared test helpers for scribe unit tests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _make_jsonl(records: list[dict[str, Any]]) -> str:
    """Convert a list of dicts to a JSONL string."""
    return "\n".join(json.dumps(r) for r in records)


def _write_jsonl(tmp_path: Path, records: list[dict[str, Any]]) -> Path:
    """Write records as JSONL to a temp file and return the path."""
    p = tmp_path / "session.jsonl"
    p.write_text(_make_jsonl(records))
    return p


def _module_listed(name: str, modules: list[str]) -> bool:
    """Return True if a module with stem `name` is in the modules: list.

    Tolerates both bare-name (``document-economy``) and full-path
    (``modules/document-economy.md``) frontmatter formats so the
    assertion survives module-list normalization changes.
    """
    return any(Path(m).stem == name for m in modules)
