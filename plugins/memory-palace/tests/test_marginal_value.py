"""Tests for marginal value filter for knowledge corpus anti-pollution.

Tests the MarginalValueFilter which implements redundancy detection,
delta analysis, and integration decisions to validate only valuable
knowledge enters the corpus.
"""

from unittest.mock import MagicMock, patch

import pytest

from memory_palace.corpus.marginal_value import (
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
    MarginalValueFilter,
    RedundancyCheck,
    RedundancyLevel,
)
from memory_palace.corpus.usage_tracker import UsageSignal


class TestRedundancyLevel:
    """Test RedundancyLevel enum."""

    def test_all_levels_defined(self) -> None:
        """Should have all expected redundancy levels."""
        assert RedundancyLevel.EXACT_MATCH.value == "exact_match"
        assert RedundancyLevel.HIGHLY_REDUNDANT.value == "redundant"
        assert RedundancyLevel.PARTIAL_OVERLAP.value == "partial"
        assert RedundancyLevel.NOVEL.value == "novel"

    def test_redundancy_levels_count(self) -> None:
        """Should have exactly 4 redundancy levels."""
        assert len(RedundancyLevel) == 4


class TestDeltaType:
    """Test DeltaType enum."""

    def test_all_delta_types_defined(self) -> None:
        """Should have all expected delta types."""
        assert DeltaType.NOVEL_INSIGHT.value == "novel_insight"
        assert DeltaType.DIFFERENT_FRAMING.value == "different_framing"
        assert DeltaType.MORE_EXAMPLES.value == "more_examples"
        assert DeltaType.CONTRADICTS.value == "contradicts"
        assert DeltaType.NONE.value == "none"

    def test_delta_types_count(self) -> None:
        """Should have exactly 5 delta types."""
        assert len(DeltaType) == 5


class TestIntegrationDecision:
    """Test IntegrationDecision enum."""

    def test_all_decisions_defined(self) -> None:
        """Should have all expected integration decisions."""
        assert IntegrationDecision.STANDALONE.value == "standalone"
        assert IntegrationDecision.MERGE.value == "merge"
        assert IntegrationDecision.REPLACE.value == "replace"
        assert IntegrationDecision.SKIP.value == "skip"

    def test_integration_decisions_count(self) -> None:
        """Should have exactly 4 integration decisions."""
        assert len(IntegrationDecision) == 4


class TestRedundancyCheck:
    """Test RedundancyCheck dataclass."""

    def test_create_redundancy_check(self) -> None:
        """Should create redundancy check with all fields."""
        check = RedundancyCheck(
            level=RedundancyLevel.PARTIAL_OVERLAP,
            overlap_score=0.6,
            matching_entries=["entry-1", "entry-2"],
            reasons=["Partial overlap with existing content"],
        )
        assert check.level == RedundancyLevel.PARTIAL_OVERLAP
        assert check.overlap_score == 0.6
        assert len(check.matching_entries) == 2
        assert len(check.reasons) == 1

    def test_overlap_score_range(self) -> None:
        """Overlap score should be between 0.0 and 1.0."""
        check = RedundancyCheck(
            level=RedundancyLevel.NOVEL,
            overlap_score=0.0,
            matching_entries=[],
            reasons=["No matches"],
        )
        assert 0.0 <= check.overlap_score <= 1.0


class TestDeltaAnalysis:
    """Test DeltaAnalysis dataclass."""

    def test_create_delta_analysis(self) -> None:
        """Should create delta analysis with all fields."""
        delta = DeltaAnalysis(
            delta_type=DeltaType.NOVEL_INSIGHT,
            value_score=0.8,
            novel_aspects=["New concept: async patterns"],
            redundant_aspects=["Already covered: basic syntax"],
            teaching_delta="Introduces 5 new concepts",
        )
        assert delta.delta_type == DeltaType.NOVEL_INSIGHT
        assert delta.value_score == 0.8
        assert len(delta.novel_aspects) == 1
        assert len(delta.redundant_aspects) == 1
        assert "5 new concepts" in delta.teaching_delta

    def test_value_score_range(self) -> None:
        """Value score should be between 0.0 and 1.0."""
        delta = DeltaAnalysis(
            delta_type=DeltaType.NONE,
            value_score=VALUE_NONE,
            novel_aspects=[],
            redundant_aspects=[],
            teaching_delta="No value",
        )
        assert 0.0 <= delta.value_score <= 1.0


class TestIntegrationPlan:
    """Test IntegrationPlan dataclass."""

    def test_create_integration_plan(self) -> None:
        """Should create integration plan with all fields."""
        plan = IntegrationPlan(
            decision=IntegrationDecision.MERGE,
            target_entries=["entry-to-merge"],
            rationale="Enhances existing with examples",
            confidence=0.7,
        )
        assert plan.decision == IntegrationDecision.MERGE
        assert plan.target_entries == ["entry-to-merge"]
        assert "examples" in plan.rationale
        assert plan.confidence == 0.7

    def test_confidence_range(self) -> None:
        """Confidence should be between 0.0 and 1.0."""
        plan = IntegrationPlan(
            decision=IntegrationDecision.STANDALONE,
            target_entries=[],
            rationale="Novel content",
            confidence=0.9,
        )
        assert 0.0 <= plan.confidence <= 1.0


class TestConstants:
    """Test module constants."""

    def test_overlap_thresholds_ordered(self) -> None:
        """Strong overlap should be higher than partial."""
        assert OVERLAP_STRONG > OVERLAP_PARTIAL

    def test_value_scores_ordered(self) -> None:
        """Value scores should be properly ordered by importance."""
        assert VALUE_NOVEL > VALUE_CONTRADICTION
        assert VALUE_CONTRADICTION > VALUE_MORE_EXAMPLES
        assert VALUE_MORE_EXAMPLES > VALUE_LOW
        assert VALUE_LOW > VALUE_NONE

    def test_value_scores_in_range(self) -> None:
        """All value scores should be between 0.0 and 1.0."""
        for score in [
            VALUE_NOVEL,
            VALUE_CONTRADICTION,
            VALUE_MORE_EXAMPLES,
            VALUE_LOW,
            VALUE_NONE,
        ]:
            assert 0.0 <= score <= 1.0


class TestMarginalValueFilter:
    """Test MarginalValueFilter main class."""

    @pytest.fixture
    def mock_filter(self, tmp_path):
        """Create filter with mocked dependencies."""
        corpus_dir = tmp_path / "corpus"
        index_dir = tmp_path / "index"
        corpus_dir.mkdir()
        index_dir.mkdir()

        with (
            patch("memory_palace.corpus.marginal_value.CacheLookup") as mock_cache,
            patch("memory_palace.corpus.marginal_value.KeywordIndexer"),
            patch("memory_palace.corpus.marginal_value.QueryTemplateManager"),
        ):
            mock_cache_instance = MagicMock()
            mock_cache.return_value = mock_cache_instance

            filter_instance = MarginalValueFilter(
                corpus_dir=str(corpus_dir),
                index_dir=str(index_dir),
            )
            filter_instance._mock_cache = mock_cache_instance
            yield filter_instance

    def test_init_creates_filter(self, mock_filter) -> None:
        """Should initialize filter with corpus and index directories."""
        assert mock_filter.corpus_dir.exists()
        assert mock_filter.index_dir.exists()

    def test_extract_keywords_from_tags(self, mock_filter) -> None:
        """Should extract keywords from provided tags."""
        content = "Some content"
        title = "Test Title"
        tags = ["python", "async", "concurrency"]

        keywords = mock_filter._extract_keywords(content, title, tags)

        assert "python" in keywords
        assert "async" in keywords
        assert "concurrency" in keywords

    def test_extract_keywords_from_title(self, mock_filter) -> None:
        """Should extract keywords from title."""
        content = "Some content"
        title = "Understanding Async Programming"
        tags = []

        keywords = mock_filter._extract_keywords(content, title, tags)

        assert "understanding" in keywords
        assert "async" in keywords
        assert "programming" in keywords

    def test_extract_keywords_removes_stop_words(self, mock_filter) -> None:
        """Should remove common stop words."""
        content = "The quick and fast"
        title = "The Big Test"
        tags = ["the", "and"]

        keywords = mock_filter._extract_keywords(content, title, tags)

        assert "the" not in keywords
        assert "and" not in keywords

    def test_extract_keywords_technical_terms(self, mock_filter) -> None:
        """Should extract hyphenated technical terms."""
        content = "Using event-driven architecture with async-await patterns"
        title = "Test"
        tags = []

        keywords = mock_filter._extract_keywords(content, title, tags)

        assert "event-driven" in keywords
        assert "async-await" in keywords

    def test_extract_keywords_emphasized_text(self, mock_filter) -> None:
        """Should extract emphasized (bold/italic) terms."""
        content = "This is **important** and *critical* for understanding"
        title = "Test"
        tags = []

        keywords = mock_filter._extract_keywords(content, title, tags)

        assert "important" in keywords
        assert "critical" in keywords

    def test_extract_keywords_from_headings(self, mock_filter) -> None:
        """Should extract keywords from markdown headings."""
        content = """# Main Topic
## Subtopic One
### Detailed Section
Some body text here.
"""
        title = "Test"
        tags = []

        keywords = mock_filter._extract_keywords(content, title, tags)

        assert "main" in keywords
        assert "topic" in keywords
        assert "subtopic" in keywords

    def test_infer_queries_how_patterns(self, mock_filter) -> None:
        """Should infer how-to queries from headings."""
        content = """# How to Implement Caching
## How to invalidate cache entries
"""
        title = "Caching Guide"

        queries = mock_filter._infer_queries(content, title)

        assert any("how" in q.lower() for q in queries)

    def test_infer_queries_pattern_approach(self, mock_filter) -> None:
        """Should infer 'what is' queries for patterns/approaches."""
        content = """# Repository Pattern
## CQRS Approach
"""
        title = "Design Patterns"

        queries = mock_filter._infer_queries(content, title)

        assert any("pattern" in q.lower() for q in queries)

    def test_check_redundancy_no_matches_novel(self, mock_filter) -> None:
        """Should return NOVEL when no matching entries found."""
        mock_filter._mock_cache.search.return_value = []

        keywords = {"python", "async", "testing"}
        queries = ["how to test async code"]
        content = "Test content"

        result = mock_filter._check_redundancy(keywords, queries, content)

        assert result.level == RedundancyLevel.NOVEL
        assert result.overlap_score == 0.0
        assert len(result.matching_entries) == 0

    def test_check_redundancy_exact_match(self, mock_filter) -> None:
        """Should detect exact content match."""
        content = "This is the exact content"

        mock_filter._mock_cache.search.return_value = [
            {"entry_id": "existing-entry", "match_score": 0.9}
        ]
        mock_filter._mock_cache.get_entry_content.return_value = content

        keywords = {"exact", "content"}
        queries = []

        result = mock_filter._check_redundancy(keywords, queries, content)

        assert result.level == RedundancyLevel.EXACT_MATCH
        assert result.overlap_score == 1.0

    def test_check_redundancy_highly_redundant(self, mock_filter) -> None:
        """Should detect highly redundant content (>= 80% overlap)."""
        mock_filter._mock_cache.search.return_value = [
            {"entry_id": "similar-entry", "match_score": 0.85}
        ]
        mock_filter._mock_cache.get_entry_content.return_value = "Different content"

        keywords = {"python", "testing"}
        queries = []
        content = "Some new content"

        result = mock_filter._check_redundancy(keywords, queries, content)

        assert result.level == RedundancyLevel.HIGHLY_REDUNDANT
        assert result.overlap_score >= OVERLAP_STRONG

    def test_check_redundancy_partial_overlap(self, mock_filter) -> None:
        """Should detect partial overlap (40-80%)."""
        mock_filter._mock_cache.search.return_value = [
            {"entry_id": "partial-entry", "match_score": 0.55}
        ]
        mock_filter._mock_cache.get_entry_content.return_value = "Different content"

        keywords = {"python", "async"}
        queries = []
        content = "New content with some overlap"

        result = mock_filter._check_redundancy(keywords, queries, content)

        assert result.level == RedundancyLevel.PARTIAL_OVERLAP
        assert OVERLAP_PARTIAL <= result.overlap_score < OVERLAP_STRONG


class TestMarginalValueFilterDecisions:
    """Test integration decision logic."""

    @pytest.fixture
    def mock_filter(self, tmp_path):
        """Create filter with mocked dependencies."""
        corpus_dir = tmp_path / "corpus"
        index_dir = tmp_path / "index"
        corpus_dir.mkdir()
        index_dir.mkdir()

        with (
            patch("memory_palace.corpus.marginal_value.CacheLookup"),
            patch("memory_palace.corpus.marginal_value.KeywordIndexer"),
            patch("memory_palace.corpus.marginal_value.QueryTemplateManager"),
        ):
            yield MarginalValueFilter(
                corpus_dir=str(corpus_dir),
                index_dir=str(index_dir),
            )

    def test_decide_integration_exact_match_skip(self, mock_filter) -> None:
        """Exact match should always result in SKIP."""
        redundancy = RedundancyCheck(
            level=RedundancyLevel.EXACT_MATCH,
            overlap_score=1.0,
            matching_entries=["dup-entry"],
            reasons=["Exact duplicate"],
        )

        plan = mock_filter._decide_integration(redundancy, None)

        assert plan.decision == IntegrationDecision.SKIP
        assert plan.confidence == 1.0

    def test_decide_integration_highly_redundant_skip(self, mock_filter) -> None:
        """Highly redundant content should result in SKIP."""
        redundancy = RedundancyCheck(
            level=RedundancyLevel.HIGHLY_REDUNDANT,
            overlap_score=0.85,
            matching_entries=["existing-1", "existing-2"],
            reasons=["High overlap"],
        )

        plan = mock_filter._decide_integration(redundancy, None)

        assert plan.decision == IntegrationDecision.SKIP
        assert plan.confidence == 0.9

    def test_decide_integration_novel_standalone(self, mock_filter) -> None:
        """Novel content should result in STANDALONE."""
        redundancy = RedundancyCheck(
            level=RedundancyLevel.NOVEL,
            overlap_score=0.1,
            matching_entries=[],
            reasons=["No matches"],
        )

        plan = mock_filter._decide_integration(redundancy, None)

        assert plan.decision == IntegrationDecision.STANDALONE
        assert plan.confidence == 0.9

    def test_decide_integration_novel_insight_standalone(self, mock_filter) -> None:
        """Novel insights should result in STANDALONE."""
        redundancy = RedundancyCheck(
            level=RedundancyLevel.PARTIAL_OVERLAP,
            overlap_score=0.5,
            matching_entries=["partial-match"],
            reasons=["Partial overlap"],
        )
        delta = DeltaAnalysis(
            delta_type=DeltaType.NOVEL_INSIGHT,
            value_score=VALUE_NOVEL,
            novel_aspects=["New pattern discovered"],
            redundant_aspects=[],
            teaching_delta="Introduces new concepts",
        )

        plan = mock_filter._decide_integration(redundancy, delta)

        assert plan.decision == IntegrationDecision.STANDALONE
        assert plan.confidence == 0.8

    def test_decide_integration_contradicts_replace(self, mock_filter) -> None:
        """Contradicting content should result in REPLACE."""
        redundancy = RedundancyCheck(
            level=RedundancyLevel.PARTIAL_OVERLAP,
            overlap_score=0.6,
            matching_entries=["outdated-entry"],
            reasons=["Partial overlap"],
        )
        delta = DeltaAnalysis(
            delta_type=DeltaType.CONTRADICTS,
            value_score=VALUE_CONTRADICTION,
            novel_aspects=["Corrects misconception"],
            redundant_aspects=[],
            teaching_delta="Alternative perspective",
        )

        plan = mock_filter._decide_integration(redundancy, delta)

        assert plan.decision == IntegrationDecision.REPLACE
        assert plan.confidence == 0.6

    def test_decide_integration_more_examples_merge(self, mock_filter) -> None:
        """More examples with sufficient value should result in MERGE."""
        redundancy = RedundancyCheck(
            level=RedundancyLevel.PARTIAL_OVERLAP,
            overlap_score=0.5,
            matching_entries=["base-entry"],
            reasons=["Partial overlap"],
        )
        delta = DeltaAnalysis(
            delta_type=DeltaType.MORE_EXAMPLES,
            value_score=VALUE_MORE_EXAMPLES,
            novel_aspects=["Additional examples"],
            redundant_aspects=["Core concept"],
            teaching_delta="Provides examples",
        )

        plan = mock_filter._decide_integration(redundancy, delta)

        assert plan.decision == IntegrationDecision.MERGE
        assert plan.confidence == 0.7

    def test_decide_integration_low_value_skip(self, mock_filter) -> None:
        """Low value content should result in SKIP."""
        redundancy = RedundancyCheck(
            level=RedundancyLevel.PARTIAL_OVERLAP,
            overlap_score=0.5,
            matching_entries=["existing"],
            reasons=["Partial overlap"],
        )
        delta = DeltaAnalysis(
            delta_type=DeltaType.DIFFERENT_FRAMING,
            value_score=VALUE_NONE,
            novel_aspects=[],
            redundant_aspects=["Everything covered"],
            teaching_delta="No new value",
        )

        plan = mock_filter._decide_integration(redundancy, delta)

        assert plan.decision == IntegrationDecision.SKIP
        assert plan.confidence == 0.7


class TestMarginalValueFilterExplanation:
    """Test explanation generation."""

    @pytest.fixture
    def mock_filter(self, tmp_path):
        """Create filter with mocked dependencies."""
        corpus_dir = tmp_path / "corpus"
        index_dir = tmp_path / "index"
        corpus_dir.mkdir()
        index_dir.mkdir()

        with (
            patch("memory_palace.corpus.marginal_value.CacheLookup"),
            patch("memory_palace.corpus.marginal_value.KeywordIndexer"),
            patch("memory_palace.corpus.marginal_value.QueryTemplateManager"),
        ):
            yield MarginalValueFilter(
                corpus_dir=str(corpus_dir),
                index_dir=str(index_dir),
            )

    def test_explain_decision_includes_redundancy(self, mock_filter) -> None:
        """Explanation should include redundancy level and score."""
        redundancy = RedundancyCheck(
            level=RedundancyLevel.PARTIAL_OVERLAP,
            overlap_score=0.6,
            matching_entries=["match-1"],
            reasons=["60% overlap"],
        )
        integration = IntegrationPlan(
            decision=IntegrationDecision.MERGE,
            target_entries=["match-1"],
            rationale="Enhances existing",
            confidence=0.7,
        )

        explanation = mock_filter.explain_decision(redundancy, None, integration)

        assert "Redundancy:" in explanation
        assert "partial" in explanation
        assert "60%" in explanation

    def test_explain_decision_includes_delta(self, mock_filter) -> None:
        """Explanation should include delta analysis when available."""
        redundancy = RedundancyCheck(
            level=RedundancyLevel.PARTIAL_OVERLAP,
            overlap_score=0.5,
            matching_entries=["match-1"],
            reasons=["Partial overlap"],
        )
        delta = DeltaAnalysis(
            delta_type=DeltaType.NOVEL_INSIGHT,
            value_score=0.8,
            novel_aspects=["New async patterns"],
            redundant_aspects=["Basic syntax"],
            teaching_delta="Introduces 3 new concepts",
        )
        integration = IntegrationPlan(
            decision=IntegrationDecision.STANDALONE,
            target_entries=[],
            rationale="Novel insights",
            confidence=0.8,
        )

        explanation = mock_filter.explain_decision(redundancy, delta, integration)

        assert "Delta Type:" in explanation
        assert "novel_insight" in explanation
        assert "Novel aspects:" in explanation
        assert "New async patterns" in explanation

    def test_explain_decision_includes_final_decision(self, mock_filter) -> None:
        """Explanation should include final integration decision."""
        redundancy = RedundancyCheck(
            level=RedundancyLevel.NOVEL,
            overlap_score=0.0,
            matching_entries=[],
            reasons=["No matches"],
        )
        integration = IntegrationPlan(
            decision=IntegrationDecision.STANDALONE,
            target_entries=[],
            rationale="Novel content",
            confidence=0.9,
        )

        explanation = mock_filter.explain_decision(redundancy, None, integration)

        assert "Decision: STANDALONE" in explanation
        assert "Confidence: 90%" in explanation
        assert "Rationale:" in explanation


class TestMarginalValueFilterRLSignals:
    """Test RL signal emission."""

    @pytest.fixture
    def mock_filter(self, tmp_path):
        """Create filter with mocked dependencies."""
        corpus_dir = tmp_path / "corpus"
        index_dir = tmp_path / "index"
        corpus_dir.mkdir()
        index_dir.mkdir()

        with (
            patch("memory_palace.corpus.marginal_value.CacheLookup"),
            patch("memory_palace.corpus.marginal_value.KeywordIndexer"),
            patch("memory_palace.corpus.marginal_value.QueryTemplateManager"),
        ):
            yield MarginalValueFilter(
                corpus_dir=str(corpus_dir),
                index_dir=str(index_dir),
            )

    def test_emit_rl_signal_standalone(self, mock_filter) -> None:
        """STANDALONE decision should emit ACCESS signal."""
        integration = IntegrationPlan(
            decision=IntegrationDecision.STANDALONE,
            target_entries=[],
            rationale="Novel",
            confidence=0.9,
        )

        signal = mock_filter.emit_rl_signal(integration, "abc123")

        assert signal["signal_type"] == UsageSignal.ACCESS
        assert signal["action"] == "new_entry_created"
        assert signal["content_hash"] == "abc123"

    def test_emit_rl_signal_merge(self, mock_filter) -> None:
        """MERGE decision should emit CORRECTION signal."""
        integration = IntegrationPlan(
            decision=IntegrationDecision.MERGE,
            target_entries=["target-1"],
            rationale="Enhances",
            confidence=0.7,
        )

        signal = mock_filter.emit_rl_signal(integration)

        assert signal["signal_type"] == UsageSignal.CORRECTION
        assert signal["action"] == "entry_enhanced"
        assert signal["target_entries"] == ["target-1"]

    def test_emit_rl_signal_replace(self, mock_filter) -> None:
        """REPLACE decision should emit CORRECTION signal."""
        integration = IntegrationPlan(
            decision=IntegrationDecision.REPLACE,
            target_entries=["old-entry"],
            rationale="Supersedes",
            confidence=0.6,
        )

        signal = mock_filter.emit_rl_signal(integration)

        assert signal["signal_type"] == UsageSignal.CORRECTION
        assert signal["action"] == "entry_superseded"

    def test_emit_rl_signal_skip(self, mock_filter) -> None:
        """SKIP decision should emit STALE_FLAG signal."""
        integration = IntegrationPlan(
            decision=IntegrationDecision.SKIP,
            target_entries=["dup"],
            rationale="Duplicate",
            confidence=1.0,
        )

        signal = mock_filter.emit_rl_signal(integration)

        assert signal["signal_type"] == UsageSignal.STALE_FLAG
        assert signal["action"] == "content_rejected"
        assert signal["weight"] < 0  # Negative signal

    def test_emit_rl_signal_includes_metadata(self, mock_filter) -> None:
        """RL signal should include decision metadata."""
        integration = IntegrationPlan(
            decision=IntegrationDecision.STANDALONE,
            target_entries=[],
            rationale="Test rationale",
            confidence=0.85,
        )

        signal = mock_filter.emit_rl_signal(integration, "hash123")

        assert signal["decision"] == "standalone"
        assert signal["confidence"] == 0.85
        assert signal["rationale"] == "Test rationale"
        assert signal["content_hash"] == "hash123"


class TestMarginalValueFilterIntegration:
    """Integration tests for full evaluation workflow."""

    @pytest.fixture
    def mock_filter(self, tmp_path):
        """Create filter with fully mocked dependencies."""
        corpus_dir = tmp_path / "corpus"
        index_dir = tmp_path / "index"
        corpus_dir.mkdir()
        index_dir.mkdir()

        with (
            patch("memory_palace.corpus.marginal_value.CacheLookup") as mock_cache,
            patch("memory_palace.corpus.marginal_value.KeywordIndexer"),
            patch("memory_palace.corpus.marginal_value.QueryTemplateManager"),
        ):
            mock_cache_instance = MagicMock()
            mock_cache.return_value = mock_cache_instance
            mock_cache_instance.search.return_value = []
            mock_cache_instance.get_entry_content.return_value = None
            mock_cache_instance.get_entry_metadata.return_value = None

            filter_instance = MarginalValueFilter(
                corpus_dir=str(corpus_dir),
                index_dir=str(index_dir),
            )
            filter_instance._mock_cache = mock_cache_instance
            yield filter_instance

    def test_evaluate_content_novel(self, mock_filter) -> None:
        """Should evaluate novel content as STANDALONE."""
        content = """# New Topic

This is completely new content that doesn't exist in the corpus.
It covers **new concepts** and *fresh ideas*.
"""

        redundancy, delta, integration = mock_filter.evaluate_content(
            content=content,
            title="New Topic",
            tags=["new", "fresh"],
        )

        assert redundancy.level == RedundancyLevel.NOVEL
        assert delta is None  # No delta for novel content
        assert integration.decision == IntegrationDecision.STANDALONE

    def test_evaluate_content_duplicate(self, mock_filter) -> None:
        """Should evaluate duplicate content as SKIP."""
        content = "Exact duplicate content"

        mock_filter._mock_cache.search.return_value = [
            {"entry_id": "existing", "match_score": 0.95}
        ]
        mock_filter._mock_cache.get_entry_content.return_value = content

        redundancy, delta, integration = mock_filter.evaluate_content(
            content=content,
            title="Duplicate",
            tags=[],
        )

        assert redundancy.level == RedundancyLevel.EXACT_MATCH
        assert integration.decision == IntegrationDecision.SKIP

    def test_evaluate_with_rl_returns_signal(self, mock_filter) -> None:
        """evaluate_with_rl should return RL signal with results."""
        content = "Novel content for RL test"

        redundancy, delta, integration, rl_signal = mock_filter.evaluate_with_rl(
            content=content,
            title="RL Test",
            tags=["test"],
        )

        assert redundancy is not None
        assert integration is not None
        assert "signal_type" in rl_signal
        assert "content_hash" in rl_signal
        assert len(rl_signal["content_hash"]) == 16  # SHA256[:16]
