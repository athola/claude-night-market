"""The discourse agent must drop the hits its parsers refuse.

``parse_lobsters_result`` and ``parse_blog_result`` return ``None`` for a
search hit with no URL. An agent that is not told so records ``None`` as a
finding, so the instruction for each parser has to say the hit is skipped.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from tome.channels.discourse import parse_blog_result, parse_lobsters_result

AGENT = Path(__file__).parents[2] / "agents" / "discourse-scanner.md"


def _step_naming(parser: str) -> str:
    """Return the numbered instruction step that names *parser*."""
    text = AGENT.read_text(encoding="utf-8")
    steps = re.split(r"\n(?=\d+\. )", text)
    for step in steps:
        if f"`{parser}`" in step:
            return step
    raise AssertionError(f"discourse-scanner.md names no step for {parser}")


@pytest.mark.unit
@pytest.mark.parametrize(
    "parser", [parse_lobsters_result, parse_blog_result], ids=lambda p: p.__name__
)
def test_step_for_each_parser_says_a_none_result_is_skipped(parser) -> None:
    assert parser({"title": "no url here"}) is None
    step = _step_naming(parser.__name__)
    assert "`None`" in step
    assert re.search(r"\bskip", step, re.IGNORECASE)
