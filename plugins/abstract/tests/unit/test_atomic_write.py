"""Tests for src/abstract/atomic_write.py.

Feature: atomic file replacement
    As a writer of shared state files
    I want a replacement to appear whole or not at all
    So that a reader never sees a half-written file
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from abstract.atomic_write import write_text_atomic


@pytest.mark.unit
def test_write_replaces_contents_and_leaves_no_temp_file(tmp_path: Path) -> None:
    target = tmp_path / "queue.json"
    target.write_text("old", encoding="utf-8")

    write_text_atomic(target, "new")

    assert target.read_text(encoding="utf-8") == "new"
    assert sorted(p.name for p in tmp_path.iterdir()) == ["queue.json"]


@pytest.mark.unit
def test_failed_replace_keeps_original_and_removes_temp_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Given a replace that fails, the error propagates, the original
    stands, and no temp file is stranded.
    """
    target = tmp_path / "queue.json"
    target.write_text("old", encoding="utf-8")

    def refuse(src: str, dst: object) -> None:
        raise OSError("disk full")

    monkeypatch.setattr(os, "replace", refuse)
    with pytest.raises(OSError, match="disk full"):
        write_text_atomic(target, "new")

    assert target.read_text(encoding="utf-8") == "old"
    assert sorted(p.name for p in tmp_path.iterdir()) == ["queue.json"]


@pytest.mark.unit
def test_temp_name_is_unique_so_a_stale_sibling_does_not_block(
    tmp_path: Path,
) -> None:
    target = tmp_path / "queue.json"
    target.with_suffix(".tmp").mkdir()

    write_text_atomic(target, "new")

    assert target.read_text(encoding="utf-8") == "new"
