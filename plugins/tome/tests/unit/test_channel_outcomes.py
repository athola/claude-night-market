"""A channel that found nothing must be distinguishable from one that broke.

Feature: Channel outcome is derivable from the session's query record.

As someone reading a research report
I want to know why a channel produced nothing
So that I can tell a thin field from a failed search

Tome could not make this distinction. A channel that errored, a channel
that was rate-limited, and a channel that searched properly and found
nothing all arrived at the report as the same thing: no findings. The
report then skipped the channel entirely, so the distinction was not
merely unavailable, it was invisible.

These tests fix the outcome vocabulary and the derivation order. The
load-bearing case is ``test_legacy_session_derives_unknown_not_empty``:
a session persisted before query logging existed has no evidence about
what any channel did, and calling that ``empty`` would relabel every
historical session "the field is thin" -- manufacturing the exact
conflation this work removes.
"""

from __future__ import annotations

import pytest

from tome.models import Finding, QueryLog, ResearchSession
from tome.synthesis.quality import channel_outcomes


def _session(
    channels: list[str], logs: list[QueryLog], findings: list[Finding] | None = None
):
    return ResearchSession(
        topic="t",
        domain="d",
        triz_depth="light",
        channels=channels,
        findings=findings or [],
        query_log=logs,
    )


class TestQueryLogErrorField:
    """Feature: A query log records why a query failed, not just that it did."""

    @pytest.mark.unit
    def test_error_kind_implies_not_succeeded(self) -> None:
        """Scenario: Setting an error marks the log as failed.

        Given a QueryLog constructed with an error kind
        When the log is inspected
        Then succeeded is False
        Because two fields expressing one fact can disagree; the
             constructor makes the illegal state unrepresentable
             instead of asking every caller to keep them in step.
        """
        log = QueryLog(channel="code", query="q", source="github", error="rate_limit")
        assert log.succeeded is False

    @pytest.mark.unit
    def test_no_error_implies_succeeded(self) -> None:
        """Scenario: A log with no error is a success.

        Given a QueryLog with error left at its default
        When the log is inspected
        Then succeeded is True
        """
        assert QueryLog(channel="code", query="q", source="github").succeeded is True

    @pytest.mark.unit
    def test_succeeded_false_without_error_is_rejected(self) -> None:
        """Scenario: Claiming failure without naming it is refused.

        Given succeeded=False and no error kind
        When the QueryLog is constructed
        Then it raises
        Because an unexplained failure is exactly the state this work
             exists to eliminate. Accepting it would let the old
             "something went wrong, unclear what" case back in.
        """
        with pytest.raises(ValueError, match="error"):
            QueryLog(channel="code", query="q", source="github", succeeded=False)

    @pytest.mark.unit
    def test_from_dict_without_error_key_loads(self) -> None:
        """Scenario: A log persisted before this field still loads.

        Given a serialized QueryLog with no "error" key
        When from_dict parses it
        Then error is None and succeeded is True
        """
        log = QueryLog.from_dict(
            {"channel": "code", "query": "q", "source": "github", "result_count": 2}
        )
        assert log.error is None
        assert log.succeeded is True


class TestSessionQueryLog:
    """Feature: The session carries the record of what was searched."""

    @pytest.mark.unit
    def test_query_log_round_trips(self) -> None:
        """Scenario: Query logs survive save and load.

        Given a session holding one query log
        When it is serialized and parsed back
        Then the log is present with its fields intact
        """
        session = _session(["code"], [QueryLog("code", "q", "github", result_count=3)])
        restored = ResearchSession.from_dict(session.to_dict())
        assert len(restored.query_log) == 1
        assert restored.query_log[0].source == "github"
        assert restored.query_log[0].result_count == 3

    @pytest.mark.unit
    def test_session_without_query_log_key_loads(self) -> None:
        """Scenario: A session persisted before query logging still loads.

        Given a serialized session with no "query_log" key
        When from_dict parses it
        Then query_log is empty rather than raising
        Because sessions on disk predate this field and a research
             tool that cannot open its own history is worse than one
             that cannot explain a gap.
        """
        raw = _session(["code"], []).to_dict()
        del raw["query_log"]
        assert ResearchSession.from_dict(raw).query_log == []


class TestChannelOutcomes:
    """Feature: Six outcomes, derived from evidence, never stored."""

    @pytest.mark.unit
    def test_ok_when_queries_succeeded_and_returned_results(self) -> None:
        """Scenario: A working channel with results is ok."""
        s = _session(["code"], [QueryLog("code", "q", "github", result_count=5)])
        assert channel_outcomes(s)["code"] == "ok"

    @pytest.mark.unit
    def test_empty_when_queries_succeeded_and_returned_nothing(self) -> None:
        """Scenario: A working channel with no results is empty.

        Given every query for the channel succeeded
        And none returned a result
        Then the outcome is empty
        Because this is the only case where absence is evidence about
             the field rather than about the search.
        """
        s = _session(["code"], [QueryLog("code", "q", "github", result_count=0)])
        assert channel_outcomes(s)["code"] == "empty"

    @pytest.mark.unit
    def test_error_when_all_queries_failed(self) -> None:
        """Scenario: A broken channel is an error, not an empty one."""
        s = _session(
            ["academic"],
            [QueryLog("academic", "q", "arxiv", error="source_error")],
        )
        assert channel_outcomes(s)["academic"] == "error"

    @pytest.mark.unit
    def test_rate_limited_outranks_error(self) -> None:
        """Scenario: A rate limit is named specifically.

        Given a channel whose queries failed, one on a rate limit
        And no results were returned
        Then the outcome is rate_limited rather than error
        Because the two carry different instructions to the reader:
             a rate limit means re-run, a source error means
             investigate.
        """
        s = _session(
            ["academic"],
            [
                QueryLog("academic", "a", "arxiv", error="source_error"),
                QueryLog("academic", "b", "semantic_scholar", error="rate_limit"),
            ],
        )
        assert channel_outcomes(s)["academic"] == "rate_limited"

    @pytest.mark.unit
    def test_degraded_when_some_failed_but_results_arrived(self) -> None:
        """Scenario: A partial failure that still produced results is degraded.

        Given one query failed and another returned results
        Then the outcome is degraded
        Because the findings are real but the coverage is not what was
             asked for, so the channel must not count as a clean probe.
        """
        s = _session(
            ["code"],
            [
                QueryLog("code", "a", "github_api", error="rate_limit"),
                QueryLog("code", "b", "websearch", result_count=4),
            ],
        )
        assert channel_outcomes(s)["code"] == "degraded"

    @pytest.mark.unit
    def test_legacy_session_derives_unknown_not_empty(self) -> None:
        """Scenario: No record means no claim.

        Given a planned channel with no query logs at all
        When outcomes are derived
        Then the outcome is unknown, and specifically not empty
        Because a session that predates query logging holds no
             evidence about the field. Reading silence as "the field
             is thin" would fabricate the finding this whole feature
             exists to avoid.
        """
        outcomes = channel_outcomes(_session(["code", "academic"], []))
        assert outcomes["code"] == "unknown"
        assert outcomes["academic"] == "unknown"

    @pytest.mark.unit
    def test_planned_channels_all_appear(self) -> None:
        """Scenario: Every planned channel gets an outcome.

        Given two planned channels and logs for only one
        Then both appear in the result
        Because the report iterates planned channels; a missing key
             would silently restore the old skip-it behavior.
        """
        s = _session(
            ["code", "academic"], [QueryLog("code", "q", "github", result_count=1)]
        )
        assert set(channel_outcomes(s)) == {"code", "academic"}
