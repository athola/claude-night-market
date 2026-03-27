"""Tests for integration_policy — decide_integration and explain_decision.

Feature: Integration Policy
  As a marginal value filter
  I want pure functions for routing and explaining integration decisions
  So that the routing logic is testable without any I/O dependencies
"""

from __future__ import annotations

import pytest

from memory_palace.corpus._mv_models import (
    VALUE_CONTRADICTION,
    VALUE_NONE,
    VALUE_NOVEL,
    DeltaAnalysis,
    DeltaType,
    IntegrationDecision,
    IntegrationPlan,
    RedundancyCheck,
    RedundancyLevel,
)
from memory_palace.corpus.integration_policy import decide_integration, explain_decision


class TestDecideIntegration:
    """Feature: Integration routing.

    As a filter
    I want to route new content to the right integration action
    So that only valuable content enters the corpus
    """

    @pytest.mark.unit
    def test_exact_match_is_skipped(self) -> None:
        """Scenario: Exact duplicate is rejected
        Given redundancy level EXACT_MATCH
        When I decide integration
        Then the decision is SKIP with confidence 1.0.
        """
        redundancy = RedundancyCheck(
            level=RedundancyLevel.EXACT_MATCH,
            overlap_score=1.0,
            matching_entries=["dup"],
            reasons=["Exact duplicate"],
        )
        plan = decide_integration(redundancy, None)
        assert plan.decision == IntegrationDecision.SKIP
        assert plan.confidence == 1.0

    @pytest.mark.unit
    def test_highly_redundant_is_skipped(self) -> None:
        """Scenario: High overlap content is rejected
        Given redundancy level HIGHLY_REDUNDANT
        When I decide integration
        Then the decision is SKIP with confidence 0.9.
        """
        redundancy = RedundancyCheck(
            level=RedundancyLevel.HIGHLY_REDUNDANT,
            overlap_score=0.85,
            matching_entries=["e1", "e2"],
            reasons=["High overlap"],
        )
        plan = decide_integration(redundancy, None)
        assert plan.decision == IntegrationDecision.SKIP
        assert plan.confidence == 0.9

    @pytest.mark.unit
    def test_novel_content_is_standalone(self) -> None:
        """Scenario: Novel content gets standalone storage
        Given redundancy level NOVEL
        When I decide integration
        Then the decision is STANDALONE with confidence 0.9.
        """
        redundancy = RedundancyCheck(
            level=RedundancyLevel.NOVEL,
            overlap_score=0.0,
            matching_entries=[],
            reasons=["No matches"],
        )
        plan = decide_integration(redundancy, None)
        assert plan.decision == IntegrationDecision.STANDALONE
        assert plan.confidence == 0.9

    @pytest.mark.unit
    def test_novel_insight_with_high_value_is_standalone(self) -> None:
        """Scenario: Novel insight with high value score
        Given partial overlap and a NOVEL_INSIGHT delta with value >= VALUE_CONTRADICTION
        When I decide integration
        Then the decision is STANDALONE.
        """
        redundancy = RedundancyCheck(
            level=RedundancyLevel.PARTIAL_OVERLAP,
            overlap_score=0.5,
            matching_entries=["m1"],
            reasons=["Partial"],
        )
        delta = DeltaAnalysis(
            delta_type=DeltaType.NOVEL_INSIGHT,
            value_score=VALUE_NOVEL,
            novel_aspects=["New pattern"],
            redundant_aspects=[],
            teaching_delta="Introduces new concepts",
        )
        plan = decide_integration(redundancy, delta)
        assert plan.decision == IntegrationDecision.STANDALONE
        assert plan.confidence == 0.8

    @pytest.mark.unit
    def test_contradicting_content_is_replaced(self) -> None:
        """Scenario: Contradicting content replaces existing
        Given partial overlap and a CONTRADICTS delta
        When I decide integration
        Then the decision is REPLACE with confidence 0.6.
        """
        redundancy = RedundancyCheck(
            level=RedundancyLevel.PARTIAL_OVERLAP,
            overlap_score=0.6,
            matching_entries=["old"],
            reasons=["Partial"],
        )
        delta = DeltaAnalysis(
            delta_type=DeltaType.CONTRADICTS,
            value_score=VALUE_CONTRADICTION,
            novel_aspects=["Correction"],
            redundant_aspects=[],
            teaching_delta="Corrects misconception",
        )
        plan = decide_integration(redundancy, delta)
        assert plan.decision == IntegrationDecision.REPLACE
        assert plan.confidence == 0.6

    @pytest.mark.unit
    def test_more_examples_is_merged(self) -> None:
        """Scenario: Additional examples are merged
        Given partial overlap and MORE_EXAMPLES delta
        When I decide integration
        Then the decision is MERGE with confidence 0.7.
        """
        redundancy = RedundancyCheck(
            level=RedundancyLevel.PARTIAL_OVERLAP,
            overlap_score=0.5,
            matching_entries=["base"],
            reasons=["Partial"],
        )
        delta = DeltaAnalysis(
            delta_type=DeltaType.MORE_EXAMPLES,
            value_score=0.4,
            novel_aspects=["More examples"],
            redundant_aspects=["Core"],
            teaching_delta="Provides examples",
        )
        plan = decide_integration(redundancy, delta)
        assert plan.decision == IntegrationDecision.MERGE
        assert plan.confidence == 0.7

    @pytest.mark.unit
    def test_no_delta_content_is_skipped(self) -> None:
        """Scenario: Content with no meaningful delta is rejected
        Given partial overlap and a NONE delta type
        When I decide integration
        Then the decision is SKIP with confidence 0.7.
        """
        redundancy = RedundancyCheck(
            level=RedundancyLevel.PARTIAL_OVERLAP,
            overlap_score=0.5,
            matching_entries=["e"],
            reasons=["Partial"],
        )
        delta = DeltaAnalysis(
            delta_type=DeltaType.NONE,
            value_score=VALUE_NONE,
            novel_aspects=[],
            redundant_aspects=["Everything"],
            teaching_delta="No new value",
        )
        plan = decide_integration(redundancy, delta)
        assert plan.decision == IntegrationDecision.SKIP
        assert plan.confidence == 0.7

    @pytest.mark.unit
    def test_returns_integration_plan(self) -> None:
        """Scenario: Return type is IntegrationPlan
        Given any valid inputs
        When I call decide_integration
        Then the return value is an IntegrationPlan.
        """
        redundancy = RedundancyCheck(
            level=RedundancyLevel.NOVEL,
            overlap_score=0.0,
            matching_entries=[],
            reasons=[],
        )
        result = decide_integration(redundancy, None)
        assert isinstance(result, IntegrationPlan)


class TestExplainDecision:
    """Feature: Decision explanation.

    As a user
    I want a human-readable explanation of the filtering decision
    So that I can understand why content was accepted or rejected
    """

    @pytest.mark.unit
    def test_explanation_includes_redundancy_level(self) -> None:
        """Scenario: Explanation shows redundancy level
        Given a partial overlap redundancy check
        When I generate an explanation
        Then the explanation mentions "partial".
        """
        redundancy = RedundancyCheck(
            level=RedundancyLevel.PARTIAL_OVERLAP,
            overlap_score=0.6,
            matching_entries=["m1"],
            reasons=["60% overlap"],
        )
        integration = IntegrationPlan(
            decision=IntegrationDecision.MERGE,
            target_entries=["m1"],
            rationale="Enhances existing",
            confidence=0.7,
        )
        text = explain_decision(redundancy, None, integration)
        assert "partial" in text
        assert "60%" in text

    @pytest.mark.unit
    def test_explanation_includes_delta_when_present(self) -> None:
        """Scenario: Delta info appears when delta is provided
        Given a delta with type NOVEL_INSIGHT
        When I generate an explanation
        Then "Delta Type:" and "novel_insight" appear.
        """
        redundancy = RedundancyCheck(
            level=RedundancyLevel.PARTIAL_OVERLAP,
            overlap_score=0.5,
            matching_entries=["m"],
            reasons=["Partial"],
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
            rationale="Novel",
            confidence=0.8,
        )
        text = explain_decision(redundancy, delta, integration)
        assert "Delta Type:" in text
        assert "novel_insight" in text

    @pytest.mark.unit
    def test_explanation_includes_final_decision(self) -> None:
        """Scenario: Final decision appears in explanation
        Given a STANDALONE integration plan
        When I generate an explanation
        Then "Decision: STANDALONE" and confidence percentage appear.
        """
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
        text = explain_decision(redundancy, None, integration)
        assert "Decision: STANDALONE" in text
        assert "90%" in text
        assert "Rationale:" in text

    @pytest.mark.unit
    def test_explanation_returns_string(self) -> None:
        """Scenario: Return type is str
        Given any valid inputs
        When I call explain_decision
        Then the return value is a string.
        """
        redundancy = RedundancyCheck(
            level=RedundancyLevel.NOVEL,
            overlap_score=0.0,
            matching_entries=[],
            reasons=[],
        )
        integration = IntegrationPlan(
            decision=IntegrationDecision.STANDALONE,
            target_entries=[],
            rationale="test",
            confidence=0.5,
        )
        result = explain_decision(redundancy, None, integration)
        assert isinstance(result, str)
