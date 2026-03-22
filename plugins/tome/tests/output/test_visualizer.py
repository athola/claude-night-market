"""Tests for domain-specific visualization."""

from __future__ import annotations

import pytest
from tome.models import Finding
from tome.output.visualizer import generate_visualization


class TestMermaidDiagram:
    """
    Feature: Mermaid diagram generation

    As a researcher studying architecture topics
    I want diagrams generated inline
    So that I can visualize system relationships
    """

    @pytest.mark.unit
    def test_generates_mermaid_for_architecture_findings(self) -> None:
        """
        Scenario: Architecture domain findings
        Given findings about system components
        When generating visualization
        Then a mermaid code block is returned
        """

        findings = [
            Finding(
                source="github",
                channel="code",
                title="Event-driven architecture",
                url="https://example.com",
                relevance=0.8,
                summary="Event bus connects services",
                metadata={"patterns": ["event-driven"]},
            ),
        ]
        result = generate_visualization(findings, "architecture")
        assert "```mermaid" in result
        assert "```" in result

    @pytest.mark.unit
    def test_generates_table_for_algorithm_findings(self) -> None:
        """
        Scenario: Algorithm domain findings
        Given findings about algorithm comparisons
        When generating visualization
        Then a markdown comparison table is returned
        """

        findings = [
            Finding(
                source="github",
                channel="code",
                title="Quick Sort",
                url="https://example.com",
                relevance=0.9,
                summary="O(n log n) average",
                metadata={"stars": 500},
            ),
            Finding(
                source="github",
                channel="code",
                title="Merge Sort",
                url="https://example.com/2",
                relevance=0.85,
                summary="O(n log n) guaranteed",
                metadata={"stars": 300},
            ),
        ]
        result = generate_visualization(findings, "algorithm")
        assert "| " in result
        assert "Quick Sort" in result

    @pytest.mark.unit
    def test_returns_empty_for_no_findings(self) -> None:
        """
        Scenario: No findings to visualize
        Given an empty findings list
        When generating visualization
        Then an empty string is returned
        """

        result = generate_visualization([], "general")
        assert result == ""

    @pytest.mark.unit
    def test_general_domain_produces_ranked_list(self) -> None:
        """
        Scenario: General domain uses ranked list
        Given findings in the general domain
        When generating visualization
        Then a numbered list is returned
        """

        findings = [
            Finding(
                source="hn",
                channel="discourse",
                title="Discussion A",
                url="https://example.com",
                relevance=0.7,
                summary="Some discussion",
                metadata={},
            ),
        ]
        result = generate_visualization(findings, "general")
        assert "1." in result


class TestVisualizationDomainRouting:
    """
    Feature: Domain-appropriate visualization selection

    As a researcher
    I want visualizations matched to my domain
    So that the presentation format fits the content
    """

    @pytest.mark.unit
    def test_financial_domain_mentions_chart(self) -> None:
        """
        Scenario: Financial domain
        Given financial findings
        When generating visualization
        Then output references chart/data visualization
        """

        findings = [
            Finding(
                source="github",
                channel="code",
                title="Portfolio optimizer",
                url="https://example.com",
                relevance=0.8,
                summary="Risk-return optimization",
                metadata={"stars": 100},
            ),
        ]
        result = generate_visualization(findings, "financial")
        # Financial should produce a table with metrics
        assert "| " in result

    @pytest.mark.unit
    def test_scientific_domain_produces_table(self) -> None:
        """
        Scenario: Scientific domain
        Given scientific findings
        When generating visualization
        Then a comparison table is returned
        """

        findings = [
            Finding(
                source="arxiv",
                channel="academic",
                title="Neural network paper",
                url="https://arxiv.org/abs/123",
                relevance=0.9,
                summary="Novel architecture",
                metadata={"citations": 50, "year": 2024},
            ),
        ]
        result = generate_visualization(findings, "scientific")
        assert "| " in result
