"""Deduplication and index management for memory-palace.

Uses fast hashing and in-memory caching for performance.
Implements atomic writes for data integrity.
"""

from __future__ import annotations

import contextlib
import hashlib
import os
import re
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

import yaml

if TYPE_CHECKING:
    from typing import Any

# Try to use xxhash for speed, fall back to hashlib
try:
    import xxhash

    _USE_XXHASH = True
except ImportError:
    _USE_XXHASH = False

# Index cache
_index_cache: dict[str, Any] | None = None
_index_mtime: float = 0


def _get_index_path() -> Path:
    """Get path to index file."""
    plugin_root = Path(__file__).parent.parent
    return plugin_root / "memory-palace-index.yaml"


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
    global _index_cache, _index_mtime

    index_path = _get_index_path()

    try:
        current_mtime = index_path.stat().st_mtime

        if _index_cache is not None and current_mtime <= _index_mtime:
            return _index_cache

        with open(index_path) as f:
            _index_cache = yaml.safe_load(f) or {"entries": {}, "hashes": {}}

        # Ensure required keys exist
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


def get_entry(url: str | None = None, path: str | None = None) -> dict[str, Any] | None:
    """Get existing entry details for comparison."""
    index = _load_index()

    if url:
        url_key = get_url_key(url)
        return index.get("entries", {}).get(url_key)

    if path:
        path_key = str(Path(path).resolve())
        return index.get("entries", {}).get(path_key)

    return None


def needs_update(
    content_hash: str, url: str | None = None, path: str | None = None
) -> bool:
    """Check if existing entry needs update (content changed)."""
    entry = get_entry(url=url, path=path)

    if not entry:
        return True  # Not indexed yet

    return entry.get("content_hash") != content_hash


def update_index(
    content_hash: str,
    stored_at: str,
    importance_score: int,
    url: str | None = None,
    path: str | None = None,
    title: str | None = None,
    maturity: str | None = None,
    routing_type: str | None = None,
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

    Note: This does write to disk - use sparingly.

    """
    global _index_cache

    index = _load_index()
    now = datetime.now(UTC).isoformat()

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

    if url:
        url_key = get_url_key(url)
        entry["url"] = url
        index["entries"][url_key] = entry
    elif path:
        path_key = str(Path(path).resolve())
        entry["path"] = path
        index["entries"][path_key] = entry

    # Also index by hash for fast lookup
    index["hashes"][content_hash] = stored_at

    # Atomic write back using tempfile + rename
    index_path = _get_index_path()
    index_path.parent.mkdir(parents=True, exist_ok=True)

    # Write to temp file in same directory (ensures same filesystem for atomic rename)
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

    # Update cache
    _index_cache = index
    _index_mtime = index_path.stat().st_mtime


def get_index_stats() -> dict[str, int]:
    """Get statistics about the index."""
    index = _load_index()
    return {
        "total_entries": len(index.get("entries", {})),
        "total_hashes": len(index.get("hashes", {})),
        "urls": sum(1 for e in index.get("entries", {}).values() if "url" in e),
        "local_docs": sum(1 for e in index.get("entries", {}).values() if "path" in e),
    }
