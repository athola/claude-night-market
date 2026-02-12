"""Tests for observability telemetry module.

Tests the ResearchTelemetryEvent dataclass and TelemetryLogger CSV writer,
including event construction, timestamp stamping, CSV header management,
and path resolution.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import pytest

# Add src to path for direct import
sys.path.insert(
    0, str(Path(__file__).parent.parent / "src")
)

from memory_palace.observability.telemetry import (
    ResearchTelemetryEvent,
    TelemetryLogger,
    resolve_telemetry_path,
)


class TestResearchTelemetryEventBuild:
    """Tests for ResearchTelemetryEvent.build() factory method."""

    def test_build_stamps_timestamp(self) -> None:
        """build() should auto-stamp the event with current UTC time."""
        event = ResearchTelemetryEvent.build(
            query_id="q-1",
            query="test query",
            tool_name="WebSearch",
            mode="cache_first",
            decision="augment",
            cache_hits=1,
            returned_entries=1,
            top_entry_id="entry-1",
            match_score=0.85,
            match_strength="strong",
            freshness_required=False,
            evergreen_topic=True,
            should_flag_for_intake=False,
            latency_ms=42,
            novelty_score=0.5,
            aligned_domains=None,
            intake_delta_reasoning="test",
            duplicate_entry_ids=None,
        )
        assert event.timestamp is not None
        assert "T" in event.timestamp  # ISO format
        assert event.query_id == "q-1"
        assert event.decision == "augment"

    def test_build_preserves_all_fields(self) -> None:
        """build() should pass through all provided fields."""
        event = ResearchTelemetryEvent.build(
            query_id="q-2",
            query="python async",
            tool_name="WebFetch",
            mode="cache_only",
            decision="block",
            cache_hits=3,
            returned_entries=2,
            top_entry_id="top-entry",
            match_score=0.95,
            match_strength="exact",
            freshness_required=True,
            evergreen_topic=False,
            should_flag_for_intake=True,
            latency_ms=100,
            novelty_score=0.1,
            aligned_domains="python,async",
            intake_delta_reasoning="high overlap",
            duplicate_entry_ids="e-1,e-2",
            notes="test note",
        )
        assert event.tool_name == "WebFetch"
        assert event.cache_hits == 3
        assert event.freshness_required is True
        assert event.notes == "test note"
        assert event.aligned_domains == "python,async"


class TestTelemetryLogger:
    """Tests for TelemetryLogger CSV output."""

    def test_log_event_creates_file_with_header(self, tmp_path: Path) -> None:
        """First event should create file with CSV header row."""
        csv_path = tmp_path / "telemetry" / "test.csv"
        logger = TelemetryLogger(csv_path)

        event = ResearchTelemetryEvent.build(
            query_id="q-1",
            query="test",
            tool_name="WebSearch",
            mode="cache_first",
            decision="allow",
            cache_hits=0,
            returned_entries=0,
            top_entry_id=None,
            match_score=None,
            match_strength=None,
            freshness_required=False,
            evergreen_topic=False,
            should_flag_for_intake=False,
            latency_ms=10,
            novelty_score=None,
            aligned_domains=None,
            intake_delta_reasoning=None,
            duplicate_entry_ids=None,
        )
        logger.log_event(event)

        assert csv_path.exists()
        with csv_path.open() as f:
            reader = csv.reader(f)
            header = next(reader)
            assert "timestamp" in header
            assert "query_id" in header
            assert "decision" in header
            data_row = next(reader)
            assert data_row[header.index("query_id")] == "q-1"

    def test_log_event_appends_without_duplicate_header(self, tmp_path: Path) -> None:
        """Subsequent events should append without adding another header."""
        csv_path = tmp_path / "telemetry.csv"
        logger = TelemetryLogger(csv_path)

        for i in range(3):
            event = ResearchTelemetryEvent.build(
                query_id=f"q-{i}",
                query=f"query {i}",
                tool_name="WebSearch",
                mode="cache_first",
                decision="allow",
                cache_hits=0,
                returned_entries=0,
                top_entry_id=None,
                match_score=None,
                match_strength=None,
                freshness_required=False,
                evergreen_topic=False,
                should_flag_for_intake=False,
                latency_ms=10,
                novelty_score=None,
                aligned_domains=None,
                intake_delta_reasoning=None,
                duplicate_entry_ids=None,
            )
            logger.log_event(event)

        lines = csv_path.read_text().strip().split("\n")
        assert len(lines) == 4  # 1 header + 3 data rows

    def test_log_event_creates_parent_directories(self, tmp_path: Path) -> None:
        """Logger should create parent directories if they don't exist."""
        csv_path = tmp_path / "deep" / "nested" / "dir" / "telemetry.csv"
        logger = TelemetryLogger(csv_path)
        assert csv_path.parent.exists()


class TestResolveTelemetryPath:
    """Tests for resolve_telemetry_path utility."""

    def test_relative_path_resolved_against_plugin_root(self, tmp_path: Path) -> None:
        """Relative paths should be resolved against plugin_root."""
        config = {"file": "data/telemetry/test.csv"}
        result = resolve_telemetry_path(tmp_path, config)
        assert result == tmp_path / "data/telemetry/test.csv"

    def test_absolute_path_used_directly(self, tmp_path: Path) -> None:
        """Absolute paths should be used as-is."""
        abs_path = "/tmp/telemetry.csv"
        config = {"file": abs_path}
        result = resolve_telemetry_path(tmp_path, config)
        assert result == Path(abs_path)

    def test_default_path_when_not_configured(self, tmp_path: Path) -> None:
        """Should use default path when config key is missing."""
        config = {}
        result = resolve_telemetry_path(tmp_path, config)
        assert result == tmp_path / "data/telemetry/memory-palace.csv"
