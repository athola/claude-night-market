# ruff: noqa: D101,D102,D103,D205,D212,PLR2004,E501
"""Unit tests for tome channel modules: github, discourse, academic.

These channels were previously sub-22% covered. The tests here exercise
URL builders, response parsers, and ranking functions to push tome's
total coverage above the 90% gate.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from tome.channels.academic import (
    build_arxiv_search_url,
    build_citation_citations_url,
    build_citation_references_url,
    build_core_search_url,
    build_openalex_search_url,
    build_paper_summary_prompt,
    build_semantic_scholar_url,
    build_unpaywall_url,
    estimate_page_chunks,
    expand_academic_queries,
    generate_access_fallback_guidance,
    parse_arxiv_response,
    parse_citation_chain_response,
    parse_semantic_scholar_response,
    parse_unpaywall_response,
)
from tome.channels.discourse import (
    build_blog_search_queries,
    build_hn_search_url,
    build_lobsters_search_url,
    build_lobsters_websearch_query,
    build_reddit_search_url,
    expand_discourse_queries,
    parse_blog_result,
    parse_hn_response,
    parse_lobsters_result,
    parse_reddit_response,
    suggest_subreddits,
)
from tome.channels.github import (
    build_github_api_search,
    build_github_search_queries,
    expand_github_queries,
    parse_github_api_response,
    parse_github_result,
    rank_github_findings,
)
from tome.models import Finding

# ============================================================================
# github.expand_github_queries / build_github_search_queries
# ============================================================================


class TestGitHubQueryBuilders:
    @pytest.mark.unit
    def test_expand_returns_unique_queries_capped_at_max(self) -> None:
        out = expand_github_queries("rate limiting", max_variants=3)
        assert len(out) == 3
        assert len(set(out)) == 3
        assert all("rate limiting" in q for q in out)

    @pytest.mark.unit
    def test_expand_default_returns_five(self) -> None:
        out = expand_github_queries("topic")
        assert len(out) == 5

    @pytest.mark.unit
    def test_build_search_queries_clamps_to_one_to_five(self) -> None:
        assert len(build_github_search_queries("x", max_queries=0)) == 1
        assert len(build_github_search_queries("x", max_queries=99)) == 5

    @pytest.mark.unit
    def test_build_api_search_uses_url_encoding(self) -> None:
        url = build_github_api_search("hello world")
        assert "hello+world" in url or "hello%20world" in url
        assert url.startswith("https://api.github.com/search/repositories")
        assert "sort=stars" in url


# ============================================================================
# github.parse_github_result
# ============================================================================


class TestParseGitHubResult:
    @pytest.mark.unit
    def test_parses_full_result(self) -> None:
        result = {
            "title": "owner/repo: A cool tool",
            "url": "https://github.com/owner/repo",
            "snippet": "A short description",
        }
        f = parse_github_result(result)
        assert f.source == "github"
        assert f.channel == "code"
        assert f.title == "owner/repo: A cool tool"
        assert f.url == "https://github.com/owner/repo"
        assert f.summary == "A short description"
        assert f.metadata.get("repo_name") == "owner/repo"

    @pytest.mark.unit
    def test_parses_with_description_alternative(self) -> None:
        result = {
            "title": "x",
            "url": "https://github.com/o/r",
            "description": "via description",
        }
        f = parse_github_result(result)
        assert f.summary == "via description"

    @pytest.mark.unit
    def test_falls_back_to_repo_name_when_no_snippet(self) -> None:
        result = {"title": "", "url": "https://github.com/foo/bar"}
        f = parse_github_result(result)
        assert "foo/bar" in f.summary
        assert f.title  # falls back to repo_name or url

    @pytest.mark.unit
    def test_handles_empty_url(self) -> None:
        f = parse_github_result({"title": "no url"})
        assert f.relevance == 0.5
        assert f.url == ""


# ============================================================================
# github.parse_github_api_response
# ============================================================================


class TestParseGitHubApiResponse:
    @pytest.mark.unit
    def test_parses_items_with_metadata(self) -> None:
        data = {
            "items": [
                {
                    "full_name": "psf/requests",
                    "html_url": "https://github.com/psf/requests",
                    "description": "Python HTTP client",
                    "stargazers_count": 50000,
                    "language": "Python",
                    "updated_at": "2024-01-15T12:00:00Z",
                }
            ]
        }
        out = parse_github_api_response(data, "http client")
        assert len(out) == 1
        f = out[0]
        assert f.title == "psf/requests"
        assert f.metadata["stars"] == 50000
        assert f.metadata["language"] == "Python"
        assert f.metadata["updated_at"] == "2024-01-15T12:00:00Z"
        assert "50,000 stars" in f.summary
        assert "Python" in f.summary

    @pytest.mark.unit
    def test_skips_items_without_html_url(self) -> None:
        data = {"items": [{"full_name": "no/url"}]}
        assert parse_github_api_response(data, "topic") == []

    @pytest.mark.unit
    def test_handles_non_list_items(self) -> None:
        assert parse_github_api_response({"items": "not a list"}, "x") == []

    @pytest.mark.unit
    def test_skips_non_dict_items(self) -> None:
        data = {"items": ["not a dict", {"html_url": "https://github.com/a/b"}]}
        out = parse_github_api_response(data, "topic")
        assert len(out) == 1

    @pytest.mark.unit
    def test_handles_minimal_item(self) -> None:
        data = {"items": [{"html_url": "https://github.com/min/imal"}]}
        out = parse_github_api_response(data, "topic")
        assert len(out) == 1
        assert out[0].metadata["stars"] == 0


# ============================================================================
# github.rank_github_findings
# ============================================================================


def _gh_finding(stars=0, updated_at=None, title="t", url="https://github.com/a/b"):
    return Finding(
        source="github",
        channel="code",
        title=title,
        url=url,
        relevance=0.5,
        summary="s",
        metadata={"stars": stars, "updated_at": updated_at}
        if updated_at
        else {"stars": stars},
    )


class TestRankGitHubFindings:
    @pytest.mark.unit
    def test_returns_empty_for_empty_input(self) -> None:
        assert rank_github_findings([]) == []

    @pytest.mark.unit
    def test_does_not_mutate_input(self) -> None:
        findings = [_gh_finding(stars=10), _gh_finding(stars=1000)]
        original_order = [f.metadata["stars"] for f in findings]
        rank_github_findings(findings)
        # Input list preserves original order
        assert [f.metadata["stars"] for f in findings] == original_order

    @pytest.mark.unit
    def test_sorts_more_recent_higher_at_equal_stars(self) -> None:
        recent = _gh_finding(
            stars=100,
            updated_at=datetime.now(tz=timezone.utc).isoformat().replace("+00:00", "Z"),
        )
        ancient = _gh_finding(stars=100, updated_at="2010-01-01T00:00:00Z")
        out = rank_github_findings([ancient, recent])
        # The recent one wins on the recency tiebreaker
        assert out[0] is recent

    @pytest.mark.unit
    def test_handles_invalid_updated_at(self) -> None:
        f = _gh_finding(stars=10, updated_at="not-a-date")
        out = rank_github_findings([f])
        assert len(out) == 1


# ============================================================================
# discourse.expand / build URLs
# ============================================================================


class TestDiscourseQueryBuilders:
    @pytest.mark.unit
    def test_expand_returns_distinct_variants(self) -> None:
        out = expand_discourse_queries("kafka")
        assert len(out) == 4
        assert len(set(out)) == 4
        assert "kafka" in out

    @pytest.mark.unit
    def test_expand_caps_at_max_variants(self) -> None:
        assert len(expand_discourse_queries("topic", max_variants=2)) == 2

    @pytest.mark.unit
    def test_hn_search_url_encodes_topic(self) -> None:
        url = build_hn_search_url("rate limit", hits_per_page=20)
        assert "rate+limit" in url or "rate%20limit" in url
        assert "hitsPerPage=20" in url
        assert "tags=story" in url

    @pytest.mark.unit
    def test_lobsters_search_url(self) -> None:
        url = build_lobsters_search_url("rust async")
        assert url.startswith("https://lobste.rs/search")
        assert "what=stories" in url

    @pytest.mark.unit
    def test_lobsters_websearch_query_uses_site_operator(self) -> None:
        assert build_lobsters_websearch_query("topic") == "site:lobste.rs topic"

    @pytest.mark.unit
    def test_reddit_search_url_uses_subreddit_path(self) -> None:
        url = build_reddit_search_url("topic", subreddit="rust")
        assert "/r/rust/search.json" in url
        assert "restrict_sr=on" in url

    @pytest.mark.unit
    def test_blog_search_queries_capped(self) -> None:
        out = build_blog_search_queries("redis", max_queries=2)
        assert len(out) == 2
        assert all("redis" in q for q in out)
        assert all(q.startswith("site:") for q in out)

    @pytest.mark.unit
    def test_blog_search_queries_clamps_max(self) -> None:
        # max_queries=0 clamps to 1, max_queries=99 clamps to len(domains)
        assert len(build_blog_search_queries("topic", max_queries=0)) == 1
        assert len(build_blog_search_queries("topic", max_queries=99)) <= 7


# ============================================================================
# discourse.parse_*
# ============================================================================


class TestParseHNResponse:
    @pytest.mark.unit
    def test_parses_hits_above_threshold(self) -> None:
        data = {
            "hits": [
                {
                    "title": "Story",
                    "url": "https://example.com",
                    "points": 250,
                    "num_comments": 80,
                    "objectID": "12345",
                },
                {
                    "title": "Low",
                    "url": "https://x.com",
                    "points": 1,
                    "objectID": "1",
                },
            ]
        }
        out = parse_hn_response(data, min_score=5)
        assert len(out) == 1
        assert out[0].title == "Story"
        assert out[0].metadata["score"] == 250
        assert "250 points" in out[0].summary
        assert "80 comments" in out[0].summary

    @pytest.mark.unit
    def test_falls_back_to_item_url_when_url_missing(self) -> None:
        data = {
            "hits": [
                {"title": "ask", "points": 100, "objectID": "999"},
            ]
        }
        out = parse_hn_response(data)
        assert "news.ycombinator.com/item?id=999" in out[0].url

    @pytest.mark.unit
    def test_handles_non_list_hits(self) -> None:
        assert parse_hn_response({"hits": None}) == []
        assert parse_hn_response({}) == []

    @pytest.mark.unit
    def test_skips_non_dict_hits(self) -> None:
        data = {"hits": ["bad", {"title": "ok", "points": 100, "url": "https://x.com"}]}
        out = parse_hn_response(data)
        assert len(out) == 1


class TestParseLobstersResult:
    @pytest.mark.unit
    def test_parses_with_snippet(self) -> None:
        f = parse_lobsters_result(
            {"title": "T", "url": "https://lobste.rs/s/abc", "snippet": "summary"}
        )
        assert f.source == "lobsters"
        assert f.channel == "discourse"
        assert f.summary == "summary"

    @pytest.mark.unit
    def test_falls_back_to_description(self) -> None:
        f = parse_lobsters_result(
            {"title": "T", "url": "https://lobste.rs/s/x", "description": "desc"}
        )
        assert f.summary == "desc"

    @pytest.mark.unit
    def test_no_snippet_uses_title_as_summary(self) -> None:
        f = parse_lobsters_result({"title": "Just a title", "url": "https://x"})
        assert f.summary == "Just a title"


class TestSuggestSubreddits:
    @pytest.mark.unit
    def test_known_domain_returns_specific_subs(self) -> None:
        subs = suggest_subreddits("rust async", "devops")
        assert "kubernetes" in subs

    @pytest.mark.unit
    def test_unknown_domain_falls_back_to_general(self) -> None:
        subs = suggest_subreddits("anything", "made-up-domain")
        assert "programming" in subs

    @pytest.mark.unit
    def test_returns_a_list_copy(self) -> None:
        subs1 = suggest_subreddits("x", "general")
        subs2 = suggest_subreddits("y", "general")
        assert subs1 is not subs2


class TestParseRedditResponse:
    @pytest.mark.unit
    def test_parses_qualifying_post(self) -> None:
        data = {
            "data": {
                "children": [
                    {
                        "data": {
                            "title": "Post",
                            "url": "https://example.com/article",
                            "score": 500,
                            "selftext": "long text" * 30,
                            "permalink": "/r/programming/comments/x",
                        }
                    }
                ]
            }
        }
        out = parse_reddit_response(data)
        assert len(out) == 1
        assert out[0].title == "Post"
        assert out[0].url == "https://example.com/article"
        assert len(out[0].summary) <= 200
        assert out[0].metadata["score"] == 500

    @pytest.mark.unit
    def test_uses_permalink_when_external_url_is_reddit(self) -> None:
        data = {
            "data": {
                "children": [
                    {
                        "data": {
                            "title": "Self",
                            "url": "https://www.reddit.com/r/x/comments/y",
                            "score": 100,
                            "permalink": "/r/x/comments/y",
                        }
                    }
                ]
            }
        }
        out = parse_reddit_response(data)
        assert "reddit.com/r/x/comments/y" in out[0].url

    @pytest.mark.unit
    def test_excludes_below_min_score(self) -> None:
        data = {
            "data": {
                "children": [
                    {"data": {"title": "low", "score": 1, "url": "https://x"}},
                ]
            }
        }
        assert parse_reddit_response(data, min_score=10) == []

    @pytest.mark.unit
    def test_handles_missing_path(self) -> None:
        assert parse_reddit_response({}) == []
        assert parse_reddit_response({"data": "not a dict"}) == []

    @pytest.mark.unit
    def test_skips_non_dict_children(self) -> None:
        data = {
            "data": {
                "children": [
                    "bad",
                    {"data": {"title": "ok", "score": 100, "url": "https://x"}},
                ]
            }
        }
        out = parse_reddit_response(data)
        assert len(out) == 1

    @pytest.mark.unit
    def test_summary_falls_back_to_score_for_link_post(self) -> None:
        data = {
            "data": {
                "children": [
                    {
                        "data": {
                            "title": "no selftext",
                            "url": "https://example.com",
                            "score": 250,
                            "permalink": "/r/x/y",
                            "selftext": "",
                        }
                    }
                ]
            }
        }
        out = parse_reddit_response(data)
        assert "250 upvotes" in out[0].summary


class TestParseBlogResult:
    @pytest.mark.unit
    def test_extracts_domain_as_source(self) -> None:
        f = parse_blog_result(
            {
                "title": "Article",
                "url": "https://danluu.com/some-post",
                "snippet": "short",
            }
        )
        assert f.source == "danluu.com"
        assert f.metadata["domain"] == "danluu.com"
        assert f.channel == "discourse"

    @pytest.mark.unit
    def test_strips_www_prefix(self) -> None:
        f = parse_blog_result({"url": "https://www.example.com/x", "title": "T"})
        assert f.source == "example.com"

    @pytest.mark.unit
    def test_no_url_uses_blog_default(self) -> None:
        f = parse_blog_result({"title": "no url"})
        assert f.source == "blog"

    @pytest.mark.unit
    def test_uses_description_alternative(self) -> None:
        f = parse_blog_result(
            {"title": "T", "url": "https://x.com/y", "description": "alt"}
        )
        assert f.summary == "alt"


# ============================================================================
# academic: query/URL builders
# ============================================================================


class TestAcademicQueryBuilders:
    @pytest.mark.unit
    def test_expand_returns_topic_first(self) -> None:
        out = expand_academic_queries("transformer attention", max_variants=5)
        assert out[0] == "transformer attention"
        assert any("survey" in q for q in out)

    @pytest.mark.unit
    def test_expand_drops_first_word_for_multiword_topics(self) -> None:
        out = expand_academic_queries("a b c d", max_variants=5)
        assert "b c d" in out

    @pytest.mark.unit
    def test_expand_preserves_short_topic(self) -> None:
        out = expand_academic_queries("ml", max_variants=5)
        assert "ml" in out

    @pytest.mark.unit
    def test_arxiv_url(self) -> None:
        url = build_arxiv_search_url("topic", max_results=5)
        assert "max_results=5" in url
        assert "search_query=all:topic" in url

    @pytest.mark.unit
    def test_semantic_scholar_url(self) -> None:
        url = build_semantic_scholar_url("topic", limit=20)
        assert "limit=20" in url
        assert "fields=" in url

    @pytest.mark.unit
    def test_unpaywall_url_uses_doi(self) -> None:
        url = build_unpaywall_url("10.1000/xyz", email="alice@example.com")
        assert "10.1000" in url
        assert "alice@example.com" in url

    @pytest.mark.unit
    def test_core_search_url(self) -> None:
        url = build_core_search_url("topic", limit=8)
        assert "limit=8" in url

    @pytest.mark.unit
    def test_openalex_search_url(self) -> None:
        url = build_openalex_search_url("topic", per_page=15)
        assert "per_page=15" in url

    @pytest.mark.unit
    def test_citation_references_url(self) -> None:
        url = build_citation_references_url("paper-123", limit=5)
        assert "paper-123/references" in url
        assert "limit=5" in url

    @pytest.mark.unit
    def test_citation_citations_url(self) -> None:
        url = build_citation_citations_url("paper-123")
        assert "paper-123/citations" in url


# ============================================================================
# academic: arxiv parser
# ============================================================================


_ARXIV_XML = """<?xml version="1.0" ?>
<feed>
  <entry>
    <id>http://arxiv.org/abs/2301.12345v1</id>
    <title>Attention Is Worth a Thousand Reads</title>
    <summary>This paper studies attention.</summary>
    <published>2023-05-10T00:00:00Z</published>
    <author><name>A. Researcher</name></author>
    <author><name>B. Co-author</name></author>
    <category term="cs.LG" />
    <category term="cs.AI" />
    <link title="pdf" href="https://arxiv.org/pdf/2301.12345v1" />
  </entry>
  <entry>
    <id>http://arxiv.org/abs/2402.99999</id>
    <title>Second Paper</title>
    <summary>Another study.</summary>
    <published>2024-01-01T00:00:00Z</published>
    <author><name>C. Author</name></author>
    <link href="https://arxiv.org/pdf/2402.99999" title="pdf" />
  </entry>
</feed>
"""


class TestParseArxivResponse:
    @pytest.mark.unit
    def test_parses_two_entries(self) -> None:
        out = parse_arxiv_response(_ARXIV_XML)
        assert len(out) == 2

    @pytest.mark.unit
    def test_extracts_title_authors_year(self) -> None:
        out = parse_arxiv_response(_ARXIV_XML)
        first = out[0]
        assert "Attention" in first.title
        assert first.metadata["year"] == 2023
        assert first.metadata["authors"] == ["A. Researcher", "B. Co-author"]
        assert first.metadata["arxiv_id"] == "2301.12345"
        assert "cs.LG" in first.metadata["categories"]

    @pytest.mark.unit
    def test_extracts_pdf_link_with_reversed_attributes(self) -> None:
        out = parse_arxiv_response(_ARXIV_XML)
        # Second entry has href before title
        assert out[1].metadata["pdf_url"].endswith("2402.99999")

    @pytest.mark.unit
    def test_handles_empty_feed(self) -> None:
        assert parse_arxiv_response("<feed></feed>") == []

    @pytest.mark.unit
    def test_falls_back_when_title_missing(self) -> None:
        xml = """
        <entry>
          <id>http://arxiv.org/abs/9999.0000</id>
          <summary>no title</summary>
        </entry>
        """
        out = parse_arxiv_response(xml)
        assert len(out) == 1
        # Falls back to arxiv_id when title missing
        assert "9999.0000" in out[0].title


# ============================================================================
# academic: semantic scholar parser
# ============================================================================


class TestParseSemanticScholarResponse:
    @pytest.mark.unit
    def test_parses_paper_with_arxiv_id(self) -> None:
        data = {
            "data": [
                {
                    "title": "Attention",
                    "abstract": "abstract text",
                    "year": 2023,
                    "citationCount": 600,
                    "isOpenAccess": True,
                    "venue": "NeurIPS",
                    "paperId": "p1",
                    "authors": [{"name": "Author A"}, {"name": "Author B"}],
                    "openAccessPdf": {"url": "https://example.com/p.pdf"},
                    "externalIds": {"DOI": "10.1/x", "ArXiv": "2301.12345"},
                }
            ]
        }
        out = parse_semantic_scholar_response(data)
        assert len(out) == 1
        f = out[0]
        assert f.url == "https://arxiv.org/abs/2301.12345"
        assert f.metadata["doi"] == "10.1/x"
        assert f.metadata["citations"] == 600
        # citations >= 500 -> landmark relevance
        assert f.relevance == 0.9

    @pytest.mark.unit
    def test_falls_back_to_s2_paper_url_when_no_arxiv(self) -> None:
        data = {
            "data": [
                {
                    "title": "T",
                    "paperId": "abc",
                    "citationCount": 5,
                    "externalIds": {},
                }
            ]
        }
        out = parse_semantic_scholar_response(data)
        assert "semanticscholar.org/paper/abc" in out[0].url

    @pytest.mark.unit
    def test_empty_paper_id_yields_empty_url(self) -> None:
        data = {"data": [{"title": "T", "citationCount": 1}]}
        out = parse_semantic_scholar_response(data)
        assert out[0].url == ""

    @pytest.mark.unit
    def test_handles_non_dict_paper(self) -> None:
        data = {"data": ["not a dict", {"title": "T", "paperId": "x"}]}
        out = parse_semantic_scholar_response(data)
        assert len(out) == 1

    @pytest.mark.unit
    def test_handles_non_list_data(self) -> None:
        assert parse_semantic_scholar_response({"data": "bad"}) == []

    @pytest.mark.unit
    def test_citation_relevance_tiers(self) -> None:
        # Confirm the 5 tiers map correctly
        for citations, expected in [
            (1000, 0.9),
            (200, 0.8),
            (75, 0.7),
            (15, 0.6),
            (1, 0.5),
        ]:
            data = {
                "data": [{"title": "T", "paperId": "p", "citationCount": citations}]
            }
            out = parse_semantic_scholar_response(data)
            assert out[0].relevance == expected


# ============================================================================
# academic: unpaywall parser
# ============================================================================


class TestParseUnpaywall:
    @pytest.mark.unit
    def test_prefers_pdf_url(self) -> None:
        out = parse_unpaywall_response(
            {"best_oa_location": {"url_for_pdf": "p.pdf", "url": "page"}}
        )
        assert out == "p.pdf"

    @pytest.mark.unit
    def test_falls_back_to_url(self) -> None:
        out = parse_unpaywall_response({"best_oa_location": {"url": "page"}})
        assert out == "page"

    @pytest.mark.unit
    def test_returns_none_when_no_location(self) -> None:
        assert parse_unpaywall_response({}) is None
        assert parse_unpaywall_response({"best_oa_location": None}) is None
        assert parse_unpaywall_response({"best_oa_location": {}}) is None


# ============================================================================
# academic: citation chain parser
# ============================================================================


class TestParseCitationChain:
    @pytest.mark.unit
    def test_handles_references_shape(self) -> None:
        data = {
            "data": [
                {
                    "citedPaper": {
                        "title": "Cited",
                        "paperId": "ref1",
                        "year": 2020,
                        "citationCount": 50,
                        "externalIds": {"ArXiv": "1234.5678"},
                        "authors": [{"name": "X"}],
                    }
                }
            ]
        }
        out = parse_citation_chain_response(data)
        assert len(out) == 1
        assert out[0].url == "https://arxiv.org/abs/1234.5678"
        assert out[0].source == "semantic_scholar_chain"

    @pytest.mark.unit
    def test_handles_citations_shape(self) -> None:
        data = {
            "data": [
                {
                    "citingPaper": {
                        "title": "Citing",
                        "paperId": "p2",
                        "citationCount": 5,
                    }
                }
            ]
        }
        out = parse_citation_chain_response(data)
        assert len(out) == 1
        assert "semanticscholar.org/paper/p2" in out[0].url

    @pytest.mark.unit
    def test_skips_items_without_title(self) -> None:
        data = {"data": [{"citedPaper": {"paperId": "p", "citationCount": 5}}]}
        assert parse_citation_chain_response(data) == []

    @pytest.mark.unit
    def test_handles_non_list_data(self) -> None:
        assert parse_citation_chain_response({"data": "bad"}) == []

    @pytest.mark.unit
    def test_skips_when_paper_field_missing(self) -> None:
        data = {"data": [{"unrelated": {"title": "x"}}]}
        assert parse_citation_chain_response(data) == []


# ============================================================================
# academic: misc helpers
# ============================================================================


class TestEstimatePageChunks:
    @pytest.mark.unit
    def test_evenly_divisible_pages(self) -> None:
        assert estimate_page_chunks(40, chunk_size=20) == ["1-20", "21-40"]

    @pytest.mark.unit
    def test_remaining_partial_chunk(self) -> None:
        assert estimate_page_chunks(55, chunk_size=20) == ["1-20", "21-40", "41-55"]

    @pytest.mark.unit
    def test_zero_pages_returns_empty(self) -> None:
        assert estimate_page_chunks(0, chunk_size=20) == []

    @pytest.mark.unit
    def test_single_chunk(self) -> None:
        assert estimate_page_chunks(5, chunk_size=20) == ["1-5"]


class TestGenerateAccessFallback:
    @pytest.mark.unit
    def test_includes_doi_section_when_doi_provided(self) -> None:
        out = generate_access_fallback_guidance("Title", doi="10.1/x")
        assert "DeepDyve" in out
        # DOI is URL-encoded into the DeepDyve link; "/" becomes "%2F"
        assert "10.1%2Fx" in out

    @pytest.mark.unit
    def test_omits_doi_section_when_no_doi(self) -> None:
        out = generate_access_fallback_guidance("Title")
        assert "DeepDyve" not in out
        assert "Public Library Access" in out

    @pytest.mark.unit
    def test_includes_google_scholar_search_link(self) -> None:
        out = generate_access_fallback_guidance("transformers")
        assert "scholar.google.com" in out


class TestBuildPaperSummaryPrompt:
    @pytest.mark.unit
    def test_includes_title_and_abstract(self) -> None:
        out = build_paper_summary_prompt("My Paper", "this is the abstract")
        assert "My Paper" in out
        assert "this is the abstract" in out
