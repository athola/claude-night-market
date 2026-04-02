"""Tests for ML feature extraction."""

from __future__ import annotations

import pytest
from gauntlet.ml.features import extract_answer_features
from gauntlet.models import Challenge


def _challenge(
    challenge_type: str,
    answer: str,
) -> Challenge:
    return Challenge(
        id="ch-test-001",
        type=challenge_type,
        knowledge_entry_id="ke-test-001",
        difficulty=2,
        prompt="Test prompt",
        context="Test context about tokens and authentication",
        answer=answer,
    )


class TestFeatureExtraction:
    """
    Feature: Extract scoring features from challenge-answer pairs

    As the gauntlet ML module
    I want to extract numeric features from answers
    So that a classifier can score answer quality
    """

    @pytest.mark.unit
    def test_returns_all_seven_features(self):
        """
        Scenario: Feature extraction produces complete feature dict
        Given a challenge and an answer
        When extract_answer_features is called
        Then the result contains all 7 expected feature keys
        """
        ch = _challenge("explain_why", "Tokens expire after 15 minutes.")
        answer = "Tokens expire quickly for security reasons."
        features = extract_answer_features(ch, answer)
        expected_keys = {
            "word_overlap_ratio",
            "length_ratio",
            "keyword_coverage",
            "structural_depth",
            "unique_word_ratio",
            "negation_density",
            "numeric_match",
        }
        assert set(features.keys()) == expected_keys

    @pytest.mark.unit
    def test_all_features_are_floats(self):
        """
        Scenario: All feature values are numeric
        Given a challenge and an answer
        When extract_answer_features is called
        Then every value in the result is a float
        """
        ch = _challenge("explain_why", "Event sourcing stores all state changes.")
        features = extract_answer_features(ch, "Events capture state mutations.")
        for key, val in features.items():
            assert isinstance(val, float), f"{key} is {type(val)}, expected float"

    @pytest.mark.unit
    def test_word_overlap_ratio_exact_match(self):
        text = "Access tokens expire after 15 minutes."
        ch = _challenge("explain_why", text)
        features = extract_answer_features(ch, text)
        assert features["word_overlap_ratio"] == pytest.approx(1.0)

    @pytest.mark.unit
    def test_word_overlap_ratio_no_match(self):
        """
        Scenario: Completely unrelated answer gives 0.0 overlap
        Given a challenge about token expiry
        When the answer is about databases
        Then word_overlap_ratio is 0.0
        """
        ch = _challenge("explain_why", "Access tokens expire after 15 minutes.")
        features = extract_answer_features(ch, "PostgreSQL indexes speed up queries.")
        assert features["word_overlap_ratio"] == pytest.approx(0.0)

    @pytest.mark.unit
    def test_length_ratio_shorter_answer(self):
        """
        Scenario: Short answer produces length ratio less than 1.0
        Given a long reference answer
        When the candidate is much shorter
        Then length_ratio is less than 1.0
        """
        ch = _challenge(
            "explain_why",
            "Access tokens expire after 15 minutes to limit exposure window.",
        )
        features = extract_answer_features(ch, "Tokens expire.")
        assert 0.0 < features["length_ratio"] < 1.0

    @pytest.mark.unit
    def test_structural_depth_with_code_block(self):
        ch = _challenge("code_completion", "def foo(): return 42")
        answer = "```python\ndef foo():\n    return 42\n```"
        features = extract_answer_features(ch, answer)
        assert features["structural_depth"] >= 1.0

    @pytest.mark.unit
    def test_negation_density_with_negatives(self):
        ch = _challenge("explain_why", "The cache is invalidated on write.")
        answer = "The cache is not invalidated and never expires, no TTL set."
        features = extract_answer_features(ch, answer)
        assert features["negation_density"] > 0.0

    @pytest.mark.unit
    def test_numeric_match_with_matching_numbers(self):
        ch = _challenge("explain_why", "Tokens expire in 15 or 30 minutes.")
        features = extract_answer_features(ch, "The expiry is 15 minutes.")
        assert 0.0 < features["numeric_match"] <= 1.0

    @pytest.mark.unit
    def test_empty_answer_returns_zero_features(self):
        ch = _challenge("explain_why", "Tokens expire after 15 minutes.")
        features = extract_answer_features(ch, "")
        for key, val in features.items():
            assert val == pytest.approx(0.0), f"{key} should be 0.0 for empty answer"

    # ------------------------------------------------------------------
    # Boundary: empty reference / context (lines 69, 75, 81)
    # ------------------------------------------------------------------

    @pytest.mark.unit
    def test_word_overlap_ratio_is_zero_when_reference_is_empty(self):
        """
        Scenario: Reference answer has no words
        Given a challenge whose answer is an empty string
        When extract_answer_features is called with a non-empty answer
        Then word_overlap_ratio is 0.0 (denominator guard)
        """
        ch = Challenge(
            id="ch-test-boundary",
            type="explain_why",
            knowledge_entry_id="ke-test-001",
            difficulty=1,
            prompt="What is X?",
            context="Some context here",
            answer="",
        )
        features = extract_answer_features(ch, "Some answer about X")
        assert features["word_overlap_ratio"] == pytest.approx(0.0)

    @pytest.mark.unit
    def test_length_ratio_is_zero_when_reference_is_empty(self):
        """
        Scenario: Reference answer has zero length
        Given a challenge whose answer is an empty string
        When extract_answer_features is called with a non-empty answer
        Then length_ratio is 0.0 (division by zero guard)
        """
        ch = Challenge(
            id="ch-test-boundary",
            type="explain_why",
            knowledge_entry_id="ke-test-001",
            difficulty=1,
            prompt="What is X?",
            context="Some context here",
            answer="",
        )
        features = extract_answer_features(ch, "Some answer")
        assert features["length_ratio"] == pytest.approx(0.0)

    @pytest.mark.unit
    def test_keyword_coverage_is_zero_when_context_is_empty(self):
        """
        Scenario: Challenge context is empty
        Given a challenge with no context words
        When extract_answer_features is called
        Then keyword_coverage is 0.0 (denominator guard)
        """
        ch = Challenge(
            id="ch-test-boundary",
            type="explain_why",
            knowledge_entry_id="ke-test-001",
            difficulty=1,
            prompt="What is X?",
            context="",
            answer="Tokens expire after 15 minutes.",
        )
        features = extract_answer_features(ch, "Tokens expire in 15 minutes.")
        assert features["keyword_coverage"] == pytest.approx(0.0)

    @pytest.mark.unit
    def test_unique_word_ratio_and_negation_density_zero_for_punctuation_only_answer(
        self,
    ):
        """
        Scenario: Answer contains only punctuation (no word tokens)
        Given an answer of "... --- !!!"
        When extract_answer_features is called
        Then unique_word_ratio and negation_density are 0.0 (empty token list guard)
        """
        ch = _challenge("explain_why", "Tokens expire after 15 minutes.")
        features = extract_answer_features(ch, "... --- !!!")
        assert features["unique_word_ratio"] == pytest.approx(0.0)
        assert features["negation_density"] == pytest.approx(0.0)

    @pytest.mark.unit
    def test_no_word_overlap_produces_zero_ratio(self):
        """
        Scenario: Answer shares no words with the reference
        Given a reference answer about token expiry
        And an answer about an unrelated topic
        When extract_answer_features is called
        Then word_overlap_ratio is exactly 0.0
        """
        ch = _challenge("explain_why", "Access tokens expire after fifteen minutes.")
        features = extract_answer_features(
            ch, "PostgreSQL uses B-tree indexes for fast lookups."
        )
        assert features["word_overlap_ratio"] == pytest.approx(0.0)
