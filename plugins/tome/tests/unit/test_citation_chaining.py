"""
Feature: Citation chaining via Semantic Scholar

As the academic channel
I want to follow citation graphs (references and "cited by")
So that important papers reachable only through citations are discovered
"""

from __future__ import annotations

import pytest
from tome.channels.academic import (
    build_citation_citations_url,
    build_citation_references_url,
    parse_citation_chain_response,
)


class TestBuildCitationReferencesUrl:
    """
    Feature: URL builder for paper references

    As the literature-reviewer agent
    I want a URL that fetches what a paper cites
    So that foundational works are discovered
    """

    @pytest.mark.unit
    def test_builds_valid_url(self) -> None:
        """
        Scenario: Build references URL from paper ID
        Given a Semantic Scholar paper ID
        When build_citation_references_url is called
        Then a valid S2 API URL is returned
        """
        url = build_citation_references_url("abc123")
        assert "api.semanticscholar.org" in url
        assert "abc123" in url
        assert "references" in url

    @pytest.mark.unit
    def test_includes_required_fields(self) -> None:
        """
        Scenario: URL includes title and year fields
        Given a paper ID
        When build_citation_references_url is called
        Then the URL requests title and year fields
        """
        url = build_citation_references_url("abc123")
        assert "title" in url
        assert "year" in url

    @pytest.mark.unit
    def test_respects_limit(self) -> None:
        """
        Scenario: Limit parameter controls result count
        Given a paper ID and limit=5
        When build_citation_references_url is called
        Then the URL contains a limit parameter
        """
        url = build_citation_references_url("abc123", limit=5)
        assert "limit=5" in url


class TestBuildCitationCitationsUrl:
    """
    Feature: URL builder for papers that cite this one

    As the literature-reviewer agent
    I want a URL that fetches papers citing a given paper
    So that downstream impact and follow-up work are discovered
    """

    @pytest.mark.unit
    def test_builds_valid_url(self) -> None:
        """
        Scenario: Build citations URL from paper ID
        Given a Semantic Scholar paper ID
        When build_citation_citations_url is called
        Then a valid S2 API URL for citations is returned
        """
        url = build_citation_citations_url("abc123")
        assert "api.semanticscholar.org" in url
        assert "abc123" in url
        assert "citations" in url

    @pytest.mark.unit
    def test_includes_required_fields(self) -> None:
        """
        Scenario: URL includes citation count field
        Given a paper ID
        When build_citation_citations_url is called
        Then the URL requests citationCount
        """
        url = build_citation_citations_url("abc123")
        assert "citationCount" in url


class TestParseCitationChainResponse:
    """
    Feature: Parse citation chain API responses

    As the synthesis pipeline
    I want citation chain results parsed into Findings
    So that chained papers integrate with the standard pipeline
    """

    @pytest.mark.unit
    def test_parses_valid_response(self) -> None:
        """
        Scenario: Valid citation chain JSON
        Given a Semantic Scholar citation response with 2 papers
        When parse_citation_chain_response is called
        Then 2 Findings are returned
        """
        data = {
            "data": [
                {
                    "citedPaper": {
                        "paperId": "p1",
                        "title": "Paper One",
                        "year": 2024,
                        "citationCount": 50,
                    }
                },
                {
                    "citedPaper": {
                        "paperId": "p2",
                        "title": "Paper Two",
                        "year": 2023,
                        "citationCount": 10,
                    }
                },
            ]
        }
        findings = parse_citation_chain_response(data)
        assert len(findings) == 2
        assert all(f.channel == "academic" for f in findings)

    @pytest.mark.unit
    def test_empty_response_returns_empty(self) -> None:
        """
        Scenario: No citations found
        Given an empty data list
        When parse_citation_chain_response is called
        Then an empty list is returned
        """
        assert parse_citation_chain_response({"data": []}) == []

    @pytest.mark.unit
    def test_source_marked_as_citation_chain(self) -> None:
        """
        Scenario: Source attribution for chained papers
        Given a citation chain response
        When parse_citation_chain_response is called
        Then findings have source "semantic_scholar_chain"
        """
        data = {
            "data": [
                {
                    "citedPaper": {
                        "paperId": "p1",
                        "title": "Chained",
                        "year": 2025,
                        "citationCount": 5,
                    }
                }
            ]
        }
        findings = parse_citation_chain_response(data)
        assert findings[0].source == "semantic_scholar_chain"
