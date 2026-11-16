"""Citation grounding: a cited URL must trace to a session finding."""

from __future__ import annotations

import pytest

from tests.factories import make_finding
from tome.models import Finding, ResearchSession
from tome.output.citations import find_ungrounded_urls
from tome.output.report import format_report


def _findings() -> list[Finding]:
    return [
        make_finding(url="https://example.com/a"),
        make_finding(url="https://arxiv.org/abs/2301.12345"),
    ]


@pytest.mark.unit
class TestFindUngroundedUrls:
    def test_invented_url_is_flagged(self) -> None:
        text = "See https://invented.example.org/paper for details."
        assert find_ungrounded_urls(text, _findings()) == [
            "https://invented.example.org/paper"
        ]

    def test_url_carried_by_a_finding_passes(self) -> None:
        text = "Source: https://example.com/a and https://arxiv.org/abs/2301.12345"
        assert find_ungrounded_urls(text, _findings()) == []

    def test_trailing_slash_does_not_false_flag(self) -> None:
        assert find_ungrounded_urls("https://example.com/a/", _findings()) == []

    def test_fragment_does_not_false_flag(self) -> None:
        text = "https://example.com/a#section-2"
        assert find_ungrounded_urls(text, _findings()) == []

    def test_host_case_does_not_false_flag(self) -> None:
        assert find_ungrounded_urls("HTTPS://Example.COM/a", _findings()) == []

    def test_sentence_punctuation_is_not_part_of_the_url(self) -> None:
        text = "As shown (https://example.com/a), and https://example.com/a."
        assert find_ungrounded_urls(text, _findings()) == []

    def test_markdown_link_target_is_checked(self) -> None:
        text = "[paper](https://invented.example.org/x)"
        assert find_ungrounded_urls(text, _findings()) == [
            "https://invented.example.org/x"
        ]

    def test_different_path_is_flagged(self) -> None:
        assert find_ungrounded_urls("https://example.com/b", _findings()) == [
            "https://example.com/b"
        ]

    def test_repeated_invented_url_reported_once_in_order(self) -> None:
        text = "https://x.test/2 https://x.test/1 https://x.test/2/"
        assert find_ungrounded_urls(text, []) == [
            "https://x.test/2",
            "https://x.test/1",
        ]

    def test_text_without_urls_yields_nothing(self) -> None:
        assert find_ungrounded_urls("no links here", _findings()) == []

    def test_generated_report_is_grounded(self) -> None:
        session = ResearchSession(
            topic="t", domain="d", triz_depth="none", channels=["code"]
        )
        for finding in _findings():
            session.add_finding(finding)
        assert find_ungrounded_urls(format_report(session), session.findings) == []
