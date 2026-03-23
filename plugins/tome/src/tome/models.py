"""Data models for tome research sessions and findings."""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


_VALID_CHANNELS = frozenset({"code", "discourse", "academic", "triz"})


@dataclass
class Finding:
    """A single research finding from a channel."""

    source: str
    channel: str
    title: str
    url: str
    relevance: float
    summary: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.relevance = max(0.0, min(1.0, self.relevance))
        if self.channel not in _VALID_CHANNELS:
            raise ValueError(
                f"Unknown channel: {self.channel!r}. Valid: {sorted(_VALID_CHANNELS)}"
            )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Finding:
        try:
            return cls(
                source=d["source"],
                channel=d["channel"],
                title=d["title"],
                url=d["url"],
                relevance=d["relevance"],
                summary=d["summary"],
                metadata=d.get("metadata", {}),
            )
        except KeyError as exc:
            raise KeyError(
                f"Finding.from_dict missing required field {exc}: "
                f"keys present = {sorted(d.keys())}"
            ) from exc


@dataclass
class DomainClassification:
    """Result of classifying a research topic into a domain."""

    domain: str
    triz_depth: str
    channel_weights: dict[str, float]
    confidence: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> DomainClassification:
        return cls(
            domain=d["domain"],
            triz_depth=d["triz_depth"],
            channel_weights=dict(d["channel_weights"]),
            confidence=d["confidence"],
        )


@dataclass
class SessionSummary:
    """Lightweight summary of a research session."""

    id: str
    topic: str
    domain: str
    status: str
    finding_count: int
    created_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "topic": self.topic,
            "domain": self.domain,
            "status": self.status,
            "finding_count": self.finding_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> SessionSummary:
        raw_created = d.get("created_at")
        return cls(
            id=d["id"],
            topic=d["topic"],
            domain=d["domain"],
            status=d["status"],
            finding_count=d["finding_count"],
            created_at=datetime.fromisoformat(raw_created) if raw_created else None,
        )


@dataclass
class ResearchSession:
    """A full research session with findings."""

    topic: str
    domain: str
    triz_depth: str
    channels: list[str]
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    findings: list[Finding] = field(default_factory=list)
    status: str = "pending"
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def add_finding(self, finding: Finding) -> None:
        """Append a finding and update the modified timestamp."""
        self.findings.append(finding)
        self.updated_at = _now()

    def mark_complete(self) -> None:
        """Transition status to complete."""
        self.status = "complete"
        self.updated_at = _now()

    def to_summary(self) -> SessionSummary:
        """Return a lightweight summary of this session."""
        return SessionSummary(
            id=self.id,
            topic=self.topic,
            domain=self.domain,
            status=self.status,
            finding_count=len(self.findings),
            created_at=self.created_at,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "topic": self.topic,
            "domain": self.domain,
            "triz_depth": self.triz_depth,
            "channels": list(self.channels),
            "findings": [f.to_dict() for f in self.findings],
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> ResearchSession:
        try:
            raw_created: str | None = d.get("created_at")
            raw_updated: str | None = d.get("updated_at")
            return cls(
                id=d["id"],
                topic=d["topic"],
                domain=d["domain"],
                triz_depth=d["triz_depth"],
                channels=list(d["channels"]),
                findings=[Finding.from_dict(f) for f in d.get("findings", [])],
                status=d.get("status", "pending"),
                created_at=datetime.fromisoformat(raw_created) if raw_created else None,
                updated_at=datetime.fromisoformat(raw_updated) if raw_updated else None,
            )
        except KeyError as exc:
            raise KeyError(
                f"ResearchSession.from_dict missing required field {exc}: "
                f"keys present = {sorted(d.keys())}"
            ) from exc


@dataclass
class Citation:
    """A formatted bibliographic citation."""

    source_type: str
    authors: list[str]
    title: str
    venue: str
    url: str
    year: int | None = None
    doi: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Citation:
        return cls(
            source_type=d["source_type"],
            authors=list(d.get("authors", [])),
            title=d["title"],
            venue=d["venue"],
            url=d["url"],
            year=d.get("year"),
            doi=d.get("doi"),
            extra=d.get("extra", {}),
        )


@dataclass
class ResearchPlan:
    """A planned research execution with channel weights and budget."""

    channels: list[str]
    weights: dict[str, float]
    triz_depth: str
    estimated_budget: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> ResearchPlan:
        return cls(
            channels=list(d["channels"]),
            weights=dict(d["weights"]),
            triz_depth=d["triz_depth"],
            estimated_budget=d["estimated_budget"],
        )
