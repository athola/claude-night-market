"""Provide Spec Driven Development toolkit with enhanced superpowers integration."""

__version__ = "1.5.7"
__author__ = "Claude Skills"
__description__ = (
    "Spec Driven Development toolkit with enhanced superpowers integration"
)

# Import key components
from .caching import CacheManager, SpecKitCache, cached, get_cache

__all__ = [
    "CacheManager",
    "SpecKitCache",
    "cached",
    "get_cache",
]
