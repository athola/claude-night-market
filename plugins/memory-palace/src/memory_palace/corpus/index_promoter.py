"""Incorporation engine for the capture index.

Drains the inert backlog in ``hooks/memory-palace-index.yaml`` by
classifying each ``pending`` entry into one of three actions:

- **promote**: a recent, authoritative, or clustered capture worth
  keeping. Assigns a real importance score, a routing type, and bumps
  maturity ``seedling -> growing``.
- **archive**: an orphaned capture (its backing file is gone) or an
  ancient one that was never revisited. Following the research finding
  that unused notes should drain rather than accumulate, these are
  marked ``archived`` instead of promoted.
- **hold**: everything else stays ``pending`` and emits no proposal.

:func:`propose_promotions` is pure (it writes nothing). It reuses the
structural ranking from
:mod:`memory_palace.corpus.index_analytics` so the promote signal is
identical to what the read-only report shows. :func:`apply_promotions`
is the imperative shell: it backs up the index, applies the proposed
changes in place, and persists atomically. Applying is idempotent
because promoted and archived entries are no longer ``pending``.
"""

from __future__ import annotations

import contextlib
import logging
import os
import shutil
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover - yaml is a hard runtime dep
    yaml = None  # type: ignore[assignment]  # optional-import fallback sentinel

from memory_palace.corpus.index_analytics import (
    INERT_ROUTING_TYPE,
    _parse_timestamp,
    load_capture_index,
    rank_promotion_candidates,
)

logger = logging.getLogger(__name__)

# A pending entry scoring at or above this is promoted; below, it holds.
PROMOTE_THRESHOLD = 0.5
# Pending captures older than this (days) are archived, not promoted.
ARCHIVE_AGE_DAYS = 180
# Routing-type sentinel for entries drained out of the active corpus.
ARCHIVED_ROUTING_TYPE = "archived"
# Importance scale: a perfect promotion score maps to this ceiling.
_IMPORTANCE_FLOOR = 50
_IMPORTANCE_SPAN = 50


@dataclass
class Proposal:
    """A single proposed change to one index entry."""

    key: str
    action: str  # "promote" | "archive"
    changes: dict[str, Any]
    reasons: list[str] = field(default_factory=list)


@dataclass
class ApplyResult:
    """Outcome of applying a batch of proposals."""

    applied: int
    backup_path: Path


def _is_orphan(entry: dict[str, Any], plugin_root: Path | None) -> bool:
    """Return True when the entry's backing file is missing."""
    if plugin_root is None:
        return False
    stored_at = entry.get("stored_at")
    if not stored_at:
        return False
    return not (plugin_root / str(stored_at)).exists()


def propose_promotions(
    index: dict[str, Any], plugin_root: Path | None = None
) -> list[Proposal]:
    """Classify pending entries into promote/archive proposals.

    Pure: the input index is never mutated and nothing is written. Held
    entries (middling score, not stale, not orphaned) emit no proposal.

    Args:
        index: A loaded index dict with ``entries`` and ``hashes``.
        plugin_root: When given, used to detect orphaned ``stored_at``
            files. When ``None`` the orphan check is skipped (age-based
            archival still applies).

    """
    entries = index.get("entries", {})
    scores = {c.key: c.score for c in rank_promotion_candidates(index)}
    now = datetime.now(timezone.utc)

    proposals: list[Proposal] = []
    for key, entry in entries.items():
        if entry.get("routing_type") != INERT_ROUTING_TYPE:
            continue

        orphan = _is_orphan(entry, plugin_root)
        age_days = (now - _parse_timestamp(entry.get("last_updated"))).days
        if orphan or age_days >= ARCHIVE_AGE_DAYS:
            reason = (
                "orphan: backing file missing"
                if orphan
                else f"stale: {age_days}d since capture"
            )
            proposals.append(
                Proposal(
                    key=key,
                    action="archive",
                    changes={"routing_type": ARCHIVED_ROUTING_TYPE},
                    reasons=[reason],
                )
            )
            continue

        score = scores.get(key, 0.0)
        if score >= PROMOTE_THRESHOLD:
            importance = min(
                100, _IMPORTANCE_FLOOR + int(round(score * _IMPORTANCE_SPAN))
            )
            # Web captures (url-keyed) are general knowledge -> meta;
            # local docs (path-keyed) are project-scoped -> local.
            routing = "local" if entry.get("path") and not entry.get("url") else "meta"
            proposals.append(
                Proposal(
                    key=key,
                    action="promote",
                    changes={
                        "importance_score": importance,
                        "routing_type": routing,
                        "maturity": "growing",
                    },
                    reasons=[
                        f"score={score:.2f}",
                        f"importance {entry.get('importance_score', 50)}->{importance}",
                    ],
                )
            )
        # else: hold -> no proposal

    return proposals


def _write_index_atomic(index: dict[str, Any], index_path: Path) -> None:
    """Persist the index via tempfile + os.replace (atomic on POSIX).

    The src package must stay independent of the hook runtime, so this
    mirrors the hook-side writer rather than importing it across the
    ``hooks/`` and ``src/`` import-root boundary.
    """
    if yaml is None:  # pragma: no cover - yaml is a hard runtime dep
        msg = "PyYAML is required to write the capture index"
        raise RuntimeError(msg)
    index_path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(
        suffix=".tmp", prefix="memory-palace-index-", dir=index_path.parent
    )
    try:
        with os.fdopen(fd, "w") as handle:
            yaml.safe_dump(index, handle, default_flow_style=False, sort_keys=False)
        os.replace(tmp_path, index_path)
    except Exception:
        with contextlib.suppress(OSError):
            os.unlink(tmp_path)
        raise


def apply_promotions(
    proposals: list[Proposal],
    index_path: Path,
    *,
    backup_dir: Path,
) -> ApplyResult:
    """Back up the index, apply proposals in place, and persist.

    Args:
        proposals: Promote/archive proposals from
            :func:`propose_promotions`.
        index_path: Path to the YAML index to mutate.
        backup_dir: Directory to write a timestamped backup into before
            any change is persisted.

    Returns:
        An :class:`ApplyResult` with the count applied and the backup
        path. Re-running with freshly proposed changes is a no-op.

    """
    index_path = Path(index_path)
    backup_dir = Path(backup_dir)
    backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_path = backup_dir / f"memory-palace-index-{timestamp}.yaml"
    if index_path.exists():
        shutil.copyfile(index_path, backup_path)

    index = load_capture_index(index_path)
    entries = index.get("entries", {})

    applied = 0
    for proposal in proposals:
        entry = entries.get(proposal.key)
        if entry is None:
            logger.warning("Proposal key not in index, skipping: %s", proposal.key)
            continue
        entry.update(proposal.changes)
        applied += 1

    _write_index_atomic(index, index_path)
    return ApplyResult(applied=applied, backup_path=backup_path)


def propose_orphan_prunes(index: dict[str, Any], plugin_root: Path | None) -> list[str]:
    """Return entry keys whose backing ``stored_at`` file is missing.

    Unlike ``propose_promotions``, this targets any entry (including
    archived ones), because an orphan record-shell carries no useful
    information regardless of routing_type. Returns an empty list when
    ``plugin_root`` is ``None`` so the function fails closed and never
    proposes destructive prunes without a root to check against.
    """
    if plugin_root is None:
        return []
    return [
        key
        for key, entry in index.get("entries", {}).items()
        if _is_orphan(entry, plugin_root)
    ]


def apply_orphan_prunes(
    keys: list[str],
    index_path: Path,
    *,
    backup_dir: Path,
) -> ApplyResult:
    """Hard-delete the listed entries plus their unreferenced hash mappings.

    Takes a timestamped backup before any change. A hash mapping is
    removed alongside its entry so a stale mapping pointing at a deleted
    file cannot re-trigger dedup confusion later, but only once no
    surviving entry still references that content: several URLs may share
    a single capture, and the mapping is what tells the survivors their
    content is already stored.
    """
    index_path = Path(index_path)
    backup_dir = Path(backup_dir)
    backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_path = backup_dir / f"memory-palace-index-prune-{timestamp}.yaml"
    if index_path.exists():
        shutil.copyfile(index_path, backup_path)

    index = load_capture_index(index_path)
    entries = index.get("entries", {})
    hashes = index.get("hashes", {})

    applied = 0
    for key in keys:
        entry = entries.pop(key, None)
        if entry is None:
            continue
        applied += 1
        # Drop the hash mapping only when no surviving entry still points
        # at this content. Two URLs can share one capture, and for the
        # survivor that mapping is its dedup memory: removing it makes
        # content already on disk look unseen, so the next fetch stores
        # a second copy.
        content_hash = entry.get("content_hash")
        still_referenced = any(
            other.get("content_hash") == content_hash for other in entries.values()
        )
        if content_hash and not still_referenced:
            hashes.pop(content_hash, None)

    _write_index_atomic(index, index_path)
    return ApplyResult(applied=applied, backup_path=backup_path)
