"""Read-only analytics over the capture index.

The capture index (``hooks/memory-palace-index.yaml``) is a URL-keyed
log of auto-captured web content produced by the web-research hooks.
Historically nothing reads it except the deduplication layer, so the
vast majority of entries sit inert at their capture defaults
(``routing_type: pending``, ``maturity: seedling``,
``importance_score: 50``).

This module turns that write-only buffer into observable metrics. It
reuses the existing :class:`~memory_palace.corpus.decay_model.DecayModel`
for staleness so the analysis layer stays consistent with the rest of
the corpus tooling. Every function here is read-only: nothing in this
module writes to disk.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any
from urllib.parse import urlparse

try:
    import yaml
except ImportError:  # pragma: no cover - yaml is a hard runtime dep
    yaml = None  # type: ignore[assignment]  # optional-import fallback sentinel

from memory_palace.corpus.decay_model import DecayModel

if TYPE_CHECKING:
    from memory_palace.corpus.decay_model import DecayState

logger = logging.getLogger(__name__)

# The capture defaults that mark an entry as never-processed ("inert").
INERT_ROUTING_TYPE = "pending"
INERT_MATURITY = "seedling"
INERT_IMPORTANCE_SCORE = 50

# URL domains we treat as higher-authority sources when ranking.
_AUTHORITY_DOMAINS = (
    "github.com",
    "arxiv.org",
    "stackoverflow.com",
    "developer.mozilla.org",
)
_AUTHORITY_PREFIXES = ("docs.", "doc.", "developer.")

# Recency horizon (days) beyond which a capture earns no recency credit.
_RECENCY_HORIZON_DAYS = 180.0

# Upper bounds (inclusive) for the coarse importance-score buckets.
_BUCKET_LOW_MAX = 25
_BUCKET_MID_MAX = 50
_BUCKET_HIGH_MAX = 75


@dataclass
class CorpusStats:
    """Aggregate statistics over the capture index."""

    total: int
    by_routing_type: dict[str, int]
    by_maturity: dict[str, int]
    by_importance_bucket: dict[str, int]
    by_domain: dict[str, int]
    orphan_count: int
    inert_count: int

    @property
    def inert_ratio(self) -> float:
        """Fraction of entries still at their capture defaults."""
        return self.inert_count / self.total if self.total else 0.0


@dataclass
class PromotionCandidate:
    """A pending entry ranked as worth incorporating."""

    key: str
    title: str
    score: float
    reasons: list[str]


def load_capture_index(index_path: Path) -> dict[str, Any]:
    """Load the YAML capture index from disk.

    A missing or unreadable file yields the empty-index sentinel rather
    than raising, mirroring the resilience of the hook-side loader.
    """
    if not index_path.exists() or yaml is None:
        return {"entries": {}, "hashes": {}}
    try:
        with index_path.open(encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
    except (OSError, yaml.YAMLError):  # type: ignore[union-attr]  # yaml non-None when reached
        logger.warning("Could not read capture index at %s", index_path)
        return {"entries": {}, "hashes": {}}
    data.setdefault("entries", {})
    data.setdefault("hashes", {})
    return data


def _domain(url: str | None) -> str:
    """Extract a normalized domain from a URL, or ``(local)``."""
    if not url:
        return "(local)"
    netloc = urlparse(url).netloc.lower()
    return netloc.removeprefix("www.") or "(local)"


def _importance_bucket(score: int) -> str:
    """Bucket an importance score into a coarse band for reporting."""
    if score <= _BUCKET_LOW_MAX:
        return "0-25"
    if score <= _BUCKET_MID_MAX:
        return "26-50"
    if score <= _BUCKET_HIGH_MAX:
        return "51-75"
    return "76-100"


def _is_inert(entry: dict[str, Any]) -> bool:
    """Return True when an entry still carries every capture default."""
    return (
        entry.get("routing_type") == INERT_ROUTING_TYPE
        and entry.get("maturity") == INERT_MATURITY
        and entry.get("importance_score") == INERT_IMPORTANCE_SCORE
    )


def _parse_timestamp(value: Any) -> datetime:
    """Parse an ISO timestamp, defaulting to now (UTC) on failure."""
    if isinstance(value, datetime):
        dt = value
    else:
        try:
            dt = datetime.fromisoformat(str(value))
        except (TypeError, ValueError):
            return datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def corpus_stats(index: dict[str, Any], plugin_root: Path | None = None) -> CorpusStats:
    """Compute aggregate statistics over the capture index.

    Args:
        index: A loaded index dict with ``entries`` and ``hashes``.
        plugin_root: When given, ``stored_at`` paths are resolved
            relative to it to detect orphans (entries whose backing file
            no longer exists). When ``None`` the orphan check is skipped.

    """
    entries = index.get("entries", {})
    by_routing_type: dict[str, int] = {}
    by_maturity: dict[str, int] = {}
    by_importance_bucket: dict[str, int] = {}
    by_domain: dict[str, int] = {}
    orphan_count = 0
    inert_count = 0

    for entry in entries.values():
        routing = entry.get("routing_type", "(unset)")
        maturity = entry.get("maturity", "(unset)")
        score = int(entry.get("importance_score", 0))
        by_routing_type[routing] = by_routing_type.get(routing, 0) + 1
        by_maturity[maturity] = by_maturity.get(maturity, 0) + 1
        bucket = _importance_bucket(score)
        by_importance_bucket[bucket] = by_importance_bucket.get(bucket, 0) + 1
        domain = _domain(entry.get("url"))
        by_domain[domain] = by_domain.get(domain, 0) + 1

        if _is_inert(entry):
            inert_count += 1

        if plugin_root is not None:
            stored_at = entry.get("stored_at")
            if stored_at and not (plugin_root / stored_at).exists():
                orphan_count += 1

    return CorpusStats(
        total=len(entries),
        by_routing_type=by_routing_type,
        by_maturity=by_maturity,
        by_importance_bucket=by_importance_bucket,
        by_domain=by_domain,
        orphan_count=orphan_count,
        inert_count=inert_count,
    )


def cluster_by_domain(index: dict[str, Any]) -> dict[str, list[str]]:
    """Group entry keys by their URL domain.

    Domain is a cheap, deterministic proxy for topic that needs no model.
    Large clusters flag research themes worth consolidating into a single
    note.
    """
    clusters: dict[str, list[str]] = {}
    for key, entry in index.get("entries", {}).items():
        domain = _domain(entry.get("url"))
        clusters.setdefault(domain, []).append(key)
    return clusters


def staleness_report(index: dict[str, Any]) -> list[DecayState]:
    """Compute decay state for every entry, worst (most decayed) first.

    Delegates to :class:`DecayModel` so staleness here matches the
    maturity-aware half-lives used elsewhere in the corpus tooling.
    """
    model = DecayModel()
    states: list[DecayState] = []
    for key, entry in index.get("entries", {}).items():
        last_updated = _parse_timestamp(entry.get("last_updated"))
        maturity = entry.get("maturity", "growing")
        score = int(entry.get("importance_score", 0))
        states.append(
            model.calculate_decay(
                entry_id=key,
                maturity=maturity,
                last_validated=last_updated,
                importance_score=score,
            )
        )
    states.sort(key=lambda state: state.decay_factor)
    return states


def _recency_credit(last_updated: datetime) -> float:
    """Linear recency credit in [0, 1]; newer captures score higher."""
    days = max(0.0, (datetime.now(timezone.utc) - last_updated).days)
    return max(0.0, 1.0 - days / _RECENCY_HORIZON_DAYS)


def _domain_authority(domain: str) -> float:
    """Return authority credit in [0, 1] for a domain."""
    if domain in _AUTHORITY_DOMAINS:
        return 1.0
    if any(domain.startswith(prefix) for prefix in _AUTHORITY_PREFIXES):
        return 0.8
    return 0.3


def rank_promotion_candidates(
    index: dict[str, Any], limit: int | None = None
) -> list[PromotionCandidate]:
    """Rank ``pending`` entries by how worth-incorporating they are.

    Uses only structural signals available in the index itself (recency,
    domain authority, and topic-cluster size), so the ranking is
    deterministic and needs no model. The importance/routing decisions
    that mutate the index live in the promotion engine, not here.
    """
    entries = index.get("entries", {})
    cluster_sizes = {
        domain: len(keys) for domain, keys in cluster_by_domain(index).items()
    }
    max_cluster = max(cluster_sizes.values(), default=1)

    candidates: list[PromotionCandidate] = []
    for key, entry in entries.items():
        if entry.get("routing_type") != INERT_ROUTING_TYPE:
            continue
        domain = _domain(entry.get("url"))
        recency = _recency_credit(_parse_timestamp(entry.get("last_updated")))
        authority = _domain_authority(domain)
        cluster_factor = cluster_sizes.get(domain, 1) / max_cluster

        score = 0.5 * recency + 0.3 * authority + 0.2 * cluster_factor
        reasons = [
            f"recency={recency:.2f}",
            f"authority={authority:.2f} ({domain})",
            f"cluster={cluster_sizes.get(domain, 1)}",
        ]
        candidates.append(
            PromotionCandidate(
                key=key,
                title=entry.get("title", key),
                score=round(score, 4),
                reasons=reasons,
            )
        )

    candidates.sort(key=lambda candidate: candidate.score, reverse=True)
    return candidates[:limit] if limit is not None else candidates
