"""Deduplication and index management for memory-palace.

Uses fast hashing and in-memory caching for performance.
Implements atomic writes for data integrity.
"""

from __future__ import annotations

import contextlib
import hashlib
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING

yaml: ModuleType | None
try:
    import yaml
except ImportError:
    yaml = None

if TYPE_CHECKING:
    from typing import Any

# hooks/shared/ -> the plugin root's src/. Hooks already put this on the
# path, but this module is imported directly by tests and by scripts
# that never ran a hook, so it cannot rely on that.
_SRC = str(Path(__file__).resolve().parents[2] / "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from memory_palace.paths import persistent_root as _persistent_root

# Try to use xxhash for speed, fall back to hashlib
try:
    import xxhash

    _USE_XXHASH = True
except ImportError:
    _USE_XXHASH = False

# Index cache
_index_cache: dict[str, Any] | None = None
_index_mtime: float = 0

# Ceiling on the staging call. `git add` on one file is milliseconds;
# anything near this bound is a lock being held, and a capture waits for
# no one.
_STAGE_TIMEOUT_SECONDS = 5


def _get_index_path() -> Path:
    """Get path to the capture index.

    The index accumulates an entry per capture, so it is user data and
    must outlive the version that wrote it. Resolving it from
    ``__file__`` alone made it version scoped: on this machine the
    1.9.17 tree held a 5,467-line index and 1.9.18 started a fresh one,
    each invisible to the other (issue #661).

    The ``hooks/`` segment is kept deliberately. Entries record
    ``stored_at`` relative to the root and a wall of consumers resolve
    the index as ``<root>/hooks/memory-palace-index.yaml`` -- the
    maintenance CLI, the pre-commit drain gate, the promoter. Because
    ``persistent_root`` is the identity in a source checkout, all of
    them keep reading the tracked file they read today.
    """
    hooks_dir = Path(__file__).resolve().parent.parent
    return _persistent_root(hooks_dir.parent) / "hooks" / "memory-palace-index.yaml"


def get_content_hash(content: str | bytes) -> str:
    """Generate fast hash of content.

    Uses xxhash if available (10x faster), otherwise SHA256.
    """
    if isinstance(content, str):
        content = content.encode("utf-8")

    if _USE_XXHASH:
        return f"xxh:{xxhash.xxh64(content).hexdigest()}"
    return f"sha256:{hashlib.sha256(content).hexdigest()[:16]}"


def get_url_key(url: str) -> str:
    """Normalize URL for consistent keying."""
    # Remove trailing slashes, fragments, common tracking params
    url = url.rstrip("/")
    if "#" in url:
        url = url.split("#")[0]

    # Remove common tracking parameters
    for param in ["utm_source", "utm_medium", "utm_campaign", "ref"]:
        if f"?{param}=" in url or f"&{param}=" in url:
            url = re.sub(rf"[?&]{param}=[^&]*", "", url)

    return url.lower()


def _load_index() -> dict[str, Any]:
    """Load index from disk with caching."""
    global _index_cache, _index_mtime  # noqa: PLW0603 - module-level cache requires global for mtime-based invalidation

    index_path = _get_index_path()

    try:
        current_mtime = index_path.stat().st_mtime

        if _index_cache is not None and current_mtime <= _index_mtime:
            return _index_cache

        if yaml is None:
            _index_cache = {"entries": {}, "hashes": {}}
            return _index_cache

        try:
            with open(index_path) as f:
                _index_cache = yaml.safe_load(f) or {"entries": {}, "hashes": {}}
        except yaml.YAMLError as exc:
            # Issue #528: a corrupt index file must not take down web-research
            # store calls. Log to stderr so the operator notices, then fall
            # back to the empty-index sentinel.
            print(
                f"[memory-palace] WARNING: corrupt YAML index at "
                f"{index_path}: {exc}; falling back to empty index. "
                f"Repair or delete the file to restore persistence.",
                file=sys.stderr,
            )
            _index_cache = {"entries": {}, "hashes": {}}
            _index_mtime = current_mtime
            return _index_cache

        # validate required keys exist
        _index_cache.setdefault("entries", {})
        _index_cache.setdefault("hashes", {})

        _index_mtime = current_mtime
        return _index_cache

    except FileNotFoundError:
        _index_cache = {"entries": {}, "hashes": {}}
        return _index_cache


def is_known(
    content_hash: str | None = None,
    url: str | None = None,
    path: str | None = None,
) -> bool:
    """Fast check if content is already indexed.

    Can check by hash, URL, or path. Returns True if any match.
    """
    index = _load_index()

    if content_hash and content_hash in index.get("hashes", {}):
        return True

    if url:
        url_key = get_url_key(url)
        if url_key in index.get("entries", {}):
            return True

    if path:
        path_key = str(Path(path).resolve())
        if path_key in index.get("entries", {}):
            return True

    return False


def get_stored_at(content_hash: str) -> str | None:
    """Return the file these bytes are stored in, or None if unseen.

    ``hashes`` is content-addressed: it answers "where does this content
    already live?" so a second URL serving the same bytes can point at
    the existing capture instead of writing a duplicate.
    """
    index = _load_index()
    stored_at = index.get("hashes", {}).get(content_hash)
    return stored_at if isinstance(stored_at, str) else None


def _drop_unreferenced_hash(
    index: dict[str, Any], superseded: str | None, current: str
) -> None:
    """Drop a hash mapping that no surviving entry points at.

    Re-indexing content that changed leaves the previous mapping behind.
    An unreferenced mapping still answers ``is_known`` with True, so it
    suppresses a later capture of content that no entry can retrieve.
    """
    if not superseded or superseded == current:
        return

    still_referenced = any(
        entry.get("content_hash") == superseded
        for entry in index.get("entries", {}).values()
    )
    if not still_referenced:
        index.get("hashes", {}).pop(superseded, None)


def get_entry(url: str | None = None, path: str | None = None) -> dict[str, Any] | None:
    """Get existing entry details for comparison."""
    index = _load_index()

    if url:
        url_key = get_url_key(url)
        entry = index.get("entries", {}).get(url_key)
        return entry if isinstance(entry, dict) else None

    if path:
        path_key = str(Path(path).resolve())
        entry = index.get("entries", {}).get(path_key)
        return entry if isinstance(entry, dict) else None

    return None


def needs_update(
    content_hash: str, url: str | None = None, path: str | None = None
) -> bool:
    """Check if existing entry needs update (content changed)."""
    entry = get_entry(url=url, path=path)

    if not entry:
        return True  # Not indexed yet

    return entry.get("content_hash") != content_hash


def update_index(  # noqa: PLR0913 - index entries have many metadata fields
    content_hash: str,
    stored_at: str,
    importance_score: int,
    *,
    url: str | None = None,
    path: str | None = None,
    title: str | None = None,
    maturity: str | None = None,
    routing_type: str | None = None,
    null_capture: str | None = None,
) -> None:
    """Add or update entry in index.

    Args:
        content_hash: Hash of content for change detection
        stored_at: Path where content was stored
        importance_score: Score from knowledge-intake evaluation (0-100)
        url: Source URL (for web content)
        path: Local path (for local docs)
        title: Content title
        maturity: Knowledge maturity level (seedling, growing, evergreen)
        routing_type: Application routing (local, meta, both)
        null_capture: Reason a 2xx fetch carried no content
            (redirect notice, empty result set). Set by the fetch
            hook; the promoter archives rather than promotes these.

    Note: This does write to disk - use sparingly.

    Raises:
        ValueError: if ``importance_score`` is outside the documented
            closed range [0, 100]. Validation runs before any state
            mutation so a bad score cannot poison the cache or the
            on-disk index.

    """
    if not 0 <= importance_score <= 100:
        raise ValueError(
            f"importance_score must be in [0, 100], got {importance_score}"
        )

    global _index_cache  # noqa: PLW0603 - invalidate module-level cache after disk write

    index = _load_index()
    now = datetime.now(timezone.utc).isoformat()

    # The index is content-addressed: one piece of content lives in one
    # file. When these bytes are already stored, the entry adopts that
    # canonical location instead of overwriting the mapping with a
    # private copy - the write that used to leave an earlier entry
    # pointing at a path `hashes` no longer agreed with.
    stored_at = index["hashes"].setdefault(content_hash, stored_at)

    entry = {
        "content_hash": content_hash,
        "stored_at": stored_at,
        "importance_score": importance_score,
        "last_updated": now,
    }

    if title:
        entry["title"] = title

    # Align with knowledge-intake evaluation schema
    if maturity:
        entry["maturity"] = maturity  # seedling, growing, evergreen
    if routing_type:
        entry["routing_type"] = routing_type  # local, meta, both
    if null_capture:
        entry["null_capture"] = null_capture

    key: str | None = None
    if url:
        key = get_url_key(url)
        entry["url"] = url
    elif path:
        key = str(Path(path).resolve())
        entry["path"] = path

    if key is not None:
        superseded = index["entries"].get(key, {}).get("content_hash")
        index["entries"][key] = entry
        _drop_unreferenced_hash(index, superseded, content_hash)

    # Atomic write back using tempfile + rename
    if yaml is None:
        # Cannot persist without yaml - cache only
        _index_cache = index
        return

    index_path = _get_index_path()
    index_path.parent.mkdir(parents=True, exist_ok=True)

    # Write to temp file in same directory (validates same filesystem for atomic rename)
    fd, tmp_path = tempfile.mkstemp(
        suffix=".tmp",
        prefix="memory-palace-index-",
        dir=index_path.parent,
    )
    try:
        with os.fdopen(fd, "w") as f:
            yaml.safe_dump(index, f, default_flow_style=False, sort_keys=False)
        # Atomic rename (works on POSIX, best-effort on Windows)
        os.replace(tmp_path, index_path)
    except Exception:
        # Clean up temp file on failure
        with contextlib.suppress(OSError):
            os.unlink(tmp_path)
        raise

    _stage_index(index_path)

    # Update cache
    _index_cache = index
    _index_mtime = index_path.stat().st_mtime


def _stage_index(index_path: Path) -> None:
    """Stage the index so the pre-commit drain can see this capture.

    ``pre-commit`` reverts unstaged changes to tracked files before
    running any pre-commit-stage hook. An index written but never staged
    is therefore absent from the tree the drain inspects: it reads the
    HEAD version, converges on it, and the fresh capture survives the
    commit still ``pending``. That is how the 47-entry backlog drained
    in 2ed3737b accumulated while the drain reported nothing to do.

    Best-effort by design. Captures happen during ordinary work, not
    during a commit, so the common failures here are unremarkable: the
    index lives outside a repository, git is absent, or an operation
    holds the index lock. None of them are worth taking a WebFetch down
    over, and none of them lose data, because the write already
    completed.
    """
    with contextlib.suppress(OSError, subprocess.SubprocessError):
        subprocess.run(
            ["git", "add", "--", str(index_path)],
            cwd=str(index_path.parent),
            capture_output=True,
            check=False,
            timeout=_STAGE_TIMEOUT_SECONDS,
        )


def get_index_stats() -> dict[str, int]:
    """Get statistics about the index."""
    index = _load_index()
    return {
        "total_entries": len(index.get("entries", {})),
        "total_hashes": len(index.get("hashes", {})),
        "urls": sum(1 for e in index.get("entries", {}).values() if "url" in e),
        "local_docs": sum(1 for e in index.get("entries", {}).values() if "path" in e),
    }
