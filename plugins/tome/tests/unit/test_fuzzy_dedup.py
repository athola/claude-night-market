"""
Feature: Fuzzy semantic deduplication

As a synthesis pipeline
I want to detect duplicate findings even when URLs differ
So that the same paper from arXiv and Semantic Scholar is not listed twice
"""

from __future__ import annotations

import pytest
from tome.synthesis.merger import fuzzy_deduplicate, normalize_title

from tests.factories import make_finding


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


class TestFuzzyDeduplicate:
    """
    Feature: Cross-source deduplication by title similarity

    As a synthesis pipeline
    I want findings from different sources about the same content merged
    So that the report does not present redundant entries
    """

    @pytest.mark.unit
    def test_same_paper_different_urls_deduplicated(self) -> None:
        """
        Scenario: Same paper found via arXiv and Semantic Scholar
        Given two findings with the same title but different URLs
        When fuzzy_deduplicate is called
        Then only one finding is kept
        """
        arxiv = make_finding(
            0.7,
            source="arxiv",
            channel="academic",
            title="Attention Is All You Need",
            url="https://arxiv.org/abs/1706.03762",
        )
        ss = make_finding(
            0.8,
            source="semantic_scholar",
            channel="academic",
            title="Attention Is All You Need",
            url="https://www.semanticscholar.org/paper/123",
        )

        result = fuzzy_deduplicate([arxiv, ss])

        assert len(result) == 1
        # Higher relevance wins
        assert result[0].relevance == 0.8

    @pytest.mark.unit
    def test_distinct_titles_preserved(self) -> None:
        """
        Scenario: Genuinely different papers
        Given two findings with different titles
        When fuzzy_deduplicate is called
        Then both are kept
        """
        a = make_finding(
            0.7,
            channel="academic",
            source="arxiv",
            title="Attention Is All You Need",
            url="https://arxiv.org/abs/1",
        )
        b = make_finding(
            0.6,
            channel="academic",
            source="arxiv",
            title="BERT Pre-training Deep Bidirectional Transformers",
            url="https://arxiv.org/abs/2",
        )

        result = fuzzy_deduplicate([a, b])

        assert len(result) == 2

    @pytest.mark.unit
    def test_cross_channel_fuzzy_match(self) -> None:
        """
        Scenario: Same repo found in code and discourse channels
        Given a GitHub finding and an HN discussion about the same repo
        When fuzzy_deduplicate is called with cross_channel=True
        Then only one finding is kept
        """
        code = make_finding(
            0.7,
            source="github",
            channel="code",
            title="facebook/react",
            url="https://github.com/facebook/react",
        )
        discourse = make_finding(
            0.6,
            source="hn",
            channel="discourse",
            title="facebook/react",
            url="https://news.ycombinator.com/item?id=123",
        )

        result = fuzzy_deduplicate([code, discourse], cross_channel=True)

        assert len(result) == 1

    @pytest.mark.unit
    def test_empty_input(self) -> None:
        """
        Scenario: No findings
        Given an empty list
        When fuzzy_deduplicate is called
        Then an empty list is returned
        """
        assert fuzzy_deduplicate([]) == []

    @pytest.mark.unit
    def test_similar_but_different_titles_kept(self) -> None:
        """
        Scenario: Similar but distinct titles below threshold
        Given "Deep Learning" and "Deep Reinforcement Learning"
        When fuzzy_deduplicate is called
        Then both are kept (Jaccard similarity below threshold)
        """
        a = make_finding(
            0.7,
            channel="academic",
            source="arxiv",
            title="Deep Learning",
            url="https://arxiv.org/abs/1",
        )
        b = make_finding(
            0.6,
            channel="academic",
            source="arxiv",
            title="Deep Reinforcement Learning",
            url="https://arxiv.org/abs/2",
        )

        result = fuzzy_deduplicate([a, b])

        assert len(result) == 2
