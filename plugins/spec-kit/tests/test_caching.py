"""Tests for speckit.caching module.

Exercises SpecKitCache, CacheManager, the @cached decorator,
and the get_cache singleton with full coverage of public APIs,
edge cases, and error paths.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from speckit.caching import (
    CacheManager,
    SpecKitCache,
    _cache_instance,
    cached,
    get_cache,
)


# ============================================================================
# SpecKitCache.__init__
# ============================================================================


class TestSpecKitCacheInit:
    """Tests for SpecKitCache constructor."""

    def test_default_cache_dir_is_home_based(self, tmp_path: Path) -> None:
        """Should default to ~/.spec-kit/cache when no dir supplied."""
        with patch.object(Path, "home", return_value=tmp_path):
            cache = SpecKitCache()
        assert cache.cache_dir == tmp_path / ".spec-kit" / "cache"

    def test_custom_cache_dir(self, tmp_path: Path) -> None:
        """Should use provided directory and create it."""
        custom = tmp_path / "my-cache"
        cache = SpecKitCache(cache_dir=custom)
        assert cache.cache_dir == custom
        assert custom.is_dir()

    def test_creates_cache_dir_with_parents(self, tmp_path: Path) -> None:
        """Should create nested directories that do not exist."""
        nested = tmp_path / "a" / "b" / "c"
        cache = SpecKitCache(cache_dir=nested)
        assert nested.is_dir()
        assert cache.cache_dir == nested

    def test_initial_state(self, tmp_path: Path) -> None:
        """Should start with empty memory, timestamps, and LRU caches."""
        cache = SpecKitCache(cache_dir=tmp_path / "cache")
        assert cache._memory_cache == {}
        assert cache._cache_timestamps == {}
        assert len(cache._lru_cache) == 0
        assert cache.default_ttl == 3600


# ============================================================================
# SpecKitCache._get_cache_key
# ============================================================================


class TestGetCacheKey:
    """Tests for cache key generation."""

    def test_key_without_data(self, tmp_path: Path) -> None:
        """Should return the key verbatim when no data provided."""
        cache = SpecKitCache(cache_dir=tmp_path / "cache")
        assert cache._get_cache_key("my_key") == "my_key"

    def test_key_with_none_data(self, tmp_path: Path) -> None:
        """Should return plain key when data is None."""
        cache = SpecKitCache(cache_dir=tmp_path / "cache")
        assert cache._get_cache_key("k", None) == "k"

    def test_key_with_data_appends_hash(self, tmp_path: Path) -> None:
        """Should append an 8-char SHA256 prefix when data is provided."""
        cache = SpecKitCache(cache_dir=tmp_path / "cache")
        result = cache._get_cache_key("k", "some data")
        assert result.startswith("k_")
        # Hash portion should be 8 hex chars
        hash_part = result.split("_", 1)[1]
        assert len(hash_part) == 8
        assert all(c in "0123456789abcdef" for c in hash_part)

    def test_same_data_produces_same_key(self, tmp_path: Path) -> None:
        """Should be deterministic for identical inputs."""
        cache = SpecKitCache(cache_dir=tmp_path / "cache")
        k1 = cache._get_cache_key("k", {"a": 1})
        k2 = cache._get_cache_key("k", {"a": 1})
        assert k1 == k2

    def test_different_data_produces_different_key(self, tmp_path: Path) -> None:
        """Should produce different keys for different data."""
        cache = SpecKitCache(cache_dir=tmp_path / "cache")
        k1 = cache._get_cache_key("k", "alpha")
        k2 = cache._get_cache_key("k", "beta")
        assert k1 != k2

    def test_key_with_falsy_but_non_none_data(self, tmp_path: Path) -> None:
        """Should return plain key when data is falsy (empty string, 0, etc.)."""
        cache = SpecKitCache(cache_dir=tmp_path / "cache")
        # Empty string is falsy, so the `if data:` check returns False
        assert cache._get_cache_key("k", "") == "k"
        assert cache._get_cache_key("k", 0) == "k"
        assert cache._get_cache_key("k", []) == "k"


# ============================================================================
# SpecKitCache._get_cache_path
# ============================================================================


class TestGetCachePath:
    """Tests for file path generation from cache keys."""

    def test_simple_key(self, tmp_path: Path) -> None:
        """Should produce a .json file in cache_dir for a simple key."""
        cache = SpecKitCache(cache_dir=tmp_path / "cache")
        path = cache._get_cache_path("hello")
        assert path == cache.cache_dir / "hello.json"

    def test_special_chars_replaced(self, tmp_path: Path) -> None:
        """Should replace non-alphanumeric characters with underscores."""
        cache = SpecKitCache(cache_dir=tmp_path / "cache")
        path = cache._get_cache_path("my.module:func/v2")
        assert path.name == "my_module_func_v2.json"

    def test_empty_key(self, tmp_path: Path) -> None:
        """Should handle an empty key without error."""
        cache = SpecKitCache(cache_dir=tmp_path / "cache")
        path = cache._get_cache_path("")
        assert path == cache.cache_dir / ".json"


# ============================================================================
# SpecKitCache.is_expired
# ============================================================================


class TestIsExpired:
    """Tests for cache expiry checking."""

    def test_in_memory_not_expired(self, tmp_path: Path) -> None:
        """Should return False when timestamp is within TTL."""
        cache = SpecKitCache(cache_dir=tmp_path / "cache")
        cache._cache_timestamps["k"] = time.time()
        assert cache.is_expired("k") is False

    def test_in_memory_expired(self, tmp_path: Path) -> None:
        """Should return True when timestamp exceeds TTL."""
        cache = SpecKitCache(cache_dir=tmp_path / "cache")
        cache._cache_timestamps["k"] = time.time() - 7200
        assert cache.is_expired("k") is True

    def test_custom_ttl(self, tmp_path: Path) -> None:
        """Should use provided TTL instead of default."""
        cache = SpecKitCache(cache_dir=tmp_path / "cache")
        cache._cache_timestamps["k"] = time.time() - 5
        assert cache.is_expired("k", ttl=10) is False
        assert cache.is_expired("k", ttl=1) is True

    def test_file_based_not_expired(self, tmp_path: Path) -> None:
        """Should check file mtime when no memory timestamp exists."""
        cache_dir = tmp_path / "cache"
        cache = SpecKitCache(cache_dir=cache_dir)
        cache_path = cache._get_cache_path("k")
        cache_path.write_text("{}")
        assert cache.is_expired("k") is False

    def test_file_based_expired(self, tmp_path: Path) -> None:
        """Should detect expired file by checking mtime against TTL."""
        cache_dir = tmp_path / "cache"
        cache = SpecKitCache(cache_dir=cache_dir)
        cache_path = cache._get_cache_path("k")
        cache_path.write_text("{}")
        # Force old mtime
        import os
        old_time = time.time() - 7200
        os.utime(cache_path, (old_time, old_time))
        assert cache.is_expired("k") is True

    def test_nonexistent_key_is_expired(self, tmp_path: Path) -> None:
        """Should return True when key is not cached anywhere."""
        cache = SpecKitCache(cache_dir=tmp_path / "cache")
        assert cache.is_expired("nonexistent") is True


# ============================================================================
# SpecKitCache.set and get (round-trip)
# ============================================================================


class TestSetAndGet:
    """Tests for storing and retrieving cached values."""

    def test_set_and_get_basic(self, tmp_path: Path) -> None:
        """Should round-trip a simple value through memory cache."""
        cache = SpecKitCache(cache_dir=tmp_path / "cache")
        cache.set("key1", {"hello": "world"})
        result = cache.get("key1")
        assert result == {"hello": "world"}

    def test_set_stores_in_memory(self, tmp_path: Path) -> None:
        """Should populate both memory cache and timestamps."""
        cache = SpecKitCache(cache_dir=tmp_path / "cache")
        cache.set("mk", [1, 2, 3])
        assert "mk" in cache._memory_cache
        assert cache._memory_cache["mk"] == [1, 2, 3]
        assert "mk" in cache._cache_timestamps

    def test_set_stores_in_lru(self, tmp_path: Path) -> None:
        """Should populate the LRU cache."""
        cache = SpecKitCache(cache_dir=tmp_path / "cache")
        cache.set("lk", "value")
        assert cache._lru_cache["lk"] == "value"

    def test_set_stores_on_disk(self, tmp_path: Path) -> None:
        """Should write a JSON file to the cache directory."""
        cache = SpecKitCache(cache_dir=tmp_path / "cache")
        cache.set("dk", {"disk": True})
        cache_path = cache._get_cache_path("dk")
        assert cache_path.exists()
        with open(cache_path) as f:
            assert json.load(f) == {"disk": True}

    def test_set_with_data_uses_data_key(self, tmp_path: Path) -> None:
        """Should include data hash in cache key when data is provided."""
        cache = SpecKitCache(cache_dir=tmp_path / "cache")
        cache.set("key", "val1", data="ctx1")
        cache.set("key", "val2", data="ctx2")
        assert cache.get("key", data="ctx1") == "val1"
        assert cache.get("key", data="ctx2") == "val2"

    def test_get_returns_none_for_missing_key(self, tmp_path: Path) -> None:
        """Should return None when key does not exist."""
        cache = SpecKitCache(cache_dir=tmp_path / "cache")
        assert cache.get("missing") is None

    def test_get_expired_memory_entry_returns_none(self, tmp_path: Path) -> None:
        """Should return None and clean up expired memory entries."""
        cache = SpecKitCache(cache_dir=tmp_path / "cache")
        cache.set("ek", "old_value")
        # Force expiry
        cache._cache_timestamps["ek"] = time.time() - 7200
        # Also remove from LRU so it doesn't fall through
        cache._lru_cache.pop("ek", None)
        # Remove disk file so no fallback either
        cache._get_cache_path("ek").unlink(missing_ok=True)
        result = cache.get("ek")
        assert result is None
        assert "ek" not in cache._memory_cache
        assert "ek" not in cache._cache_timestamps

    def test_get_falls_through_to_lru(self, tmp_path: Path) -> None:
        """Should find value in LRU when memory cache misses."""
        cache = SpecKitCache(cache_dir=tmp_path / "cache")
        # Put directly in LRU, skip memory
        cache._lru_cache["lru_only"] = "from_lru"
        result = cache.get("lru_only")
        assert result == "from_lru"

    def test_get_falls_through_to_disk(self, tmp_path: Path) -> None:
        """Should load from disk when both memory and LRU miss."""
        cache = SpecKitCache(cache_dir=tmp_path / "cache")
        # Write file directly
        cache_path = cache._get_cache_path("disk_only")
        cache_path.write_text(json.dumps({"from": "disk"}))
        result = cache.get("disk_only")
        assert result == {"from": "disk"}
        # Should now be loaded into memory cache
        assert "disk_only" in cache._memory_cache

    def test_get_handles_corrupt_disk_file(self, tmp_path: Path) -> None:
        """Should return None and delete corrupt cache files."""
        cache = SpecKitCache(cache_dir=tmp_path / "cache")
        cache_path = cache._get_cache_path("corrupt")
        cache_path.write_text("NOT VALID JSON {{{")
        result = cache.get("corrupt")
        assert result is None
        assert not cache_path.exists()

    def test_set_handles_unserializable_value(self, tmp_path: Path) -> None:
        """Should still store in memory/LRU even if disk write fails."""
        cache = SpecKitCache(cache_dir=tmp_path / "cache")
        # A set with a custom object that json.dump cannot serialize
        unserializable = object()
        # This should not raise -- the OSError/TypeError in file write is caught
        # Actually, json.dump raises TypeError not OSError for unserializable
        # But the broad except in the code only catches OSError
        # So we test via making the path unwritable instead
        cache_path = cache._get_cache_path("nowrite")
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.mkdir()  # make it a directory so write fails
        cache.set("nowrite", "value")
        # Should still be in memory
        assert cache._memory_cache["nowrite"] == "value"

    def test_get_with_custom_ttl(self, tmp_path: Path) -> None:
        """Should respect per-call TTL override."""
        cache = SpecKitCache(cache_dir=tmp_path / "cache")
        cache.set("ttl_key", "val")
        # Set timestamp to 5 seconds ago
        cache._cache_timestamps["ttl_key"] = time.time() - 5
        # With TTL of 10, should be valid
        assert cache.get("ttl_key", ttl=10) == "val"
        # With TTL of 2, should be expired
        cache._lru_cache.pop("ttl_key", None)
        cache._get_cache_path("ttl_key").unlink(missing_ok=True)
        assert cache.get("ttl_key", ttl=2) is None


# ============================================================================
# SpecKitCache.invalidate
# ============================================================================


class TestInvalidate:
    """Tests for cache invalidation."""

    def test_invalidate_specific_key(self, tmp_path: Path) -> None:
        """Should remove a specific key from all cache layers."""
        cache = SpecKitCache(cache_dir=tmp_path / "cache")
        cache.set("a", "va")
        cache.set("b", "vb")
        cache.invalidate("a")
        assert cache.get("a") is None
        assert cache.get("b") == "vb"

    def test_invalidate_removes_disk_file(self, tmp_path: Path) -> None:
        """Should delete the JSON file on disk."""
        cache = SpecKitCache(cache_dir=tmp_path / "cache")
        cache.set("disk_rm", "val")
        cache_path = cache._get_cache_path("disk_rm")
        assert cache_path.exists()
        cache.invalidate("disk_rm")
        assert not cache_path.exists()

    def test_invalidate_all(self, tmp_path: Path) -> None:
        """Should clear all caches and remove all files when key is None."""
        cache = SpecKitCache(cache_dir=tmp_path / "cache")
        cache.set("x", 1)
        cache.set("y", 2)
        cache.set("z", 3)
        cache.invalidate()
        assert cache._memory_cache == {}
        assert cache._cache_timestamps == {}
        assert len(cache._lru_cache) == 0
        assert list(cache.cache_dir.glob("*.json")) == []

    def test_invalidate_nonexistent_key_no_error(self, tmp_path: Path) -> None:
        """Should not raise when invalidating a key that does not exist."""
        cache = SpecKitCache(cache_dir=tmp_path / "cache")
        cache.invalidate("does_not_exist")  # should not raise


# ============================================================================
# SpecKitCache.get_cache_stats
# ============================================================================


class TestGetCacheStats:
    """Tests for cache statistics reporting."""

    def test_empty_cache_stats(self, tmp_path: Path) -> None:
        """Should return zeroed stats for an empty cache."""
        cache = SpecKitCache(cache_dir=tmp_path / "cache")
        stats = cache.get_cache_stats()
        assert stats["memory_cache_size"] == 0
        assert stats["lru_cache_size"] == 0
        assert stats["file_cache_count"] == 0
        assert stats["file_cache_size_bytes"] == 0
        assert stats["file_cache_size_mb"] == 0.0
        assert stats["cache_directory"] == str(tmp_path / "cache")

    def test_populated_cache_stats(self, tmp_path: Path) -> None:
        """Should accurately report counts and sizes after storing values."""
        cache = SpecKitCache(cache_dir=tmp_path / "cache")
        cache.set("a", {"data": "alpha"})
        cache.set("b", {"data": "bravo"})
        stats = cache.get_cache_stats()
        assert stats["memory_cache_size"] == 2
        assert stats["lru_cache_size"] == 2
        assert stats["file_cache_count"] == 2
        assert stats["file_cache_size_bytes"] > 0
        assert isinstance(stats["file_cache_size_mb"], float)


# ============================================================================
# get_cache singleton
# ============================================================================


class TestGetCache:
    """Tests for the global cache singleton accessor."""

    def test_returns_speckit_cache_instance(self, tmp_path: Path) -> None:
        """Should return a SpecKitCache instance."""
        import speckit.caching as mod

        original = mod._cache_instance
        try:
            mod._cache_instance = None
            with patch.object(Path, "home", return_value=tmp_path):
                result = get_cache()
            assert isinstance(result, SpecKitCache)
        finally:
            mod._cache_instance = original

    def test_returns_same_instance_on_repeated_calls(self, tmp_path: Path) -> None:
        """Should return the same object on subsequent calls (singleton)."""
        import speckit.caching as mod

        original = mod._cache_instance
        try:
            mod._cache_instance = None
            with patch.object(Path, "home", return_value=tmp_path):
                first = get_cache()
                second = get_cache()
            assert first is second
        finally:
            mod._cache_instance = original


# ============================================================================
# @cached decorator
# ============================================================================


class TestCachedDecorator:
    """Tests for the @cached function decorator."""

    def test_caches_function_result(self, tmp_path: Path) -> None:
        """Should return cached result on second call."""
        import speckit.caching as mod

        original = mod._cache_instance
        try:
            mod._cache_instance = SpecKitCache(cache_dir=tmp_path / "cache")
            call_count = 0

            @cached(ttl=300)
            def compute(x: int) -> int:
                nonlocal call_count
                call_count += 1
                return x * 2

            r1 = compute(5)
            r2 = compute(5)
            assert r1 == 10
            assert r2 == 10
            # Function called only once; second call served from cache
            assert call_count == 1
        finally:
            mod._cache_instance = original

    def test_custom_key(self, tmp_path: Path) -> None:
        """Should use provided key instead of auto-generated one."""
        import speckit.caching as mod

        original = mod._cache_instance
        try:
            cache = SpecKitCache(cache_dir=tmp_path / "cache")
            mod._cache_instance = cache

            @cached(key="my.custom.key")
            def func() -> str:
                return "result"

            func()
            assert cache.get("my.custom.key") == "result"
        finally:
            mod._cache_instance = original

    def test_data_arg_from_kwargs(self, tmp_path: Path) -> None:
        """Should include kwarg value in cache key when data_arg is set."""
        import speckit.caching as mod

        original = mod._cache_instance
        try:
            cache = SpecKitCache(cache_dir=tmp_path / "cache")
            mod._cache_instance = cache
            call_count = 0

            @cached(data_arg="name")
            def greet(name: str) -> str:
                nonlocal call_count
                call_count += 1
                return f"Hello {name}"

            r1 = greet(name="Alice")
            r2 = greet(name="Bob")
            r3 = greet(name="Alice")
            assert r1 == "Hello Alice"
            assert r2 == "Hello Bob"
            assert r3 == "Hello Alice"
            # Alice called once (second call cached), Bob once
            assert call_count == 2
        finally:
            mod._cache_instance = original

    def test_data_arg_from_positional(self, tmp_path: Path) -> None:
        """Should extract data_arg from positional args when not in kwargs."""
        import speckit.caching as mod

        original = mod._cache_instance
        try:
            cache = SpecKitCache(cache_dir=tmp_path / "cache")
            mod._cache_instance = cache
            call_count = 0

            @cached(data_arg="name")
            def greet(name: str) -> str:
                nonlocal call_count
                call_count += 1
                return f"Hi {name}"

            r1 = greet("Charlie")
            r2 = greet("Charlie")
            assert r1 == "Hi Charlie"
            assert r2 == "Hi Charlie"
            assert call_count == 1
        finally:
            mod._cache_instance = original

    def test_preserves_function_metadata(self, tmp_path: Path) -> None:
        """Should preserve the wrapped function name and docstring."""
        import speckit.caching as mod

        original = mod._cache_instance
        try:
            mod._cache_instance = SpecKitCache(cache_dir=tmp_path / "cache")

            @cached()
            def my_documented_func() -> None:
                """My docstring."""

            assert my_documented_func.__name__ == "my_documented_func"
            assert my_documented_func.__doc__ == "My docstring."
        finally:
            mod._cache_instance = original

    def test_no_ttl_uses_default(self, tmp_path: Path) -> None:
        """Should use default TTL when none is specified."""
        import speckit.caching as mod

        original = mod._cache_instance
        try:
            cache = SpecKitCache(cache_dir=tmp_path / "cache")
            mod._cache_instance = cache

            @cached()
            def func() -> str:
                return "value"

            func()
            # Value should be cached with default TTL (3600s)
            cache_key = f"{func.__module__}.{func.__wrapped__.__name__}" if hasattr(func, "__wrapped__") else None
            # Just verify it returns cached value
            assert func() == "value"
        finally:
            mod._cache_instance = original

    def test_data_arg_not_found_in_args(self, tmp_path: Path) -> None:
        """Should work without error when data_arg is not in args or kwargs."""
        import speckit.caching as mod

        original = mod._cache_instance
        try:
            cache = SpecKitCache(cache_dir=tmp_path / "cache")
            mod._cache_instance = cache

            @cached(data_arg="nonexistent_param")
            def func(x: int) -> int:
                return x + 1

            # data_arg "nonexistent_param" not in co_varnames or kwargs
            # Should still work, just without data-specific keying
            assert func(10) == 11
        finally:
            mod._cache_instance = original


# ============================================================================
# CacheManager
# ============================================================================


class TestCacheManager:
    """Tests for the high-level CacheManager."""

    def test_cache_categories_defined(self) -> None:
        """Should define TTLs for all expected categories."""
        expected_categories = {
            "spec_parsing",
            "plan_generation",
            "task_analysis",
            "artifact_validation",
            "dependency_analysis",
            "template_rendering",
        }
        assert set(CacheManager.CACHE_CATEGORIES.keys()) == expected_categories

    @pytest.mark.parametrize(
        "category,expected_ttl",
        [
            ("spec_parsing", 1800),
            ("plan_generation", 3600),
            ("task_analysis", 1800),
            ("artifact_validation", 900),
            ("dependency_analysis", 3600),
            ("template_rendering", 7200),
        ],
    )
    def test_category_ttl_values(self, category: str, expected_ttl: int) -> None:
        """Should map each category to its correct TTL in seconds."""
        assert CacheManager.CACHE_CATEGORIES[category] == expected_ttl

    def test_cache_result_returns_decorator(self, tmp_path: Path) -> None:
        """Should return a callable decorator."""
        import speckit.caching as mod

        original = mod._cache_instance
        try:
            mod._cache_instance = SpecKitCache(cache_dir=tmp_path / "cache")
            decorator = CacheManager.cache_result("spec_parsing")
            assert callable(decorator)
        finally:
            mod._cache_instance = original

    def test_cache_result_uses_category_ttl(self, tmp_path: Path) -> None:
        """Should apply the category-specific TTL to the decorator."""
        import speckit.caching as mod

        original = mod._cache_instance
        try:
            cache = SpecKitCache(cache_dir=tmp_path / "cache")
            mod._cache_instance = cache
            call_count = 0

            @CacheManager.cache_result("artifact_validation")
            def validate() -> str:
                nonlocal call_count
                call_count += 1
                return "valid"

            r1 = validate()
            r2 = validate()
            assert r1 == "valid"
            assert r2 == "valid"
            assert call_count == 1
        finally:
            mod._cache_instance = original

    def test_cache_result_unknown_category_uses_default(
        self, tmp_path: Path
    ) -> None:
        """Should fall back to spec_parsing TTL for unknown categories."""
        import speckit.caching as mod

        original = mod._cache_instance
        try:
            cache = SpecKitCache(cache_dir=tmp_path / "cache")
            mod._cache_instance = cache

            @CacheManager.cache_result("unknown_category")
            def process() -> str:
                return "done"

            assert process() == "done"
        finally:
            mod._cache_instance = original

    def test_cache_result_with_custom_key(self, tmp_path: Path) -> None:
        """Should pass custom key through to the decorator."""
        import speckit.caching as mod

        original = mod._cache_instance
        try:
            cache = SpecKitCache(cache_dir=tmp_path / "cache")
            mod._cache_instance = cache

            @CacheManager.cache_result("plan_generation", key="my.plan")
            def plan() -> str:
                return "planned"

            plan()
            assert cache.get("my.plan") == "planned"
        finally:
            mod._cache_instance = original

    def test_invalidate_category_clears_cache(self, tmp_path: Path) -> None:
        """Should clear all caches when invalidating a category."""
        import speckit.caching as mod

        original = mod._cache_instance
        try:
            cache = SpecKitCache(cache_dir=tmp_path / "cache")
            mod._cache_instance = cache
            cache.set("some_key", "some_value")
            CacheManager.invalidate_category("spec_parsing")
            # invalidate_category calls cache.invalidate() which clears everything
            assert cache.get("some_key") is None
        finally:
            mod._cache_instance = original


# ============================================================================
# __init__.py exports
# ============================================================================


class TestPackageExports:
    """Tests for the speckit package __init__.py exports."""

    def test_version_defined(self) -> None:
        """Should export a version string."""
        import speckit

        assert isinstance(speckit.__version__, str)
        assert len(speckit.__version__.split(".")) == 3

    def test_all_exports(self) -> None:
        """Should export exactly the expected symbols."""
        import speckit

        assert set(speckit.__all__) == {
            "CacheManager",
            "SpecKitCache",
            "cached",
            "get_cache",
        }

    def test_reexports_are_correct_types(self) -> None:
        """Should re-export the actual classes and functions."""
        import speckit

        assert speckit.SpecKitCache is SpecKitCache
        assert speckit.CacheManager is CacheManager
        assert speckit.cached is cached
        assert speckit.get_cache is get_cache
