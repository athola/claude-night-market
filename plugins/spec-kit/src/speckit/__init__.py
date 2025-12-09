"""Spec-Kit: Spec Driven Development toolkit with enhanced superpowers integration."""

__version__ = "3.1.0"
__author__ = "Claude Skills"
__description__ = (
    "Spec Driven Development toolkit with enhanced superpowers integration"
)

# Import key components
from .caching import CacheManager, SpecKitCache, cached, get_cache

__all__ = [
    "SpecKitCache",
    "get_cache",
    "cached",
    "CacheManager",
]
