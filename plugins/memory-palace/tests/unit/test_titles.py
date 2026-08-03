"""Tests for the shared capture-title shape rules.

These rules were extracted from the capture hook when the index
promoter needed the same answer to repair titles stored before the
rules were right. Two consumers now depend on them, so the contract is
tested directly rather than only through the hook that owns the
capture path.

Following BDD principles with Given/When/Then scenarios.
"""

from __future__ import annotations

import pytest

from memory_palace.corpus.titles import (
    TITLE_MAX_CHARS,
    looks_like_title,
    slug_title_from_url,
    title_from_url,
)


class TestLooksLikeTitle:
    """Feature: separate a page title from a fragment of model answer.

    As the capture hook and the index promoter
    I want one shared ruling on what a title looks like
    So that a repaired title matches what capture would store today
    """

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "genuine",
        [
            "Python Async Patterns",
            "What Is Rust Ownership?",
            "C++ Move Semantics",
            "*args and **kwargs in Python",
            "Response Times Explained",
        ],
    )
    def test_accepts_genuine_titles(self, genuine: str) -> None:
        """Given a real page title, accept it."""
        assert looks_like_title(genuine)

    @pytest.mark.unit
    @pytest.mark.parametrize(
        ("junk", "why"),
        [
            ("Based on the repository data provided:", "preamble"),
            ("The document shows:", "terminal colon"),
            ("- A loading state", "bullet"),
            ("* A bulleted line", "bullet"),
            ("1. A readable version of the document, or", "ordered marker"),
            ("2) Parenthesised ordered marker", "ordered marker"),
            ("Response", "generic heading"),
            ("SUMMARY", "generic heading, case-insensitive"),
        ],
    )
    def test_rejects_answer_body_fragments(self, junk: str, why: str) -> None:
        """Given a fragment of model answer, reject it."""
        assert not looks_like_title(junk), why

    @pytest.mark.unit
    def test_rejects_a_line_past_the_budget(self) -> None:
        """Given a paragraph, reject rather than truncate it.

        Truncation is what produced the mid-sentence titles in the
        live index, so length must reject outright.
        """
        assert not looks_like_title("x" * (TITLE_MAX_CHARS + 1))

    @pytest.mark.unit
    def test_accepts_a_line_exactly_at_the_budget(self) -> None:
        """Given a line at the limit, accept it. The bound is inclusive."""
        assert looks_like_title("x" * TITLE_MAX_CHARS)


class TestUrlDerivedTitles:
    """Feature: derive a fallback title from the URL.

    As the capture hook, which must always store something
    And as the promoter, which must not churn the index for nothing
    I want the "no better title available" case to be distinguishable
    """

    @pytest.mark.unit
    def test_slug_reads_the_last_path_segment(self) -> None:
        """Given a URL with a path, derive a title from its last segment."""
        assert slug_title_from_url("https://docs.example.com/user-guide") == (
            "User Guide"
        )

    @pytest.mark.unit
    def test_slug_treats_underscores_as_word_breaks(self) -> None:
        """Given an underscored slug, read it as words."""
        assert slug_title_from_url("https://x.test/deep/async_patterns") == (
            "Async Patterns"
        )

    @pytest.mark.unit
    def test_slug_collapses_whitespace_runs(self) -> None:
        """Given adjacent separators, do not emit doubled spaces.

        A real index key produced "Cont Awd Doleta14P00008 1605  None
        None " from consecutive hyphens and underscores. A repair that
        introduces its own sloppiness is not a repair.
        """
        url = "https://spend.test/award/cont_awd_x_1605_-none-_-none-"
        slug = slug_title_from_url(url)
        assert slug is not None
        assert "  " not in slug
        assert slug == slug.strip()

    @pytest.mark.unit
    def test_slug_of_only_separators_is_none(self) -> None:
        """Given a segment that is all separators, report nothing usable."""
        assert slug_title_from_url("https://x.test/---") is None

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "pathless",
        ["https://example.com", "https://example.com/", ""],
    )
    def test_slug_returns_none_without_a_path(self, pathless: str) -> None:
        """Given no path, report that nothing better is available.

        The promoter reads None as "leave this entry alone". A bare
        hostname is not an improvement over a bad title, and rewriting
        the index to gain nothing is its own defect (#605).
        """
        assert slug_title_from_url(pathless) is None

    @pytest.mark.unit
    def test_title_from_url_falls_back_to_the_host(self) -> None:
        """Given no path, the hook's variant still yields something."""
        assert title_from_url("https://example.com") == "example.com"

    @pytest.mark.unit
    def test_title_from_url_prefers_the_slug(self) -> None:
        """Given a path, prefer the slug over the host."""
        assert title_from_url("https://docs.example.com/user-guide") == ("User Guide")
