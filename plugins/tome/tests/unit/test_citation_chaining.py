"""
Feature: Citation chaining via Semantic Scholar

As the academic channel
I want to follow citation graphs (references and "cited by")
So that important papers reachable only through citations are discovered
"""

from __future__ import annotations

import pytest

from tome.channels.academic import (
    parse_citation_chain_response,
)


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
