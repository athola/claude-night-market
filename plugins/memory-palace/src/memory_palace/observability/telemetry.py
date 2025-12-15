"""Telemetry helpers for Memory Palace hooks."""

from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class ResearchTelemetryEvent:
    """CSV-friendly representation of a cache interception."""

    timestamp: str
    query_id: str
    query: str
    tool_name: str
    mode: str
    decision: str
    cache_hits: int
    returned_entries: int
    top_entry_id: str | None
    match_score: float | None
    match_strength: str | None
    freshness_required: bool
    evergreen_topic: bool
    should_flag_for_intake: bool
    latency_ms: int
    novelty_score: float | None
    aligned_domains: str | None
    intake_delta_reasoning: str | None
    duplicate_entry_ids: str | None
    notes: str | None = None

    @classmethod
    def build(  # noqa: PLR0913 - telemetry events require rich fields
        cls,
        *,
        query_id: str,
        query: str,
        tool_name: str,
        mode: str,
        decision: str,
        cache_hits: int,
        returned_entries: int,
        top_entry_id: str | None,
        match_score: float | None,
        match_strength: str | None,
        freshness_required: bool,
        evergreen_topic: bool,
        should_flag_for_intake: bool,
        latency_ms: int,
        novelty_score: float | None,
        aligned_domains: str | None,
        intake_delta_reasoning: str | None,
        duplicate_entry_ids: str | None,
        notes: str | None = None,
    ) -> ResearchTelemetryEvent:
        """Build and stamp the event with current timestamp."""
        timestamp = datetime.now(UTC).isoformat()
        return cls(
            timestamp=timestamp,
            query_id=query_id,
            query=query,
            tool_name=tool_name,
            mode=mode,
            decision=decision,
            cache_hits=cache_hits,
            returned_entries=returned_entries,
            top_entry_id=top_entry_id,
            match_score=match_score,
            match_strength=match_strength,
            freshness_required=freshness_required,
            evergreen_topic=evergreen_topic,
            should_flag_for_intake=should_flag_for_intake,
            latency_ms=latency_ms,
            novelty_score=novelty_score,
            aligned_domains=aligned_domains,
            intake_delta_reasoning=intake_delta_reasoning,
            duplicate_entry_ids=duplicate_entry_ids,
            notes=notes,
        )


class TelemetryLogger:
    """Append-only CSV writer with automatic header management."""

    def __init__(self, file_path: str | Path) -> None:
        """Initialize logger and ensure directory exists."""
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self._fieldnames = [
            "timestamp",
            "query_id",
            "query",
            "tool_name",
            "mode",
            "decision",
            "cache_hits",
            "returned_entries",
            "top_entry_id",
            "match_score",
            "match_strength",
            "freshness_required",
            "evergreen_topic",
            "should_flag_for_intake",
            "latency_ms",
            "novelty_score",
            "aligned_domains",
            "intake_delta_reasoning",
            "duplicate_entry_ids",
            "notes",
        ]

    def log_event(self, event: ResearchTelemetryEvent) -> None:
        """Persist the event to CSV, adding a header if needed."""
        row = asdict(event)
        needs_header = not self.file_path.exists() or self.file_path.stat().st_size == 0

        with self.file_path.open("a", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=self._fieldnames)
            if needs_header:
                writer.writeheader()
            writer.writerow(row)


def resolve_telemetry_path(
    plugin_root: Path,
    telemetry_config: dict[str, Any],
) -> Path:
    """Resolve the configured telemetry file relative to plugin root."""
    configured_path = telemetry_config.get("file", "data/telemetry/memory-palace.csv")
    telemetry_path = Path(configured_path)
    if not telemetry_path.is_absolute():
        telemetry_path = plugin_root / telemetry_path
    return telemetry_path
