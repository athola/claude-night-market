"""Corpus management for Memory Palace knowledge base.

Nothing here is imported eagerly, for the reason the package root
above records: importing ``memory_palace.corpus.titles``, which is
stdlib-only, had to execute this file first, and this file reached
PyYAML through ``cache_lookup``. That cost ``web_research_handler`` its
PostToolUse run under the operator's interpreter.

Resolving each export on first attribute access keeps the stdlib-only
modules in this package reachable on their own, and keeps the
deliberately unguarded import in ``web_research_handler`` that issue
#624 put there.
"""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from memory_palace.corpus.cache_lookup import CacheLookup
    from memory_palace.corpus.counter_reinforcement import (
        SIMILARITY_THRESHOLD,
        CounterReinforcementTracker,
        FeedbackType,
        ReinforcementCounter,
    )
    from memory_palace.corpus.decay_model import (
        DECAY_CONFIG,
        DecayCurve,
        DecayModel,
        DecayState,
    )
    from memory_palace.corpus.keyword_index import KeywordIndexer
    from memory_palace.corpus.knowledge_orchestrator import (
        KnowledgeOrchestrator,
        QualityAssessment,
    )
    from memory_palace.corpus.marginal_value import (
        DeltaAnalysis,
        DeltaType,
        IntegrationDecision,
        IntegrationPlan,
        MarginalValueFilter,
        RedundancyCheck,
        RedundancyLevel,
    )
    from memory_palace.corpus.query_templates import QueryTemplateManager
    from memory_palace.corpus.semantic_deduplicator import (
        DEFAULT_THRESHOLD,
        SemanticDeduplicator,
    )
    from memory_palace.corpus.source_lineage import (
        FullLineage,
        SimpleLineage,
        SourceLineageManager,
        SourceReference,
        SourceType,
    )
    from memory_palace.corpus.usage_tracker import (
        SIGNAL_WEIGHTS,
        UsageEvent,
        UsageScore,
        UsageSignal,
        UsageTracker,
    )

__all__ = [
    # Semantic deduplication
    "DEFAULT_THRESHOLD",
    "SemanticDeduplicator",
    # Cache and indexing
    "CacheLookup",
    "KeywordIndexer",
    "QueryTemplateManager",
    # Counter-based reinforcement (ACE Playbook pattern)
    "CounterReinforcementTracker",
    "FeedbackType",
    "ReinforcementCounter",
    "SIMILARITY_THRESHOLD",
    # Marginal value filter
    "DeltaAnalysis",
    "DeltaType",
    "IntegrationDecision",
    "IntegrationPlan",
    "MarginalValueFilter",
    "RedundancyCheck",
    "RedundancyLevel",
    # Usage tracking (RL signals)
    "SIGNAL_WEIGHTS",
    "UsageEvent",
    "UsageScore",
    "UsageSignal",
    "UsageTracker",
    # Decay model
    "DECAY_CONFIG",
    "DecayCurve",
    "DecayModel",
    "DecayState",
    # Source lineage
    "FullLineage",
    "SimpleLineage",
    "SourceLineageManager",
    "SourceReference",
    "SourceType",
    # Knowledge orchestrator
    "KnowledgeOrchestrator",
    "QualityAssessment",
]

#: The module each exported name is resolved from on first access.
_EXPORT_SOURCES = {
    "CacheLookup": "memory_palace.corpus.cache_lookup",
    "CounterReinforcementTracker": "memory_palace.corpus.counter_reinforcement",
    "DECAY_CONFIG": "memory_palace.corpus.decay_model",
    "DeltaAnalysis": "memory_palace.corpus.marginal_value",
    "DeltaType": "memory_palace.corpus.marginal_value",
    "DecayCurve": "memory_palace.corpus.decay_model",
    "DecayModel": "memory_palace.corpus.decay_model",
    "DecayState": "memory_palace.corpus.decay_model",
    "FeedbackType": "memory_palace.corpus.counter_reinforcement",
    "FullLineage": "memory_palace.corpus.source_lineage",
    "IntegrationDecision": "memory_palace.corpus.marginal_value",
    "IntegrationPlan": "memory_palace.corpus.marginal_value",
    "KeywordIndexer": "memory_palace.corpus.keyword_index",
    "KnowledgeOrchestrator": "memory_palace.corpus.knowledge_orchestrator",
    "MarginalValueFilter": "memory_palace.corpus.marginal_value",
    "QualityAssessment": "memory_palace.corpus.knowledge_orchestrator",
    "QueryTemplateManager": "memory_palace.corpus.query_templates",
    "RedundancyCheck": "memory_palace.corpus.marginal_value",
    "RedundancyLevel": "memory_palace.corpus.marginal_value",
    "ReinforcementCounter": "memory_palace.corpus.counter_reinforcement",
    "SIGNAL_WEIGHTS": "memory_palace.corpus.usage_tracker",
    "SIMILARITY_THRESHOLD": "memory_palace.corpus.counter_reinforcement",
    "SimpleLineage": "memory_palace.corpus.source_lineage",
    "SourceLineageManager": "memory_palace.corpus.source_lineage",
    "SourceReference": "memory_palace.corpus.source_lineage",
    "SourceType": "memory_palace.corpus.source_lineage",
    "UsageEvent": "memory_palace.corpus.usage_tracker",
    "UsageScore": "memory_palace.corpus.usage_tracker",
    "UsageSignal": "memory_palace.corpus.usage_tracker",
    "UsageTracker": "memory_palace.corpus.usage_tracker",
}

#: Exports whose module needs a dependency this package treats as
#: optional, and the value each takes when it is absent.
_OPTIONAL_EXPORTS = {
    "DEFAULT_THRESHOLD": ("memory_palace.corpus.semantic_deduplicator", 0.85),
    "SemanticDeduplicator": ("memory_palace.corpus.semantic_deduplicator", None),
}


def __getattr__(name: str) -> Any:
    """Resolve an export from the module that defines it."""
    optional = _OPTIONAL_EXPORTS.get(name)
    if optional is not None:
        source, fallback = optional
        try:
            return getattr(import_module(source), name)
        except ImportError:
            return fallback

    source = _EXPORT_SOURCES.get(name)
    if source is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    return getattr(import_module(source), name)


def __dir__() -> list[str]:
    """List the exports alongside this module's own globals."""
    return sorted({*globals(), *__all__})
