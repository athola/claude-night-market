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
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
import yaml

# The wiring test needs the fetch hook, which lives outside the package.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "hooks"))
from web_research_handler import (  # noqa: E402 - needs the sys.path line above
    detect_null_capture,
)

from memory_palace.corpus import index_promoter
from memory_palace.corpus.index_promoter import (
    CorpusUnavailableError,
    Proposal,
    apply_orphan_prunes,
    apply_promotions,
    apply_title_repairs,
    propose_orphan_prunes,
    propose_promotions,
    propose_title_repairs,
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

    def test_entry_without_stored_at_is_not_orphan(self, tmp_path: Path) -> None:
        """An entry that never recorded a backing file is not an orphan.

        Orphan detection keys off a *missing* file at a known path. An
        entry with no ``stored_at`` has no path to check, so it must not
        be misclassified as orphaned (which would wrongly archive it).
        """
        index = {
            "entries": {
                "https://no-file.test": _entry(
                    stored_at="", url="https://no-file.test", last_updated=_iso(2)
                )
            },
            "hashes": {},
        }
        proposals = _by_key(propose_promotions(index, plugin_root=tmp_path))
        archived = proposals.get("https://no-file.test")
        assert archived is None or archived.action != "archive"

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

    def test_skips_proposal_for_key_absent_from_index(self, tmp_path: Path) -> None:
        """A stale proposal whose key is gone is skipped, not applied.

        Encodes the invariant: a proposal referencing an entry deleted
        since classification can never resurrect or corrupt the index.
        """
        index = {"entries": {"https://kept.test": _entry(url="https://kept.test")}}
        index_path = self._write_index(tmp_path, index)
        backup_dir = tmp_path / "backups"
        stale = Proposal(
            key="https://deleted.test",
            action="promote",
            changes={"routing_type": "meta"},
        )

        result = apply_promotions([stale], index_path, backup_dir=backup_dir)

        assert result.applied == 0
        reloaded = yaml.safe_load(index_path.read_text(encoding="utf-8"))
        assert "https://deleted.test" not in reloaded["entries"]
        assert reloaded["entries"]["https://kept.test"]["routing_type"] == "pending"

    def test_apply_without_existing_index_makes_no_backup(self, tmp_path: Path) -> None:
        """Applying against a missing index is a no-op with no backup copy."""
        index_path = tmp_path / "absent.yaml"
        backup_dir = tmp_path / "backups"

        result = apply_promotions([], index_path, backup_dir=backup_dir)

        assert result.applied == 0
        assert not result.backup_path.exists()

    def test_atomic_write_failure_leaves_no_temp_file(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """If the atomic replace fails, the temp file is cleaned and the
        error propagates -- a half-written index is never left behind.
        """
        index = {"entries": {"https://x.test": _entry(url="https://x.test")}}
        index_path = self._write_index(tmp_path, index)
        backup_dir = tmp_path / "backups"
        proposal = Proposal(
            key="https://x.test", action="promote", changes={"routing_type": "meta"}
        )

        def _boom(*_args: object) -> None:
            raise OSError("disk full")

        monkeypatch.setattr(index_promoter.os, "replace", _boom)

        with pytest.raises(OSError, match="disk full"):
            apply_promotions([proposal], index_path, backup_dir=backup_dir)

        leftovers = list(index_path.parent.glob("memory-palace-index-*.tmp"))
        assert leftovers == []


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

    def test_apply_keeps_hash_still_referenced_by_surviving_entry(
        self, plugin_root_with_files: Path
    ) -> None:
        """Pruning one of two entries that share content keeps the hash.

        ``hashes`` is the dedup memory: ``is_known(content_hash=...)`` is
        a membership test against it. When two URLs share one piece of
        content and only one is orphaned, dropping the hash mapping
        would leave the survivor's ``content_hash`` dangling and make
        its content look unseen, so the next fetch re-captures content
        already on disk.
        """
        shared = "sha256:shared"
        index = {
            "entries": {
                "https://keep.example/x": _entry(
                    content_hash=shared,
                    stored_at="data/staging/recent.md",
                    url="https://keep.example/x",
                ),
                "https://gone.example/y": _entry(
                    content_hash=shared,
                    stored_at="data/staging/missing.md",
                    url="https://gone.example/y",
                ),
            },
            "hashes": {shared: "data/staging/recent.md"},
        }
        index_path = self._write_index(plugin_root_with_files, index)
        backup_dir = plugin_root_with_files / "data" / "backups"

        keys = propose_orphan_prunes(index, plugin_root_with_files)
        assert keys == ["https://gone.example/y"]
        result = apply_orphan_prunes(keys, index_path, backup_dir=backup_dir)

        assert result.applied == 1
        reloaded = yaml.safe_load(index_path.read_text(encoding="utf-8"))
        assert "https://gone.example/y" not in reloaded["entries"]
        assert shared in reloaded["hashes"], (
            "hash dropped while a surviving entry still references it: dedup memory lost"
        )
        survivor = reloaded["entries"]["https://keep.example/x"]
        assert reloaded["hashes"][shared] == survivor["stored_at"]

    def test_apply_skips_keys_absent_from_index(self, tmp_path: Path) -> None:
        """Pruning a key that is no longer present is a safe no-op."""
        index = {
            "entries": {"https://kept.test": _entry(url="https://kept.test")},
            "hashes": {"sha256:0000": "data/staging/x.md"},
        }
        index_path = self._write_index(tmp_path, index)
        backup_dir = tmp_path / "backups"

        result = apply_orphan_prunes(
            ["https://already-gone.test"], index_path, backup_dir=backup_dir
        )

        assert result.applied == 0
        reloaded = yaml.safe_load(index_path.read_text(encoding="utf-8"))
        assert "https://kept.test" in reloaded["entries"]

    def test_apply_without_existing_index_makes_no_backup(self, tmp_path: Path) -> None:
        """Pruning against a missing index is a no-op with no backup copy."""
        index_path = tmp_path / "absent.yaml"
        backup_dir = tmp_path / "backups"

        result = apply_orphan_prunes(
            ["https://x.test"], index_path, backup_dir=backup_dir
        )

        assert result.applied == 0
        assert not result.backup_path.exists()

    def test_prunes_entry_whose_hash_is_absent(self, tmp_path: Path) -> None:
        """An entry pruned without a matching hash mapping still deletes
        cleanly -- the hashes dict is simply left untouched.
        """
        index = {
            "entries": {
                "https://gone.test": _entry(
                    content_hash="sha256:orphanhash", url="https://gone.test"
                )
            },
            "hashes": {"sha256:unrelated": "data/staging/other.md"},
        }
        index_path = self._write_index(tmp_path, index)
        backup_dir = tmp_path / "backups"

        result = apply_orphan_prunes(
            ["https://gone.test"], index_path, backup_dir=backup_dir
        )

        assert result.applied == 1
        reloaded = yaml.safe_load(index_path.read_text(encoding="utf-8"))
        assert "https://gone.test" not in reloaded["entries"]
        assert reloaded["hashes"] == {"sha256:unrelated": "data/staging/other.md"}


class TestNullCaptureGate:
    """A capture the fetch hook flagged as empty must not be promoted.

    Promotion scores on structural signals only (recency, domain
    authority, cluster size), so a failed fetch inherits the score of
    its domain and cluster. Before this gate, redirect notices and
    zero-result API responses promoted to importance 79-90, above much
    of the real corpus (issue #649).
    """

    def test_null_capture_archives_instead_of_promoting(self) -> None:
        """A flagged capture drains instead of promoting."""
        index = {
            "entries": {"https://ex.com/a": _entry(null_capture="redirect-notice")},
            "hashes": {},
        }
        proposals = propose_promotions(index)
        assert len(proposals) == 1
        assert proposals[0].action == "archive"
        assert proposals[0].changes["routing_type"] == "archived"
        assert any("null" in r.lower() for r in proposals[0].reasons)

    def test_same_entry_without_flag_still_promotes(self) -> None:
        """Control: the gate, not the fixture, is what blocks promotion."""
        index = {"entries": {"https://ex.com/a": _entry()}, "hashes": {}}
        proposals = propose_promotions(index)
        assert [p.action for p in proposals] == ["promote"]

    def test_null_capture_never_reaches_growing_maturity(self) -> None:
        """Archived entries get no importance bump and stay seedling."""
        index = {
            "entries": {"https://ex.com/a": _entry(null_capture="empty-results")},
            "hashes": {},
        }
        changes = propose_promotions(index)[0].changes
        assert changes.get("maturity") != "growing"
        assert "importance_score" not in changes


class TestNullCaptureWiring:
    """The flag must survive the capture path, or the gate is dead code."""

    def test_detector_output_feeds_the_gate(self) -> None:
        """Detector reason string is what the promoter archives on."""
        reason = detect_null_capture({}, "REDIRECT DETECTED: bounced elsewhere")
        assert reason is not None

        index = {
            "entries": {"https://ex.com/a": _entry(null_capture=reason)},
            "hashes": {},
        }
        proposals = propose_promotions(index)
        assert [p.action for p in proposals] == ["archive"]


class TestCorpusAbsenceRefusesMassPrune:
    """A tree without the capture corpus must not be read as mass rot.

    Only 15 of the ~1538 files under ``data/staging`` are tracked in git,
    so a fresh worktree checks out an index describing hundreds of
    captures whose backing files were never there. Every entry then looks
    orphaned, and a prune that trusts that reading deletes the corpus.

    That is not hypothetical: 6092ff2d, a commit whose message describes
    a sanctum ``_should_exclude`` fix, emptied this index to
    ``entries: {}`` because the pre-commit hook ran from a worktree.

    The invariant: orphan detection is only meaningful when the corpus is
    present, and a proposal to delete most of the index is evidence that
    it is not.
    """

    @pytest.fixture
    def empty_plugin_root(self, tmp_path: Path) -> Path:
        """Build a tree with a staging directory but none of the captures."""
        (tmp_path / "data" / "staging").mkdir(parents=True)
        return tmp_path

    def test_refuses_to_prune_when_no_backing_file_is_present(
        self, sample_index: dict, empty_plugin_root: Path
    ) -> None:
        """Scenario: The whole corpus is missing from this checkout
        Given an index describing five captures
        And a tree where none of their files exist
        When orphan prunes are proposed
        Then the proposal is refused
        And no key is offered for deletion
        """
        with pytest.raises(CorpusUnavailableError):
            propose_orphan_prunes(sample_index, empty_plugin_root)

    def test_refuses_when_the_majority_are_orphaned(
        self, sample_index: dict, tmp_path: Path
    ) -> None:
        """Scenario: Most of the corpus is missing, but not all
        Given an index of five captures with one backing file present
        When orphan prunes are proposed
        Then the proposal is refused
        And a partial checkout is not mistaken for partial rot
        """
        staging = tmp_path / "data" / "staging"
        staging.mkdir(parents=True)
        (staging / "recent.md").write_text("stub", encoding="utf-8")
        with pytest.raises(CorpusUnavailableError):
            propose_orphan_prunes(sample_index, tmp_path)

    def test_still_prunes_a_lone_orphan(
        self, sample_index: dict, plugin_root_with_files: Path
    ) -> None:
        """Scenario: Ordinary curation removes one capture
        Given an index where four of five backing files are present
        When orphan prunes are proposed
        Then the single orphan is proposed for deletion
        And the guard does not disable routine pruning
        """
        assert propose_orphan_prunes(sample_index, plugin_root_with_files) == [
            "https://example.com/orphan"
        ]

    def test_an_empty_index_is_not_refused(self, empty_plugin_root: Path) -> None:
        """Scenario: There is nothing to protect
        Given an index with no entries
        When orphan prunes are proposed
        Then no refusal is raised
        And an empty index stays a no-op rather than an error
        """
        assert (
            propose_orphan_prunes({"entries": {}, "hashes": {}}, empty_plugin_root)
            == []
        )

    def test_refusal_reports_the_counts_that_triggered_it(
        self, sample_index: dict, empty_plugin_root: Path
    ) -> None:
        """Scenario: A human has to judge whether the corpus is really gone
        Given a tree missing every backing file
        When the refusal is raised
        Then its message carries how many of how many looked orphaned
        And names the directory it expected to find them in
        """
        with pytest.raises(CorpusUnavailableError) as excinfo:
            propose_orphan_prunes(sample_index, empty_plugin_root)
        message = str(excinfo.value)
        assert "5 of 5" in message
        assert "data/staging" in message

    def test_missing_plugin_root_still_fails_closed(self, sample_index: dict) -> None:
        """Scenario: The caller has no root to check against
        Given a plugin root of None
        When orphan prunes are proposed
        Then the existing empty-list default is preserved
        And the guard does not convert a quiet skip into a raise
        """
        assert propose_orphan_prunes(sample_index, None) == []

    def test_promotion_does_not_mass_archive_a_missing_corpus(
        self, empty_plugin_root: Path
    ) -> None:
        """Scenario: The promoter runs in a tree without the corpus
        Given four pending captures whose backing files are all absent
        When promotions are proposed
        Then none of them is archived as an orphan
        And absence of the corpus stops meaning every capture died

        Pruning deletes and archiving only relabels, so this is the
        milder half of the same bug. It still writes a wrong verdict
        onto every pending entry and re-stages it, which is how the
        curated state drifts without anyone deciding that it should.
        """
        index = {
            "entries": {
                f"https://example.com/{i}": _entry(
                    content_hash=f"sha256:{i:04d}",
                    stored_at=f"data/staging/absent-{i}.md",
                    last_updated=_iso(2),
                    url=f"https://example.com/{i}",
                )
                for i in range(4)
            },
            "hashes": {},
        }
        proposals = propose_promotions(index, empty_plugin_root)
        assert [p.action for p in proposals if p.action == "archive"] == []


class TestProposeTitleRepairs:
    """Feature: repair titles the extractor should never have stored.

    #621 and #624 fixed the extractor, but a fix to the extractor only
    governs future captures. 59 of the 929 titles already committed
    still fail the repaired filter. The repair re-derives them from the
    stored URL, which is exactly what the extractor's own fallback
    would have produced had the filter been right at capture time.
    """

    @pytest.mark.unit
    def test_junk_title_is_proposed_for_repair(self) -> None:
        """Given a list-fragment title, propose the URL-derived title."""
        index = {
            "entries": {
                "https://docs.example.com/user-guide": _entry(
                    title="- A loading state",
                    url="https://docs.example.com/user-guide",
                )
            }
        }
        proposals = propose_title_repairs(index)
        assert len(proposals) == 1
        assert proposals[0].action == "retitle"
        assert proposals[0].changes["title"] == "User Guide"

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "junk",
        [
            "Based on the repository data provided:",
            "Response",
            "1. A readable version of the document, or",
            "3. **Color swatches** - CMYK color definitions",
        ],
    )
    def test_every_live_junk_shape_is_caught(self, junk: str) -> None:
        """Given each junk shape seen in the live index, propose a repair."""
        index = {
            "entries": {
                "https://docs.example.com/user-guide": _entry(
                    title=junk, url="https://docs.example.com/user-guide"
                )
            }
        }
        assert len(propose_title_repairs(index)) == 1

    @pytest.mark.unit
    def test_good_title_is_left_alone(self) -> None:
        """Given a real title, propose nothing."""
        index = {
            "entries": {
                "https://docs.example.com/user-guide": _entry(
                    title="Python Async Patterns",
                    url="https://docs.example.com/user-guide",
                )
            }
        }
        assert propose_title_repairs(index) == []

    @pytest.mark.unit
    def test_entry_whose_url_yields_no_better_title_is_skipped(self) -> None:
        """Given a URL with no usable slug, leave the entry alone.

        Replacing junk with a bare hostname is not an improvement, and
        churning the index for no gain is what #605 objects to.
        """
        index = {
            "entries": {
                "https://example.com": _entry(
                    title="Response", url="https://example.com"
                )
            }
        }
        assert propose_title_repairs(index) == []

    @pytest.mark.unit
    def test_missing_url_is_skipped_not_crashed(self) -> None:
        """Given an entry with no URL, skip it rather than fail."""
        index = {"entries": {"k": {"title": "Response"}}}
        assert propose_title_repairs(index) == []


class TestApplyTitleRepairs:
    """Feature: applying repairs is atomic and idempotent."""

    def _index_file(self, tmp_path: Path, title: str) -> Path:
        path = tmp_path / "memory-palace-index.yaml"
        path.write_text(
            yaml.safe_dump(
                {
                    "entries": {
                        "https://docs.example.com/user-guide": _entry(
                            title=title,
                            url="https://docs.example.com/user-guide",
                        )
                    }
                }
            )
        )
        return path

    @pytest.mark.unit
    def test_apply_rewrites_the_title(self, tmp_path: Path) -> None:
        """Given a junk title on disk, apply writes the repaired one."""
        path = self._index_file(tmp_path, "- A loading state")
        index = yaml.safe_load(path.read_text())
        result = apply_title_repairs(index, propose_title_repairs(index), path)
        assert result.applied == 1
        written = yaml.safe_load(path.read_text())
        entry = written["entries"]["https://docs.example.com/user-guide"]
        assert entry["title"] == "User Guide"

    @pytest.mark.unit
    def test_apply_is_idempotent(self, tmp_path: Path) -> None:
        """Given an already-repaired index, a second pass changes nothing."""
        path = self._index_file(tmp_path, "- A loading state")
        index = yaml.safe_load(path.read_text())
        apply_title_repairs(index, propose_title_repairs(index), path)

        reloaded = yaml.safe_load(path.read_text())
        assert propose_title_repairs(reloaded) == []

    @pytest.mark.unit
    def test_apply_leaves_a_backup(self, tmp_path: Path) -> None:
        """Given a repair, the pre-repair index is recoverable."""
        path = self._index_file(tmp_path, "- A loading state")
        index = yaml.safe_load(path.read_text())
        result = apply_title_repairs(index, propose_title_repairs(index), path)
        assert result.backup_path.exists()
        backed_up = yaml.safe_load(result.backup_path.read_text())
        entry = backed_up["entries"]["https://docs.example.com/user-guide"]
        assert entry["title"] == "- A loading state"

    @pytest.mark.unit
    def test_apply_preserves_other_fields(self, tmp_path: Path) -> None:
        """Given a repair, only the title changes."""
        path = self._index_file(tmp_path, "- A loading state")
        index = yaml.safe_load(path.read_text())
        before = copy.deepcopy(index)
        apply_title_repairs(index, propose_title_repairs(index), path)
        written = yaml.safe_load(path.read_text())
        key = "https://docs.example.com/user-guide"
        for field_name, value in before["entries"][key].items():
            if field_name != "title":
                assert written["entries"][key][field_name] == value
