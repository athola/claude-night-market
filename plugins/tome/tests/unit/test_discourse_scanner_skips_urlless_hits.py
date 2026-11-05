"""Channel agents must drop the hits their parsers refuse.

``parse_lobsters_result``, ``parse_blog_result``, ``parse_websearch_result``
and ``parse_github_result`` return ``None`` for a search hit with no URL.
An agent that is not told so records ``None`` as a finding, so the step that
parses hits with each one has to say the hit is skipped.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from tome.channels.discourse import parse_blog_result, parse_lobsters_result
from tome.channels.github import parse_github_result
from tome.channels.web import parse_websearch_result

AGENTS = Path(__file__).parents[2] / "agents"


def _step_parsing_with(agent: str, parser: str) -> str:
    """Return the numbered instruction step that parses hits with *parser*."""
    text = (AGENTS / agent).read_text(encoding="utf-8")
    steps = re.split(r"\n(?=\d+\. )", text)
    for step in steps:
        if f"with `{parser}`" in step:
            return step
    raise AssertionError(f"{agent} names no step parsing with {parser}")


@pytest.mark.unit
@pytest.mark.parametrize(
    ("agent", "parser", "hit"),
    [
        ("discourse-scanner.md", parse_lobsters_result, ({"title": "no url"},)),
        ("discourse-scanner.md", parse_blog_result, ({"title": "no url"},)),
        ("web-searcher.md", parse_websearch_result, ({"title": "no url"}, "t")),
        ("code-searcher.md", parse_github_result, ({"title": "no url"},)),
    ],
    ids=lambda v: v.__name__ if callable(v) else None,
)
def test_step_for_each_parser_says_a_none_result_is_skipped(
    agent: str, parser, hit: tuple
) -> None:
    assert parser(*hit) is None
    step = _step_parsing_with(agent, parser.__name__)
    assert "`None`" in step
    assert re.search(r"\bskip", step, re.IGNORECASE)
