"""Invariant checks against the committed capture index.

``hooks/memory-palace-index.yaml`` is a live artifact: a session hook
appends to it on every web capture, and the result is committed. The
rest of the suite pins the index-handling *logic* against synthesized
fixtures in ``tmp_path``. Nothing read the file that actually ships.

That gap is the one this module closes. The invariants below are the
same ones ``test_deduplication`` and ``test_index_promoter`` enforce on
synthetic indices, applied to the real corpus so a hook that corrupts
the artifact fails a gate instead of landing silently in a commit.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from memory_palace.corpus.index_analytics import load_capture_index

INDEX_PATH = Path(__file__).resolve().parents[1] / "hooks" / "memory-palace-index.yaml"


@pytest.fixture(scope="module")
def committed_index() -> dict:
    """Load the capture index exactly as it is committed to the repo."""
    if not INDEX_PATH.exists():
        pytest.skip(f"No committed capture index at {INDEX_PATH}")
    return load_capture_index(INDEX_PATH)


class TestCommittedCaptureIndex:
    """The shipped artifact must satisfy the dedup invariants."""

    def test_every_entry_hash_is_present_in_hashes(self, committed_index: dict) -> None:
        """No entry references a content_hash absent from ``hashes``.

        A dangling reference means ``is_known(content_hash=...)`` reports
        the content unseen, so a re-fetch re-captures a file already on
        disk. This is the state a non-refcounted prune used to leave
        behind when two entries shared one hash.
        """
        hashes = committed_index["hashes"]
        dangling = {
            key: entry.get("content_hash")
            for key, entry in committed_index["entries"].items()
            if entry.get("content_hash") not in hashes
        }
        assert not dangling, (
            f"entries with a content_hash missing from hashes: {dangling}"
        )

    def test_hashes_agree_with_entries_on_stored_at(
        self, committed_index: dict
    ) -> None:
        """``hashes[H]`` names the same file the entry claims.

        The two structures record where content lives; dedup consults
        ``hashes`` and retrieval consults ``entries``. Disagreement means
        the index points at the wrong file for content it believes it
        already has.
        """
        hashes = committed_index["hashes"]
        disagreements = [
            (key, entry["stored_at"], hashes[entry["content_hash"]])
            for key, entry in committed_index["entries"].items()
            if entry.get("content_hash") in hashes
            and hashes[entry["content_hash"]] != entry.get("stored_at")
        ]
        assert not disagreements, (
            "entries disagree with hashes on stored_at "
            f"(key, entry.stored_at, hashes[H]): {disagreements}"
        )

    def test_no_orphan_hashes(self, committed_index: dict) -> None:
        """Every hash mapping is referenced by at least one entry.

        An orphan hash suppresses a future capture of content no entry
        can retrieve: the index claims to know it, but nothing points at
        the file.
        """
        referenced = {
            entry.get("content_hash") for entry in committed_index["entries"].values()
        }
        orphans = set(committed_index["hashes"]) - referenced
        assert not orphans, f"hash mappings no entry references: {sorted(orphans)}"

    def test_entries_carry_the_fields_consumers_read(
        self, committed_index: dict
    ) -> None:
        """Each entry carries the fields the analytics and prune layers read."""
        required = {"content_hash", "stored_at", "importance_score", "last_updated"}
        incomplete = {
            key: sorted(required - set(entry))
            for key, entry in committed_index["entries"].items()
            if not required.issubset(entry)
        }
        assert not incomplete, f"entries missing required fields: {incomplete}"

    def test_importance_scores_stay_in_range(self, committed_index: dict) -> None:
        """``update_index`` rejects scores outside [0, 100]; the corpus agrees."""
        out_of_range = {
            key: entry["importance_score"]
            for key, entry in committed_index["entries"].items()
            if not 0 <= entry.get("importance_score", 0) <= 100
        }
        assert not out_of_range, f"importance_score outside [0, 100]: {out_of_range}"
