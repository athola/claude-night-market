"""Marginal value filter for knowledge corpus anti-pollution.

Implements redundancy detection, delta analysis, and integration decisions
to ensure only valuable knowledge enters the corpus. Follows the principle:
"If it can't teach something the existing corpus can't already teach → skip it."
"""

import hashlib
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from memory_palace.corpus.cache_lookup import CacheLookup
from memory_palace.corpus.keyword_index import KeywordIndexer
from memory_palace.corpus.query_templates import QueryTemplateManager
from memory_palace.corpus.usage_tracker import UsageSignal

OVERLAP_STRONG = 0.8
OVERLAP_PARTIAL = 0.4
VALUE_NOVEL = 0.8
VALUE_CONTRADICTION = 0.7
VALUE_MORE_EXAMPLES = 0.4
VALUE_LOW = 0.3
VALUE_NONE = 0.1
MIN_NOVEL_HEADINGS = 2
MIN_NOVEL_KEYWORD_RATIO = 0.5


class RedundancyLevel(Enum):
    """Classification of content redundancy."""

    EXACT_MATCH = "exact_match"  # Duplicate - reject
    HIGHLY_REDUNDANT = "redundant"  # 80%+ overlap - reject
    PARTIAL_OVERLAP = "partial"  # Some overlap - evaluate delta
    NOVEL = "novel"  # New content - likely valuable


class DeltaType(Enum):
    """Type of new information in partially overlapping content."""

    NOVEL_INSIGHT = "novel_insight"  # New pattern/concept - valuable
    DIFFERENT_FRAMING = "different_framing"  # Same info, different words - low value
    MORE_EXAMPLES = "more_examples"  # Additional examples - marginal
    CONTRADICTS = "contradicts"  # Contradicts existing - investigate
    NONE = "none"  # No new information


class IntegrationDecision(Enum):
    """How to handle new knowledge."""

    STANDALONE = "standalone"  # Store as new entry
    MERGE = "merge"  # Enhance existing entry
    REPLACE = "replace"  # Supersedes existing entry
    SKIP = "skip"  # No marginal value


@dataclass
class RedundancyCheck:
    """Result of redundancy analysis."""

    level: RedundancyLevel
    overlap_score: float  # 0.0 to 1.0
    matching_entries: list[str]  # IDs of overlapping entries
    reasons: list[str]  # Why this redundancy classification


@dataclass
class DeltaAnalysis:
    """Analysis of what's new in partially overlapping content."""

    delta_type: DeltaType
    value_score: float  # 0.0 to 1.0 (marginal value)
    novel_aspects: list[str]  # What's new/different
    redundant_aspects: list[str]  # What's already covered
    teaching_delta: str  # "What can this teach that existing can't?"


@dataclass
class IntegrationPlan:
    """Decision on how to integrate new knowledge."""

    decision: IntegrationDecision
    target_entries: list[str]  # Entries to merge/replace
    rationale: str  # Why this decision
    confidence: float  # 0.0 to 1.0


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

        # Initialize search components
        self.cache_lookup = CacheLookup(corpus_dir, index_dir)
        self.keyword_indexer = KeywordIndexer(corpus_dir, index_dir)
        self.query_manager = QueryTemplateManager(corpus_dir, index_dir)

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
            Tuple of (redundancy check, delta analysis, integration plan)
            Delta analysis is None if content is exact match or novel

        """
        # Extract concepts from new content
        keywords = self._extract_keywords(content, title, tags or [])
        queries = self._infer_queries(content, title)

        # Step 1: Check redundancy
        redundancy = self._check_redundancy(keywords, queries, content)

        # Step 2: Analyze delta (only for partial overlap)
        delta = None
        if redundancy.level == RedundancyLevel.PARTIAL_OVERLAP:
            delta = self._analyze_delta(
                content, title, redundancy.matching_entries, keywords
            )

        # Step 3: Make integration decision
        integration = self._decide_integration(redundancy, delta)

        return redundancy, delta, integration

    def _extract_keywords(self, content: str, title: str, tags: list[str]) -> set[str]:
        """Extract keywords from content for comparison.

        Args:
            content: Content text
            title: Content title
            tags: Content tags

        Returns:
            Set of keywords

        """
        keywords: set[str] = set()

        # Add tags
        keywords.update(tag.lower() for tag in tags)

        # Extract from title
        title_words = re.findall(r"\b[a-z]{3,}\b", title.lower())
        keywords.update(title_words)

        # Extract technical terms (hyphenated)
        technical_terms = re.findall(r"\b[a-z]+(?:-[a-z]+)+\b", content.lower())
        keywords.update(technical_terms)

        # Extract emphasized terms
        emphasized = re.findall(r"\*\*([^*]+)\*\*|\*([^*]+)\*", content)
        for match in emphasized:
            term = match[0] or match[1]
            term_words = re.findall(r"\b[a-z]{3,}\b", term.lower())
            keywords.update(term_words)

        # Extract headings
        headings = re.findall(r"^#{1,3}\s+(.+)$", content, re.MULTILINE)
        for heading in headings:
            heading_words = re.findall(r"\b[a-z]{3,}\b", heading.lower())
            keywords.update(heading_words)

        # Remove stop words
        stop_words = {
            "the",
            "and",
            "for",
            "that",
            "this",
            "with",
            "from",
            "are",
            "was",
            "were",
            "been",
            "have",
            "has",
            "had",
            "not",
            "but",
            "can",
            "will",
            "what",
            "when",
            "where",
            "who",
            "why",
            "how",
            "all",
            "each",
            "which",
            "their",
            "said",
            "them",
            "these",
            "than",
            "into",
            "very",
            "her",
            "our",
            "out",
            "only",
        }
        return {k for k in keywords if k not in stop_words}

    def _infer_queries(self, content: str, title: str) -> list[str]:
        """Infer potential queries this content could answer.

        Args:
            content: Content text
            title: Content title

        Returns:
            List of inferred query strings

        """
        queries = []

        # Common question patterns from title/headings
        headings = [title, *re.findall(r"^#{1,3}\s+(.+)$", content, re.MULTILINE)]

        for heading in headings:
            heading_lower = heading.lower()

            # "How to X" patterns
            if "how" in heading_lower:
                queries.append(heading_lower)

            # "X pattern" or "X approach"
            if "pattern" in heading_lower or "approach" in heading_lower:
                queries.append(f"what is {heading_lower}")

            # "X best practices"
            if "practice" in heading_lower or "tip" in heading_lower:
                queries.append(f"best practices for {heading_lower}")

        return queries

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
        matching_entries = []
        overlap_scores = []
        reasons = []

        # Search by keywords
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

        # Search by queries
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

        # Check for exact content match
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

        # Determine redundancy level from overlap scores
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
                f"Partial overlap ({max_overlap:.0%}) with {len(matching_entries)} entries",
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
        novel_aspects = []
        redundant_aspects = []

        # Gather existing content
        existing_contents = []
        existing_keywords: set[str] = set()

        for entry_id in matching_entry_ids:
            content = self.cache_lookup.get_entry_content(entry_id)
            if content:
                existing_contents.append(content)

                # Extract keywords from existing
                metadata = self.cache_lookup.get_entry_metadata(entry_id)
                if metadata and "tags" in metadata:
                    existing_keywords.update(tag.lower() for tag in metadata["tags"])

        # Find novel keywords
        novel_keywords = new_keywords - existing_keywords
        if novel_keywords:
            novel_aspects.append(f"New concepts: {', '.join(list(novel_keywords)[:5])}")

        # Find redundant keywords
        overlap_keywords = new_keywords & existing_keywords
        if overlap_keywords:
            redundant_aspects.append(
                f"Already covered: {', '.join(list(overlap_keywords)[:5])}"
            )

        # Analyze content structure differences
        new_headings = set(re.findall(r"^#{1,3}\s+(.+)$", new_content, re.MULTILINE))
        existing_headings = set()
        for content in existing_contents:
            existing_headings.update(
                re.findall(r"^#{1,3}\s+(.+)$", content, re.MULTILINE)
            )

        novel_headings = new_headings - existing_headings
        if novel_headings:
            novel_aspects.append(f"New topics: {', '.join(list(novel_headings)[:3])}")

        # Check for contradictions (heuristic: "not", "wrong", "incorrect" near existing concepts)
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

        # Determine delta type and value
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

    def _decide_integration(  # noqa: PLR0911 - explicit branch decisions for clarity
        self,
        redundancy: RedundancyCheck,
        delta: DeltaAnalysis | None,
    ) -> IntegrationPlan:
        """Decide how to integrate new knowledge (or skip it).

        Args:
            redundancy: Redundancy check result
            delta: Delta analysis (None if exact match or novel)

        Returns:
            IntegrationPlan with decision

        """
        # Exact match: always skip
        if redundancy.level == RedundancyLevel.EXACT_MATCH:
            return IntegrationPlan(
                decision=IntegrationDecision.SKIP,
                target_entries=redundancy.matching_entries,
                rationale="Exact duplicate of existing content",
                confidence=1.0,
            )

        # Highly redundant: skip unless special case
        if redundancy.level == RedundancyLevel.HIGHLY_REDUNDANT:
            return IntegrationPlan(
                decision=IntegrationDecision.SKIP,
                target_entries=redundancy.matching_entries,
                rationale=(
                    "80%+ overlap with existing entries: "
                    f"{', '.join(redundancy.matching_entries[:3])}"
                ),
                confidence=0.9,
            )

        # Novel: store as standalone
        if redundancy.level == RedundancyLevel.NOVEL:
            return IntegrationPlan(
                decision=IntegrationDecision.STANDALONE,
                target_entries=[],
                rationale="Novel content with no significant overlap",
                confidence=0.9,
            )

        # Partial overlap: decide based on delta
        if delta:
            if (
                delta.delta_type == DeltaType.NOVEL_INSIGHT
                and delta.value_score >= VALUE_CONTRADICTION
            ):
                return IntegrationPlan(
                    decision=IntegrationDecision.STANDALONE,
                    target_entries=[],
                    rationale=f"Novel insights justify standalone: {delta.teaching_delta}",
                    confidence=0.8,
                )

            if delta.delta_type == DeltaType.CONTRADICTS:
                return IntegrationPlan(
                    decision=IntegrationDecision.REPLACE,
                    target_entries=redundancy.matching_entries[:1],
                    rationale=f"Contradicts/corrects existing: {delta.teaching_delta}",
                    confidence=0.6,
                )

            if (
                delta.delta_type == DeltaType.MORE_EXAMPLES
                and delta.value_score >= VALUE_MORE_EXAMPLES
            ):
                return IntegrationPlan(
                    decision=IntegrationDecision.MERGE,
                    target_entries=redundancy.matching_entries[:1],
                    rationale=f"Enhances existing with examples: {delta.teaching_delta}",
                    confidence=0.7,
                )

            if delta.value_score < VALUE_LOW:
                return IntegrationPlan(
                    decision=IntegrationDecision.SKIP,
                    target_entries=redundancy.matching_entries,
                    rationale=f"Insufficient marginal value: {delta.teaching_delta}",
                    confidence=0.7,
                )

        # Default: suggest merge but with low confidence
        return IntegrationPlan(
            decision=IntegrationDecision.MERGE,
            target_entries=redundancy.matching_entries[:1]
            if redundancy.matching_entries
            else [],
            rationale="Partial overlap suggests merge, but needs human review",
            confidence=0.5,
        )

    def explain_decision(
        self,
        redundancy: RedundancyCheck,
        delta: DeltaAnalysis | None,
        integration: IntegrationPlan,
    ) -> str:
        """Generate human-readable explanation of the filtering decision.

        Args:
            redundancy: Redundancy check result
            delta: Delta analysis (if applicable)
            integration: Integration decision

        Returns:
            Formatted explanation string

        """
        lines = []
        lines.append("=== Marginal Value Assessment ===\n")

        # Redundancy
        lines.append(f"Redundancy: {redundancy.level.value}")
        lines.append(f"Overlap: {redundancy.overlap_score:.0%}")
        if redundancy.matching_entries:
            lines.append(f"Matches: {', '.join(redundancy.matching_entries[:5])}")
        for reason in redundancy.reasons:
            lines.append(f"  - {reason}")
        lines.append("")

        # Delta
        if delta:
            lines.append(f"Delta Type: {delta.delta_type.value}")
            lines.append(f"Value Score: {delta.value_score:.0%}")
            lines.append(f"Teaching Delta: {delta.teaching_delta}")

            if delta.novel_aspects:
                lines.append("Novel aspects:")
                for aspect in delta.novel_aspects[:3]:
                    lines.append(f"  + {aspect}")

            if delta.redundant_aspects:
                lines.append("Already covered:")
                for aspect in delta.redundant_aspects[:3]:
                    lines.append(f"  - {aspect}")
            lines.append("")

        # Integration decision
        lines.append(f"Decision: {integration.decision.value.upper()}")
        lines.append(f"Confidence: {integration.confidence:.0%}")
        lines.append(f"Rationale: {integration.rationale}")
        if integration.target_entries:
            lines.append(f"Target entries: {', '.join(integration.target_entries)}")

        return "\n".join(lines)

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
        # Map integration decisions to RL signals
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

        Combines evaluate_content with RL signal emission for
        reinforcement learning integration.

        Args:
            content: The new knowledge content (markdown)
            title: Title/summary of the content
            tags: Optional tags describing the content

        Returns:
            Tuple of (redundancy, delta, integration, rl_signal)

        """
        # Generate content hash for tracking
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

        # Evaluate content
        redundancy, delta, integration = self.evaluate_content(content, title, tags)

        # Emit RL signal
        rl_signal = self.emit_rl_signal(integration, content_hash)

        return redundancy, delta, integration, rl_signal
