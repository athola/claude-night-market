"""Tests for _mv_models — shared enums, dataclasses, and constants.

Feature: Marginal Value Models
  As a corpus filter
  I want shared data models that both marginal_value and integration_policy
  can import without circular dependencies
  So that the subsystem is importable and structurally sound
"""

from __future__ import annotations

import pytest

from memory_palace.corpus._mv_models import (
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


class TestConstants:
    """Feature: Threshold constants are correctly ordered.

    As a filter
    I want well-ordered thresholds
    So that routing decisions are consistent
    """

    @pytest.mark.unit
    def test_overlap_strong_greater_than_overlap_partial(self) -> None:
        """Scenario: Overlap thresholds are ordered high-to-low
        Given OVERLAP_STRONG and OVERLAP_PARTIAL
        When compared
        Then OVERLAP_STRONG > OVERLAP_PARTIAL.
        """
        assert OVERLAP_STRONG > OVERLAP_PARTIAL

    @pytest.mark.unit
    def test_value_scores_are_ordered(self) -> None:
        """Scenario: Value scores decrease in priority order
        Given VALUE_NOVEL, VALUE_CONTRADICTION, VALUE_MORE_EXAMPLES, VALUE_LOW, VALUE_NONE
        When compared pairwise
        Then each is strictly greater than the next.
        """
        assert VALUE_NOVEL > VALUE_CONTRADICTION
        assert VALUE_CONTRADICTION > VALUE_MORE_EXAMPLES
        assert VALUE_MORE_EXAMPLES > VALUE_LOW
        assert VALUE_LOW > VALUE_NONE

    @pytest.mark.unit
    def test_all_value_scores_in_unit_range(self) -> None:
        """Scenario: All value scores are valid probabilities
        Given all five value score constants
        When checked
        Then each is between 0.0 and 1.0 inclusive.
        """
        for score in (
            VALUE_NOVEL,
            VALUE_CONTRADICTION,
            VALUE_MORE_EXAMPLES,
            VALUE_LOW,
            VALUE_NONE,
        ):
            assert 0.0 <= score <= 1.0


class TestRedundancyLevel:
    """Feature: RedundancyLevel enum has the expected members.

    As a filter
    I want exactly four redundancy levels
    So that routing covers all cases
    """

    @pytest.mark.unit
    def test_all_levels_present(self) -> None:
        """Scenario: All four levels exist
        Given the RedundancyLevel enum
        When inspected
        Then EXACT_MATCH, HIGHLY_REDUNDANT, PARTIAL_OVERLAP, NOVEL are present.
        """
        assert RedundancyLevel.EXACT_MATCH.value == "exact_match"
        assert RedundancyLevel.HIGHLY_REDUNDANT.value == "redundant"
        assert RedundancyLevel.PARTIAL_OVERLAP.value == "partial"
        assert RedundancyLevel.NOVEL.value == "novel"

    @pytest.mark.unit
    def test_exactly_four_levels(self) -> None:
        """Scenario: Enum has exactly four members
        Given the RedundancyLevel enum
        When counted
        Then len == 4.
        """
        assert len(RedundancyLevel) == 4


class TestDeltaType:
    """Feature: DeltaType enum has the expected members.

    As a filter
    I want exactly five delta types
    So that every delta case is named
    """

    @pytest.mark.unit
    def test_all_delta_types_present(self) -> None:
        """Scenario: All five delta types exist
        Given the DeltaType enum
        When inspected
        Then NOVEL_INSIGHT, DIFFERENT_FRAMING, MORE_EXAMPLES, CONTRADICTS, NONE are present.
        """
        assert DeltaType.NOVEL_INSIGHT.value == "novel_insight"
        assert DeltaType.DIFFERENT_FRAMING.value == "different_framing"
        assert DeltaType.MORE_EXAMPLES.value == "more_examples"
        assert DeltaType.CONTRADICTS.value == "contradicts"
        assert DeltaType.NONE.value == "none"

    @pytest.mark.unit
    def test_exactly_five_delta_types(self) -> None:
        """Scenario: Enum has exactly five members
        Given the DeltaType enum
        When counted
        Then len == 5.
        """
        assert len(DeltaType) == 5


class TestIntegrationDecision:
    """Feature: IntegrationDecision enum has the expected members.

    As a filter
    I want exactly four decisions
    So that every routing outcome is named
    """

    @pytest.mark.unit
    def test_all_decisions_present(self) -> None:
        """Scenario: All four decisions exist
        Given the IntegrationDecision enum
        When inspected
        Then STANDALONE, MERGE, REPLACE, SKIP are present.
        """
        assert IntegrationDecision.STANDALONE.value == "standalone"
        assert IntegrationDecision.MERGE.value == "merge"
        assert IntegrationDecision.REPLACE.value == "replace"
        assert IntegrationDecision.SKIP.value == "skip"

    @pytest.mark.unit
    def test_exactly_four_decisions(self) -> None:
        """Scenario: Enum has exactly four members
        Given the IntegrationDecision enum
        When counted
        Then len == 4.
        """
        assert len(IntegrationDecision) == 4


class TestRedundancyCheck:
    """Feature: RedundancyCheck dataclass stores all analysis fields.

    As a filter
    I want a structured result for redundancy analysis
    So that downstream steps can inspect it predictably
    """

    @pytest.mark.unit
    def test_create_with_all_fields(self) -> None:
        """Scenario: Construct a RedundancyCheck with all fields
        Given level, score, matching_entries, and reasons
        When I construct a RedundancyCheck
        Then all fields are accessible and correct.
        """
        check = RedundancyCheck(
            level=RedundancyLevel.PARTIAL_OVERLAP,
            overlap_score=0.55,
            matching_entries=["entry-a", "entry-b"],
            reasons=["55% overlap"],
        )
        assert check.level == RedundancyLevel.PARTIAL_OVERLAP
        assert check.overlap_score == 0.55
        assert check.matching_entries == ["entry-a", "entry-b"]
        assert check.reasons == ["55% overlap"]


class TestDeltaAnalysis:
    """Feature: DeltaAnalysis dataclass stores all delta fields.

    As a filter
    I want a structured result for delta analysis
    So that integration policy can reason over it
    """

    @pytest.mark.unit
    def test_create_with_all_fields(self) -> None:
        """Scenario: Construct a DeltaAnalysis with all fields
        Given delta_type, value_score, aspects, and teaching_delta
        When I construct a DeltaAnalysis
        Then all fields are accessible and correct.
        """
        delta = DeltaAnalysis(
            delta_type=DeltaType.NOVEL_INSIGHT,
            value_score=0.8,
            novel_aspects=["new concept"],
            redundant_aspects=["old concept"],
            teaching_delta="Introduces 2 new ideas",
        )
        assert delta.delta_type == DeltaType.NOVEL_INSIGHT
        assert delta.value_score == 0.8
        assert delta.novel_aspects == ["new concept"]
        assert delta.redundant_aspects == ["old concept"]
        assert "2 new ideas" in delta.teaching_delta


class TestIntegrationPlan:
    """Feature: IntegrationPlan dataclass stores all decision fields.

    As a filter
    I want a structured integration decision
    So that callers know exactly what to do with new content
    """

    @pytest.mark.unit
    def test_create_with_all_fields(self) -> None:
        """Scenario: Construct an IntegrationPlan with all fields
        Given decision, target_entries, rationale, and confidence
        When I construct an IntegrationPlan
        Then all fields are accessible and correct.
        """
        plan = IntegrationPlan(
            decision=IntegrationDecision.MERGE,
            target_entries=["target-1"],
            rationale="Enhances existing entry",
            confidence=0.7,
        )
        assert plan.decision == IntegrationDecision.MERGE
        assert plan.target_entries == ["target-1"]
        assert "Enhances" in plan.rationale
        assert plan.confidence == 0.7
