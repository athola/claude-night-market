"""
Feature: Academic literature channel

As a research pipeline
I want to build academic search URLs and parse responses into Findings
So that agents can retrieve papers from arXiv, Semantic Scholar,
and open-access sources without coupling to HTTP.
"""

from __future__ import annotations

from typing import Any

import pytest
from tome.channels.academic import (
    build_arxiv_search_url,
    build_core_search_url,
    build_openalex_search_url,
    build_paper_summary_prompt,
    build_semantic_scholar_url,
    build_unpaywall_url,
    estimate_page_chunks,
    generate_access_fallback_guidance,
    parse_arxiv_response,
    parse_semantic_scholar_response,
    parse_unpaywall_response,
)

# ---------------------------------------------------------------------------
# Sample fixtures
# ---------------------------------------------------------------------------

ARXIV_SAMPLE_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <id>http://arxiv.org/abs/2301.12345v1</id>
    <title>A Survey of Async Programming</title>
    <summary>This paper surveys asynchronous programming models across languages.</summary>
    <author><name>John Smith</name></author>
    <author><name>Jane Doe</name></author>
    <published>2023-01-15T00:00:00Z</published>
    <category term="cs.PL"/>
    <category term="cs.SE"/>
    <link href="http://arxiv.org/pdf/2301.12345v1" title="pdf" type="application/pdf"/>
  </entry>
</feed>
"""

ARXIV_EMPTY_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
</feed>
"""

SEMANTIC_SCHOLAR_SAMPLE: dict[str, Any] = {
    "data": [
        {
            "paperId": "abc123",
            "title": "Attention Is All You Need",
            "abstract": "We propose a new architecture called the Transformer.",
            "year": 2017,
            "citationCount": 80000,
            "influentialCitationCount": 5000,
            "isOpenAccess": True,
            "openAccessPdf": {"url": "https://arxiv.org/pdf/1706.03762"},
            "authors": [{"name": "Ashish Vaswani"}, {"name": "Noam Shazeer"}],
            "venue": "NeurIPS",
            "externalIds": {"DOI": "10.48550/arXiv.1706.03762", "ArXiv": "1706.03762"},
        }
    ]
}

UNPAYWALL_SAMPLE: dict[str, Any] = {
    "doi": "10.1234/test",
    "is_oa": True,
    "best_oa_location": {
        "url_for_pdf": "https://example.org/paper.pdf",
        "url": "https://example.org/paper",
    },
}

UNPAYWALL_NO_OA: dict[str, Any] = {
    "doi": "10.1234/closed",
    "is_oa": False,
    "best_oa_location": None,
}


# ---------------------------------------------------------------------------
# TestArxivSearch
# ---------------------------------------------------------------------------


class TestArxivSearch:
    """
    Feature: arXiv search URL builder and XML parser

    As a research agent
    I want URL strings and parsed Findings from arXiv API responses
    So that I can retrieve academic papers without writing HTTP code
    """

    @pytest.mark.unit
    def test_build_arxiv_search_url_includes_encoded_topic(self) -> None:
        """
        Scenario: Topic is URL-encoded in the search URL
        Given topic "async programming"
        When build_arxiv_search_url is called
        Then the URL contains the encoded form of the topic
        """
        url = build_arxiv_search_url("async programming")

        assert "async+programming" in url or "async%20programming" in url

    @pytest.mark.unit
    def test_build_arxiv_search_url_includes_max_results(self) -> None:
        """
        Scenario: max_results is embedded in the search URL
        Given max_results=5
        When build_arxiv_search_url is called
        Then the URL contains max_results=5
        """
        url = build_arxiv_search_url("transformers", max_results=5)

        assert "max_results=5" in url

    @pytest.mark.unit
    def test_build_arxiv_search_url_points_to_export_api(self) -> None:
        """
        Scenario: URL uses the correct arXiv export API base
        """
        url = build_arxiv_search_url("topic")

        assert url.startswith("https://export.arxiv.org/api/query")

    @pytest.mark.unit
    def test_parse_arxiv_response_extracts_title(self) -> None:
        """
        Scenario: Title is extracted from XML entry
        Given valid arXiv Atom XML
        When parse_arxiv_response is called
        Then the Finding title matches the <title> element
        """
        findings = parse_arxiv_response(ARXIV_SAMPLE_XML)

        assert len(findings) == 1
        assert findings[0].title == "A Survey of Async Programming"

    @pytest.mark.unit
    def test_parse_arxiv_response_extracts_authors(self) -> None:
        """
        Scenario: Authors are extracted from multiple <author> elements
        Given XML with two authors
        When parse_arxiv_response is called
        Then metadata["authors"] contains both names
        """
        findings = parse_arxiv_response(ARXIV_SAMPLE_XML)

        authors = findings[0].metadata["authors"]
        assert "John Smith" in authors
        assert "Jane Doe" in authors

    @pytest.mark.unit
    def test_parse_arxiv_response_extracts_abstract(self) -> None:
        """
        Scenario: Abstract becomes the Finding summary
        Given XML with a <summary> element
        When parse_arxiv_response is called
        Then the Finding summary contains the abstract text
        """
        findings = parse_arxiv_response(ARXIV_SAMPLE_XML)

        assert "asynchronous programming" in findings[0].summary

    @pytest.mark.unit
    def test_parse_arxiv_response_handles_empty_response(self) -> None:
        """
        Scenario: Empty feed yields no findings
        Given Atom XML with no <entry> elements
        When parse_arxiv_response is called
        Then an empty list is returned
        """
        findings = parse_arxiv_response(ARXIV_EMPTY_XML)

        assert findings == []

    @pytest.mark.unit
    def test_parse_arxiv_response_sets_source_and_channel(self) -> None:
        """
        Scenario: Finding has correct source and channel identifiers
        Given valid arXiv XML
        When parse_arxiv_response is called
        Then source="arxiv" and channel="academic"
        """
        findings = parse_arxiv_response(ARXIV_SAMPLE_XML)

        assert findings[0].source == "arxiv"
        assert findings[0].channel == "academic"

    @pytest.mark.unit
    def test_parse_arxiv_response_extracts_pdf_url(self) -> None:
        """
        Scenario: PDF link is captured from <link title="pdf"> element
        Given XML with a pdf link element
        When parse_arxiv_response is called
        Then metadata["pdf_url"] points to the PDF
        """
        findings = parse_arxiv_response(ARXIV_SAMPLE_XML)

        assert findings[0].metadata["pdf_url"] == "http://arxiv.org/pdf/2301.12345v1"

    @pytest.mark.unit
    def test_parse_arxiv_response_extracts_arxiv_id(self) -> None:
        """
        Scenario: arXiv ID is extracted from the <id> URL
        Given XML with id http://arxiv.org/abs/2301.12345v1
        When parse_arxiv_response is called
        Then metadata["arxiv_id"] == "2301.12345"
        """
        findings = parse_arxiv_response(ARXIV_SAMPLE_XML)

        assert findings[0].metadata["arxiv_id"] == "2301.12345"

    @pytest.mark.unit
    def test_parse_arxiv_response_extracts_categories(self) -> None:
        """
        Scenario: Categories are collected from <category> elements
        Given XML with cs.PL and cs.SE categories
        When parse_arxiv_response is called
        Then metadata["categories"] contains both
        """
        findings = parse_arxiv_response(ARXIV_SAMPLE_XML)

        categories = findings[0].metadata["categories"]
        assert "cs.PL" in categories
        assert "cs.SE" in categories

    @pytest.mark.unit
    def test_parse_arxiv_response_sets_base_relevance(self) -> None:
        """
        Scenario: Relevance is set to the arXiv base value 0.7
        """
        findings = parse_arxiv_response(ARXIV_SAMPLE_XML)

        assert findings[0].relevance == 0.7

    @pytest.mark.unit
    def test_parse_arxiv_response_extracts_year(self) -> None:
        """
        Scenario: Year is parsed from the <published> element
        Given published date 2023-01-15T00:00:00Z
        When parse_arxiv_response is called
        Then metadata["year"] == 2023
        """
        findings = parse_arxiv_response(ARXIV_SAMPLE_XML)

        assert findings[0].metadata["year"] == 2023


# ---------------------------------------------------------------------------
# TestSemanticScholar
# ---------------------------------------------------------------------------


class TestSemanticScholar:
    """
    Feature: Semantic Scholar API URL builder and JSON parser

    As a research agent
    I want Findings from Semantic Scholar search results
    So that I can retrieve citation-ranked academic papers
    """

    @pytest.mark.unit
    def test_build_semantic_scholar_url_includes_topic(self) -> None:
        """
        Scenario: Topic is embedded in the search URL
        Given topic "attention mechanism"
        When build_semantic_scholar_url is called
        Then the URL contains the encoded topic
        """
        url = build_semantic_scholar_url("attention mechanism")

        assert "attention" in url
        assert "mechanism" in url

    @pytest.mark.unit
    def test_build_semantic_scholar_url_includes_fields(self) -> None:
        """
        Scenario: The URL requests the expected API fields
        Given any topic
        When build_semantic_scholar_url is called
        Then the URL contains "fields=" with key field names
        """
        url = build_semantic_scholar_url("neural networks")

        assert "fields=" in url
        assert "citationCount" in url
        assert "abstract" in url

    @pytest.mark.unit
    def test_build_semantic_scholar_url_includes_limit(self) -> None:
        """
        Scenario: limit parameter appears in the URL
        Given limit=7
        When build_semantic_scholar_url is called
        Then the URL contains limit=7
        """
        url = build_semantic_scholar_url("graphs", limit=7)

        assert "limit=7" in url

    @pytest.mark.unit
    def test_parse_semantic_scholar_response_extracts_papers(self) -> None:
        """
        Scenario: Papers are extracted from the data array
        Given a response with one paper
        When parse_semantic_scholar_response is called
        Then one Finding is returned with the correct title
        """
        findings = parse_semantic_scholar_response(SEMANTIC_SCHOLAR_SAMPLE)

        assert len(findings) == 1
        assert findings[0].title == "Attention Is All You Need"

    @pytest.mark.unit
    def test_parse_semantic_scholar_response_computes_high_citation_relevance(
        self,
    ) -> None:
        """
        Scenario: Papers with 500+ citations get relevance 0.9
        Given a paper with citationCount=80000
        When parse_semantic_scholar_response is called
        Then Finding.relevance == 0.9
        """
        findings = parse_semantic_scholar_response(SEMANTIC_SCHOLAR_SAMPLE)

        assert findings[0].relevance == 0.9

    @pytest.mark.unit
    def test_parse_semantic_scholar_response_computes_relevance_from_citations(
        self,
    ) -> None:
        """
        Scenario: Citation tiers map to correct relevance values
        Given papers with 0, 10, 50, 100, 500 citations
        When parse_semantic_scholar_response is called
        Then each paper gets the expected relevance
        """
        cases = [
            (0, 0.5),
            (10, 0.6),
            (50, 0.7),
            (100, 0.8),
            (500, 0.9),
        ]
        for citations, expected in cases:
            data: dict[str, Any] = {
                "data": [
                    {
                        "paperId": "x",
                        "title": "Test",
                        "abstract": "Abstract.",
                        "year": 2020,
                        "citationCount": citations,
                        "influentialCitationCount": 0,
                        "isOpenAccess": False,
                        "openAccessPdf": None,
                        "authors": [],
                        "venue": "ICML",
                        "externalIds": {},
                    }
                ]
            }
            findings = parse_semantic_scholar_response(data)
            assert findings[0].relevance == expected, (
                f"citations={citations} expected relevance={expected}, got {findings[0].relevance}"
            )

    @pytest.mark.unit
    def test_parse_semantic_scholar_response_handles_none_abstract(self) -> None:
        """
        Scenario: None abstract does not raise an error
        Given a paper with abstract=None
        When parse_semantic_scholar_response is called
        Then the Finding summary is an empty string or placeholder
        """
        data: dict[str, Any] = {
            "data": [
                {
                    "paperId": "y",
                    "title": "No Abstract Paper",
                    "abstract": None,
                    "year": 2021,
                    "citationCount": 0,
                    "influentialCitationCount": 0,
                    "isOpenAccess": False,
                    "openAccessPdf": None,
                    "authors": [],
                    "venue": None,
                    "externalIds": {},
                }
            ]
        }
        findings = parse_semantic_scholar_response(data)

        assert len(findings) == 1
        assert isinstance(findings[0].summary, str)

    @pytest.mark.unit
    def test_parse_semantic_scholar_response_handles_missing_venue(self) -> None:
        """
        Scenario: Missing venue does not crash the parser
        Given a paper with venue=None
        When parse_semantic_scholar_response is called
        Then metadata["venue"] is None or absent without raising
        """
        data: dict[str, Any] = {
            "data": [
                {
                    "paperId": "z",
                    "title": "Venuceless Paper",
                    "abstract": "Some abstract.",
                    "year": 2022,
                    "citationCount": 5,
                    "influentialCitationCount": 0,
                    "isOpenAccess": False,
                    "openAccessPdf": None,
                    "authors": [{"name": "Author One"}],
                    "venue": None,
                    "externalIds": {},
                }
            ]
        }
        findings = parse_semantic_scholar_response(data)

        assert len(findings) == 1
        # venue key present and falsy, or absent — either is acceptable
        venue = findings[0].metadata.get("venue")
        assert venue is None or venue == ""

    @pytest.mark.unit
    def test_parse_semantic_scholar_response_handles_empty_data(self) -> None:
        """
        Scenario: Empty data array returns no findings
        Given {"data": []}
        When parse_semantic_scholar_response is called
        Then an empty list is returned
        """
        findings = parse_semantic_scholar_response({"data": []})

        assert findings == []

    @pytest.mark.unit
    def test_parse_semantic_scholar_response_sets_source_and_channel(self) -> None:
        """
        Scenario: Finding identifies its origin correctly
        Given a valid Semantic Scholar response
        When parse_semantic_scholar_response is called
        Then source="semantic_scholar" and channel="academic"
        """
        findings = parse_semantic_scholar_response(SEMANTIC_SCHOLAR_SAMPLE)

        assert findings[0].source == "semantic_scholar"
        assert findings[0].channel == "academic"

    @pytest.mark.unit
    def test_parse_semantic_scholar_response_captures_pdf_url(self) -> None:
        """
        Scenario: Open access PDF URL is stored in metadata
        Given a paper with openAccessPdf.url set
        When parse_semantic_scholar_response is called
        Then metadata["pdf_url"] equals that URL
        """
        findings = parse_semantic_scholar_response(SEMANTIC_SCHOLAR_SAMPLE)

        assert findings[0].metadata["pdf_url"] == "https://arxiv.org/pdf/1706.03762"


# ---------------------------------------------------------------------------
# TestOpenAccess
# ---------------------------------------------------------------------------


class TestOpenAccess:
    """
    Feature: Open access discovery helpers

    As a research agent
    I want Unpaywall, CORE, OpenAlex, and fallback helpers
    So that I can find or access paywalled papers
    """

    @pytest.mark.unit
    def test_build_unpaywall_url_formats_doi(self) -> None:
        """
        Scenario: DOI is embedded in the Unpaywall URL
        Given DOI "10.1234/test"
        When build_unpaywall_url is called
        Then the URL contains the DOI and the email parameter
        """
        url = build_unpaywall_url("10.1234/test")

        assert "10.1234%2Ftest" in url
        assert "email=" in url

    @pytest.mark.unit
    def test_build_unpaywall_url_uses_correct_base(self) -> None:
        """
        Scenario: URL uses the Unpaywall v2 API base
        """
        url = build_unpaywall_url("10.1234/test")

        assert url.startswith("https://api.unpaywall.org/v2/")

    @pytest.mark.unit
    def test_parse_unpaywall_response_extracts_pdf_url(self) -> None:
        """
        Scenario: PDF URL is returned when best_oa_location has url_for_pdf
        Given an Unpaywall response with a PDF URL
        When parse_unpaywall_response is called
        Then the PDF URL is returned
        """
        result = parse_unpaywall_response(UNPAYWALL_SAMPLE)

        assert result == "https://example.org/paper.pdf"

    @pytest.mark.unit
    def test_parse_unpaywall_response_falls_back_to_url(self) -> None:
        """
        Scenario: Falls back to url when url_for_pdf is absent
        Given best_oa_location with url but no url_for_pdf
        When parse_unpaywall_response is called
        Then the location url is returned
        """
        data: dict[str, Any] = {
            "best_oa_location": {
                "url_for_pdf": None,
                "url": "https://example.org/landing",
            }
        }
        result = parse_unpaywall_response(data)

        assert result == "https://example.org/landing"

    @pytest.mark.unit
    def test_parse_unpaywall_response_returns_none_when_no_oa(self) -> None:
        """
        Scenario: None is returned when best_oa_location is absent
        Given an Unpaywall response with best_oa_location=None
        When parse_unpaywall_response is called
        Then None is returned
        """
        result = parse_unpaywall_response(UNPAYWALL_NO_OA)

        assert result is None

    @pytest.mark.unit
    def test_build_core_search_url_includes_topic(self) -> None:
        """
        Scenario: Topic appears in the CORE search URL
        Given topic "open access"
        When build_core_search_url is called
        Then "open" and "access" appear in the URL
        """
        url = build_core_search_url("open access")

        assert "open" in url.lower() or "access" in url.lower()
        assert "core.ac.uk" in url

    @pytest.mark.unit
    def test_build_openalex_search_url_includes_topic(self) -> None:
        """
        Scenario: Topic appears in the OpenAlex search URL
        Given topic "graph neural networks"
        When build_openalex_search_url is called
        Then the URL contains "graph" and points to openalex.org
        """
        url = build_openalex_search_url("graph neural networks")

        assert "openalex.org" in url
        assert "graph" in url.lower()

    @pytest.mark.unit
    def test_generate_access_fallback_guidance_includes_library_section(
        self,
    ) -> None:
        """
        Scenario: Library access section is present in guidance
        Given a paywalled title
        When generate_access_fallback_guidance is called
        Then the result mentions library access
        """
        guidance = generate_access_fallback_guidance("Some Paywalled Paper")

        assert "library" in guidance.lower()

    @pytest.mark.unit
    def test_generate_access_fallback_guidance_includes_author_email_template(
        self,
    ) -> None:
        """
        Scenario: Author email template is included in guidance
        Given a paper title
        When generate_access_fallback_guidance is called
        Then the result contains a mailto or email template reference
        """
        guidance = generate_access_fallback_guidance("Some Paper Title")

        lower = guidance.lower()
        assert "email" in lower or "author" in lower

    @pytest.mark.unit
    def test_generate_access_fallback_guidance_includes_deepdyve_link_with_doi(
        self,
    ) -> None:
        """
        Scenario: DeepDyve rental link appears when DOI is provided
        Given a DOI "10.1234/test"
        When generate_access_fallback_guidance is called with that DOI
        Then the result mentions DeepDyve
        """
        guidance = generate_access_fallback_guidance("Some Paper", doi="10.1234/test")

        assert "deepdyve" in guidance.lower()

    @pytest.mark.unit
    def test_generate_access_fallback_guidance_no_deepdyve_without_doi(
        self,
    ) -> None:
        """
        Scenario: DeepDyve section is omitted when no DOI is available
        Given no DOI
        When generate_access_fallback_guidance is called
        Then the result does not mention DeepDyve
        """
        guidance = generate_access_fallback_guidance("Some Paper", doi=None)

        assert "deepdyve" not in guidance.lower()


# ---------------------------------------------------------------------------
# TestPdfProcessing
# ---------------------------------------------------------------------------


class TestPdfProcessing:
    """
    Feature: PDF chunking and prompt generation helpers

    As a research agent
    I want page range strings and structured prompts
    So that I can read and summarise long PDF papers in chunks
    """

    @pytest.mark.unit
    def test_estimate_page_chunks_returns_correct_ranges(self) -> None:
        """
        Scenario: 55-page paper splits into three chunks
        Given total_pages=55 and chunk_size=20
        When estimate_page_chunks is called
        Then the result is ["1-20", "21-40", "41-55"]
        """
        result = estimate_page_chunks(55, chunk_size=20)

        assert result == ["1-20", "21-40", "41-55"]

    @pytest.mark.unit
    def test_estimate_page_chunks_handles_exact_multiple(self) -> None:
        """
        Scenario: 40-page paper splits into exactly two chunks
        Given total_pages=40 and chunk_size=20
        When estimate_page_chunks is called
        Then the result is ["1-20", "21-40"]
        """
        result = estimate_page_chunks(40, chunk_size=20)

        assert result == ["1-20", "21-40"]

    @pytest.mark.unit
    def test_estimate_page_chunks_handles_single_chunk(self) -> None:
        """
        Scenario: 15-page paper fits in one chunk
        Given total_pages=15 and chunk_size=20
        When estimate_page_chunks is called
        Then the result is ["1-15"]
        """
        result = estimate_page_chunks(15, chunk_size=20)

        assert result == ["1-15"]

    @pytest.mark.unit
    def test_estimate_page_chunks_uses_default_chunk_size(self) -> None:
        """
        Scenario: Default chunk_size of 20 is applied when not specified
        Given total_pages=25 with default chunk_size
        When estimate_page_chunks is called
        Then first chunk is "1-20" and second is "21-25"
        """
        result = estimate_page_chunks(25)

        assert result[0] == "1-20"
        assert result[1] == "21-25"

    @pytest.mark.unit
    def test_build_paper_summary_prompt_includes_title(self) -> None:
        """
        Scenario: The prompt string contains the paper title
        Given title "Deep Learning Survey"
        When build_paper_summary_prompt is called
        Then the returned string contains "Deep Learning Survey"
        """
        prompt = build_paper_summary_prompt(
            "Deep Learning Survey", "A survey of DL approaches."
        )

        assert "Deep Learning Survey" in prompt

    @pytest.mark.unit
    def test_build_paper_summary_prompt_requests_key_findings(self) -> None:
        """
        Scenario: The prompt asks for key findings
        Given any title and abstract
        When build_paper_summary_prompt is called
        Then the prompt mentions "findings" or "key"
        """
        prompt = build_paper_summary_prompt("Title", "Abstract text here.")

        lower = prompt.lower()
        assert "finding" in lower or "key" in lower

    @pytest.mark.unit
    def test_build_paper_summary_prompt_requests_methodology(self) -> None:
        """
        Scenario: The prompt asks for a methodology summary
        Given any title and abstract
        When build_paper_summary_prompt is called
        Then the prompt mentions "methodology" or "method"
        """
        prompt = build_paper_summary_prompt("Title", "Abstract text here.")

        lower = prompt.lower()
        assert "method" in lower

    @pytest.mark.unit
    def test_build_paper_summary_prompt_requests_limitations(self) -> None:
        """
        Scenario: The prompt asks for limitations
        Given any title and abstract
        When build_paper_summary_prompt is called
        Then the prompt mentions "limitation"
        """
        prompt = build_paper_summary_prompt("Title", "Abstract text here.")

        assert "limitation" in prompt.lower()
