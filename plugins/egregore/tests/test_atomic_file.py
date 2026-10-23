"""A write that fails partway must leave the last good state file.

The watchdog, the Stop hook and the night runner read manifest.json and
budget.json at any moment. The mode tests in test_manifest.py and
test_budget.py cover the success path; these cover the failure path the
module docstring promises.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from atomic_file import write_text_atomic

GOOD = '{"session_count": 1}\n'


def _leftovers(path: Path) -> list[str]:
    return sorted(p.name for p in path.parent.iterdir() if p != path)


def test_failed_encode_keeps_the_last_good_copy(tmp_path: Path) -> None:
    """A lone surrogate cannot be encoded as UTF-8 and fails mid-write."""
    path = tmp_path / "manifest.json"
    path.write_text(GOOD, encoding="utf-8")

    with pytest.raises(UnicodeEncodeError):
        write_text_atomic(path, "\ud800")

    assert path.read_text(encoding="utf-8") == GOOD
    assert _leftovers(path) == []


def test_failed_rename_keeps_the_last_good_copy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "budget.json"
    path.write_text(GOOD, encoding="utf-8")

    def refuse(src: str, dst: object) -> None:
        raise OSError("rename refused")

    monkeypatch.setattr(os, "replace", refuse)

    with pytest.raises(OSError, match="rename refused"):
        write_text_atomic(path, '{"session_count": 2}\n')

    assert path.read_text(encoding="utf-8") == GOOD
    assert _leftovers(path) == []


def test_interrupt_removes_the_temp_file_and_propagates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Ctrl-C is a BaseException; cleanup must still run and not swallow it."""
    path = tmp_path / "manifest.json"
    path.write_text(GOOD, encoding="utf-8")

    def interrupt(src: str, dst: object) -> None:
        raise KeyboardInterrupt

    monkeypatch.setattr(os, "replace", interrupt)

    with pytest.raises(KeyboardInterrupt):
        write_text_atomic(path, '{"session_count": 2}\n')

    assert path.read_text(encoding="utf-8") == GOOD
    assert _leftovers(path) == []


def test_new_file_is_written_without_a_leftover(tmp_path: Path) -> None:
    path = tmp_path / "budget.json"

    write_text_atomic(path, GOOD)

    assert path.read_text(encoding="utf-8") == GOOD
    assert _leftovers(path) == []


def test_write_text_atomic_flushes_to_disk_before_the_rename(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The temp file reaches disk before it replaces the target.

    GIVEN a target file to replace
    WHEN it is written atomically
    THEN os.fsync runs on the temp file before os.replace publishes it,
    so a crash after the rename cannot leave an empty or stale file.
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

    assert events == ["fsync", "replace"]
