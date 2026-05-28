"""Tests for read-only analytics over the capture index.

The capture index (``hooks/memory-palace-index.yaml``) is a URL-keyed
log of auto-captured web content. These tests pin the analysis layer
that turns that write-only buffer into observable metrics: corpus
statistics, inert-entry detection, orphan detection, topic clustering,
staleness (via the existing DecayModel), and promotion-candidate
ranking.

The analysis layer mutates nothing.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
import yaml

from memory_palace.corpus.index_analytics import (
    CorpusStats,
    PromotionCandidate,
    cluster_by_domain,
    corpus_stats,
    load_capture_index,
    rank_promotion_candidates,
    staleness_report,
)


def _iso(days_ago: float) -> str:
    """ISO timestamp ``days_ago`` days before now (UTC)."""
    return (datetime.now(timezone.utc) - timedelta(days=days_ago)).isoformat()


@pytest.fixture
def sample_index() -> dict:
    """Build a small synthetic capture index covering interesting cases."""
    return {
        "entries": {
            # Two inert seedlings sharing the github.com domain (a cluster).
            "https://github.com/bevyengine/bevy": {
                "content_hash": "sha256:aaaa",
                "stored_at": "data/staging/bevy.md",
                "importance_score": 50,
                "last_updated": _iso(60),
                "title": "Bevy Engine README",
                "maturity": "seedling",
                "routing_type": "pending",
                "url": "https://github.com/bevyengine/bevy",
            },
            "https://github.com/not-fl3/macroquad": {
                "content_hash": "sha256:bbbb",
                "stored_at": "data/staging/macroquad.md",
                "importance_score": 50,
                "last_updated": _iso(2),
                "title": "Macroquad README",
                "maturity": "seedling",
                "routing_type": "pending",
                "url": "https://github.com/not-fl3/macroquad",
            },
            # A promoted (non-inert) entry.
            "https://docs.litellm.ai/blog/x": {
                "content_hash": "sha256:cccc",
                "stored_at": "data/staging/litellm.md",
                "importance_score": 82,
                "last_updated": _iso(5),
                "title": "LiteLLM Security Update",
                "maturity": "growing",
                "routing_type": "meta",
                "url": "https://docs.litellm.ai/blog/x",
            },
            # An orphan: stored_at points at a file that will not exist.
            "https://example.com/gone": {
                "content_hash": "sha256:dddd",
                "stored_at": "data/staging/this-file-does-not-exist.md",
                "importance_score": 50,
                "last_updated": _iso(1),
                "title": "Vanished Article",
                "maturity": "seedling",
                "routing_type": "pending",
                "url": "https://example.com/gone",
            },
        },
        "hashes": {
            "sha256:aaaa": "data/staging/bevy.md",
            "sha256:bbbb": "data/staging/macroquad.md",
            "sha256:cccc": "data/staging/litellm.md",
            "sha256:dddd": "data/staging/this-file-does-not-exist.md",
        },
    }


@pytest.fixture
def plugin_root_with_files(tmp_path: Path) -> Path:
    """Create a fake plugin root where 3 of the 4 stored_at files exist."""
    staging = tmp_path / "data" / "staging"
    staging.mkdir(parents=True)
    for name in ("bevy.md", "macroquad.md", "litellm.md"):
        (staging / name).write_text("stub", encoding="utf-8")
    # Intentionally omit this-file-does-not-exist.md -> one orphan.
    return tmp_path


class TestLoadCaptureIndex:
    """Loading the YAML index from disk."""

    def test_parses_entries_and_hashes(self, tmp_path: Path) -> None:
        """Loads a real YAML file into entries + hashes dicts."""
        index_path = tmp_path / "memory-palace-index.yaml"
        index_path.write_text(
            yaml.safe_dump(
                {
                    "entries": {"https://x.test": {"importance_score": 50}},
                    "hashes": {"sha256:zz": "data/staging/x.md"},
                }
            ),
            encoding="utf-8",
        )
        index = load_capture_index(index_path)
        assert "https://x.test" in index["entries"]
        assert index["hashes"]["sha256:zz"] == "data/staging/x.md"

    def test_missing_file_returns_empty_index(self, tmp_path: Path) -> None:
        """A missing index yields the empty sentinel, not an exception."""
        index = load_capture_index(tmp_path / "nope.yaml")
        assert index == {"entries": {}, "hashes": {}}


class TestCorpusStats:
    """Aggregate statistics over the index."""

    def test_counts_by_dimension(self, sample_index: dict) -> None:
        """Counts entries by routing_type and maturity."""
        stats = corpus_stats(sample_index)
        assert isinstance(stats, CorpusStats)
        assert stats.total == 4
        assert stats.by_routing_type["pending"] == 3
        assert stats.by_routing_type["meta"] == 1
        assert stats.by_maturity["seedling"] == 3
        assert stats.by_maturity["growing"] == 1

    def test_detects_inert_entries(self, sample_index: dict) -> None:
        """Inert == pending AND seedling AND importance 50."""
        stats = corpus_stats(sample_index)
        # 3 pending seedlings at score 50 are inert; the growing/meta is not.
        assert stats.inert_count == 3
        assert stats.inert_ratio == pytest.approx(0.75)

    def test_flags_orphans(
        self, sample_index: dict, plugin_root_with_files: Path
    ) -> None:
        """Entries whose stored_at file is missing are orphans."""
        stats = corpus_stats(sample_index, plugin_root=plugin_root_with_files)
        assert stats.orphan_count == 1

    def test_no_orphan_check_without_root(self, sample_index: dict) -> None:
        """Without a plugin_root, orphan_count is 0 (check skipped)."""
        stats = corpus_stats(sample_index)
        assert stats.orphan_count == 0


class TestClusterByDomain:
    """Topic clustering by URL domain."""

    def test_groups_entries_by_domain(self, sample_index: dict) -> None:
        """Two github.com entries land in the same cluster."""
        clusters = cluster_by_domain(sample_index)
        assert set(clusters["github.com"]) == {
            "https://github.com/bevyengine/bevy",
            "https://github.com/not-fl3/macroquad",
        }
        assert clusters["docs.litellm.ai"] == ["https://docs.litellm.ai/blog/x"]


class TestStalenessReport:
    """Staleness via the existing DecayModel."""

    def test_old_seedling_is_not_fresh(self, sample_index: dict) -> None:
        """A 60-day-old seedling (14d half-life) is past fresh."""
        report = {s.entry_id: s for s in staleness_report(sample_index)}
        old = report["https://github.com/bevyengine/bevy"]
        assert old.status != "fresh"
        fresh = report["https://github.com/not-fl3/macroquad"]
        assert fresh.status == "fresh"


class TestRankPromotionCandidates:
    """Ranking pending entries worth incorporating."""

    def test_only_pending_entries_ranked(self, sample_index: dict) -> None:
        """The promoted (meta) entry is never a candidate."""
        candidates = rank_promotion_candidates(sample_index)
        keys = {c.key for c in candidates}
        assert "https://docs.litellm.ai/blog/x" not in keys
        assert all(isinstance(c, PromotionCandidate) for c in candidates)
        assert keys  # at least one pending candidate

    def test_sorted_by_score_descending(self, sample_index: dict) -> None:
        """Candidates are returned best-first."""
        candidates = rank_promotion_candidates(sample_index)
        scores = [c.score for c in candidates]
        assert scores == sorted(scores, reverse=True)

    def test_limit_caps_results(self, sample_index: dict) -> None:
        """The limit argument bounds the candidate list."""
        candidates = rank_promotion_candidates(sample_index, limit=1)
        assert len(candidates) == 1
