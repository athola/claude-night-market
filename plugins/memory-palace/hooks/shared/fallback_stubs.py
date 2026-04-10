"""Fallback stubs for memory_palace types when the package is unavailable.

These provide no-op implementations so the research interceptor can
degrade gracefully on system Python 3.9 without pyyaml.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace
from typing import Any


@dataclass
class DomainAlignment:
    configured_domains: list = field(default_factory=list)
    matched_domains: list = field(default_factory=list)

    @property
    def is_aligned(self) -> bool:
        return bool(self.matched_domains)


@dataclass
class IntakeFlagPayload:
    query: str = ""
    should_flag_for_intake: bool = False
    novelty_score: float = 0.0
    domain_alignment: Any = None
    delta_reasoning: str = ""
    duplicate_entry_ids: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "query": self.query,
            "should_flag_for_intake": self.should_flag_for_intake,
            "novelty_score": self.novelty_score,
            "delta_reasoning": self.delta_reasoning,
            "duplicate_entry_ids": self.duplicate_entry_ids,
        }


class RedundancyLevel:
    EXACT_MATCH = "exact_match"
    HIGHLY_REDUNDANT = "redundant"
    PARTIAL_OVERLAP = "partial"
    NOVEL = "novel"


@dataclass
class AutonomyProfile:
    global_level: int = 0
    domain_controls: dict = field(default_factory=dict)

    def effective_level_for(self, domains: Any = None) -> int:
        return self.global_level

    def should_auto_approve_duplicates(self, domains: Any = None) -> bool:
        return self.effective_level_for(domains) >= 1

    def should_auto_approve_partial(self, domains: Any = None) -> bool:
        return self.effective_level_for(domains) >= 2

    def should_auto_approve_all(self, domains: Any = None) -> bool:
        return self.effective_level_for(domains) >= 3


class CacheLookup:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize no-op cache lookup stub."""

    def search(self, *args: Any, **kwargs: Any) -> list:
        return []


class AutonomyStateStore:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize no-op autonomy state store stub."""

    def load_profile(self, *args: Any, **kwargs: Any) -> AutonomyProfile:
        return AutonomyProfile()

    def build_profile(self, *args: Any, **kwargs: Any) -> AutonomyProfile:
        return AutonomyProfile()


class ResearchTelemetryEvent:
    @staticmethod
    def build(*args: Any, **kwargs: Any) -> Any:
        return SimpleNamespace(**kwargs)


class TelemetryLogger:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize no-op telemetry logger stub."""

    def emit(self, *args: Any, **kwargs: Any) -> None:
        pass


def resolve_telemetry_path(*args: Any, **kwargs: Any) -> Path:
    """Return a no-op path stub when leyline is absent."""
    return Path("/dev/null")
