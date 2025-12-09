"""Shared curation/intake payload models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class DomainAlignment:
    """Describes how a query aligns with configured domains of interest."""

    configured_domains: list[str] = field(default_factory=list)
    matched_domains: list[str] = field(default_factory=list)

    @property
    def is_aligned(self) -> bool:
        return bool(self.matched_domains)

    def to_dict(self) -> dict[str, Any]:
        return {
            "configured_domains": self.configured_domains,
            "matched_domains": self.matched_domains,
            "is_aligned": self.is_aligned,
        }


@dataclass(slots=True)
class IntakeFlagPayload:
    """Payload describing why the hook should flag a query for intake."""

    query: str
    should_flag_for_intake: bool
    novelty_score: float
    domain_alignment: DomainAlignment
    delta_reasoning: str
    duplicate_entry_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize for JSON/telemetry consumption."""
        return {
            "query": self.query,
            "should_flag_for_intake": self.should_flag_for_intake,
            "novelty_score": round(self.novelty_score, 3),
            "domain_alignment": self.domain_alignment.to_dict(),
            "delta_reasoning": self.delta_reasoning,
            "duplicate_entry_ids": self.duplicate_entry_ids,
        }
