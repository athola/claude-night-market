"""usage_log_rotation outside POSIX, where fcntl does not exist."""

from __future__ import annotations

import os
import stat
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

import usage_log_rotation  # noqa: E402 - after the scripts/ path insert


@pytest.mark.unit
def test_append_without_fcntl_still_rotates_and_appends(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Without flock the append runs unlocked rather than raising."""
    monkeypatch.setattr(usage_log_rotation, "fcntl", None)
    log, backup = tmp_path / "usage.jsonl", tmp_path / "usage.jsonl.1"
    log.write_text("x" * 20 + "\n")

    usage_log_rotation.append_line(log, backup, '{"n": 1}', max_bytes=10)

    assert backup.read_text() == "x" * 20 + "\n"
    assert log.read_text() == '{"n": 1}\n'


def test_new_usage_log_is_private_to_the_user(tmp_path: Path) -> None:
    """The log holds prompt lengths and errors; it was created 0644 (CNJ-5)."""
    log = tmp_path / "usage.jsonl"
    old_umask = os.umask(0o022)
    try:
        usage_log_rotation.append_line(log, tmp_path / "usage.jsonl.1", "{}", 1024)
    finally:
        os.umask(old_umask)
    assert stat.S_IMODE(log.stat().st_mode) == 0o600
