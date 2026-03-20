"""
Feature: Domain classifier

As a research pipeline entry point
I want to classify a free-text topic into a research domain
So that downstream planners select appropriate channels and TRIZ depth
"""

from __future__ import annotations

import pytest
from tome.models import DomainClassification
from tome.scripts.domain_classifier import classify


class TestDomainClassifierBasicRouting:
    """
    Feature: Keyword-based domain routing

    As a pipeline orchestrator
    I want topics classified by keyword frequency
    So that each domain's channels receive relevant queries
    """

    @pytest.mark.unit
    def test_async_python_patterns_classifies_as_algorithm(self) -> None:
        """
        Scenario: Algorithm topic from concurrent/async keywords
        Given the topic "async python patterns"
        When classify is called
        Then domain is algorithm and triz_depth is medium
        """

        result = classify("async python patterns")

        assert result.domain == "algorithm"
        assert result.triz_depth == "medium"

    @pytest.mark.unit
    def test_react_component_library_classifies_as_ui_ux(self) -> None:
        """
        Scenario: UI/UX topic from frontend keywords
        Given the topic "react component library design"
        When classify is called
        Then domain is ui-ux and triz_depth is light
        """

        result = classify("react component library design")

        assert result.domain == "ui-ux"
        assert result.triz_depth == "light"

    @pytest.mark.unit
    def test_raft_consensus_classifies_as_algorithm_or_architecture(self) -> None:
        """
        Scenario: Consensus algorithm spans two plausible domains
        Given the topic "raft consensus algorithm"
        When classify is called
        Then domain is algorithm or architecture, triz_depth is medium
        """

        result = classify("raft consensus algorithm")

        assert result.domain in ("algorithm", "architecture")
        assert result.triz_depth == "medium"

    @pytest.mark.unit
    def test_cache_eviction_classifies_as_data_structure(self) -> None:
        """
        Scenario: Data structure topic from cache/eviction keywords
        Given the topic "novel cache eviction policy"
        When classify is called
        Then domain is data-structure and triz_depth is deep
        """

        result = classify("novel cache eviction policy")

        assert result.domain == "data-structure"
        assert result.triz_depth == "deep"

    @pytest.mark.unit
    def test_kubernetes_pipeline_classifies_as_devops(self) -> None:
        """
        Scenario: DevOps topic from kubernetes/pipeline keywords
        Given the topic "kubernetes deployment pipeline"
        When classify is called
        Then domain is devops and triz_depth is light
        """

        result = classify("kubernetes deployment pipeline")

        assert result.domain == "devops"
        assert result.triz_depth == "light"


class TestDomainClassifierFallback:
    """
    Feature: Fallback to general domain on low confidence

    As a pipeline orchestrator
    I want unrecognised topics to fall back to general/light
    So that every input produces a usable plan rather than an error
    """

    @pytest.mark.unit
    def test_gibberish_falls_back_to_general(self) -> None:
        """
        Scenario: Unrecognised topic falls back to general
        Given the topic "random gibberish xyz"
        When classify is called
        Then domain is general and triz_depth is light
        """

        result = classify("random gibberish xyz")

        assert result.domain == "general"
        assert result.triz_depth == "light"

    @pytest.mark.unit
    def test_low_confidence_falls_back_to_general(self) -> None:
        """
        Scenario: Single keyword match yields low confidence
        Given a topic with exactly one algorithm keyword
        When classify is called
        Then confidence is below 0.6 and domain falls back to general
        """

        # Only one algorithm keyword — not enough for confident classification
        result = classify("sort")

        assert result.domain == "general"
        assert result.confidence < 0.6

    @pytest.mark.unit
    def test_empty_topic_falls_back_to_general(self) -> None:
        """
        Scenario: Empty topic string is handled gracefully
        Given an empty topic string
        When classify is called
        Then domain is general and triz_depth is light
        """

        result = classify("")

        assert result.domain == "general"
        assert result.triz_depth == "light"


class TestDomainClassifierOutputShape:
    """
    Feature: classify() always returns a well-formed DomainClassification

    As a downstream planner
    I want the classification result to have valid, consistent weights
    So that I never need to guard against malformed data
    """

    @pytest.mark.unit
    def test_returns_domain_classification_instance(self) -> None:
        """
        Scenario: Return type is always DomainClassification
        Given any topic string
        When classify is called
        Then result is a DomainClassification
        """

        result = classify("async python patterns")

        assert isinstance(result, DomainClassification)

    @pytest.mark.unit
    def test_channel_weights_sum_to_one_for_algorithm(self) -> None:
        """
        Scenario: Algorithm domain weights are normalised
        Given "async python patterns" which classifies as algorithm
        When classify is called
        Then channel_weights sum to 1.0 (within floating-point tolerance)
        """

        result = classify("async python patterns")

        total = sum(result.channel_weights.values())
        assert abs(total - 1.0) < 1e-9

    @pytest.mark.unit
    def test_channel_weights_sum_to_one_for_ui_ux(self) -> None:
        """
        Scenario: UI-UX domain weights are normalised
        Given "react component library design"
        When classify is called
        Then channel_weights sum to 1.0
        """

        result = classify("react component library design")

        total = sum(result.channel_weights.values())
        assert abs(total - 1.0) < 1e-9

    @pytest.mark.unit
    def test_channel_weights_sum_to_one_for_general_fallback(self) -> None:
        """
        Scenario: General fallback weights are normalised
        Given "random gibberish xyz"
        When classify is called
        Then channel_weights sum to 1.0
        """

        result = classify("random gibberish xyz")

        total = sum(result.channel_weights.values())
        assert abs(total - 1.0) < 1e-9

    @pytest.mark.unit
    def test_all_four_channel_keys_present(self) -> None:
        """
        Scenario: channel_weights always contains all four keys
        Given any topic
        When classify is called
        Then channel_weights has keys code, discourse, academic, triz
        """

        result = classify("kubernetes deployment pipeline")

        assert set(result.channel_weights.keys()) == {
            "code",
            "discourse",
            "academic",
            "triz",
        }

    @pytest.mark.unit
    def test_confidence_between_zero_and_one(self) -> None:
        """
        Scenario: Confidence is always a valid probability
        Given any topic
        When classify is called
        Then confidence is in [0.0, 1.0]
        """

        for topic in [
            "async python patterns",
            "random gibberish xyz",
            "react component",
        ]:
            result = classify(topic)
            assert 0.0 <= result.confidence <= 1.0, (
                f"confidence {result.confidence} out of range for topic {topic!r}"
            )
