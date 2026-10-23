"""Tests for src/abstract/atomic_write.py.

Feature: atomic file replacement
    As a writer of shared state files
    I want a replacement to appear whole or not at all
    So that a reader never sees a half-written file
"""

from __future__ import annotations

import os
import sys
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


def test_write_text_atomic_flushes_to_disk_before_the_rename(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The temp file reaches disk before it replaces the target.

    GIVEN a target file to replace
    WHEN it is written atomically
    THEN os.fsync runs on the temp file before os.replace publishes it,
    and on the directory after, so a crash cannot lose the data or the
    rename.
    """
    events: list[str] = []
    real_fsync, real_replace = os.fsync, os.replace

    def _fsync(fd: int) -> None:
        events.append("fsync")
        real_fsync(fd)

    def _replace(src: str, dst: str) -> None:
        events.append("replace")
        real_replace(src, dst)

    monkeypatch.setattr(os, "fsync", _fsync)
    monkeypatch.setattr(os, "replace", _replace)
    target = tmp_path / "state.json"

    write_text_atomic(target, "{}")

    assert events == ["fsync", "replace", "fsync"]


def test_directory_sync_is_skipped_on_windows(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Windows cannot open a directory to fsync it.

    GIVEN the platform reports win32
    WHEN a file is written atomically
    THEN only the temp file is synced, and the write still succeeds.
    """
    events: list[str] = []
    real_fsync = os.fsync

    def _fsync(fd: int) -> None:
        events.append("fsync")
        real_fsync(fd)

    monkeypatch.setattr(os, "fsync", _fsync)
    monkeypatch.setattr(sys, "platform", "win32")
    target = tmp_path / "state.json"

    write_text_atomic(target, "{}")

    assert events == ["fsync"]
    assert target.exists()
