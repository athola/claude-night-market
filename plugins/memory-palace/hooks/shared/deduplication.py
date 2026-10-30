"""Deduplication and index management for memory-palace.

Uses fast hashing and in-memory caching for performance.
Implements atomic writes for data integrity.
"""

from __future__ import annotations

import contextlib
import hashlib
import os
import subprocess
import sys
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

from memory_palace._vendored_leyline_atomic_file import write_atomic
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
# True while the cached index stands in for a file that failed to parse.
# update_index reads it to set that file aside before writing.
_index_load_failed = False
_warned_no_yaml = False

# Ceiling on the staging call. `git add` on one file is milliseconds;
# anything near this bound is a lock being held, and a capture waits for
# no one.
#: Budget for the ``git add`` this module runs.
#:
#: This was 5, equal to the 5s cap the registering hooks declare in
#: hooks.json, leaving zero margin for the fetch, the safety checks and the
#: yaml write that already ran in the same invocation. A hook killed at the
#: cap has done its work and recorded none of it.
_STAGE_TIMEOUT_SECONDS = 1.5


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


_TRACKING_PARAMS = frozenset({"utm_source", "utm_medium", "utm_campaign", "ref"})


def get_url_key(url: str) -> str:
    """Normalize URL for consistent keying."""
    # Fragment first: a trailing slash before "#" is still a trailing slash.
    url = url.split("#", 1)[0]

    # Remove common tracking parameters, rebuilding the query so the
    # first surviving parameter keeps the "?" separator.
    base, has_query, query = url.partition("?")
    if has_query:
        kept = [
            pair
            for pair in query.split("&")
            if pair and pair.split("=", 1)[0] not in _TRACKING_PARAMS
        ]
        url = f"{base}?{'&'.join(kept)}" if kept else base

    # Scheme and host are case-insensitive; a path or query may not be
    # (a video id, a base64 token), so folding it merged distinct pages.
    # A string with no scheme is folded whole, since its host cannot be
    # told apart from its path.
    scheme, sep, rest = url.rstrip("/").partition("://")
    if not sep:
        return scheme.lower()
    host = rest.split("/", 1)[0].split("?", 1)[0]
    return f"{scheme.lower()}://{host.lower()}{rest[len(host) :]}"


def _legacy_url_key(url: str) -> str:
    """Return the key older index entries were stored under.

    Before path and query case were kept, the whole normalized URL was
    lowercased. Lookups try this key too, so existing entries are not
    orphaned and re-captured as duplicates.
    """
    return get_url_key(url).lower()


def _warn_no_yaml_once() -> None:
    """Tell the operator once per process that captures are not persisted."""
    global _warned_no_yaml  # noqa: PLW0603 - once-per-process latch
    if not _warned_no_yaml:
        _warned_no_yaml = True
        print(
            "[memory-palace] WARNING: PyYAML is not installed; dedup "
            "persistence is off and the capture index is neither read nor "
            "written.",
            file=sys.stderr,
        )


def _set_aside_corrupt_index(index_path: Path) -> None:
    """Rename an unparsable index to a timestamped sibling and say where.

    Renaming rather than refusing the write keeps captures persisting,
    and keeps the unreadable bytes for a person to repair or merge.
    """
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    target = index_path.with_name(f"{index_path.name}.corrupt-{stamp}")
    os.replace(index_path, target)
    print(
        f"[memory-palace] WARNING: moved unparsable index to {target}; "
        f"starting a fresh index at {index_path}.",
        file=sys.stderr,
    )


def _load_index() -> dict[str, Any]:
    """Load index from disk with caching."""
    global _index_cache, _index_mtime, _index_load_failed  # noqa: PLW0603 - module-level cache requires global for mtime-based invalidation

    if yaml is None:
        _warn_no_yaml_once()

    index_path = _get_index_path()

    try:
        current_mtime = index_path.stat().st_mtime

        if _index_cache is not None and current_mtime <= _index_mtime:
            return _index_cache

        if yaml is None:
            _index_cache = {"entries": {}, "hashes": {}}
            return _index_cache

        _index_load_failed = False
        try:
            with open(index_path) as f:
                _index_cache = yaml.safe_load(f) or {"entries": {}, "hashes": {}}
        except yaml.YAMLError as exc:
            # Issue #528: a corrupt index file must not take down web-research
            # store calls. Reads proceed on an empty index and leave the file
            # alone. The next update_index moves the file aside before writing,
            # so the unparsable entries are never overwritten.
            print(
                f"[memory-palace] WARNING: corrupt YAML index at "
                f"{index_path}: {exc}; using an empty index. The next "
                f"capture moves the file to a .corrupt-<timestamp> sibling.",
                file=sys.stderr,
            )
            _index_load_failed = True
            _index_cache = {"entries": {}, "hashes": {}}
            _index_mtime = current_mtime
            return _index_cache

        # validate required keys exist
        _index_cache.setdefault("entries", {})
        _index_cache.setdefault("hashes", {})

        _index_mtime = current_mtime
        return _index_cache

    except FileNotFoundError:
        _index_load_failed = False
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
        entries = index.get("entries", {})
        if get_url_key(url) in entries or _legacy_url_key(url) in entries:
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
        entries = index.get("entries", {})
        entry = entries.get(get_url_key(url)) or entries.get(_legacy_url_key(url))
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

    global _index_cache, _index_mtime, _index_load_failed  # noqa: PLW0603 - invalidate module-level cache after disk write

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
        _warn_no_yaml_once()
        _index_cache = index
        return

    index_path = _get_index_path()
    index_path.parent.mkdir(parents=True, exist_ok=True)
    if _index_load_failed:
        _set_aside_corrupt_index(index_path)
        _index_load_failed = False

    write_atomic(
        index_path, yaml.safe_dump(index, default_flow_style=False, sort_keys=False)
    )

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
