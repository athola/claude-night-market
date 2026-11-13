"""Concurrent captures must not lose each other's index entries.

Parallel WebFetch calls run one hook process each, and every one of
them loads, mutates and rewrites the same capture index. Without a
lock across that sequence, the last writer drops the entries the
others added, leaving staged files no index entry points at.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

_SHARED = Path(__file__).resolve().parents[2] / "hooks" / "shared"
_WRITERS = 12

_WRITER = """
import sys
sys.path.insert(0, {shared!r})
import deduplication
deduplication.update_index(
    content_hash="sha256:" + sys.argv[1],
    stored_at="data/staging/" + sys.argv[1] + ".md",
    importance_score=50,
    url="https://example.com/" + sys.argv[1],
)
"""


@pytest.mark.skipif(sys.platform == "win32", reason="flock is POSIX-only")
def test_parallel_update_index_keeps_every_entry(tmp_path: Path) -> None:
    """GIVEN twelve hook processes capturing distinct URLs at once
    WHEN each one calls update_index
    THEN the index on disk holds all twelve entries
    """
    env = {**os.environ, "MEMORY_PALACE_DATA_DIR": str(tmp_path)}
    env.pop("CLAUDE_PLUGIN_DATA", None)
    script = _WRITER.format(shared=str(_SHARED))
    procs = [
        subprocess.Popen(
            [sys.executable, "-c", script, f"k{n}"],
            env=env,
            cwd=tmp_path,
            stderr=subprocess.PIPE,
        )
        for n in range(_WRITERS)
    ]
    for proc in procs:
        _, err = proc.communicate(timeout=60)
        assert proc.returncode == 0, err.decode()

    index = yaml.safe_load(
        (tmp_path / "hooks" / "memory-palace-index.yaml").read_text()
    )
    assert len(index["entries"]) == _WRITERS
