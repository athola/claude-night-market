"""Central knowledge orchestrator.

Coordinates usage tracking, decay model, and source lineage
for comprehensive knowledge quality assessment and management.
"""

import logging
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)

from memory_palace.corpus.decay_model import DecayModel
from memory_palace.corpus.marginal_value import IntegrationDecision, MarginalValueFilter
from memory_palace.corpus.source_lineage import (
    FullLineage,
    SimpleLineage,
    SourceLineageManager,
    SourceReference,
)
from memory_palace.corpus.usage_tracker import UsageEvent, UsageSignal, UsageTracker


@dataclass
class QualityAssessment:
    """Quality assessment for a knowledge entry."""

    entry_id: str
    overall_score: float  # 0.0 to 1.0
    usage_score: float  # 0.0 to 1.0
    decay_score: float  # 0.0 to 1.0
    status: str  # "healthy", "needs_attention", "critical"
    recommendations: list[str] = field(default_factory=list)


# Recommendation thresholds
RECOMMENDATION_DECAY_THRESHOLD = 0.5
RECOMMENDATION_LOW_USAGE_THRESHOLD = 0.3
RECOMMENDATION_HIGH_USAGE_THRESHOLD = 0.8


class KnowledgeOrchestrator:
    """Central orchestrator for knowledge quality management.

    Coordinates:
    - UsageTracker: RL-based usage scoring
    - DecayModel: Time-based quality decay
    - SourceLineageManager: Provenance tracking
    - MarginalValueFilter: Integration decisions

    Provides unified quality assessment and maintenance workflows.
    """

    QUALITY_WEIGHTS: dict[str, float] = {
        "usage": 0.6,
        "decay": 0.4,
    }

    QUALITY_THRESHOLDS: dict[str, float] = {
        "healthy": 0.7,
        "needs_attention": 0.4,
        "critical": 0.2,
    }

    def __init__(
        self,
        corpus_dir: str | None = None,
        index_dir: str | None = None,
    ) -> None:
        """Initialize the knowledge orchestrator.

        Args:
            corpus_dir: Optional directory for corpus (for MarginalValueFilter)
            index_dir: Optional directory for indexes (for MarginalValueFilter)

        """
        self.usage_tracker = UsageTracker()
        self.decay_model = DecayModel()
        self.lineage_manager = SourceLineageManager()

        # Optional marginal value filter (requires corpus)
        self._marginal_filter: MarginalValueFilter | None = None
        if corpus_dir and index_dir:
            self._marginal_filter = MarginalValueFilter(corpus_dir, index_dir)

        # Signal handler for RL integration
        self._signal_handler: Callable[[str, UsageSignal, dict], None] | None = None

    def set_signal_handler(
        self,
        handler: Callable[[str, UsageSignal, dict], None],
    ) -> None:
        """Set handler for RL signal emission.

        Args:
            handler: Callback function(entry_id, signal, context)

        """
        self._signal_handler = handler

    def assess_entry(self, entry: dict[str, Any]) -> QualityAssessment:
        """Assess quality of a knowledge entry.

        Combines usage score and decay score with configured weights.

        Args:
            entry: Entry dict with 'id', 'maturity', optional 'last_validated'

        Returns:
            QualityAssessment with overall score and recommendations

        Raises:
            KeyError: If entry is missing required 'id' field.

        """
        if "id" not in entry:
            raise KeyError("Entry must contain 'id' field")
        entry_id = entry["id"]
        maturity = entry.get("maturity", "growing")

        # Get usage score
        usage_score_obj = self.usage_tracker.get_score(entry_id)
        usage_score = usage_score_obj.normalized_score

        # Get decay score
        last_validated_str = entry.get("last_validated")
        if last_validated_str:
            try:
                last_validated = datetime.fromisoformat(last_validated_str)
            except ValueError:
                logger.warning(
                    "Invalid last_validated date format for entry %s: %r",
                    entry_id,
                    last_validated_str,
                )
                last_validated = datetime.now(UTC)
        else:
            # Check decay model
            last_validated = self.decay_model.get_validation_date(entry_id)
            if last_validated is None:
                # Use creation date or now
                created_str = entry.get("created_at")
                if created_str:
                    try:
                        last_validated = datetime.fromisoformat(created_str)
                    except ValueError:
                        logger.warning(
                            "Invalid created_at date format for entry %s: %r",
                            entry_id,
                            created_str,
                        )
                        last_validated = datetime.now(UTC)
                else:
                    last_validated = datetime.now(UTC)

        decay_state = self.decay_model.calculate_decay(
            entry_id, maturity, last_validated
        )
        decay_score = decay_state.decay_factor

        # Calculate overall score
        overall_score = (
            self.QUALITY_WEIGHTS["usage"] * usage_score
            + self.QUALITY_WEIGHTS["decay"] * decay_score
        )

        # Determine status
        if overall_score >= self.QUALITY_THRESHOLDS["healthy"]:
            status = "healthy"
        elif overall_score >= self.QUALITY_THRESHOLDS["needs_attention"]:
            status = "needs_attention"
        else:
            status = "critical"

        # Generate recommendations
        recommendations = self._generate_recommendations(
            usage_score, decay_score, decay_state.status
        )

        return QualityAssessment(
            entry_id=entry_id,
            overall_score=overall_score,
            usage_score=usage_score,
            decay_score=decay_score,
            status=status,
            recommendations=recommendations,
        )

    def _generate_recommendations(
        self,
        usage_score: float,
        decay_score: float,
        decay_status: str,
    ) -> list[str]:
        """Generate recommendations based on scores.

        Args:
            usage_score: Normalized usage score
            decay_score: Decay factor
            decay_status: Decay status string

        Returns:
            List of recommendation strings

        """
        recommendations = []

        # Decay-based recommendations
        if decay_score < RECOMMENDATION_DECAY_THRESHOLD:
            recommendations.append("Review and validate content for accuracy")
        if decay_status in ["stale", "critical"]:
            recommendations.append("Content may be outdated - verify currency")

        # Usage-based recommendations
        if usage_score < RECOMMENDATION_LOW_USAGE_THRESHOLD:
            recommendations.append("Consider promoting or archiving low-usage content")
        if usage_score > RECOMMENDATION_HIGH_USAGE_THRESHOLD:
            recommendations.append("High-value content - consider making evergreen")

        return recommendations

    def record_usage(
        self,
        entry_id: str,
        signal: UsageSignal,
        context: dict[str, Any] | None = None,
    ) -> UsageEvent:
        """Record a usage event and emit RL signal.

        Args:
            entry_id: ID of the knowledge entry
            signal: Type of usage signal
            context: Optional context metadata

        Returns:
            The recorded UsageEvent

        """
        event = self.usage_tracker.record_event(entry_id, signal, context)

        # Emit RL signal if handler configured
        if self._signal_handler:
            self._signal_handler(entry_id, signal, context or {})

        return event

    def get_maintenance_queue(
        self,
        entries: list[dict[str, Any]],
    ) -> list[QualityAssessment]:
        """Get prioritized queue of entries needing maintenance.

        Args:
            entries: List of entry dicts

        Returns:
            List of QualityAssessments sorted by priority (worst first)

        """
        assessments = []
        for entry in entries:
            assessment = self.assess_entry(entry)
            if assessment.status != "healthy":
                assessments.append(assessment)

        # Sort by overall score (worst first)
        assessments.sort(key=lambda a: a.overall_score)

        return assessments

    def validate_entry(self, entry_id: str) -> None:
        """Record validation for an entry.

        Args:
            entry_id: ID of the knowledge entry

        """
        self.decay_model.validate_entry(entry_id)

        # Also record as positive usage signal
        self.record_usage(entry_id, UsageSignal.CORRECTION, {"action": "validated"})

    def ingest_with_lineage(
        self,
        content: str,
        title: str,
        source: SourceReference,
        tags: list[str] | None = None,
    ) -> tuple[str, IntegrationDecision]:
        """Ingest new content with lineage tracking.

        Uses MarginalValueFilter to make integration decision,
        then creates appropriate lineage.

        Args:
            content: The knowledge content
            title: Title of the content
            source: Source reference
            tags: Optional tags

        Returns:
            Tuple of (entry_id, IntegrationDecision)

        """
        # Determine integration decision
        if self._marginal_filter:
            _, delta, integration = self._marginal_filter.evaluate_content(
                content, title, tags
            )
            decision = integration.decision
            importance_score = delta.value_score if delta else 0.5
        else:
            # Without filter, default to standalone
            decision = IntegrationDecision.STANDALONE
            importance_score = 0.5

        if decision == IntegrationDecision.SKIP:
            return "", decision

        # Generate entry ID
        entry_id = f"entry-{uuid.uuid4().hex[:8]}"

        # Create and register lineage
        lineage = self.lineage_manager.create_lineage(
            entry_id, source, importance_score
        )
        self.lineage_manager.register_lineage(lineage)

        # Validate the new entry
        self.decay_model.validate_entry(entry_id)

        # Emit RL signal for new content
        if self._signal_handler:
            self._signal_handler(
                entry_id,
                UsageSignal.ACCESS,
                {"action": "ingested", "decision": decision.value},
            )

        return entry_id, decision

    def get_source_lineage(
        self,
        entry_id: str,
    ) -> FullLineage | SimpleLineage | None:
        """Get source lineage for an entry.

        Args:
            entry_id: ID of the knowledge entry

        Returns:
            Lineage or None

        """
        return self.lineage_manager.get_lineage(entry_id)

    def get_statistics(
        self,
        entries: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Get corpus statistics.

        Args:
            entries: List of entry dicts

        Returns:
            Statistics dictionary

        """
        assessments = [self.assess_entry(e) for e in entries]

        healthy_count = sum(1 for a in assessments if a.status == "healthy")
        needs_attention_count = sum(
            1 for a in assessments if a.status == "needs_attention"
        )
        critical_count = sum(1 for a in assessments if a.status == "critical")

        usage_scores = [a.usage_score for a in assessments]
        decay_scores = [a.decay_score for a in assessments]

        return {
            "total_entries": len(entries),
            "healthy_count": healthy_count,
            "needs_attention_count": needs_attention_count,
            "critical_count": critical_count,
            "average_usage_score": sum(usage_scores) / len(usage_scores)
            if usage_scores
            else 0.0,
            "average_decay_score": sum(decay_scores) / len(decay_scores)
            if decay_scores
            else 0.0,
        }

    def batch_assess(
        self,
        entries: list[dict[str, Any]],
    ) -> list[QualityAssessment]:
        """Batch assess multiple entries.

        Args:
            entries: List of entry dicts

        Returns:
            List of QualityAssessments

        """
        return [self.assess_entry(e) for e in entries]

    def get_entry_history(self, entry_id: str) -> dict[str, Any]:
        """Get full history for an entry.

        Args:
            entry_id: ID of the knowledge entry

        Returns:
            History dictionary with events and validations

        """
        events = self.usage_tracker.get_events(entry_id)
        validation_date = self.decay_model.get_validation_date(entry_id)

        return {
            "usage_events": [
                {
                    "signal": e.signal.value,
                    "timestamp": e.timestamp.isoformat(),
                    "context": e.context,
                }
                for e in events
            ],
            "validation_dates": [validation_date.isoformat()]
            if validation_date
            else [],
            "lineage": self.lineage_manager.export_lineage().get(entry_id),
        }

    def export_state(self) -> dict[str, Any]:
        """Export full orchestrator state.

        Returns:
            State dictionary

        """
        return {
            "usage_events": self.usage_tracker.export_events(),
            "validation_dates": self.decay_model.export_state(),
            "lineage": self.lineage_manager.export_lineage(),
        }

    def import_state(self, state: dict[str, Any]) -> None:
        """Import orchestrator state.

        Args:
            state: State dictionary

        """
        if "usage_events" in state:
            self.usage_tracker.import_events(state["usage_events"])
        if "validation_dates" in state:
            self.decay_model.import_state(state["validation_dates"])
        if "lineage" in state:
            self.lineage_manager.import_lineage(state["lineage"])
