"""Tests for deduplication module."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml as real_yaml

# Add hooks to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../hooks"))

import shared.deduplication as dedup_module
from shared.deduplication import (
    get_content_hash,
    get_entry,
    get_index_stats,
    get_url_key,
    is_known,
    needs_update,
    update_index,
)

# Resolved once: the staging tests shell out to git, and an absolute
# path keeps them independent of whatever PATH the runner exports.
_GIT = shutil.which("git") or "git"


class TestGetContentHash:
    """Tests for content hashing."""

    def test_string_hashed(self) -> None:
        """Strings should be hashed."""
        hash1 = get_content_hash("Hello World")
        assert hash1.startswith(("xxh:", "sha256:"))

    def test_bytes_hashed(self) -> None:
        """Bytes should be hashed."""
        hash1 = get_content_hash(b"Hello World")
        assert hash1.startswith(("xxh:", "sha256:"))

    def test_same_content_same_hash(self) -> None:
        """Same content should produce same hash."""
        hash1 = get_content_hash("Test content")
        hash2 = get_content_hash("Test content")
        assert hash1 == hash2

    def test_different_content_different_hash(self) -> None:
        """Different content should produce different hash."""
        hash1 = get_content_hash("Content A")
        hash2 = get_content_hash("Content B")
        assert hash1 != hash2


class TestGetUrlKey:
    """Tests for URL normalization."""

    def test_trailing_slash_removed(self) -> None:
        """Trailing slashes should be removed."""
        assert get_url_key("https://example.com/") == "https://example.com"
        assert get_url_key("https://example.com/path/") == "https://example.com/path"

    def test_fragment_removed(self) -> None:
        """URL fragments should be removed."""
        assert get_url_key("https://example.com#section") == "https://example.com"

    def test_tracking_params_removed(self) -> None:
        """Common tracking parameters should be removed."""
        url = "https://example.com?utm_source=twitter&article=123"
        result = get_url_key(url)
        assert "utm_source" not in result
        assert "article=123" in result or "article" in result

    def test_lowercase(self) -> None:
        """URLs should be lowercased."""
        assert get_url_key("HTTPS://EXAMPLE.COM/Path") == "https://example.com/path"


class TestIsKnown:
    """Tests for index lookup."""

    def test_unknown_content_returns_false(self) -> None:
        """Unknown content should return False."""
        # Generate a unique hash that won't be in any index
        unique_hash = get_content_hash(f"unique-{os.urandom(16).hex()}")
        assert not is_known(content_hash=unique_hash)

    def test_unknown_url_returns_false(self) -> None:
        """Unknown URLs should return False."""
        assert not is_known(url="https://definitely-not-indexed-12345.com/page")


class TestNeedsUpdate:
    """Tests for update detection."""

    def test_new_content_needs_update(self) -> None:
        """New content (not in index) should need update."""
        unique_hash = get_content_hash(f"new-{os.urandom(16).hex()}")
        assert needs_update(unique_hash, url="https://new-url-12345.com")


class TestGetIndexStats:
    """Tests for index statistics."""

    def test_stats_returns_dict(self) -> None:
        """Stats should return a dictionary."""
        stats = get_index_stats()
        assert isinstance(stats, dict)

    def test_stats_has_required_keys(self) -> None:
        """Stats should have required keys."""
        stats = get_index_stats()
        assert "total_entries" in stats
        assert "total_hashes" in stats
        assert "urls" in stats
        assert "local_docs" in stats

    def test_stats_are_non_negative(self) -> None:
        """All stats should be non-negative."""
        stats = get_index_stats()
        assert stats["total_entries"] >= 0
        assert stats["total_hashes"] >= 0
        assert stats["urls"] >= 0
        assert stats["local_docs"] >= 0


class TestYamlUnavailable:
    """Tests for graceful degradation when pyyaml is not installed."""

    def setup_method(self) -> None:
        """Reset dedup caches before each test."""
        dedup_module._index_cache = None
        dedup_module._index_mtime = 0

    def teardown_method(self) -> None:
        """Reset dedup caches after each test."""
        dedup_module._index_cache = None
        dedup_module._index_mtime = 0

    def test_load_index_returns_empty_when_yaml_unavailable(
        self, monkeypatch: object
    ) -> None:
        """When yaml is None, _load_index returns empty structure."""
        monkeypatch.setattr(dedup_module, "yaml", None)
        index = dedup_module._load_index()
        assert index == {"entries": {}, "hashes": {}}

    def test_load_index_recovers_from_corrupt_yaml(
        self, tmp_path: object, monkeypatch: object, capsys: object
    ) -> None:
        """A corrupt YAML index file must not take down web-research store
        calls. The loader catches yaml.YAMLError, logs to stderr, and
        returns the empty-index sentinel (issue #528).
        """
        index_path = tmp_path / "dedup-index.yaml"
        # Write a syntactically invalid YAML file.
        index_path.write_text(
            "entries:\n  - this is malformed because: : :\n  bad: }\n"
        )
        monkeypatch.setattr(dedup_module, "_get_index_path", lambda: index_path)
        monkeypatch.setattr(dedup_module, "yaml", real_yaml)

        # Should NOT raise; should return the empty-index sentinel.
        index = dedup_module._load_index()
        assert index == {"entries": {}, "hashes": {}}
        # Should log to stderr so the operator notices.
        err = capsys.readouterr().err
        assert (
            "yaml" in err.lower() or "corrupt" in err.lower() or "index" in err.lower()
        )

    def test_is_known_returns_false_when_yaml_unavailable(
        self, monkeypatch: object
    ) -> None:
        """When yaml is None, nothing is known."""
        monkeypatch.setattr(dedup_module, "yaml", None)
        assert not is_known(content_hash="sha256:abc123")
        assert not is_known(url="https://example.com")

    def test_update_index_caches_only_when_yaml_unavailable(
        self, monkeypatch: object
    ) -> None:
        """When yaml is None, update_index stores in memory but doesn't persist."""
        monkeypatch.setattr(dedup_module, "yaml", None)
        content_hash = get_content_hash("test content for no-yaml")
        update_index(
            content_hash=content_hash,
            stored_at="docs/test.md",
            importance_score=50,
        )
        # Should be cached in memory
        assert isinstance(dedup_module._index_cache, dict)
        assert content_hash in dedup_module._index_cache.get("hashes", {})

    def test_get_index_stats_works_when_yaml_unavailable(
        self, monkeypatch: object
    ) -> None:
        """When yaml is None, stats should still return valid structure."""
        monkeypatch.setattr(dedup_module, "yaml", None)
        stats = get_index_stats()
        assert isinstance(stats, dict)
        assert stats["total_entries"] == 0
        assert stats["total_hashes"] == 0


class TestUpdateIndexIntegration:
    """Round-trip and invariant tests for update_index → lookup paths.

    These tests cross the write/read boundary that earlier unit tests
    skip: each test calls ``update_index`` against an isolated YAML
    file (via ``_get_index_path`` monkeypatch) and then asserts that
    the matching lookup function (``is_known``, ``get_entry``,
    ``needs_update``) reports the entry consistent with what was
    written. The original diff (knowledge-corpus QA-tier ingest)
    exercises exactly this round-trip in production.
    """

    def setup_method(self) -> None:
        """Reset dedup caches before each test."""
        dedup_module._index_cache = None
        dedup_module._index_mtime = 0

    def teardown_method(self) -> None:
        """Reset dedup caches after each test."""
        dedup_module._index_cache = None
        dedup_module._index_mtime = 0

    @staticmethod
    def _isolate_index(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
        """Redirect the index file to an isolated tmp_path location.

        Returns the path so individual tests can read raw YAML if
        they need to assert on-disk shape.
        """
        index_path = tmp_path / "memory-palace-index.yaml"
        monkeypatch.setattr(dedup_module, "_get_index_path", lambda: index_path)
        return index_path

    def test_url_entry_round_trip_marks_known(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """GIVEN an isolated empty index
        WHEN update_index writes a URL-keyed entry
        THEN is_known(url=...) returns True for the same URL.
        """
        self._isolate_index(monkeypatch, tmp_path)
        url = "https://github.com/pytest-dev/pytest"
        content_hash = get_content_hash("pytest readme content")

        update_index(
            content_hash=content_hash,
            stored_at="docs/knowledge-corpus/qa-testing-tiers.md",
            importance_score=82,
            url=url,
            title="pytest",
            maturity="growing",
            routing_type="meta",
        )

        assert is_known(url=url)
        assert is_known(content_hash=content_hash)

    def test_full_metadata_preserved_by_get_entry(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """GIVEN an isolated empty index
        WHEN update_index writes an entry with title, maturity, and
             routing_type
        THEN get_entry(url=...) returns each field verbatim.
        """
        self._isolate_index(monkeypatch, tmp_path)
        url = "https://github.com/microsoft/playwright"
        content_hash = get_content_hash("playwright doc content")

        update_index(
            content_hash=content_hash,
            stored_at="docs/knowledge-corpus/qa-testing-tiers.md",
            importance_score=82,
            url=url,
            title="Playwright",
            maturity="growing",
            routing_type="meta",
        )

        entry = get_entry(url=url)
        assert entry is not None
        assert entry["content_hash"] == content_hash
        assert entry["stored_at"] == "docs/knowledge-corpus/qa-testing-tiers.md"
        assert entry["importance_score"] == 82
        assert entry["title"] == "Playwright"
        assert entry["maturity"] == "growing"
        assert entry["routing_type"] == "meta"
        assert entry["url"] == url
        # last_updated is stamped server-side and must be present
        assert "last_updated" in entry

    def test_needs_update_false_when_hash_unchanged(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """GIVEN an entry already written for a URL
        WHEN needs_update is called with the same content_hash
        THEN it returns False (no rewrite needed).
        AND when called with a different hash, it returns True.
        """
        self._isolate_index(monkeypatch, tmp_path)
        url = "https://github.com/google/openhtf"
        original_hash = get_content_hash("openhtf v1 content")
        update_index(
            content_hash=original_hash,
            stored_at="docs/knowledge-corpus/qa-testing-tiers.md",
            importance_score=82,
            url=url,
            title="OpenHTF bench tests",
            maturity="growing",
            routing_type="meta",
        )

        assert needs_update(original_hash, url=url) is False

        changed_hash = get_content_hash("openhtf v2 content")
        assert needs_update(changed_hash, url=url) is True

    def test_url_normalization_invariant_across_write_and_read(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Encodes the design invariant that get_url_key normalization
        binds writes and reads together. Cosmetic URL variants
        (trailing slash, fragment, mixed case) MUST hit the same
        entry; if this test breaks, get_url_key has diverged
        between write-side and read-side and the index is no
        longer deduplicating reliably.

        Three resolution options if this ever fails:
          1. Preserve: revert the change to get_url_key
          2. Layer:    add an explicit migration step
          3. Revise:   rebuild the index under the new normalization
        Picking the wrong one corrupts dedup silently — this is
        not a test to weaken without human review.
        """
        self._isolate_index(monkeypatch, tmp_path)
        canonical = "https://testing-library.com/docs/guiding-principles"
        content_hash = get_content_hash("testing-library guiding principles")

        # Write under one cosmetic form
        update_index(
            content_hash=content_hash,
            stored_at="docs/knowledge-corpus/qa-testing-tiers.md",
            importance_score=82,
            url=canonical + "/",  # trailing slash
            title="Testing Library Guiding Principles",
            maturity="growing",
            routing_type="meta",
        )

        # Read under cosmetic variants — all must resolve to the
        # same entry
        assert is_known(url=canonical)
        assert is_known(url=canonical + "#section-1")
        assert is_known(url="HTTPS://Testing-Library.com/docs/guiding-principles")

    def test_path_keyed_entry_round_trip(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """GIVEN an isolated empty index
        WHEN update_index writes a path-keyed (local-doc) entry
        THEN get_entry(path=...) and is_known(path=...) recover it.

        The diff exercises the URL branch; this test guards the
        symmetric path branch so a regression there cannot ship
        unnoticed.
        """
        self._isolate_index(monkeypatch, tmp_path)
        local_doc = tmp_path / "local-doc.md"
        local_doc.write_text("local doc body")
        content_hash = get_content_hash(local_doc.read_text())

        update_index(
            content_hash=content_hash,
            stored_at=str(local_doc),
            importance_score=50,
            path=str(local_doc),
            title="local doc",
        )

        assert is_known(path=str(local_doc))
        entry = get_entry(path=str(local_doc))
        assert entry is not None
        assert entry["path"] == str(local_doc)
        assert entry["content_hash"] == content_hash

    def test_index_stats_count_matches_writes(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """GIVEN an isolated empty index
        WHEN update_index is called N times with distinct URLs and
             distinct content
        THEN get_index_stats reports total_entries == N and
             total_hashes == N.

        The diff added 9 entries in one ingest pass; this test
        guards the counter invariant under a small N=3 batch so a
        regression in the cache-invalidation logic surfaces.
        """
        self._isolate_index(monkeypatch, tmp_path)
        for i, url in enumerate(
            [
                "https://github.com/pytest-dev/pytest",
                "https://github.com/microsoft/playwright",
                "https://github.com/google/openhtf",
            ]
        ):
            update_index(
                content_hash=get_content_hash(f"body-{i}"),
                stored_at="docs/knowledge-corpus/qa-testing-tiers.md",
                importance_score=82,
                url=url,
                title=f"entry-{i}",
                maturity="growing",
                routing_type="meta",
            )

        stats = get_index_stats()
        assert stats["total_entries"] == 3
        assert stats["total_hashes"] == 3
        assert stats["urls"] == 3
        assert stats["local_docs"] == 0

    def test_hashes_and_entries_agree_on_stored_at(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """GIVEN an isolated empty index
        WHEN update_index writes several distinct URL entries
        THEN the two parallel index structures agree, at value level,
             on where each piece of content is stored.

        update_index records the same ``stored_at`` in two places:
        ``entries[url_key]["stored_at"]`` and
        ``hashes[content_hash]``. ``is_known`` consults ``hashes``;
        retrieval consults ``entries``. If the two ever disagree,
        dedup-by-hash returns a stale path and the index silently
        points at the wrong file. The count-matching test above
        guards cardinality only; two structures can share a count
        while disagreeing on values. This test guards the
        value-level agreement.

        Three resolution options if this ever fails:
          1. Preserve: revert the change that decoupled the writes
          2. Layer:    add a reconciliation step that repairs hashes
          3. Revise:   collapse entries and hashes into one structure
        Picking the wrong one breaks dedup silently — this is not
        a test to weaken without human review.
        """
        index_path = self._isolate_index(monkeypatch, tmp_path)
        writes = [
            ("https://github.com/pytest-dev/pytest", "docs/pytest.md"),
            ("https://github.com/microsoft/playwright", "docs/playwright.md"),
            ("https://github.com/google/openhtf", "docs/openhtf.md"),
        ]
        for url, stored_at in writes:
            update_index(
                content_hash=get_content_hash(url),
                stored_at=stored_at,
                importance_score=82,
                url=url,
                maturity="growing",
                routing_type="meta",
            )

        # Read the persisted file directly so the assertion sees what
        # is on disk, not the in-memory cache.
        with open(index_path) as f:
            on_disk = real_yaml.safe_load(f)

        assert len(on_disk["entries"]) == len(writes)
        for entry in on_disk["entries"].values():
            h = entry["content_hash"]
            assert h in on_disk["hashes"], (
                f"content_hash {h} in entries but missing from hashes"
            )
            assert on_disk["hashes"][h] == entry["stored_at"], (
                f"hashes[{h}] = {on_disk['hashes'][h]!r} but entry "
                f"stored_at = {entry['stored_at']!r}"
            )

    def test_duplicate_content_on_new_url_reuses_canonical_stored_at(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """GIVEN content already stored under one URL
        WHEN a second, different URL yields byte-identical content
        THEN the new entry points at the first URL's stored file.

        The index is content-addressed: ``hashes[content_hash]`` names
        the one file those bytes live in. Two URLs serving the same
        content (an empty HN Algolia result, a mirror, a redirect
        target) must converge on that file rather than each claiming a
        private copy. Without this, the second write overwrites
        ``hashes[H]`` and the first entry is left pointing at a path
        the hash map no longer agrees with.
        """
        self._isolate_index(monkeypatch, tmp_path)
        content = "no stories to list" * 20
        content_hash = get_content_hash(content)

        update_index(
            content_hash=content_hash,
            stored_at="data/staging/alpha.md",
            importance_score=50,
            url="https://hn.algolia.com/api/v1/search?query=alpha",
        )
        update_index(
            content_hash=content_hash,
            stored_at="data/staging/beta.md",
            importance_score=50,
            url="https://hn.algolia.com/api/v1/search?query=beta",
        )

        alpha = get_entry(url="https://hn.algolia.com/api/v1/search?query=alpha")
        beta = get_entry(url="https://hn.algolia.com/api/v1/search?query=beta")
        assert alpha is not None and beta is not None
        assert beta["stored_at"] == "data/staging/alpha.md", (
            "second capture of identical content must reuse the canonical "
            f"file, got {beta['stored_at']!r}"
        )
        assert alpha["stored_at"] == "data/staging/alpha.md", (
            "first capture must not be repointed by a later duplicate"
        )

    def test_hashes_and_entries_agree_when_two_urls_share_content(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """GIVEN two URLs whose content hashes to the same value
        WHEN both are written to the index
        THEN every entry still agrees with hashes on where it is stored.

        This is ``test_hashes_and_entries_agree_on_stored_at`` under the
        one condition that test cannot reach: it derives each hash from
        the URL, so no two entries can ever collide. A real collision is
        the normal dedup path, and it is exactly where the two
        structures used to drift apart.
        """
        index_path = self._isolate_index(monkeypatch, tmp_path)
        content_hash = get_content_hash("identical body")

        for url, stored_at in (
            ("https://example.com/a", "data/staging/a.md"),
            ("https://example.com/b", "data/staging/b.md"),
        ):
            update_index(
                content_hash=content_hash,
                stored_at=stored_at,
                importance_score=50,
                url=url,
            )

        with open(index_path) as f:
            on_disk = real_yaml.safe_load(f)

        # Two entries, one piece of content, therefore one hash mapping.
        assert len(on_disk["entries"]) == 2
        assert len(on_disk["hashes"]) == 1
        for key, entry in on_disk["entries"].items():
            h = entry["content_hash"]
            assert h in on_disk["hashes"], f"{key}: content_hash absent from hashes"
            assert on_disk["hashes"][h] == entry["stored_at"], (
                f"{key}: hashes[{h}] = {on_disk['hashes'][h]!r} but entry "
                f"stored_at = {entry['stored_at']!r}"
            )


class TestImportanceScoreBounds:
    """Bounds enforcement for the documented ``importance_score`` contract.

    The function's docstring declares a 0-100 closed range (knowledge
    intake evaluation scale). Until now the code accepted any int and
    a -1 or 101 score would silently corrupt the dedup index. These
    tests lock the contract: in-range scores succeed, out-of-range
    scores raise ValueError before any state mutation.
    """

    def setup_method(self) -> None:
        """Reset dedup caches before each test."""
        dedup_module._index_cache = None
        dedup_module._index_mtime = 0

    def teardown_method(self) -> None:
        """Reset dedup caches after each test."""
        dedup_module._index_cache = None
        dedup_module._index_mtime = 0

    @staticmethod
    def _isolate_index(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
        """Redirect index file to an isolated tmp_path location."""
        index_path = tmp_path / "memory-palace-index.yaml"
        monkeypatch.setattr(dedup_module, "_get_index_path", lambda: index_path)
        return index_path

    @pytest.mark.parametrize("score", [0, 50, 100])
    def test_in_range_score_accepted(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        score: int,
    ) -> None:
        """GIVEN an isolated empty index
        WHEN update_index is called with a score in the closed
             [0, 100] range
        THEN it succeeds and writes the entry.
        """
        self._isolate_index(monkeypatch, tmp_path)
        update_index(
            content_hash=get_content_hash(f"body-{score}"),
            stored_at="docs/test.md",
            importance_score=score,
            url=f"https://example.com/score-{score}",
        )
        entry = get_entry(url=f"https://example.com/score-{score}")
        assert entry is not None
        assert entry["importance_score"] == score

    @pytest.mark.parametrize("score", [-1, -100, 101, 1000])
    def test_out_of_range_score_raises(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        score: int,
    ) -> None:
        """GIVEN an isolated empty index
        WHEN update_index is called with a score outside [0, 100]
        THEN it raises ValueError before mutating the index.

        Failure-mode rationale: a silently-accepted out-of-range
        score corrupts downstream consumers that rank by score
        (knowledge-intake evaluation, garden curation). Fail-fast
        at the boundary is cheaper than debugging poisoned scores.
        """
        self._isolate_index(monkeypatch, tmp_path)
        with pytest.raises(ValueError, match="importance_score"):
            update_index(
                content_hash=get_content_hash(f"body-{score}"),
                stored_at="docs/test.md",
                importance_score=score,
                url=f"https://example.com/score-{score}",
            )
        # Index must remain untouched on validation failure.
        assert get_entry(url=f"https://example.com/score-{score}") is None
        assert get_index_stats()["total_entries"] == 0


class TestNullCapturePersisted:
    """update_index must write null_capture, or the promoter gate is dead.

    The gate in memory_palace.corpus.index_promoter archives on this
    field. If the write path drops it, the gate silently never fires and
    empty captures promote exactly as before (issue #649).
    """

    @staticmethod
    def _isolate_index(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
        """Redirect the index file to an isolated tmp_path location."""
        index_path = tmp_path / "memory-palace-index.yaml"
        monkeypatch.setattr(dedup_module, "_get_index_path", lambda: index_path)
        return index_path

    def test_null_capture_round_trips_to_disk(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """GIVEN an isolated empty index
        WHEN update_index writes an entry flagged null_capture
        THEN the on-disk entry carries the reason verbatim.
        """
        index_path = self._isolate_index(monkeypatch, tmp_path)
        url = "https://hn.example/api/v1/search?query=x"

        update_index(
            content_hash=get_content_hash("redirect notice body"),
            stored_at="data/staging/x.md",
            importance_score=50,
            url=url,
            title="REDIRECT DETECTED: The URL redirects to a different host.",
            maturity="seedling",
            routing_type="pending",
            null_capture="redirect-notice",
        )

        on_disk = real_yaml.safe_load(index_path.read_text())
        assert on_disk["entries"][url]["null_capture"] == "redirect-notice"

    def test_absent_flag_writes_no_key(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """A normal capture must not gain a null_capture key."""
        index_path = self._isolate_index(monkeypatch, tmp_path)
        url = "https://example.com/real-article"

        update_index(
            content_hash=get_content_hash("real article body"),
            stored_at="data/staging/y.md",
            importance_score=50,
            url=url,
            title="Real Article",
            maturity="seedling",
            routing_type="pending",
        )

        on_disk = real_yaml.safe_load(index_path.read_text())
        assert "null_capture" not in on_disk["entries"][url]


class TestUpdateIndexStaging:
    """The write must stage the index, or the pre-commit drain never sees it.

    ``pre-commit`` reverts unstaged changes to tracked files before
    running any pre-commit-stage hook, restoring them afterward. An
    index written but never staged is therefore absent from the tree
    ``precommit_palace_maintenance.sh`` inspects: the drain reads the
    HEAD version, converges on it, and the fresh capture survives the
    commit still ``pending``. That is the mechanism behind the 47-entry
    backlog drained in 2ed3737b.

    Staging at write time puts the capture in the tree the drain reads,
    which is what makes the zero-pending gate reachable rather than a
    permanent block.
    """

    def setup_method(self) -> None:
        """Reset dedup caches before each test."""
        dedup_module._index_cache = None
        dedup_module._index_mtime = 0

    def teardown_method(self) -> None:
        """Reset dedup caches after each test."""
        dedup_module._index_cache = None
        dedup_module._index_mtime = 0

    @staticmethod
    def _git_repo(tmp_path: Path) -> Path:
        """Initialize a throwaway repo to observe staging in."""
        subprocess.run([_GIT, "init", "--quiet"], cwd=tmp_path, check=True)
        return tmp_path

    @staticmethod
    def _staged_paths(repo: Path) -> set[str]:
        """Return the paths currently in the git index."""
        result = subprocess.run(
            [_GIT, "diff", "--cached", "--name-only"],
            cwd=repo,
            capture_output=True,
            text=True,
            check=True,
        )
        return {line for line in result.stdout.splitlines() if line}

    def test_write_stages_the_index(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """GIVEN an index inside a git repository
        WHEN update_index persists an entry
        THEN the index is staged.
        """
        repo = self._git_repo(tmp_path)
        index_path = repo / "memory-palace-index.yaml"
        monkeypatch.setattr(dedup_module, "_get_index_path", lambda: index_path)

        update_index(
            content_hash="sha256:staged",
            stored_at="data/staging/capture.md",
            importance_score=50,
            url="https://example.com/staged",
        )

        assert "memory-palace-index.yaml" in self._staged_paths(repo)

    def test_write_outside_a_repository_still_persists(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """GIVEN a tree that is not a git repository
        WHEN update_index persists an entry
        THEN the write succeeds and the failed staging stays silent.

        Captures happen during ordinary work, not during a commit. A
        WebFetch outside a repo, mid-rebase, or with git absent must
        never take down the fetch hook.
        """
        index_path = tmp_path / "memory-palace-index.yaml"
        monkeypatch.setattr(dedup_module, "_get_index_path", lambda: index_path)

        update_index(
            content_hash="sha256:norepo",
            stored_at="data/staging/capture.md",
            importance_score=50,
            url="https://example.com/norepo",
        )

        on_disk = real_yaml.safe_load(index_path.read_text())
        assert "https://example.com/norepo" in on_disk["entries"]

    def test_missing_git_binary_is_survivable(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """GIVEN git is not installed
        WHEN update_index persists an entry
        THEN the write still succeeds.
        """
        repo = self._git_repo(tmp_path)
        index_path = repo / "memory-palace-index.yaml"
        monkeypatch.setattr(dedup_module, "_get_index_path", lambda: index_path)

        def _no_git(*args: object, **kwargs: object) -> None:
            raise FileNotFoundError("git")

        monkeypatch.setattr(dedup_module.subprocess, "run", _no_git)

        update_index(
            content_hash="sha256:nogit",
            stored_at="data/staging/capture.md",
            importance_score=50,
            url="https://example.com/nogit",
        )

        on_disk = real_yaml.safe_load(index_path.read_text())
        assert "https://example.com/nogit" in on_disk["entries"]
