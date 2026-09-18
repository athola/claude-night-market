"""Palace state must never be readable half-written.

``open(path, "w")`` truncates before it writes, so an interrupted write
leaves a path that exists and holds invalid JSON, and a concurrent reader
can observe the file mid-write. Three sites wrote palace JSON, the master
index and the budget that way while
``corpus/index_promoter.py`` in the same plugin already used
``tempfile.mkstemp`` plus ``os.replace``. The correct pattern was next
door and unused on the paths that matter.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from memory_palace.palace_repository import _atomic_write_json


def test_a_failed_write_leaves_the_previous_content_intact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An exception mid-write must not truncate what was already there."""
    target = tmp_path / "palace.json"
    target.write_text(json.dumps({"id": "original", "rooms": [1, 2, 3]}))

    def explode(*args: object, **kwargs: object) -> None:
        raise OSError("disk full")

    monkeypatch.setattr(json, "dump", explode)
    with pytest.raises(OSError):
        _atomic_write_json(str(target), {"id": "replacement"})

    assert json.loads(target.read_text()) == {"id": "original", "rooms": [1, 2, 3]}


def test_a_failed_write_leaves_no_temporary_file_behind(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The temp file is cleaned up, so the directory does not accumulate."""
    target = tmp_path / "palace.json"

    def explode(*args: object, **kwargs: object) -> None:
        raise OSError("disk full")

    monkeypatch.setattr(json, "dump", explode)
    with pytest.raises(OSError):
        _atomic_write_json(str(target), {"id": "replacement"})

    assert list(tmp_path.iterdir()) == []


def test_a_successful_write_replaces_the_content(tmp_path: Path) -> None:
    """The happy path still writes what was asked for."""
    target = tmp_path / "nested" / "palace.json"
    _atomic_write_json(str(target), {"id": "written"})
    assert json.loads(target.read_text()) == {"id": "written"}
