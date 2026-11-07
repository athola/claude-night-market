"""
Feature: Fuzzy semantic deduplication

As a synthesis pipeline
I want to detect duplicate findings even when URLs differ
So that the same paper from arXiv and Semantic Scholar is not listed twice
"""

from __future__ import annotations

import pytest

from tome.synthesis.merger import normalize_title


class TestNormalizeTitle:
    """
    Feature: Title normalization for comparison

    As the deduplication engine
    I want titles reduced to a canonical form
    So that minor differences do not prevent matching
    """

    @pytest.mark.unit
    def test_lowercases(self) -> None:
        """
        Scenario: Mixed case title
        Given "Attention Is All You Need"
        When normalize_title is called
        Then the result is all lowercase
        """
        assert normalize_title("Attention Is All You Need") == normalize_title(
            "attention is all you need"
        )

    @pytest.mark.unit
    def test_strips_punctuation(self) -> None:
        """
        Scenario: Title with colons and hyphens
        Given "BERT: Pre-training of Deep Bidirectional Transformers"
        When normalize_title is called
        Then punctuation is removed
        """
        normalized = normalize_title(
            "BERT: Pre-training of Deep Bidirectional Transformers"
        )
        assert ":" not in normalized
        assert "-" not in normalized

    @pytest.mark.unit
    def test_sorts_words(self) -> None:
        """
        Scenario: Word-order independence
        Given two titles with the same words in different order
        When normalize_title is called on both
        Then the results are identical
        """
        a = normalize_title("deep learning review")
        b = normalize_title("review deep learning")
        assert a == b

    @pytest.mark.unit
    def test_empty_string(self) -> None:
        """
        Scenario: Empty title
        Given an empty string
        When normalize_title is called
        Then an empty string is returned
        """
        assert normalize_title("") == ""
