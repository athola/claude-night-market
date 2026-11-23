"""Citation grounding: a cited URL must trace to a session finding."""

from __future__ import annotations

from pathlib import Path

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

    def test_scheme_does_not_false_flag(self) -> None:
        assert find_ungrounded_urls("http://example.com/a", _findings()) == []

    def test_www_prefix_does_not_false_flag(self) -> None:
        assert find_ungrounded_urls("https://www.example.com/a", _findings()) == []

    def test_query_parameter_order_does_not_false_flag(self) -> None:
        findings = [make_finding(url="https://example.com/s?q=1&page=2")]
        assert find_ungrounded_urls("https://example.com/s?page=2&q=1", findings) == []

    def test_different_query_value_is_flagged(self) -> None:
        findings = [make_finding(url="https://example.com/s?q=1")]
        assert find_ungrounded_urls("https://example.com/s?q=2", findings) == [
            "https://example.com/s?q=2"
        ]

    def test_malformed_finding_url_does_not_abort_the_check(self) -> None:
        findings = [make_finding(url="http://[bad"), *_findings()]
        text = "https://example.com/a https://invented.example.org/p"
        assert find_ungrounded_urls(text, findings) == [
            "https://invented.example.org/p"
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


@pytest.mark.unit
@pytest.mark.parametrize("skill", ["research", "synthesize"])
def test_skill_runs_grounding_where_prose_is_written(skill: str) -> None:
    # The function only helps if the stage that writes report prose calls it
    text = (Path(__file__).parents[2] / "skills" / skill / "SKILL.md").read_text()
    assert "find_ungrounded_urls" in text


class TestGroundedUrlsInMarkdown:
    """Markdown wrapping and parentheses produced false "ungrounded" URLs,
    and the skills tell the model to drop each one (TOM-1).
    """

    def test_backticked_and_bold_urls_are_grounded(self) -> None:
        findings = [make_finding(url="https://a.com/x")]
        report = "See `https://a.com/x` and **https://a.com/x**."
        assert find_ungrounded_urls(report, findings) == []

    def test_url_with_parentheses_is_grounded(self) -> None:
        url = "https://en.wikipedia.org/wiki/Foo_(bar)"
        findings = [make_finding(url=url)]
        assert find_ungrounded_urls(f"Per {url}, and [w]({url}).", findings) == []

    def test_url_in_a_finding_summary_is_grounded(self) -> None:
        findings = [make_finding(summary="Docs at https://docs.a.com/guide say so.")]
        assert find_ungrounded_urls("See https://docs.a.com/guide.", findings) == []

    def test_an_invented_url_is_still_reported(self) -> None:
        findings = [make_finding(url="https://a.com/x")]
        assert find_ungrounded_urls("`https://b.com/y`", findings) == [
            "https://b.com/y"
        ]
