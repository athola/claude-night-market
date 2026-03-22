"""Tests for memory-palace export."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from tome.models import Finding, ResearchSession
from tome.output.export import export_for_memory_palace


class TestMemoryPalaceExport:
    """
    Feature: Export to memory-palace format

    As a researcher
    I want to export findings to memory-palace
    So that I can store research in my knowledge base
    """

    @pytest.mark.unit
    def test_export_includes_yaml_frontmatter(self) -> None:
        """
        Scenario: Export format
        Given a completed research session
        When exporting to memory-palace format
        Then output includes YAML frontmatter
        """

        session = _make_session()
        result = export_for_memory_palace(session)
        assert result.startswith("---\n")
        assert "\n---\n" in result[4:]

    @pytest.mark.unit
    def test_export_includes_topic_in_frontmatter(self) -> None:
        """
        Scenario: Topic in metadata
        Given a session about "async patterns"
        When exporting
        Then frontmatter contains the topic
        """

        session = _make_session()
        result = export_for_memory_palace(session)
        assert "async patterns" in result

    @pytest.mark.unit
    def test_export_includes_all_finding_urls(self) -> None:
        """
        Scenario: Finding URLs preserved
        Given a session with findings
        When exporting
        Then all finding URLs appear in the output
        """

        session = _make_session()
        result = export_for_memory_palace(session)
        assert "https://github.com/example/async" in result
        assert "https://news.ycombinator.com/item?id=1" in result

    @pytest.mark.unit
    def test_export_includes_relevance_scores(self) -> None:
        """
        Scenario: Relevance scores preserved
        Given findings with relevance scores
        When exporting
        Then scores appear in the output
        """

        session = _make_session()
        result = export_for_memory_palace(session)
        assert "0.85" in result

    @pytest.mark.unit
    def test_export_empty_session_still_valid(self) -> None:
        """
        Scenario: Empty session export
        Given a session with no findings
        When exporting
        Then valid markdown with frontmatter is returned
        """

        session = ResearchSession(
            topic="empty topic",
            domain="general",
            triz_depth="light",
            channels=["code"],
            id="empty-001",
            findings=[],
            status="complete",
            created_at=datetime(2026, 3, 20, tzinfo=timezone.utc),
        )
        result = export_for_memory_palace(session)
        assert result.startswith("---\n")
        assert "empty topic" in result


def _make_session() -> ResearchSession:
    """Helper to build a test session."""
    return ResearchSession(
        topic="async patterns",
        domain="algorithm",
        triz_depth="medium",
        channels=["code", "discourse"],
        id="test-export-001",
        findings=[
            Finding(
                source="github",
                channel="code",
                title="example/async",
                url="https://github.com/example/async",
                relevance=0.85,
                summary="Async library",
                metadata={"stars": 500},
            ),
            Finding(
                source="hn",
                channel="discourse",
                title="Async discussion",
                url="https://news.ycombinator.com/item?id=1",
                relevance=0.72,
                summary="Community views on async",
                metadata={"score": 150},
            ),
        ],
        status="complete",
        created_at=datetime(2026, 3, 20, tzinfo=timezone.utc),
    )
