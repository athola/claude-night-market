"""Provide caching utilities for spec-kit performance optimization."""

import hashlib
import json
import time
from collections.abc import Callable
from functools import wraps
from pathlib import Path
from typing import Any

import cachetools  # type: ignore[import-untyped]


class SpecKitCache:
    """Provide a detailed caching system for spec-kit operations."""

    def __init__(self, cache_dir: Path | None = None) -> None:
        """Initialize cache with optional custom directory."""
        self.cache_dir = cache_dir or Path.home() / ".spec-kit" / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Memory cache for frequently accessed data
        self._memory_cache: dict[str, Any] = {}
        self._cache_timestamps: dict[str, float] = {}

        # Default TTL: 1 hour
        self.default_ttl = 3600

        # Initialize cachetools LRU cache
        self._lru_cache: cachetools.LRUCache = cachetools.LRUCache(maxsize=128)

    def _get_cache_key(self, key: str, data: Any | None = None) -> str:
        """Generate a unique cache key."""
        if data:
            # Include data hash in key for data-specific caching
            # Using SHA256 for better collision resistance (not for cryptographic security)
            data_hash = hashlib.sha256(str(data).encode()).hexdigest()[:8]
            return f"{key}_{data_hash}"
        return key

    def _get_cache_path(self, key: str) -> Path:
        """Get file path for cached data."""
        safe_key = "".join(c if c.isalnum() else "_" for c in key)
        return self.cache_dir / f"{safe_key}.json"

    def is_expired(self, key: str, ttl: int | None = None) -> bool:
        """Check if cached data is expired."""
        ttl = ttl or self.default_ttl

        if key in self._cache_timestamps:
            return time.time() - self._cache_timestamps[key] > ttl

        # Check file-based cache
        cache_path = self._get_cache_path(key)
        if cache_path.exists():
            file_age = time.time() - cache_path.stat().st_mtime
            return file_age > ttl

        return True  # Not cached = expired

    def get(
        self,
        key: str,
        data: Any | None = None,
        ttl: int | None = None,
    ) -> Any | None:
        """Get cached data."""
        cache_key = self._get_cache_key(key, data)

        # Check memory cache first
        if cache_key in self._memory_cache:
            if not self.is_expired(cache_key, ttl):
                return self._memory_cache[cache_key]
            # Remove expired entry
            del self._memory_cache[cache_key]
            if cache_key in self._cache_timestamps:
                del self._cache_timestamps[cache_key]

        # Check LRU cache
        try:
            return self._lru_cache[cache_key]
        except KeyError:
            pass

        # Check file-based cache
        cache_path = self._get_cache_path(cache_key)
        if cache_path.exists() and not self.is_expired(cache_key, ttl):
            try:
                with open(cache_path, encoding="utf-8") as f:
                    cached_data = json.load(f)
                    # Load into memory cache for faster access
                    self._memory_cache[cache_key] = cached_data
                    self._cache_timestamps[cache_key] = time.time()
                    return cached_data
            except (OSError, json.JSONDecodeError):
                # Invalid cache file, remove it
                cache_path.unlink(missing_ok=True)

        return None

    def set(
        self,
        key: str,
        value: Any,
        data: Any | None = None,
        ttl: int | None = None,
    ) -> None:
        """Cache data with optional TTL."""
        cache_key = self._get_cache_key(key, data)

        # Store in memory cache
        self._memory_cache[cache_key] = value
        self._cache_timestamps[cache_key] = time.time()

        # Store in LRU cache
        self._lru_cache[cache_key] = value

        # Store in file-based cache
        cache_path = self._get_cache_path(cache_key)
        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(value, f, ensure_ascii=False, indent=2)
        except OSError:
            # Log error but don't fail
            pass

    def invalidate(self, key: str | None = None) -> None:
        """Invalidate cache entries."""
        if key:
            cache_key = self._get_cache_key(key)

            # Remove from memory cache
            self._memory_cache.pop(cache_key, None)
            self._cache_timestamps.pop(cache_key, None)

            # Remove from LRU cache
            self._lru_cache.pop(cache_key, None)

            # Remove file-based cache
            cache_path = self._get_cache_path(cache_key)
            cache_path.unlink(missing_ok=True)
        else:
            # Clear all caches
            self._memory_cache.clear()
            self._cache_timestamps.clear()
            self._lru_cache.clear()

            # Remove all cache files
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink(missing_ok=True)

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        cache_files = list(self.cache_dir.glob("*.json"))
        total_size = sum(f.stat().st_size for f in cache_files)

        return {
            "memory_cache_size": len(self._memory_cache),
            "lru_cache_size": len(self._lru_cache),
            "file_cache_count": len(cache_files),
            "file_cache_size_bytes": total_size,
            "file_cache_size_mb": round(total_size / 1024 / 1024, 2),
            "cache_directory": str(self.cache_dir),
        }


# Global cache instance
_cache_instance: SpecKitCache | None = None


def get_cache() -> SpecKitCache:
    """Get or create global cache instance."""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = SpecKitCache()
    return _cache_instance


def cached(
    ttl: int | None = None,
    key: str | None = None,
    data_arg: str | None = None,
) -> Any:
    """Cache function results with TTL.

    Args:
        ttl: Time to live in seconds
        key: Custom cache key (defaults to function name)
        data_arg: Argument name to include in cache key

    """

    def decorator(func: Callable) -> Any:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            cache = get_cache()

            # Generate cache key
            cache_key = key or f"{func.__module__}.{func.__name__}"

            # Include specific argument in key if specified
            cache_data = None
            if data_arg:
                if data_arg in kwargs:
                    cache_data = kwargs[data_arg]
                else:
                    # Try to get from positional args
                    arg_names = func.__code__.co_varnames
                    if data_arg in arg_names:
                        arg_index = arg_names.index(data_arg)
                        if arg_index < len(args):
                            cache_data = args[arg_index]

            # Try to get from cache
            cached_result = cache.get(cache_key, cache_data, ttl)
            if cached_result is not None:
                return cached_result

            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, cache_data, ttl)

            return result

        return wrapper

    return decorator


class CacheManager:
    """Manage caches for spec-kit operations at a high level."""

    CACHE_CATEGORIES = {
        "spec_parsing": 1800,  # 30 minutes
        "plan_generation": 3600,  # 1 hour
        "task_analysis": 1800,  # 30 minutes
        "artifact_validation": 900,  # 15 minutes
        "dependency_analysis": 3600,  # 1 hour
        "template_rendering": 7200,  # 2 hours
    }

    @classmethod
    def cache_result(cls, category: str, key: str | None = None) -> Any:
        """Create a decorator with category-based TTL."""
        ttl = cls.CACHE_CATEGORIES.get(category, cls.CACHE_CATEGORIES["spec_parsing"])
        return cached(ttl=ttl, key=key)

    @classmethod
    def invalidate_category(cls, category: str) -> None:
        """Invalidate all cache entries for a category."""
        cache = get_cache()
        # This is a simplified implementation
        # In practice, you might want more sophisticated category tracking
        cache.invalidate()


# Performance monitoring
def cache_performance_monitor(func: Callable) -> Any:
    """Monitor cache performance for a function."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.time()

        # Check if result is cached
        cache = get_cache()
        cache_key = f"perf:{func.__module__}.{func.__name__}"
        is_cached = cache.get(cache_key) is not None

        result = func(*args, **kwargs)

        execution_time = time.time() - start_time

        # Log performance metrics
        metrics = {
            "function": f"{func.__module__}.{func.__name__}",
            "execution_time": execution_time,
            "cached": is_cached,
            "timestamp": time.time(),
        }

        # Store performance metrics
        perf_key = f"perf_metrics:{func.__name__}"
        cache.set(perf_key, metrics, ttl=86400)  # Keep for 24 hours

        return result

    return wrapper


def get_performance_report() -> dict[str, Any]:
    """Get performance report for cached functions."""
    cache = get_cache()
    report = {"cache_stats": cache.get_cache_stats(), "function_metrics": {}}

    # Collect performance metrics
    for cache_file in cache.cache_dir.glob("perf_metrics_*.json"):
        try:
            with open(cache_file, encoding="utf-8") as f:
                metrics = json.load(f)
                func_name = metrics.get("function", "unknown")
                report["function_metrics"][func_name] = metrics
        except (OSError, json.JSONDecodeError):
            continue

    return report
