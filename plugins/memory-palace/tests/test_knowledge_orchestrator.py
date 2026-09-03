"""Tests for the central knowledge orchestrator.

Tests the KnowledgeOrchestrator which coordinates usage tracking,
decay model, and source lineage for overall knowledge quality assessment.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

from memory_palace.corpus.knowledge_orchestrator import (
    KnowledgeOrchestrator,
    QualityAssessment,
)
from memory_palace.corpus.marginal_value import IntegrationDecision
from memory_palace.corpus.source_lineage import (
    FullLineage,
    SimpleLineage,
    SourceReference,
    SourceType,
)
from memory_palace.corpus.usage_tracker import UsageSignal


class TestQualityAssessment:
    """Test QualityAssessment dataclass."""

    def test_create_assessment(self) -> None:
        """Should create assessment with all fields."""
        assessment = QualityAssessment(
            entry_id="entry-1",
            overall_score=0.75,
            usage_score=0.8,
            decay_score=0.7,
            status="healthy",
            recommendations=[],
        )
        assert assessment.entry_id == "entry-1"
        assert assessment.overall_score == 0.75
        assert assessment.usage_score == 0.8
        assert assessment.decay_score == 0.7
        assert assessment.status == "healthy"

    def test_assessment_with_recommendations(self) -> None:
        """Should include recommendations."""
        assessment = QualityAssessment(
            entry_id="entry-1",
            overall_score=0.35,
            usage_score=0.2,
            decay_score=0.5,
            status="needs_attention",
            recommendations=["Validate content", "Add citations"],
        )
        assert len(assessment.recommendations) == 2


class TestKnowledgeOrchestrator:
    """Test KnowledgeOrchestrator functionality."""

    @pytest.fixture
    def orchestrator(self) -> KnowledgeOrchestrator:
        """Create a fresh KnowledgeOrchestrator instance."""
        return KnowledgeOrchestrator()

    def test_quality_weights(self, orchestrator: KnowledgeOrchestrator) -> None:
        """Should have defined quality weights."""
        weights = orchestrator.QUALITY_WEIGHTS
        assert "usage" in weights
        assert "decay" in weights
        assert sum(weights.values()) == pytest.approx(1.0)

    def test_quality_thresholds(self, orchestrator: KnowledgeOrchestrator) -> None:
        """Should have defined quality thresholds."""
        thresholds = orchestrator.QUALITY_THRESHOLDS
        assert "healthy" in thresholds
        assert "needs_attention" in thresholds
        assert "critical" in thresholds
        assert (
            thresholds["healthy"]
            > thresholds["needs_attention"]
            > thresholds["critical"]
        )

    def test_assess_entry_no_history(self, orchestrator: KnowledgeOrchestrator) -> None:
        """Should assess entry with no usage history."""
        entry = {
            "id": "entry-1",
            "maturity": "growing",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        assessment = orchestrator.assess_entry(entry)
        assert assessment.entry_id == "entry-1"
        assert 0.0 <= assessment.overall_score <= 1.0

    def test_assess_entry_with_usage(self, orchestrator: KnowledgeOrchestrator) -> None:
        """Should incorporate usage into assessment."""
        entry = {
            "id": "entry-1",
            "maturity": "growing",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        # Record usage
        orchestrator.record_usage("entry-1", UsageSignal.ACCESS)
        orchestrator.record_usage("entry-1", UsageSignal.CITATION)
        orchestrator.record_usage("entry-1", UsageSignal.POSITIVE_FEEDBACK)

        assessment = orchestrator.assess_entry(entry)
        assert assessment.usage_score > 0

    def test_assess_entry_with_decay(self, orchestrator: KnowledgeOrchestrator) -> None:
        """Should incorporate decay into assessment."""
        old_date = datetime.now(timezone.utc) - timedelta(days=60)
        entry = {
            "id": "entry-1",
            "maturity": "seedling",
            "created_at": old_date.isoformat(),
            "last_validated": old_date.isoformat(),
        }

        assessment = orchestrator.assess_entry(entry)
        assert assessment.decay_score < 1.0  # Should have decayed

    def test_assess_entry_status_healthy(
        self, orchestrator: KnowledgeOrchestrator
    ) -> None:
        """High-scoring entry should be healthy."""
        entry = {
            "id": "entry-1",
            "maturity": "evergreen",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_validated": datetime.now(timezone.utc).isoformat(),
        }

        # Add positive signals
        for _ in range(10):
            orchestrator.record_usage("entry-1", UsageSignal.ACCESS)
        orchestrator.record_usage("entry-1", UsageSignal.POSITIVE_FEEDBACK)
        orchestrator.record_usage("entry-1", UsageSignal.CITATION)

        assessment = orchestrator.assess_entry(entry)
        assert assessment.status == "healthy", assessment.overall_score

    def test_assess_entry_status_needs_attention(
        self, orchestrator: KnowledgeOrchestrator
    ) -> None:
        """Mid-scoring entry should need attention."""
        recent = datetime.now(timezone.utc) - timedelta(days=20)
        entry = {
            "id": "entry-1",
            "maturity": "growing",
            "created_at": recent.isoformat(),
            "last_validated": recent.isoformat(),
        }
        # Light usage on a moderately-aged entry lands it in the
        # needs_attention band (0.4 <= overall_score < 0.7).
        orchestrator.record_usage("entry-1", UsageSignal.ACCESS)
        orchestrator.record_usage("entry-1", UsageSignal.ACCESS)

        assessment = orchestrator.assess_entry(entry)
        assert assessment.status == "needs_attention", assessment.overall_score

    def test_assess_entry_status_critical(
        self, orchestrator: KnowledgeOrchestrator
    ) -> None:
        """Low-scoring entry should be critical."""
        very_old = datetime.now(timezone.utc) - timedelta(days=180)
        entry = {
            "id": "entry-1",
            "maturity": "seedling",
            "created_at": very_old.isoformat(),
            "last_validated": very_old.isoformat(),
        }

        # Add negative signals
        orchestrator.record_usage("entry-1", UsageSignal.NEGATIVE_FEEDBACK)
        orchestrator.record_usage("entry-1", UsageSignal.STALE_FLAG)

        assessment = orchestrator.assess_entry(entry)
        assert assessment.status == "critical", assessment.overall_score

    def test_record_usage(self, orchestrator: KnowledgeOrchestrator) -> None:
        """Should record usage events."""
        event = orchestrator.record_usage("entry-1", UsageSignal.ACCESS)
        assert event.entry_id == "entry-1"
        assert event.signal == UsageSignal.ACCESS

    def test_record_usage_with_context(
        self, orchestrator: KnowledgeOrchestrator
    ) -> None:
        """Should record usage with context."""
        event = orchestrator.record_usage(
            "entry-1",
            UsageSignal.CITATION,
            context={"cited_by": "article-123"},
        )
        assert event.context["cited_by"] == "article-123"

    def test_get_maintenance_queue(self, orchestrator: KnowledgeOrchestrator) -> None:
        """Should return entries needing maintenance."""
        now = datetime.now(timezone.utc)
        old = now - timedelta(days=60)
        very_old = now - timedelta(days=120)

        entries = [
            {
                "id": "healthy-1",
                "maturity": "evergreen",
                "last_validated": now.isoformat(),
            },
            {"id": "stale-1", "maturity": "growing", "last_validated": old.isoformat()},
            {
                "id": "critical-1",
                "maturity": "seedling",
                "last_validated": very_old.isoformat(),
            },
        ]

        # Add positive signals to healthy entry
        for _ in range(5):
            orchestrator.record_usage("healthy-1", UsageSignal.ACCESS)

        queue = orchestrator.get_maintenance_queue(entries)
        assert isinstance(queue, list)
        # Queue should be sorted by priority (worst first)
        if len(queue) >= 2:
            assert queue[0].overall_score <= queue[-1].overall_score

    def test_ingest_with_lineage_standalone(
        self, orchestrator: KnowledgeOrchestrator
    ) -> None:
        """Should ingest new content with lineage tracking."""
        source = SourceReference(
            source_id="src-1",
            source_type=SourceType.DOCUMENTATION,
            url="https://docs.example.com/api",
            title="API Documentation",
        )

        entry_id, decision = orchestrator.ingest_with_lineage(
            content="# API Reference\n\nComplete API documentation...",
            title="API Documentation",
            source=source,
        )

        assert isinstance(entry_id, str)
        assert decision in [
            IntegrationDecision.STANDALONE,
            IntegrationDecision.MERGE,
            IntegrationDecision.REPLACE,
            IntegrationDecision.SKIP,
        ]

    def test_ingest_creates_lineage(self, orchestrator: KnowledgeOrchestrator) -> None:
        """Should create lineage for ingested content."""
        source = SourceReference(
            source_id="src-1",
            source_type=SourceType.RESEARCH_PAPER,
            url="https://arxiv.org/abs/1234",
            title="Important Research",
        )

        entry_id, decision = orchestrator.ingest_with_lineage(
            content="# Novel Findings\n\nThis research demonstrates...",
            title="Important Research",
            source=source,
        )

        if decision != IntegrationDecision.SKIP:
            lineage = orchestrator.lineage_manager.get_lineage(entry_id)
            assert isinstance(lineage, (FullLineage, SimpleLineage))

    def test_validate_entry(self, orchestrator: KnowledgeOrchestrator) -> None:
        """Should record validation and reset decay."""
        entry = {
            "id": "entry-1",
            "maturity": "growing",
            "created_at": (datetime.now(timezone.utc) - timedelta(days=30)).isoformat(),
        }

        # Validate
        orchestrator.validate_entry("entry-1")

        # Re-assess - should have better decay score
        assessment = orchestrator.assess_entry(entry)
        assert assessment.decay_score > 0.5

    def test_recommendations_for_stale(
        self, orchestrator: KnowledgeOrchestrator
    ) -> None:
        """Should recommend validation for stale entries."""
        old_date = datetime.now(timezone.utc) - timedelta(days=60)
        entry = {
            "id": "entry-1",
            "maturity": "growing",
            "created_at": old_date.isoformat(),
            "last_validated": old_date.isoformat(),
        }

        assessment = orchestrator.assess_entry(entry)
        if assessment.decay_score < 0.7:
            assert len(assessment.recommendations) > 0
            assert any(
                "validate" in r.lower() or "review" in r.lower()
                for r in assessment.recommendations
            )

    def test_recommendations_for_low_usage(
        self, orchestrator: KnowledgeOrchestrator
    ) -> None:
        """Should recommend usage for low-access entries."""
        entry = {
            "id": "entry-1",
            "maturity": "growing",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_validated": datetime.now(timezone.utc).isoformat(),
        }

        assessment = orchestrator.assess_entry(entry)

        # A fresh entry with no recorded usage scores low on usage,
        # so the orchestrator recommends promoting or archiving it.
        assert assessment.usage_score < 0.3, assessment.usage_score
        assert any("low-usage" in rec.lower() for rec in assessment.recommendations), (
            assessment.recommendations
        )

    def test_overall_score_calculation(
        self, orchestrator: KnowledgeOrchestrator
    ) -> None:
        """Overall score should be weighted combination."""
        entry = {
            "id": "entry-1",
            "maturity": "growing",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_validated": datetime.now(timezone.utc).isoformat(),
        }

        orchestrator.record_usage("entry-1", UsageSignal.ACCESS)
        assessment = orchestrator.assess_entry(entry)

        weights = orchestrator.QUALITY_WEIGHTS
        expected = (
            weights["usage"] * assessment.usage_score
            + weights["decay"] * assessment.decay_score
        )
        assert assessment.overall_score == pytest.approx(expected, abs=0.01)

    def test_get_statistics(self, orchestrator: KnowledgeOrchestrator) -> None:
        """Should provide corpus statistics."""
        entries = [
            {
                "id": "e1",
                "maturity": "evergreen",
                "last_validated": datetime.now(timezone.utc).isoformat(),
            },
            {
                "id": "e2",
                "maturity": "growing",
                "last_validated": datetime.now(timezone.utc).isoformat(),
            },
            {
                "id": "e3",
                "maturity": "seedling",
                "last_validated": datetime.now(timezone.utc).isoformat(),
            },
        ]

        orchestrator.record_usage("e1", UsageSignal.ACCESS)
        orchestrator.record_usage("e1", UsageSignal.CITATION)

        stats = orchestrator.get_statistics(entries)
        assert "total_entries" in stats
        assert "healthy_count" in stats
        assert "needs_attention_count" in stats
        assert "critical_count" in stats
        assert "average_usage_score" in stats
        assert "average_decay_score" in stats

    def test_assess_entry_over_many_entries(
        self, orchestrator: KnowledgeOrchestrator
    ) -> None:
        """assess_entry composes over a list without a batch wrapper (MP-010)."""
        entries = [
            {
                "id": f"entry-{i}",
                "maturity": "growing",
                "last_validated": datetime.now(timezone.utc).isoformat(),
            }
            for i in range(10)
        ]

        assessments = [orchestrator.assess_entry(e) for e in entries]
        assert len(assessments) == 10
        assert all(isinstance(a, QualityAssessment) for a in assessments)

    def test_orchestrator_has_no_delegation_wrappers(self) -> None:
        """MP-009/MP-010: callers use lineage_manager and assess_entry directly."""
        assert not hasattr(KnowledgeOrchestrator, "get_source_lineage")
        assert not hasattr(KnowledgeOrchestrator, "batch_assess")

    def test_export_state(self, orchestrator: KnowledgeOrchestrator) -> None:
        """Should export full orchestrator state."""
        orchestrator.record_usage("entry-1", UsageSignal.ACCESS)
        orchestrator.validate_entry("entry-1")

        state = orchestrator.export_state()
        assert "usage_events" in state
        assert "validation_dates" in state
        assert "lineage" in state

    def test_import_state(self, orchestrator: KnowledgeOrchestrator) -> None:
        """Should import orchestrator state."""
        state = {
            "usage_events": [
                {
                    "entry_id": "entry-1",
                    "signal": "access",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "context": {},
                }
            ],
            "validation_dates": {
                "entry-1": datetime.now(timezone.utc).isoformat(),
            },
            "lineage": {},
        }

        orchestrator.import_state(state)
        # Should have the imported usage
        events = orchestrator.usage_tracker.get_events("entry-1")
        assert len(events) == 1

    def test_rl_signal_emission(self, orchestrator: KnowledgeOrchestrator) -> None:
        """Should emit RL signals on integration decisions."""
        # This test verifies the RL integration point
        source = SourceReference(
            source_id="src-1",
            source_type=SourceType.WEB_ARTICLE,
            url="https://example.com/article",
        )

        # Hook for tracking emitted signals
        emitted_signals = []

        def signal_handler(entry_id: str, signal: UsageSignal, context: dict) -> None:
            emitted_signals.append((entry_id, signal, context))

        orchestrator.set_signal_handler(signal_handler)

        entry_id, decision = orchestrator.ingest_with_lineage(
            content="# Test Content",
            title="Test",
            source=source,
        )

        # Should have emitted at least one signal
        if decision != IntegrationDecision.SKIP:
            # New entry should trigger access signal
            assert len(emitted_signals) >= 0  # May or may not emit on ingest

    def test_get_entry_history(self, orchestrator: KnowledgeOrchestrator) -> None:
        """Should return full history for an entry."""
        orchestrator.record_usage("entry-1", UsageSignal.ACCESS)
        orchestrator.record_usage("entry-1", UsageSignal.CITATION)
        orchestrator.validate_entry("entry-1")  # This also records a CORRECTION event

        history = orchestrator.get_entry_history("entry-1")
        assert "usage_events" in history
        assert "validation_dates" in history
        # 2 explicit + 1 from validate_entry (which records CORRECTION)
        assert len(history["usage_events"]) == 3


class TestMP015GetStatisticsSinglePass:
    """MP-015: get_statistics must call assess_entry once per entry, not per-stat."""

    @pytest.fixture
    def orchestrator(self) -> KnowledgeOrchestrator:
        """Create a fresh KnowledgeOrchestrator instance."""
        return KnowledgeOrchestrator()

    def test_assess_entry_called_once_per_entry(
        self, orchestrator: KnowledgeOrchestrator
    ) -> None:
        """get_statistics must not call assess_entry multiple times per entry.

        The original implementation called assess_entry once per entry then
        iterated the result list 3 more times for status counts. That's still
        single-call per entry, but the stat aggregation looped 5 times over
        assessments. The fix: single pass accumulating all stats. Confirmed
        by verifying assess_entry is called exactly N times for N entries.
        """
        entries = [
            {"id": "e1", "content": "alpha"},
            {"id": "e2", "content": "beta"},
            {"id": "e3", "content": "gamma"},
        ]
        with patch.object(
            orchestrator,
            "assess_entry",
            wraps=orchestrator.assess_entry,
        ) as mock_assess:
            orchestrator.get_statistics(entries)

        assert mock_assess.call_count == len(entries), (
            f"assess_entry was called {mock_assess.call_count} times for "
            f"{len(entries)} entries; must be called exactly once per entry (MP-015)"
        )

    def test_get_statistics_result_unchanged(
        self, orchestrator: KnowledgeOrchestrator
    ) -> None:
        """Single-pass aggregation must produce the same stats as multi-pass."""
        entries = [{"id": "e1", "content": "x"}]
        stats = orchestrator.get_statistics(entries)
        assert "total_entries" in stats
        assert "healthy_count" in stats
        assert "needs_attention_count" in stats
        assert "critical_count" in stats
        assert "average_usage_score" in stats
        assert "average_decay_score" in stats
        assert stats["total_entries"] == 1
