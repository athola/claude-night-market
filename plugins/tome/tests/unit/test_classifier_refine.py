"""Tests for vocabulary coverage and the refine option.

Feature: Abstention must not silently narrow research coverage
  The planner activates the academic channel only at depth medium and
  the triz channel only at depth deep. A topic that falls back to
  general therefore loses half its channels. Doing that BECAUSE the
  topic was unfamiliar is backwards: an unrecognized topic needs more
  coverage, not less.

  The fix follows the reject-and-refine framework (Zhang, Wang & Qiao,
  arXiv:1701.02265), where low confidence defers to a broader candidate
  set rather than collapsing to one narrow fallback.
"""

from __future__ import annotations

import pytest

from tome.scripts.domain_classifier import classify
from tome.scripts.research_planner import plan

_DEPTH_ORDER = {"light": 0, "medium": 1, "deep": 2, "maximum": 3}


class TestVocabularyCoverage:
    """Feature: the vocabulary covers agent and retrieval topics."""

    @pytest.mark.unit
    def test_agent_memory_topic_is_recognized(self) -> None:
        """Scenario: a rich agent-memory topic no longer reads as noise."""
        result = classify(
            "retrieval augmented generation with vector embeddings for agent memory"
        )
        assert result.domain != "general", (
            "an explicit agent-memory topic must classify, not fall back"
        )

    @pytest.mark.unit
    def test_agent_topic_gets_full_channel_coverage(self) -> None:
        """Scenario: the topic that motivated this work gets four channels."""
        result = classify(
            "persistent session memory and on-demand recall for AI coding agents"
        )
        assert len(plan(result).channels) == 4

    @pytest.mark.unit
    def test_existing_domains_still_classify(self) -> None:
        """Scenario: adding vocabulary does not steal existing topics."""
        assert classify("cache eviction policies for b-tree index").domain == (
            "data-structure"
        )
        assert classify("react component css layout responsive").domain == "ui-ux"


class TestRefineOnAmbiguity:
    """Feature: ambiguity widens the search instead of narrowing it."""

    @pytest.mark.unit
    def test_ambiguous_topic_keeps_at_least_its_best_candidate_depth(self) -> None:
        """Scenario: a topic spanning domains is not demoted to light.

        A topic touching several vocabularies is the definition of
        cross-domain, which is exactly when the triz channel earns its
        cost.
        """
        result = classify("distributed cache index sharding for microservice search")
        assert result.triz_depth != "light", (
            f"ambiguous topic was demoted to light: {result}"
        )

    @pytest.mark.unit
    def test_refine_records_the_candidates_considered(self) -> None:
        """Scenario: the abstention is inspectable, not silent."""
        result = classify("distributed cache index sharding for microservice search")
        assert len(result.candidates) >= 2

    @pytest.mark.unit
    def test_confident_classification_has_no_candidate_list(self) -> None:
        """Scenario: candidates are the abstention record, not always-on."""
        assert classify("cache eviction policies for b-tree index").candidates == []


class TestNoSignalStaysCheap:
    """Feature: nothing to refine means nothing to escalate.

    Gibberish is genuinely unresearchable. Escalating it to four
    channels would burn budget on noise, so the no-signal path is
    deliberately distinct from the ambiguous path.
    """

    @pytest.mark.unit
    def test_gibberish_stays_light(self) -> None:
        """Scenario: no keyword hits at all keeps the cheap plan."""
        result = classify("qwerty zxcvbn plugh xyzzy")
        assert result.domain == "general"
        assert result.triz_depth == "light"
        assert result.candidates == []

    @pytest.mark.unit
    def test_empty_topic_stays_light(self) -> None:
        """Scenario: an empty topic is the same case as gibberish."""
        assert classify("").triz_depth == "light"


class TestConfidenceReflectsEvidence:
    """Feature: confidence rises with evidence, not just purity.

    best_count/total_hits is a purity measure. Two hits in exactly one
    domain scores 1.0 while twenty hits mostly in one domain scores
    less, so thin evidence outranks rich evidence. Saturating on match
    count corrects the direction.
    """

    @pytest.mark.unit
    def test_thin_evidence_scores_below_rich_evidence(self) -> None:
        """Scenario: one pure domain, two hits versus many hits."""
        thin = classify("sort complexity")
        rich = classify(
            "sort search graph tree hash complexity optimization scheduling"
        )
        assert rich.confidence >= thin.confidence

    @pytest.mark.unit
    def test_confidence_stays_in_range(self) -> None:
        """Scenario: the score remains a valid [0, 1] quantity."""
        for topic in ("", "sort", "cache eviction b-tree index", "react css"):
            assert 0.0 <= classify(topic).confidence <= 1.0
