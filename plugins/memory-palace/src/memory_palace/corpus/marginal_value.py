"""Marginal value filter for knowledge corpus anti-pollution.

Implements redundancy detection, delta analysis, and integration decisions
to validate only valuable knowledge enters the corpus. Follows the principle:
"If it can't teach something the existing corpus can't already teach → skip it."
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

from memory_palace.corpus._mv_models import (
    MIN_NOVEL_HEADINGS,
    MIN_NOVEL_KEYWORD_RATIO,
    OVERLAP_PARTIAL,
    OVERLAP_STRONG,
    VALUE_CONTRADICTION,
    VALUE_LOW,
    VALUE_MORE_EXAMPLES,
    VALUE_NONE,
    VALUE_NOVEL,
    DeltaAnalysis,
    DeltaType,
    IntegrationDecision,
    IntegrationPlan,
    RedundancyCheck,
    RedundancyLevel,
)
from memory_palace.corpus.cache_lookup import CacheLookup
from memory_palace.corpus.content_features import extract_keywords, infer_queries
from memory_palace.corpus.integration_policy import (
    decide_integration as _decide_integration_fn,
)
from memory_palace.corpus.integration_policy import (
    explain_decision as _explain_decision_fn,
)
from memory_palace.corpus.keyword_index import KeywordIndexer
from memory_palace.corpus.query_templates import QueryTemplateManager
from memory_palace.corpus.usage_tracker import UsageSignal

# Re-export everything so existing importers of marginal_value work unchanged.
__all__ = [
    "OVERLAP_STRONG",
    "OVERLAP_PARTIAL",
    "VALUE_NOVEL",
    "VALUE_CONTRADICTION",
    "VALUE_MORE_EXAMPLES",
    "VALUE_LOW",
    "VALUE_NONE",
    "MIN_NOVEL_HEADINGS",
    "MIN_NOVEL_KEYWORD_RATIO",
    "RedundancyLevel",
    "DeltaType",
    "IntegrationDecision",
    "RedundancyCheck",
    "DeltaAnalysis",
    "IntegrationPlan",
    "MarginalValueFilter",
    "KeywordIndexer",
    "QueryTemplateManager",
]


class MarginalValueFilter:
    """Filter for detecting redundant knowledge and assessing marginal value.

    Implements the "Teach Me Something New" test:
    If the new knowledge can't teach something the existing corpus
    can't already teach → skip it.

    Process:
    1. Redundancy Check: Exact/high/partial/novel
    2. Delta Analysis: What's actually new?
    3. Integration Decision: Standalone/merge/replace/skip
    """

    def __init__(self, corpus_dir: str, index_dir: str) -> None:
        """Initialize the marginal value filter.

        Args:
            corpus_dir: Directory containing knowledge corpus markdown files
            index_dir: Directory where index files are stored

        """
        self.corpus_dir = Path(corpus_dir)
        self.index_dir = Path(index_dir)

        self.cache_lookup = CacheLookup(corpus_dir, index_dir)

    def evaluate_content(
        self,
        content: str,
        title: str = "",
        tags: list[str] | None = None,
    ) -> tuple[RedundancyCheck, DeltaAnalysis | None, IntegrationPlan]:
        """Evaluate new content for marginal value.

        Args:
            content: The new knowledge content (markdown)
            title: Title/summary of the content
            tags: Optional tags describing the content

        Returns:
            Tuple of (redundancy check, delta analysis, integration plan).
            Delta analysis is None if content is exact match or novel.

        """
        keywords = self._extract_keywords(content, title, tags or [])
        queries = self._infer_queries(content, title)

        redundancy = self._check_redundancy(keywords, queries, content)

        delta = None
        if redundancy.level == RedundancyLevel.PARTIAL_OVERLAP:
            delta = self._analyze_delta(
                content, title, redundancy.matching_entries, keywords
            )

        integration = self._decide_integration(redundancy, delta)

        return redundancy, delta, integration

    def _extract_keywords(self, content: str, title: str, tags: list[str]) -> set[str]:
        """Extract keywords from content for comparison.

        Delegates to
        :func:`memory_palace.corpus.content_features.extract_keywords`.
        """
        return extract_keywords(content, title, tags)

    def _infer_queries(self, content: str, title: str) -> list[str]:
        """Infer potential queries this content could answer.

        Delegates to
        :func:`memory_palace.corpus.content_features.infer_queries`.
        """
        return infer_queries(content, title)

    def _check_redundancy(
        self,
        keywords: set[str],
        queries: list[str],
        content: str,
    ) -> RedundancyCheck:
        """Check if content is redundant with existing corpus.

        Args:
            keywords: Keywords from new content
            queries: Inferred queries from new content
            content: Full content text

        Returns:
            RedundancyCheck result

        """
        matching_entries: list[str] = []
        overlap_scores: list[float] = []
        reasons: list[str] = []

        if keywords:
            keyword_results = self.cache_lookup.search(
                list(keywords),
                mode="keywords",
                min_score=0.3,
            )

            for result in keyword_results:
                entry_id = result["entry_id"]
                score = result["match_score"]

                if entry_id not in matching_entries:
                    matching_entries.append(entry_id)
                    overlap_scores.append(score)

        for query in queries:
            query_results = self.cache_lookup.search(
                query, mode="queries", min_score=0.3
            )

            for result in query_results:
                entry_id = result["entry_id"]
                score = result["match_score"]

                if entry_id not in matching_entries:
                    matching_entries.append(entry_id)
                    overlap_scores.append(score)

        normalized_content = content.strip()
        for entry_id in matching_entries:
            existing_content = self.cache_lookup.get_entry_content(entry_id)
            if existing_content and existing_content.strip() == normalized_content:
                reasons.append(f"Exact content match with {entry_id}")
                return RedundancyCheck(
                    level=RedundancyLevel.EXACT_MATCH,
                    overlap_score=1.0,
                    matching_entries=[entry_id],
                    reasons=reasons,
                )

        if not overlap_scores:
            return RedundancyCheck(
                level=RedundancyLevel.NOVEL,
                overlap_score=0.0,
                matching_entries=[],
                reasons=["No matching entries found"],
            )

        max_overlap = max(overlap_scores)

        if max_overlap >= OVERLAP_STRONG:
            reasons.append(
                f"High overlap ({max_overlap:.0%}) with {len(matching_entries)} entries"
            )
            level = RedundancyLevel.HIGHLY_REDUNDANT
        elif max_overlap >= OVERLAP_PARTIAL:
            reasons.append(
                f"Partial overlap ({max_overlap:.0%}) with"
                f" {len(matching_entries)} entries",
            )
            level = RedundancyLevel.PARTIAL_OVERLAP
        else:
            reasons.append(f"Low overlap ({max_overlap:.0%}), appears novel")
            level = RedundancyLevel.NOVEL

        return RedundancyCheck(
            level=level,
            overlap_score=max_overlap,
            matching_entries=matching_entries,
            reasons=reasons,
        )

    def _analyze_delta(
        self,
        new_content: str,
        new_title: str,
        matching_entry_ids: list[str],
        new_keywords: set[str],
    ) -> DeltaAnalysis:
        """Analyze what's genuinely new in partially overlapping content.

        Args:
            new_content: New content text
            new_title: New content title
            matching_entry_ids: IDs of overlapping entries
            new_keywords: Keywords from new content

        Returns:
            DeltaAnalysis result

        """
        novel_aspects: list[str] = []
        redundant_aspects: list[str] = []

        existing_contents: list[str] = []
        existing_keywords: set[str] = set()

        for entry_id in matching_entry_ids:
            content = self.cache_lookup.get_entry_content(entry_id)
            if content:
                existing_contents.append(content)

                metadata = self.cache_lookup.get_entry_metadata(entry_id)
                if metadata and "tags" in metadata:
                    existing_keywords.update(tag.lower() for tag in metadata["tags"])

        novel_keywords = new_keywords - existing_keywords
        if novel_keywords:
            novel_aspects.append(f"New concepts: {', '.join(list(novel_keywords)[:5])}")

        overlap_keywords = new_keywords & existing_keywords
        if overlap_keywords:
            redundant_aspects.append(
                f"Already covered: {', '.join(list(overlap_keywords)[:5])}"
            )

        new_headings = set(re.findall(r"^#{1,3}\s+(.+)$", new_content, re.MULTILINE))
        existing_headings: set[str] = set()
        for content in existing_contents:
            existing_headings.update(
                re.findall(r"^#{1,3}\s+(.+)$", content, re.MULTILINE)
            )

        novel_headings = new_headings - existing_headings
        if novel_headings:
            novel_aspects.append(f"New topics: {', '.join(list(novel_headings)[:3])}")

        contradiction_markers = [
            "not",
            "wrong",
            "incorrect",
            "avoid",
            "instead",
            "better",
            "prefer",
        ]
        has_contradiction = any(
            marker in new_content.lower() for marker in contradiction_markers
        )

        if len(novel_keywords) > len(overlap_keywords) * MIN_NOVEL_KEYWORD_RATIO:
            delta_type = DeltaType.NOVEL_INSIGHT
            value_score = VALUE_NOVEL
            teaching_delta = f"Introduces {len(novel_keywords)} new concepts"
        elif has_contradiction and len(novel_aspects) > 0:
            delta_type = DeltaType.CONTRADICTS
            value_score = VALUE_CONTRADICTION
            teaching_delta = "Presents alternative perspective or correction"
        elif len(novel_headings) >= MIN_NOVEL_HEADINGS:
            delta_type = DeltaType.MORE_EXAMPLES
            value_score = VALUE_MORE_EXAMPLES
            teaching_delta = "Provides additional examples/coverage"
        elif len(novel_keywords) > 0:
            delta_type = DeltaType.DIFFERENT_FRAMING
            value_score = VALUE_LOW
            teaching_delta = "Mostly reframing of existing knowledge"
        else:
            delta_type = DeltaType.NONE
            value_score = VALUE_NONE
            teaching_delta = "No significant new teaching value"

        return DeltaAnalysis(
            delta_type=delta_type,
            value_score=value_score,
            novel_aspects=novel_aspects,
            redundant_aspects=redundant_aspects,
            teaching_delta=teaching_delta,
        )

    def _decide_integration(
        self,
        redundancy: RedundancyCheck,
        delta: DeltaAnalysis | None,
    ) -> IntegrationPlan:
        """Decide how to integrate new knowledge (or skip it).

        Delegates to
        :func:`memory_palace.corpus.integration_policy.decide_integration`.
        """
        return _decide_integration_fn(redundancy, delta)

    def explain_decision(
        self,
        redundancy: RedundancyCheck,
        delta: DeltaAnalysis | None,
        integration: IntegrationPlan,
    ) -> str:
        """Generate human-readable explanation of the filtering decision.

        Delegates to
        :func:`memory_palace.corpus.integration_policy.explain_decision`.
        """
        return _explain_decision_fn(redundancy, delta, integration)

    def emit_rl_signal(
        self,
        integration: IntegrationPlan,
        content_hash: str | None = None,
    ) -> dict:
        """Emit RL signal based on integration decision.

        Creates a signal dict that can be consumed by the UsageTracker
        or other RL systems to reinforce or penalize integration decisions.

        Args:
            integration: The integration decision made
            content_hash: Optional hash of the content for deduplication

        Returns:
            Signal dict with decision context for RL processing

        """
        decision_signals = {
            IntegrationDecision.STANDALONE: {
                "signal": UsageSignal.ACCESS,
                "weight": 0.3,
                "action": "new_entry_created",
            },
            IntegrationDecision.MERGE: {
                "signal": UsageSignal.CORRECTION,
                "weight": 0.2,
                "action": "entry_enhanced",
            },
            IntegrationDecision.REPLACE: {
                "signal": UsageSignal.CORRECTION,
                "weight": 0.4,
                "action": "entry_superseded",
            },
            IntegrationDecision.SKIP: {
                "signal": UsageSignal.STALE_FLAG,
                "weight": -0.1,
                "action": "content_rejected",
            },
        }

        signal_info = decision_signals.get(
            integration.decision,
            {"signal": UsageSignal.ACCESS, "weight": 0.0, "action": "unknown"},
        )

        return {
            "signal_type": signal_info["signal"],
            "weight": signal_info["weight"],
            "action": signal_info["action"],
            "decision": integration.decision.value,
            "confidence": integration.confidence,
            "target_entries": integration.target_entries,
            "content_hash": content_hash,
            "rationale": integration.rationale,
        }

    def evaluate_with_rl(
        self,
        content: str,
        title: str = "",
        tags: list[str] | None = None,
    ) -> tuple[RedundancyCheck, DeltaAnalysis | None, IntegrationPlan, dict]:
        """Evaluate content and emit RL signal.

        Args:
            content: The new knowledge content (markdown)
            title: Title/summary of the content
            tags: Optional tags describing the content

        Returns:
            Tuple of (redundancy, delta, integration, rl_signal)

        """
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

        redundancy, delta, integration = self.evaluate_content(content, title, tags)

        rl_signal = self.emit_rl_signal(integration, content_hash)

        return redundancy, delta, integration, rl_signal
