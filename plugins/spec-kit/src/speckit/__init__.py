"""Provide Spec Driven Development toolkit with enhanced superpowers integration."""

__version__ = "1.6.4"

# Import key components
from .caching import CacheManager, SpecKitCache, cached, get_cache

__all__ = [
    "CacheManager",
    "SpecKitCache",
    "cached",
    "get_cache",
]
