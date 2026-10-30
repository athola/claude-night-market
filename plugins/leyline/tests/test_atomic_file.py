"""Tests for leyline.atomic_file, the one atomic writer every plugin vendors.

Feature: atomic file replacement
    As a writer of state that other processes read at any moment
    I want a replacement to appear whole or not at all
    So that a reader, a crash or a second writer never sees half a file
"""

from __future__ import annotations

import os
import stat
import sys
import threading
from pathlib import Path

import pytest

from leyline.atomic_file import write_atomic

GOOD = '{"session_count": 1}\n'


def _leftovers(path: Path) -> list[str]:
    return sorted(p.name for p in path.parent.iterdir() if p != path)


@pytest.mark.unit
def test_write_replaces_contents_and_leaves_no_temp_file(tmp_path: Path) -> None:
    target = tmp_path / "state.json"
    target.write_text("old", encoding="utf-8")

    write_atomic(target, "new")

    assert target.read_text(encoding="utf-8") == "new"
    assert _leftovers(target) == []


@pytest.mark.unit
def test_bytes_are_written_unchanged(tmp_path: Path) -> None:
    target = tmp_path / "archive.txt"

    write_atomic(target, b"\xff\x00raw")

    assert target.read_bytes() == b"\xff\x00raw"


@pytest.mark.unit
def test_str_path_is_accepted(tmp_path: Path) -> None:
    target = tmp_path / "state.json"

    write_atomic(str(target), GOOD)

    assert target.read_text(encoding="utf-8") == GOOD


@pytest.mark.unit
def test_failed_encode_keeps_the_last_good_copy(tmp_path: Path) -> None:
    """A lone surrogate cannot be encoded as strict UTF-8."""
    target = tmp_path / "manifest.json"
    target.write_text(GOOD, encoding="utf-8")

    with pytest.raises(UnicodeEncodeError):
        write_atomic(target, "\ud800")

    assert target.read_text(encoding="utf-8") == GOOD
    assert _leftovers(target) == []


@pytest.mark.unit
def test_failed_replace_keeps_original_and_removes_temp_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "state.json"
    target.write_text(GOOD, encoding="utf-8")

    def refuse(src: str, dst: object) -> None:
        raise OSError("disk full")

    monkeypatch.setattr(os, "replace", refuse)

    with pytest.raises(OSError, match="disk full"):
        write_atomic(target, "new")

    assert target.read_text(encoding="utf-8") == GOOD
    assert _leftovers(target) == []


@pytest.mark.unit
def test_interrupt_removes_the_temp_file_and_propagates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Ctrl-C is a BaseException: cleanup still runs and does not swallow it."""
    target = tmp_path / "journal.md"
    target.write_text(GOOD, encoding="utf-8")

    def interrupt(src: str, dst: object) -> None:
        raise KeyboardInterrupt

    monkeypatch.setattr(os, "replace", interrupt)

    with pytest.raises(KeyboardInterrupt):
        write_atomic(target, "new")

    assert target.read_text(encoding="utf-8") == GOOD
    assert _leftovers(target) == []


@pytest.mark.unit
def test_two_writes_never_share_a_temp_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A fixed sibling name let one writer's rename publish another's half file."""
    sources: list[str] = []
    real_replace = os.replace

    def record(src: str, dst: str) -> None:
        sources.append(str(src))
        real_replace(src, dst)

    monkeypatch.setattr(os, "replace", record)
    target = tmp_path / "tracker.json"

    write_atomic(target, "first")
    write_atomic(target, "second")

    assert len(set(sources)) == 2


@pytest.mark.unit
def test_concurrent_writers_each_publish_a_whole_file(tmp_path: Path) -> None:
    target = tmp_path / "shared.json"
    payloads = [f"writer-{n}-" + "x" * 4096 for n in range(8)]

    def write(payload: str) -> None:
        for _ in range(20):
            write_atomic(target, payload)

    threads = [threading.Thread(target=write, args=(p,)) for p in payloads]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert target.read_text(encoding="utf-8") in payloads
    assert _leftovers(target) == []


@pytest.mark.unit
def test_stale_fixed_sibling_does_not_block_the_write(tmp_path: Path) -> None:
    target = tmp_path / "queue.json"
    target.with_suffix(".json.tmp").mkdir()

    write_atomic(target, "new")

    assert target.read_text(encoding="utf-8") == "new"


@pytest.mark.unit
@pytest.mark.skipif(sys.platform == "win32", reason="POSIX modes")
def test_default_mode_is_private_to_the_owner(tmp_path: Path) -> None:
    target = tmp_path / "queue.json"
    target.write_text("old", encoding="utf-8")
    target.chmod(0o644)

    write_atomic(target, "new")

    assert stat.S_IMODE(target.stat().st_mode) == 0o600


@pytest.mark.unit
@pytest.mark.skipif(sys.platform == "win32", reason="POSIX modes")
def test_mode_none_keeps_the_existing_mode(tmp_path: Path) -> None:
    target = tmp_path / "manifest.json"
    target.write_text("old", encoding="utf-8")
    target.chmod(0o640)

    write_atomic(target, "new", mode=None)

    assert stat.S_IMODE(target.stat().st_mode) == 0o640


@pytest.mark.unit
@pytest.mark.skipif(sys.platform == "win32", reason="POSIX modes")
def test_mode_none_gives_a_new_file_the_umask_default(tmp_path: Path) -> None:
    target = tmp_path / "budget.json"
    umask = os.umask(0o022)
    try:
        write_atomic(target, "new", mode=None)
    finally:
        os.umask(umask)

    assert stat.S_IMODE(target.stat().st_mode) == 0o644


@pytest.mark.unit
@pytest.mark.skipif(sys.platform == "win32", reason="POSIX modes")
def test_explicit_mode_is_applied(tmp_path: Path) -> None:
    target = tmp_path / "shared.json"

    write_atomic(target, "new", mode=0o640)

    assert stat.S_IMODE(target.stat().st_mode) == 0o640


@pytest.mark.unit
def test_file_reaches_disk_before_the_rename(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """GIVEN a target WHEN written THEN fsync file, replace, fsync directory."""
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

    write_atomic(tmp_path / "state.json", "{}")

    assert events == ["fsync", "replace", "fsync"]


@pytest.mark.unit
def test_directory_sync_is_skipped_on_windows(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Windows cannot open a directory to fsync it; the write still succeeds."""
    events: list[str] = []
    real_fsync = os.fsync

    def _fsync(fd: int) -> None:
        events.append("fsync")
        real_fsync(fd)

    monkeypatch.setattr(os, "fsync", _fsync)
    monkeypatch.setattr(sys, "platform", "win32")
    target = tmp_path / "state.json"

    write_atomic(target, "{}")

    assert events == ["fsync"]
    assert target.exists()
