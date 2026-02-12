"""Tests for deduplication module."""

from __future__ import annotations

import os
import sys

# Add hooks to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../hooks"))

import shared.deduplication as dedup_module
from shared.deduplication import (
    get_content_hash,
    get_index_stats,
    get_url_key,
    is_known,
    needs_update,
    update_index,
)


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
        assert is_known(content_hash=unique_hash) is False

    def test_unknown_url_returns_false(self) -> None:
        """Unknown URLs should return False."""
        assert is_known(url="https://definitely-not-indexed-12345.com/page") is False


class TestNeedsUpdate:
    """Tests for update detection."""

    def test_new_content_needs_update(self) -> None:
        """New content (not in index) should need update."""
        unique_hash = get_content_hash(f"new-{os.urandom(16).hex()}")
        assert needs_update(unique_hash, url="https://new-url-12345.com") is True


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

    def test_load_index_returns_empty_when_yaml_unavailable(self) -> None:
        """When yaml is None, _load_index returns empty structure."""
        original_yaml = dedup_module.yaml
        try:
            dedup_module.yaml = None
            index = dedup_module._load_index()
            assert index == {"entries": {}, "hashes": {}}
        finally:
            dedup_module.yaml = original_yaml

    def test_is_known_returns_false_when_yaml_unavailable(self) -> None:
        """When yaml is None, nothing is known."""
        original_yaml = dedup_module.yaml
        try:
            dedup_module.yaml = None
            assert is_known(content_hash="sha256:abc123") is False
            assert is_known(url="https://example.com") is False
        finally:
            dedup_module.yaml = original_yaml

    def test_update_index_caches_only_when_yaml_unavailable(self) -> None:
        """When yaml is None, update_index stores in memory but doesn't persist."""
        original_yaml = dedup_module.yaml
        try:
            dedup_module.yaml = None
            content_hash = get_content_hash("test content for no-yaml")
            update_index(
                content_hash=content_hash,
                stored_at="docs/test.md",
                importance_score=50,
            )
            # Should be cached in memory
            assert dedup_module._index_cache is not None
            assert content_hash in dedup_module._index_cache.get("hashes", {})
        finally:
            dedup_module.yaml = original_yaml

    def test_get_index_stats_works_when_yaml_unavailable(self) -> None:
        """When yaml is None, stats should still return valid structure."""
        original_yaml = dedup_module.yaml
        try:
            dedup_module.yaml = None
            stats = get_index_stats()
            assert isinstance(stats, dict)
            assert stats["total_entries"] == 0
            assert stats["total_hashes"] == 0
        finally:
            dedup_module.yaml = original_yaml
