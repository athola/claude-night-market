"""What the agent said it did becomes a record, or it becomes `unknown`.

Feature: Agent envelopes are parsed into query logs.

As a research session
I want each channel agent's report of its own work recorded
So that an empty channel can be interpreted instead of guessed at

The four channel agents already return `errors` and per-channel
metadata. `skills/research/SKILL.md` told the orchestrator to parse the
findings and nothing else, so both were dropped at that boundary and no
Python type ever modeled the envelope.

The parse is deliberately tolerant of the four shapes that predate the
standard envelope, because an agent that ignores the new contract
should degrade to a weaker record rather than to no record. What it is
not tolerant of is inventing detail: an envelope with no per-query
breakdown yields one synthesized log marked as such, never a plausible
list of queries nobody ran.
"""

from __future__ import annotations

import pytest

from tome.synthesis.quality import UNRECORDED_QUERY, parse_envelope


def _finding(url: str = "https://example.com/a") -> dict:
    return {
        "source": "github",
        "channel": "code",
        "title": "t",
        "url": url,
        "relevance": 0.5,
        "summary": "s",
    }


class TestStandardEnvelope:
    """Feature: The standardized envelope yields one log per query."""

    @pytest.mark.unit
    def test_per_query_records_are_preserved(self) -> None:
        """Scenario: A conforming agent reports each query it ran.

        Given an envelope carrying a queries list
        When it is parsed
        Then one QueryLog exists per query, with its own count
        Because per-query granularity is what lets a later reader see
             that a channel ran four queries and found nothing, rather
             than that it ran once.
        """
        logs = parse_envelope(
            {
                "channel": "code",
                "findings": [_finding()],
                "errors": [],
                "metadata": {
                    "queries": [
                        {"source": "github", "query": "a", "result_count": 1},
                        {"source": "github", "query": "b", "result_count": 0},
                    ]
                },
            }
        )
        assert [log.query for log in logs] == ["a", "b"]
        assert [log.result_count for log in logs] == [1, 0]
        assert all(log.channel == "code" for log in logs)

    @pytest.mark.unit
    def test_structured_error_becomes_the_error_kind(self) -> None:
        """Scenario: A structured error names its kind on the log.

        Given a query entry carrying an error kind
        When it is parsed
        Then the QueryLog carries that kind and is not succeeded
        """
        logs = parse_envelope(
            {
                "channel": "academic",
                "findings": [],
                "errors": [{"kind": "rate_limit", "source": "arxiv", "message": "429"}],
                "metadata": {
                    "queries": [
                        {
                            "source": "arxiv",
                            "query": "q",
                            "result_count": 0,
                            "error": "rate_limit",
                        }
                    ]
                },
            }
        )
        assert logs[0].error == "rate_limit"
        assert logs[0].succeeded is False


class TestLegacyEnvelopes:
    """Feature: Envelopes written before the standard still record something."""

    @pytest.mark.unit
    def test_envelope_without_queries_synthesizes_one_log(self) -> None:
        """Scenario: No per-query breakdown yields one honest log.

        Given an envelope with findings but no queries list
        When it is parsed
        Then exactly one log exists, counting the findings
        And its query text marks itself as unrecorded
        Because the alternative is fabricating query strings. One log
             that admits it does not know what was asked is worth more
             than four that pretend.
        """
        logs = parse_envelope(
            {"channel": "code", "findings": [_finding(), _finding()], "errors": []}
        )
        assert len(logs) == 1
        assert logs[0].result_count == 2
        assert logs[0].query == UNRECORDED_QUERY

    @pytest.mark.unit
    def test_papers_found_is_read_as_a_count(self) -> None:
        """Scenario: literature-reviewer's own key is understood.

        Given an envelope using papers_found rather than results_found
        When it is parsed
        Then the count is taken from it
        Because the four agents disagreed on this key and the parse
             should not punish the channel that chose a different word.
        """
        logs = parse_envelope(
            {
                "channel": "academic",
                "findings": [],
                "errors": [],
                "metadata": {"papers_found": 7},
            }
        )
        assert logs[0].result_count == 7

    @pytest.mark.unit
    def test_bare_string_error_is_classified_not_dropped(self) -> None:
        """Scenario: An untyped error still marks the log failed.

        Given an envelope whose errors are plain strings
        When it is parsed
        Then the synthesized log is marked failed
        Because dropping an unstructured error would read the channel
             as a clean empty search, which is the single worst
             misreading available here.
        """
        logs = parse_envelope(
            {"channel": "academic", "findings": [], "errors": ["arXiv returned 500"]}
        )
        assert logs[0].succeeded is False
        assert logs[0].error == "source_error"

    @pytest.mark.unit
    def test_rate_limit_is_recognized_in_unstructured_text(self) -> None:
        """Scenario: A rate limit is classified from prose as a fallback.

        Given an untyped error mentioning a 429
        When it is parsed
        Then the kind is rate_limit
        Because the two kinds carry different instructions and this
             heuristic recovers the distinction for agents that have
             not adopted the structured form. It is a tolerant-parse
             path, not the contract.
        """
        logs = parse_envelope(
            {
                "channel": "discourse",
                "findings": [],
                "errors": ["HN Algolia returned HTTP 429 Too Many Requests"],
            }
        )
        assert logs[0].error == "rate_limit"

    @pytest.mark.unit
    def test_empty_envelope_yields_a_log_not_silence(self) -> None:
        """Scenario: An agent that reported nothing still leaves a trace.

        Given an envelope with a channel and nothing else
        When it is parsed
        Then one log exists with a zero count and no error
        Because the agent did run. A channel with no log at all derives
             `unknown`, which is reserved for sessions where no agent
             reported, and conflating the two would lose the difference
             between "searched, found nothing" and "never ran".
        """
        logs = parse_envelope({"channel": "triz"})
        assert len(logs) == 1
        assert logs[0].result_count == 0
        assert logs[0].succeeded is True

    @pytest.mark.unit
    def test_missing_channel_is_refused(self) -> None:
        """Scenario: An envelope with no channel cannot be filed.

        Given an envelope lacking a channel
        When it is parsed
        Then it raises
        Because a log with no channel attaches to nothing and would sit
             in the session invisible to every consumer, which is worse
             than a loud failure at the boundary.
        """
        with pytest.raises(ValueError, match="channel"):
            parse_envelope({"findings": []})
