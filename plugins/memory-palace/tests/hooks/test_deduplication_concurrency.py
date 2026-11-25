"""Concurrent captures must not lose each other's index entries.

Parallel WebFetch calls run one hook process each, and every one of
them loads, mutates and rewrites the same capture index. Without a
lock across that sequence, the last writer drops the entries the
others added, leaving staged files no index entry points at.
"""

from __future__ import annotations

import fcntl
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
import web_research_handler
import yaml

_SHARED = Path(__file__).resolve().parents[2] / "hooks" / "shared"
_WRITERS = 12
# Hooks run under the system interpreter, which is slower than the venv's.
_HOOK_PYTHON = (
    "/usr/bin/python3" if Path("/usr/bin/python3").exists() else sys.executable
)

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


_HOLDER_GIVES_UP = """
import sys, time
sys.path.insert(0, {shared!r})
import deduplication
deduplication._LOCK_TIMEOUT_SECONDS = 0.3
start = time.monotonic()
try:
    deduplication.update_index(
        content_hash="sha256:blocked",
        stored_at="data/staging/blocked.md",
        importance_score=50,
        url="https://example.com/blocked",
    )
except TimeoutError:
    print(round(time.monotonic() - start, 2))
    sys.exit(0)
sys.exit(1)
"""


def _lock_path(data_dir: Path) -> Path:
    return data_dir / "hooks" / "memory-palace-index.yaml.lock"


@pytest.mark.skipif(sys.platform == "win32", reason="flock is POSIX-only")
def test_update_index_gives_up_when_lock_is_held_past_deadline(
    tmp_path: Path,
) -> None:
    """GIVEN another process holding the index lock
    WHEN a hook calls update_index
    THEN it raises TimeoutError within the deadline instead of blocking
        past the 5s hook budget, which would kill it mid-capture
    """
    env = {**os.environ, "MEMORY_PALACE_DATA_DIR": str(tmp_path)}
    env.pop("CLAUDE_PLUGIN_DATA", None)
    lock_path = _lock_path(tmp_path)
    lock_path.parent.mkdir(parents=True)
    with open(lock_path, "a") as held:
        fcntl.flock(held, fcntl.LOCK_EX)
        proc = subprocess.run(
            [sys.executable, "-c", _HOLDER_GIVES_UP.format(shared=str(_SHARED))],
            env=env,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    assert proc.returncode == 0, proc.stderr
    assert float(proc.stdout) < 2.0


def test_queue_file_is_removed_when_index_lock_times_out(tmp_path: Path) -> None:
    """GIVEN the index lock cannot be taken before the deadline
    WHEN a capture is stored
    THEN no queue file is left that no index entry points at
    """
    queue = tmp_path / "queue"
    with (
        patch.object(web_research_handler, "QUEUE_DIR", queue),
        patch.object(web_research_handler, "DATA_ROOT", tmp_path),
        patch.object(
            web_research_handler, "update_index", side_effect=TimeoutError("held")
        ),
    ):
        stored = web_research_handler.store_webfetch_content(
            "Substantive body text about a topic.",
            "https://example.com/article",
            "summarize this",
        )
    assert stored is None
    assert list(queue.iterdir()) == []


@pytest.mark.skipif(sys.platform == "win32", reason="flock is POSIX-only")
@pytest.mark.skipif(not yaml.__with_libyaml__, reason="needs the libyaml C loader")
def test_parallel_writers_on_a_large_index_all_finish_inside_the_lock_deadline(
    tmp_path: Path,
) -> None:
    """GIVEN an index of 1500 entries, the size a real capture history reaches
    WHEN six hook processes call update_index at once
    THEN none times out: each one reloads and rewrites the whole index under
        a 3 s lock, and the pure-Python loader took about 1.2 s a cycle
    """
    index_path = tmp_path / "hooks" / "memory-palace-index.yaml"
    index_path.parent.mkdir(parents=True)
    entries = {
        f"https://example.com/search?query=seed%20topic%20{n}&tags=story": {
            "content_hash": f"sha256:{n:016x}",
            "stored_at": f"data/staging/webfetch-seed-topic-{n}-2026-07-02_11-04-24.md",
            "importance_score": 85,
            "last_updated": "2026-07-02T11:04:24.508854+00:00",
            "title": f"Stories About Seed Topic Number {n} and Its Documentation",
            "maturity": "growing",
            "routing_type": "meta",
            "url": f"https://example.com/search?query=seed%20topic%20{n}&tags=story",
        }
        for n in range(1500)
    }
    hashes = {e["content_hash"]: e["stored_at"] for e in entries.values()}
    index_path.write_text(yaml.safe_dump({"entries": entries, "hashes": hashes}))
    env = {**os.environ, "MEMORY_PALACE_DATA_DIR": str(tmp_path)}
    env.pop("CLAUDE_PLUGIN_DATA", None)
    script = _WRITER.format(shared=str(_SHARED))
    procs = [
        subprocess.Popen(
            [_HOOK_PYTHON, "-c", script, f"big{n}"],
            env=env,
            cwd=tmp_path,
            stderr=subprocess.PIPE,
        )
        for n in range(_WRITERS)
    ]
    for proc in procs:
        _, err = proc.communicate(timeout=60)
        assert proc.returncode == 0, err.decode()
