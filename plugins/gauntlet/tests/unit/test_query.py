"""Tests for the agent-facing query API."""

from __future__ import annotations

from pathlib import Path

import pytest
from gauntlet.query import (
    get_context_for_files,
    query_knowledge,
    validate_understanding,
)


class TestQueryKnowledge:
    """
    Feature: query_knowledge wraps KnowledgeStore.query()

    As an agent integrating with gauntlet,
    I want to retrieve knowledge entries by filter,
    So that I can surface relevant knowledge programmatically.
    """

    @pytest.mark.unit
    def test_query_all_returns_three_entries(self, sample_knowledge_base: Path) -> None:
        """
        Scenario: Query with no filters returns all entries
        Given a knowledge base with 3 entries
        When query_knowledge is called with no filters
        Then all 3 entries are returned
        """
        gauntlet_dir = sample_knowledge_base.parent
        entries = query_knowledge(gauntlet_dir)
        assert len(entries) == 3

    @pytest.mark.unit
    def test_query_by_file(self, sample_knowledge_base: Path) -> None:
        """
        Scenario: Query by file returns matching entries only
        Given a knowledge base with entries for billing, core, and auth
        When query_knowledge is called with files=["billing"]
        Then only the billing entry is returned
        """
        gauntlet_dir = sample_knowledge_base.parent
        entries = query_knowledge(gauntlet_dir, files=["billing"])
        assert len(entries) == 1
        assert entries[0].module == "billing"

    @pytest.mark.unit
    def test_query_by_category(self, sample_knowledge_base: Path) -> None:
        """
        Scenario: Query by category filters correctly
        Given a knowledge base with business_logic, architecture, data_flow entries
        When query_knowledge is called with categories=["architecture"]
        Then only the architecture entry is returned
        """
        gauntlet_dir = sample_knowledge_base.parent
        entries = query_knowledge(gauntlet_dir, categories=["architecture"])
        assert len(entries) == 1
        assert entries[0].category == "architecture"

    @pytest.mark.unit
    def test_query_empty_dir(self, tmp_gauntlet_dir: Path) -> None:
        """
        Scenario: Query against an empty gauntlet directory
        Given a gauntlet directory with no knowledge.json
        When query_knowledge is called
        Then an empty list is returned
        """
        entries = query_knowledge(tmp_gauntlet_dir)
        assert entries == []


class TestGetContextForFiles:
    """
    Feature: get_context_for_files returns a markdown summary

    As an agent,
    I want a formatted markdown block for relevant files,
    So that I can inject gauntlet context into my prompts.
    """

    @pytest.mark.unit
    def test_returns_markdown_with_heading(self, sample_knowledge_base: Path) -> None:
        """
        Scenario: Matching files produce a markdown summary
        Given a knowledge base with a billing entry
        When get_context_for_files is called with ["billing"]
        Then the result contains "##" level headings
        """
        gauntlet_dir = sample_knowledge_base.parent
        result = get_context_for_files(gauntlet_dir, ["billing"])
        assert "##" in result
        assert "Pro-rata calculation" in result

    @pytest.mark.unit
    def test_no_matching_files_returns_no_knowledge_message(
        self, sample_knowledge_base: Path
    ) -> None:
        """
        Scenario: No matching entries returns a helpful message
        Given a knowledge base with no entry for "nonexistent_module"
        When get_context_for_files is called with ["nonexistent_module"]
        Then the result contains "No knowledge entries"
        """
        gauntlet_dir = sample_knowledge_base.parent
        result = get_context_for_files(gauntlet_dir, ["nonexistent_module"])
        assert "No knowledge entries" in result

    @pytest.mark.unit
    def test_context_includes_module_category_difficulty(
        self, sample_knowledge_base: Path
    ) -> None:
        """
        Scenario: Context block includes all required fields
        Given a knowledge base with a billing entry at difficulty 2
        When get_context_for_files is called with ["billing"]
        Then the result includes Module, Category, and Difficulty fields
        """
        gauntlet_dir = sample_knowledge_base.parent
        result = get_context_for_files(gauntlet_dir, ["billing"])
        assert "**Module:**" in result
        assert "**Category:**" in result
        assert "**Difficulty:**" in result
        assert "2/5" in result


class TestValidateUnderstanding:
    """
    Feature: validate_understanding scores a claim against knowledge entries

    As an agent,
    I want to measure how well a developer's claim covers known concepts,
    So that I can identify knowledge gaps before a commit proceeds.
    """

    @pytest.mark.unit
    def test_accurate_claim_scores_at_least_half(
        self, sample_knowledge_base: Path
    ) -> None:
        """
        Scenario: A claim that closely paraphrases the entry detail scores >= 0.5
        Given a billing knowledge entry about pro-rata subscription charges
        When validate_understanding is called with a claim repeating key terms
        Then the score is >= 0.5
        """
        gauntlet_dir = sample_knowledge_base.parent
        # Reuse the exact detail text to guarantee high overlap
        claim = (
            "When a subscription upgrades mid-cycle, the charge is "
            "pro-rated based on remaining days in the billing period."
        )
        result = validate_understanding(gauntlet_dir, ["billing"], claim)
        assert result["score"] >= 0.5

    @pytest.mark.unit
    def test_wrong_claim_scores_below_threshold(
        self, sample_knowledge_base: Path
    ) -> None:
        """
        Scenario: A completely unrelated claim scores < 0.3
        Given a billing knowledge entry
        When validate_understanding is called with an unrelated claim
        Then the score is < 0.3
        """
        gauntlet_dir = sample_knowledge_base.parent
        claim = "The sky is blue and clouds are white."
        result = validate_understanding(gauntlet_dir, ["billing"], claim)
        assert result["score"] < 0.3

    @pytest.mark.unit
    def test_returns_gaps_list(self, sample_knowledge_base: Path) -> None:
        """
        Scenario: Concepts with low overlap appear in gaps
        Given a billing knowledge entry
        When validate_understanding is called with an unrelated claim
        Then the gaps list contains the billing concept name
        """
        gauntlet_dir = sample_knowledge_base.parent
        claim = "The sky is blue and clouds are white."
        result = validate_understanding(gauntlet_dir, ["billing"], claim)
        assert isinstance(result["gaps"], list)
        assert "Pro-rata calculation" in result["gaps"]

    @pytest.mark.unit
    def test_no_matching_files_returns_zero_score(
        self, sample_knowledge_base: Path
    ) -> None:
        """
        Scenario: No matching entries produces a zero score with no gaps
        Given a knowledge base with no entry for "nonexistent"
        When validate_understanding is called
        Then score is 0.0 and gaps is empty
        """
        gauntlet_dir = sample_knowledge_base.parent
        result = validate_understanding(gauntlet_dir, ["nonexistent"], "any claim")
        assert result["score"] == 0.0
        assert result["gaps"] == []
