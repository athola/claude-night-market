"""
Feature: Citation and bibliography formatting

As a researcher producing a report
I want findings formatted as proper citations
So that readers can locate original sources and understand their provenance
"""

from __future__ import annotations

import pytest
from tome.models import Finding
from tome.output.citations import format_citation, generate_bibliography


def _academic_finding() -> Finding:
    return Finding(
        source="arxiv",
        channel="academic",
        title="A Survey of Asynchronous Programming Models",
        url="https://arxiv.org/abs/2301.12345",
        relevance=0.90,
        summary="Survey paper.",
        metadata={
            "authors": ["Smith, J.", "Doe, A."],
            "year": 2023,
            "citations": 45,
            "venue": "arXiv",
            "doi": "10.48550/arXiv.2301.12345",
        },
    )


def _github_finding() -> Finding:
    return Finding(
        source="github",
        channel="code",
        title="example/async-lib",
        url="https://github.com/example/async-lib",
        relevance=0.85,
        summary="Async patterns library.",
        metadata={"stars": 2100, "owner": "example"},
    )


def _hn_finding() -> Finding:
    return Finding(
        source="hn",
        channel="discourse",
        title="Why async/await is better than callbacks",
        url="https://news.ycombinator.com/item?id=12345",
        relevance=0.72,
        summary="HN discussion.",
        metadata={"score": 200, "username": "thrower42"},
    )


def _reddit_finding() -> Finding:
    return Finding(
        source="reddit",
        channel="discourse",
        title="Async patterns in Python - megathread",
        url="https://reddit.com/r/python/comments/abc123",
        relevance=0.65,
        summary="Reddit megathread.",
        metadata={"score": 150, "username": "py_fan"},
    )


class TestFormatCitation:
    """
    Feature: Single-finding citation formatting

    As a report generator
    I want each finding converted to a human-readable citation string
    So that the bibliography section is consistent and informative
    """

    @pytest.mark.unit
    def test_academic_citation_includes_authors(self) -> None:
        """
        Scenario: Academic finding has author metadata
        Given an arXiv finding with authors ['Smith, J.', 'Doe, A.']
        When format_citation is called
        Then the citation string contains at least one author name
        """
        citation = format_citation(_academic_finding())
        assert "Smith" in citation or "Doe" in citation

    @pytest.mark.unit
    def test_academic_citation_includes_year(self) -> None:
        """
        Scenario: Academic finding has year metadata
        Given an arXiv finding with year 2023
        When format_citation is called
        Then '2023' appears in the citation string
        """
        citation = format_citation(_academic_finding())
        assert "2023" in citation

    @pytest.mark.unit
    def test_academic_citation_includes_url(self) -> None:
        """
        Scenario: Academic finding URL is referenced
        Given an arXiv finding
        When format_citation is called
        Then the arXiv URL appears in the citation
        """
        citation = format_citation(_academic_finding())
        assert "https://arxiv.org/abs/2301.12345" in citation

    @pytest.mark.unit
    def test_academic_citation_includes_title(self) -> None:
        """
        Scenario: Academic citation includes the paper title
        Given an arXiv finding with a known title
        When format_citation is called
        Then the title appears in the citation string
        """
        citation = format_citation(_academic_finding())
        assert "Survey" in citation or "Asynchronous" in citation

    @pytest.mark.unit
    def test_github_citation_includes_stars(self) -> None:
        """
        Scenario: GitHub finding includes star count
        Given a GitHub repo finding with 2100 stars
        When format_citation is called
        Then '2100' appears in the citation string
        """
        citation = format_citation(_github_finding())
        assert "2100" in citation

    @pytest.mark.unit
    def test_github_citation_includes_url(self) -> None:
        """
        Scenario: GitHub citation includes repository URL
        Given a GitHub finding
        When format_citation is called
        Then the GitHub URL appears in the citation
        """
        citation = format_citation(_github_finding())
        assert "https://github.com/example/async-lib" in citation

    @pytest.mark.unit
    def test_github_citation_includes_title(self) -> None:
        """
        Scenario: GitHub citation includes repository name
        Given a GitHub finding with title 'example/async-lib'
        When format_citation is called
        Then 'async-lib' or 'example' appears in the citation
        """
        citation = format_citation(_github_finding())
        assert "async-lib" in citation or "example" in citation

    @pytest.mark.unit
    def test_discourse_citation_includes_score(self) -> None:
        """
        Scenario: Discourse (HN) finding includes score
        Given an HN finding with score 200
        When format_citation is called
        Then '200' appears in the citation string
        """
        citation = format_citation(_hn_finding())
        assert "200" in citation

    @pytest.mark.unit
    def test_discourse_citation_includes_url(self) -> None:
        """
        Scenario: Discourse citation includes post URL
        Given an HN finding
        When format_citation is called
        Then the HN URL appears in the citation
        """
        citation = format_citation(_hn_finding())
        assert "https://news.ycombinator.com/item?id=12345" in citation

    @pytest.mark.unit
    def test_discourse_citation_includes_platform(self) -> None:
        """
        Scenario: Discourse citation identifies the platform
        Given an HN finding
        When format_citation is called
        Then 'HN', 'Hacker News', or 'hn' appears in the citation
        """
        citation = format_citation(_hn_finding())
        assert any(term in citation for term in ("HN", "Hacker News", "hn", "hacker"))

    @pytest.mark.unit
    def test_citation_returns_string(self) -> None:
        """
        Scenario: Citation output type
        Given any finding
        When format_citation is called
        Then a non-empty string is returned
        """
        for finding in [_academic_finding(), _github_finding(), _hn_finding()]:
            result = format_citation(finding)
            assert isinstance(result, str)
            assert len(result.strip()) > 0


class TestGenerateBibliography:
    """
    Feature: Numbered bibliography from all findings

    As a report formatter
    I want a numbered list of all citations
    So that readers can locate sources by number from inline references
    """

    @pytest.mark.unit
    def test_bibliography_numbers_entries(self) -> None:
        """
        Scenario: Bibliography entries are numbered
        Given two findings
        When generate_bibliography is called
        Then the output contains '1' and '2' as entry markers
        """
        findings = [_academic_finding(), _github_finding()]
        bib = generate_bibliography(findings)
        assert "1" in bib
        assert "2" in bib

    @pytest.mark.unit
    def test_bibliography_contains_all_urls(self) -> None:
        """
        Scenario: Every finding URL appears in the bibliography
        Given academic, GitHub, and HN findings
        When generate_bibliography is called
        Then all three URLs appear
        """
        findings = [_academic_finding(), _github_finding(), _hn_finding()]
        bib = generate_bibliography(findings)
        assert "https://arxiv.org/abs/2301.12345" in bib
        assert "https://github.com/example/async-lib" in bib
        assert "https://news.ycombinator.com/item?id=12345" in bib

    @pytest.mark.unit
    def test_bibliography_empty_input_returns_string(self) -> None:
        """
        Scenario: Empty findings list
        Given no findings
        When generate_bibliography is called
        Then an empty string or placeholder is returned without raising
        """
        result = generate_bibliography([])
        assert isinstance(result, str)

    @pytest.mark.unit
    def test_bibliography_single_entry(self) -> None:
        """
        Scenario: One finding produces one numbered entry
        Given a single academic finding
        When generate_bibliography is called
        Then the output contains entry number 1 and the finding's URL
        """
        bib = generate_bibliography([_academic_finding()])
        assert "1" in bib
        assert "https://arxiv.org/abs/2301.12345" in bib

    @pytest.mark.unit
    def test_bibliography_entries_are_in_order(self) -> None:
        """
        Scenario: Entry order matches input order
        Given academic finding first, then GitHub
        When generate_bibliography is called
        Then the academic URL appears before the GitHub URL in the output
        """
        findings = [_academic_finding(), _github_finding()]
        bib = generate_bibliography(findings)
        arxiv_pos = bib.index("arxiv.org")
        github_pos = bib.index("github.com")
        assert arxiv_pos < github_pos
