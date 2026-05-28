"""Tests for the capture-index incorporation engine.

The promoter drains the inert backlog. ``propose_promotions`` is a pure
function that classifies each ``pending`` entry into promote, archive,
or hold and returns the proposed field changes without writing anything.
``apply_promotions`` is the imperative shell: it backs up the index,
applies the changes, and persists atomically. Re-running must be a
no-op (idempotent).
"""

from __future__ import annotations

import copy
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
import yaml

from memory_palace.corpus.index_promoter import (
    Proposal,
    apply_orphan_prunes,
    apply_promotions,
    propose_orphan_prunes,
    propose_promotions,
)


def _iso(days_ago: float) -> str:
    """Return an ISO timestamp ``days_ago`` days before now (UTC)."""
    return (datetime.now(timezone.utc) - timedelta(days=days_ago)).isoformat()


def _entry(**overrides: object) -> dict:
    """Build a capture entry at the inert defaults, with overrides."""
    base = {
        "content_hash": "sha256:0000",
        "stored_at": "data/staging/x.md",
        "importance_score": 50,
        "last_updated": _iso(1),
        "title": "Untitled",
        "maturity": "seedling",
        "routing_type": "pending",
        "url": "https://example.com/x",
    }
    base.update(overrides)
    return base


@pytest.fixture
def sample_index() -> dict:
    """Build an index spanning promote, hold, archive, and skip cases."""
    return {
        "entries": {
            # Recent + authoritative -> promote.
            "https://github.com/acme/recent": _entry(
                content_hash="sha256:aaaa",
                stored_at="data/staging/recent.md",
                last_updated=_iso(2),
                title="Recent Repo",
                url="https://github.com/acme/recent",
            ),
            # Old, low authority, singleton cluster -> hold.
            "https://obscure.example/old": _entry(
                content_hash="sha256:bbbb",
                stored_at="data/staging/old.md",
                last_updated=_iso(150),
                title="Old Obscure Page",
                url="https://obscure.example/old",
            ),
            # Backing file missing -> archive (orphan), despite recency.
            "https://example.com/orphan": _entry(
                content_hash="sha256:cccc",
                stored_at="data/staging/missing.md",
                last_updated=_iso(1),
                title="Vanished",
                url="https://example.com/orphan",
            ),
            # Ancient capture -> archive (age).
            "https://old.example/ancient": _entry(
                content_hash="sha256:dddd",
                stored_at="data/staging/ancient.md",
                last_updated=_iso(300),
                title="Ancient",
                url="https://old.example/ancient",
            ),
            # Already promoted -> never touched.
            "https://docs.litellm.ai/meta": _entry(
                content_hash="sha256:eeee",
                stored_at="data/staging/meta.md",
                importance_score=82,
                last_updated=_iso(5),
                title="Promoted Meta",
                maturity="growing",
                routing_type="meta",
                url="https://docs.litellm.ai/meta",
            ),
        },
        "hashes": {},
    }


@pytest.fixture
def plugin_root_with_files(tmp_path: Path) -> Path:
    """Create a plugin root where every stored_at exists except the orphan."""
    staging = tmp_path / "data" / "staging"
    staging.mkdir(parents=True)
    for name in ("recent.md", "old.md", "ancient.md", "meta.md"):
        (staging / name).write_text("stub", encoding="utf-8")
    # missing.md intentionally absent -> one orphan.
    return tmp_path


def _by_key(proposals: list[Proposal]) -> dict[str, Proposal]:
    return {p.key: p for p in proposals}


class TestProposePromotions:
    """The pure classification step."""

    def test_promotes_recent_authoritative(self, sample_index: dict) -> None:
        """A recent, authoritative pending entry is promoted."""
        proposals = _by_key(propose_promotions(sample_index))
        recent = proposals["https://github.com/acme/recent"]
        assert recent.action == "promote"
        assert recent.changes["maturity"] == "growing"
        assert recent.changes["routing_type"] == "meta"
        assert recent.changes["importance_score"] > 50

    def test_archives_orphan(
        self, sample_index: dict, plugin_root_with_files: Path
    ) -> None:
        """An entry whose backing file is gone is archived."""
        proposals = _by_key(
            propose_promotions(sample_index, plugin_root=plugin_root_with_files)
        )
        orphan = proposals["https://example.com/orphan"]
        assert orphan.action == "archive"
        assert orphan.changes["routing_type"] == "archived"

    def test_archives_ancient(self, sample_index: dict) -> None:
        """A very old capture is archived even without a plugin root."""
        proposals = _by_key(propose_promotions(sample_index))
        assert proposals["https://old.example/ancient"].action == "archive"

    def test_holds_low_score(self, sample_index: dict) -> None:
        """A middling pending entry is held (no proposal emitted)."""
        proposals = _by_key(propose_promotions(sample_index))
        assert "https://obscure.example/old" not in proposals

    def test_skips_non_pending(self, sample_index: dict) -> None:
        """Already-promoted entries are never proposed."""
        proposals = _by_key(propose_promotions(sample_index))
        assert "https://docs.litellm.ai/meta" not in proposals

    def test_does_not_mutate_index(self, sample_index: dict) -> None:
        """Proposing changes nothing in the input index."""
        before = copy.deepcopy(sample_index)
        propose_promotions(sample_index)
        assert sample_index == before

    def test_importance_scores_within_bounds(self, sample_index: dict) -> None:
        """Every proposed importance score stays in [0, 100]."""
        for proposal in propose_promotions(sample_index):
            if "importance_score" in proposal.changes:
                assert 0 <= proposal.changes["importance_score"] <= 100


class TestApplyPromotions:
    """The imperative shell: backup, apply, persist."""

    def _write_index(self, tmp_path: Path, index: dict) -> Path:
        index_path = tmp_path / "memory-palace-index.yaml"
        index_path.write_text(yaml.safe_dump(index), encoding="utf-8")
        return index_path

    def test_creates_backup_and_mutates(
        self, sample_index: dict, plugin_root_with_files: Path
    ) -> None:
        """Apply backs up the index, then writes the proposed changes."""
        index_path = self._write_index(plugin_root_with_files, sample_index)
        backup_dir = plugin_root_with_files / "data" / "backups"
        proposals = propose_promotions(sample_index, plugin_root=plugin_root_with_files)

        result = apply_promotions(proposals, index_path, backup_dir=backup_dir)

        assert result.backup_path.exists()
        assert result.applied == len(proposals)
        reloaded = yaml.safe_load(index_path.read_text(encoding="utf-8"))
        entries = reloaded["entries"]
        assert entries["https://github.com/acme/recent"]["routing_type"] == "meta"
        assert entries["https://github.com/acme/recent"]["maturity"] == "growing"
        assert entries["https://example.com/orphan"]["routing_type"] == "archived"
        # A held entry is untouched.
        assert entries["https://obscure.example/old"]["routing_type"] == "pending"

    def test_is_idempotent(
        self, sample_index: dict, plugin_root_with_files: Path
    ) -> None:
        """Re-proposing after apply yields no further actions."""
        index_path = self._write_index(plugin_root_with_files, sample_index)
        backup_dir = plugin_root_with_files / "data" / "backups"
        proposals = propose_promotions(sample_index, plugin_root=plugin_root_with_files)
        apply_promotions(proposals, index_path, backup_dir=backup_dir)

        reloaded = yaml.safe_load(index_path.read_text(encoding="utf-8"))
        again = propose_promotions(reloaded, plugin_root=plugin_root_with_files)
        assert again == []


class TestOrphanPrune:
    """Hard-delete orphaned entries (record-shells with missing files)."""

    def _write_index(self, tmp_path: Path, index: dict) -> Path:
        index_path = tmp_path / "memory-palace-index.yaml"
        index_path.write_text(yaml.safe_dump(index), encoding="utf-8")
        return index_path

    def test_proposes_only_entries_with_missing_files(
        self, sample_index: dict, plugin_root_with_files: Path
    ) -> None:
        """Returns keys for entries whose backing file is gone."""
        keys = propose_orphan_prunes(sample_index, plugin_root_with_files)
        assert keys == ["https://example.com/orphan"]

    def test_no_plugin_root_proposes_nothing(self, sample_index: dict) -> None:
        """Without a plugin_root, orphan detection is skipped (safety default)."""
        assert propose_orphan_prunes(sample_index, None) == []

    def test_apply_deletes_entries_and_hashes_with_backup(
        self, plugin_root_with_files: Path
    ) -> None:
        """Apply removes both entry and hash; backup exists; idempotent."""
        index = {
            "entries": {
                "https://keep.example/x": _entry(
                    content_hash="sha256:keep",
                    stored_at="data/staging/recent.md",
                    url="https://keep.example/x",
                ),
                "https://gone.example/y": _entry(
                    content_hash="sha256:gone",
                    stored_at="data/staging/missing.md",
                    url="https://gone.example/y",
                ),
            },
            "hashes": {
                "sha256:keep": "data/staging/recent.md",
                "sha256:gone": "data/staging/missing.md",
            },
        }
        index_path = self._write_index(plugin_root_with_files, index)
        backup_dir = plugin_root_with_files / "data" / "backups"

        keys = propose_orphan_prunes(index, plugin_root_with_files)
        result = apply_orphan_prunes(keys, index_path, backup_dir=backup_dir)

        assert result.applied == 1
        assert result.backup_path.exists()
        reloaded = yaml.safe_load(index_path.read_text(encoding="utf-8"))
        assert "https://gone.example/y" not in reloaded["entries"]
        assert "sha256:gone" not in reloaded["hashes"]
        assert "https://keep.example/x" in reloaded["entries"]
        assert "sha256:keep" in reloaded["hashes"]
        # Idempotent: nothing left to prune.
        assert propose_orphan_prunes(reloaded, plugin_root_with_files) == []
