"""The four channel agents must document the envelope the parser reads.

Feature: Agent instructions and the envelope parser stay in step.

As a research session
I want every channel agent told to emit the same record shape
So that one agent's private convention does not become a blind spot

The four agents disagreed. Only code-searcher reported a result count
at all; literature-reviewer called it `papers_found`; discourse-scanner
and triz-analyst reported no count. All four listed `errors` as an
untyped array with no documented element shape. `parse_envelope`
tolerates every one of those shapes, which is what keeps a
non-conforming agent producing a coarse record instead of none, but
tolerance is a fallback and not the contract.

These tests hold the contract. They parse the fenced JSON block out of
each agent's markdown, so they fail when an agent's documented envelope
drifts from what the parser reads, rather than when someone rewords a
sentence near it.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from tome.synthesis.quality import RATE_LIMIT, SOURCE_ERROR, parse_envelope

AGENTS_DIR = Path(__file__).parents[2] / "agents"

CHANNEL_AGENTS = {
    "code-searcher.md": "code",
    "discourse-scanner.md": "discourse",
    "literature-reviewer.md": "academic",
    "triz-analyst.md": "triz",
}

_JSON_BLOCK = re.compile(r"```json\n(.*?)\n```", re.DOTALL)


def _envelope_block(filename: str) -> dict:
    """Return the documented envelope from an agent's markdown."""
    text = (AGENTS_DIR / filename).read_text(encoding="utf-8")
    for block in _JSON_BLOCK.findall(text):
        parsed = json.loads(block)
        if isinstance(parsed, dict) and "channel" in parsed:
            return parsed
    raise AssertionError(f"{filename} documents no envelope JSON block")


@pytest.mark.parametrize("filename,channel", sorted(CHANNEL_AGENTS.items()))
class TestDocumentedEnvelope:
    """Feature: Each agent documents a parseable, complete envelope."""

    @pytest.mark.unit
    def test_documented_envelope_parses(self, filename: str, channel: str) -> None:
        """Scenario: The example an agent is shown is one the parser accepts.

        Given the JSON envelope in an agent's instructions
        When parse_envelope reads it
        Then it yields query logs for the right channel
        Because the example is the specification an agent copies. If it
             does not parse, every conforming agent produces a record
             the session cannot read.
        """
        logs = parse_envelope(_envelope_block(filename))
        assert logs, f"{filename} envelope produced no query log"
        assert all(log.channel == channel for log in logs)

    @pytest.mark.unit
    def test_envelope_documents_a_per_query_record(
        self, filename: str, channel: str
    ) -> None:
        """Scenario: The agent is told to report each query.

        Given an agent's documented envelope
        Then metadata.queries is present with at least one entry
        Because without it the parser synthesizes a single log and the
             channel loses the difference between one query that found
             nothing and four that did. Four empty queries is a much
             stronger statement about a topic than one.
        """
        metadata = _envelope_block(filename).get("metadata", {})
        queries = metadata.get("queries")
        assert queries, f"{filename} documents no metadata.queries"
        assert "result_count" in queries[0]
        assert "source" in queries[0]

    @pytest.mark.unit
    def test_envelope_documents_structured_errors(
        self, filename: str, channel: str
    ) -> None:
        """Scenario: The agent is shown a typed error, not a bare string.

        Given an agent's documented envelope
        Then errors holds objects carrying a known kind
        Because a bare string forces the parser onto a keyword
             heuristic, and mistaking a rate limit for a source error
             tells the reader to investigate a source that only needed
             re-running.
        """
        errors = _envelope_block(filename).get("errors")
        assert errors, f"{filename} documents no example error"
        first = errors[0]
        assert isinstance(first, dict), f"{filename} documents a bare-string error"
        assert first.get("kind") in (RATE_LIMIT, SOURCE_ERROR)
        assert "source" in first


class TestAgentsUseTheChannelSeam:
    """Feature: Agents are told to build queries with tome, not freehand."""

    @pytest.mark.unit
    @pytest.mark.parametrize("filename", sorted(CHANNEL_AGENTS))
    def test_agent_references_its_channel_module(self, filename: str) -> None:
        """Scenario: Each agent names the builder module it must use.

        Given an agent's instructions
        Then they reference tome.channels
        Because tome has 25 tested query builders and parsers that the
             research pipeline routed around entirely: the agents
             improvised queries and self-reported counts. A count tome
             derived and a count an agent invented are indistinguishable
             to a reader, and only one of them is evidence.
        """
        text = (AGENTS_DIR / filename).read_text(encoding="utf-8")
        assert "tome.channels" in text, f"{filename} never names a channel builder"

    @pytest.mark.unit
    @pytest.mark.parametrize("filename", sorted(CHANNEL_AGENTS))
    def test_agent_forbids_fabricated_queries(self, filename: str) -> None:
        """Scenario: The no-hallucination rule covers the query record.

        Given an agent's rules
        Then they forbid reporting a query that was not run
        Because every agent already forbade hallucinating findings
             while saying nothing about the query record, and the query
             record is what the frontier signal is computed from.
        """
        text = (AGENTS_DIR / filename).read_text(encoding="utf-8").lower()
        assert "never report a query you did not run" in text, filename
