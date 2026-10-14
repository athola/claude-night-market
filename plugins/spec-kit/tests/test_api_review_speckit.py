"""Regression tests from the API review."""

from __future__ import annotations

import warnings
from pathlib import Path

import pytest

import speckit.caching as caching
from speckit.caching import CacheManager, SpecKitCache, cached


@pytest.fixture
def isolated_cache(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> SpecKitCache:
    """Given a global cache pointed at a temp directory."""
    cache = SpecKitCache(cache_dir=tmp_path)
    monkeypatch.setattr(caching, "_cache_instance", cache)
    return cache


def test_cached_none_result_is_a_hit(isolated_cache: SpecKitCache) -> None:
    """A function returning None runs once, not on every call."""
    calls: list[int] = []

    @cached(key="none-fn")
    def returns_none() -> None:
        calls.append(1)

    returns_none()
    returns_none()
    assert len(calls) == 1


def test_set_keeps_result_when_value_is_not_json_serializable(
    isolated_cache: SpecKitCache, tmp_path: Path
) -> None:
    """A set result is returned and held in memory, with no partial file."""
    calls: list[int] = []

    @cached(key="set-fn")
    def returns_set() -> set[int]:
        calls.append(1)
        return {1, 2}

    assert returns_set() == {1, 2}
    assert returns_set() == {1, 2}
    assert len(calls) == 1
    assert list(tmp_path.glob("*.json")) == []


def test_set_with_ttl_warns_because_ttl_is_ignored(tmp_path: Path) -> None:
    """Passing ttl to set is deprecated: only get honors a ttl."""
    cache = SpecKitCache(cache_dir=tmp_path)
    with pytest.warns(DeprecationWarning, match="ttl"):
        cache.set("a", "v", ttl=1)


def test_cached_decorator_does_not_emit_deprecation_warning(
    isolated_cache: SpecKitCache,
) -> None:
    """The decorator no longer forwards ttl to set."""

    @cached(ttl=5, key="quiet")
    def fn() -> int:
        return 1

    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        fn()


def test_invalidate_prefix_leaves_longer_category_files(tmp_path: Path) -> None:
    """Invalidating 'spec:' must not delete 'spec_extra:' disk entries."""
    cache = SpecKitCache(cache_dir=tmp_path)
    cache.set("spec:1", "a")
    cache.set("spec_extra:1", "b")
    cache.invalidate_prefix("spec:")
    cache._memory_cache.clear()
    cache._cache_timestamps.clear()
    assert cache.get("spec:1") is None
    assert cache.get("spec_extra:1") == "b"


def test_cache_result_rejects_unknown_category() -> None:
    """A typo'd category fails instead of taking the spec_parsing TTL."""
    with pytest.raises(ValueError, match="plan_generaton"):
        CacheManager.cache_result("plan_generaton")


def test_invalidate_category_rejects_unknown_category() -> None:
    """A typo'd category fails instead of invalidating nothing."""
    with pytest.raises(ValueError, match="typo_cat"):
        CacheManager.invalidate_category("typo_cat")
