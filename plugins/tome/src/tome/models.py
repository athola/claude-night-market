"""Data models for tome research sessions and findings."""

from __future__ import annotations

import uuid
import warnings
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


_VALID_CHANNELS = frozenset({"code", "discourse", "academic", "triz"})

# Channels that answer by probing an external index. Their silence is a
# fact about the world once a positive control shows they were not
# blind, so they are the only channels a coverage verdict may reason
# over.
#
# ``triz`` is excluded because it generates cross-domain analogies
# rather than retrieving records of prior work. Counting its output as
# evidence would let the tool manufacture the finding that a field is
# well covered, and demanding an index probe of a channel with no index
# would pin every session to INCONCLUSIVE for an unrelated reason.
RETRIEVAL_CHANNELS = frozenset({"academic", "code", "discourse"})


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
            warnings.warn(
                f"Unknown channel: {self.channel!r}. Valid: {sorted(_VALID_CHANNELS)}",
                stacklevel=2,
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
                f"Finding.from_dict missing required field {exc}: keys present = {sorted(d.keys())}"
            ) from exc


@dataclass(frozen=True)
class CitationEdge:
    """A directed citation edge: ``citing_id`` cites ``cited_id``.

    Both endpoints are Semantic Scholar paper IDs. The edge is the
    relationship tome used to discard when flattening citation-chain
    responses into a list of papers.

    Edges are parsed from API responses and written straight into the
    knowledge graph, so the shapes the graph cannot represent are
    refused here instead of persisted: an empty ID becomes an
    empty-keyed entity, and a self-citation becomes a synapse loop that
    inflates the node's own centrality. Callers parsing untrusted
    payloads skip such items at the boundary rather than construct them.

    Raises:
        ValueError: When either endpoint is blank, or when both
            endpoints name the same paper.
    """

    citing_id: str
    cited_id: str

    def __post_init__(self) -> None:
        if not self.citing_id.strip() or not self.cited_id.strip():
            raise ValueError(
                "citation edges require non-empty paper IDs, got "
                f"citing_id={self.citing_id!r}, cited_id={self.cited_id!r}"
            )
        if self.citing_id == self.cited_id:
            raise ValueError(f"a paper cannot cite itself: {self.citing_id!r}")

    def to_dict(self) -> dict[str, str]:
        return {"citing_id": self.citing_id, "cited_id": self.cited_id}

    @classmethod
    def from_dict(cls, d: dict[str, str]) -> CitationEdge:
        return cls(citing_id=d["citing_id"], cited_id=d["cited_id"])


@dataclass
class DomainClassification:
    """Result of classifying a research topic into a domain."""

    domain: str
    triz_depth: str
    channel_weights: dict[str, float]
    confidence: float
    # Domains that had keyword support when the classifier abstained.
    # Empty on a confident classification. This is what makes an
    # abstention inspectable instead of silent.
    candidates: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> DomainClassification:
        return cls(
            domain=d["domain"],
            triz_depth=d["triz_depth"],
            channel_weights=dict(d["channel_weights"]),
            confidence=d["confidence"],
            candidates=list(d.get("candidates", [])),
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
    # What each channel actually searched. Findings record what was
    # found; this records what was looked for, which is the only thing
    # that makes an empty channel interpretable. Channel status is
    # derived from these logs (tome.synthesis.quality.channel_outcomes)
    # and deliberately not stored: a stored status and the logs behind
    # it can drift apart, and then neither can be trusted.
    query_log: list[QueryLog] = field(default_factory=list)

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
            "query_log": [q.to_dict() for q in self.query_log],
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
                # Sessions on disk predate this field. Defaulting to []
                # makes them load as "no record", which channel_outcomes
                # reads as unknown rather than as an empty field.
                query_log=[QueryLog.from_dict(q) for q in d.get("query_log", [])],
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
class QueryLog:
    """A record of a query attempted during research.

    ``error`` names why a query failed, and ``succeeded`` is derived
    from it rather than set independently. The two fields express one
    fact, so letting callers set both invites them to disagree: a log
    reading ``succeeded=False, error=None`` is the unexplained failure
    this record exists to eliminate, and one reading
    ``succeeded=True, error="rate_limit"`` is worse, because a reader
    downstream will believe the count.
    """

    channel: str
    query: str
    source: str
    result_count: int = 0
    succeeded: bool = True
    # Error kind, not an error message: "rate_limit" and "source_error"
    # carry different instructions to a reader (re-run vs investigate),
    # and a free-text message cannot be dispatched on.
    error: str | None = None

    def __post_init__(self) -> None:
        if self.error is not None:
            self.succeeded = False
        elif not self.succeeded:
            raise ValueError(
                "QueryLog(succeeded=False) requires an error kind; a failure "
                "with no named cause is indistinguishable from a channel that "
                "searched properly and found nothing, which is the confusion "
                "this record exists to remove"
            )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> QueryLog:
        return cls(
            channel=d["channel"],
            query=d["query"],
            source=d["source"],
            result_count=d.get("result_count", 0),
            succeeded=d.get("succeeded", True),
            error=d.get("error"),
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
