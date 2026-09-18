"""
Feature: Context verification between research passes

As the research orchestrator
I want one STOP or CONTINUE decision computed from the session record
So that a second pass happens for a named reason and never without bound

OctoTools (arXiv 2502.11271) asks an LLM to judge completeness, unused
tools, inconsistencies, verification needs and ambiguities, then say STOP
or CONTINUE. Later work found self-judged stop signals drift from true
quality (VRR-Stop, arXiv 2607.17641; arXiv 2607.24300), so here each
criterion is read from records the agents did not grade: query logs,
positive controls, and the frontier verdict.
"""

from __future__ import annotations

import pytest

from tome.models import Finding, QueryLog, ResearchSession
from tome.synthesis.quality import CANARY_SOURCE
from tome.synthesis.verifier import CONTINUE, STOP, verify_context


def _finding(channel: str, n: int = 0) -> Finding:
    return Finding(
        source="s",
        channel=channel,
        title=f"t{n}",
        url=f"https://example.com/{channel}/{n}",
        relevance=0.5,
        summary="s",
    )


def _canary(channel: str, *, found: bool = True) -> QueryLog:
    return QueryLog(
        channel=channel,
        query="known target",
        source=CANARY_SOURCE,
        result_count=1 if found else 0,
    )


def _query(channel: str, results: int, error: str | None = None) -> QueryLog:
    return QueryLog(
        channel=channel,
        query="topic",
        source=channel,
        result_count=results,
        error=error,
    )


def _session(channels, logs, findings=()) -> ResearchSession:
    return ResearchSession(
        topic="t",
        domain="d",
        triz_depth="medium",
        channels=list(channels),
        findings=list(findings),
        query_log=list(logs),
    )


def _clean(channel: str, results: int = 3) -> list[QueryLog]:
    return [_canary(channel), _query(channel, results)]


def _check(result, criterion: str):
    return next(c for c in result.checks if c.criterion == criterion)


class TestACleanCoveredRunStops:
    @pytest.mark.unit
    def test_every_channel_clean_and_controlled_stops(self) -> None:
        """
        Given three retrieval channels that ran a passing control
        And each returned findings
        When the session is verified after one pass
        Then the conclusion is STOP with nothing to rerun or add
        """
        channels = ["code", "discourse", "academic"]
        session = _session(
            channels,
            [log for c in channels for log in _clean(c)],
            [_finding(c, i) for c in channels for i in range(3)],
        )
        result = verify_context(session, passes_run=1)
        assert result.conclusion == STOP
        assert result.rerun == result.reformulate == result.add == ()
        assert all(check.passed for check in result.checks)


class TestAFailedSearchIsRerun:
    @pytest.mark.unit
    @pytest.mark.parametrize("error", ["rate_limit", "source_error"])
    def test_a_channel_that_failed_is_rerun(self, error: str) -> None:
        """
        Given discourse failed every query
        When verified with passes left
        Then CONTINUE, rerunning discourse, and completeness fails
        """
        session = _session(
            ["code", "discourse"],
            [*_clean("code"), _canary("discourse"), _query("discourse", 0, error)],
            [_finding("code")],
        )
        result = verify_context(session, passes_run=1)
        assert result.conclusion == CONTINUE
        assert result.rerun == ("discourse",)
        assert not _check(result, "completeness").passed

    @pytest.mark.unit
    def test_a_channel_with_no_record_is_rerun(self) -> None:
        """
        Given academic was planned and left no query record
        Then it is rerun: silence is not evidence the channel ran
        """
        session = _session(["code", "academic"], _clean("code"), [_finding("code")])
        assert verify_context(session, passes_run=1).rerun == ("academic",)

    @pytest.mark.unit
    def test_a_failed_generative_channel_is_rerun_too(self) -> None:
        """
        Given triz errored
        Then it is rerun, since completeness covers every dispatched channel
        """
        session = _session(
            ["code", "triz"],
            [*_clean("code"), _query("triz", 0, "source_error")],
            [_finding("code")],
        )
        assert verify_context(session, passes_run=1).rerun == ("triz",)


class TestABlindChannelIsNotTrusted:
    @pytest.mark.unit
    def test_a_failed_control_is_rerun(self) -> None:
        """
        Given code could not retrieve its known target
        Then verification fails and code is rerun
        """
        session = _session(
            ["code", "discourse"],
            [_canary("code", found=False), _query("code", 0), *_clean("discourse")],
            [_finding("discourse")],
        )
        result = verify_context(session, passes_run=1)
        assert result.conclusion == CONTINUE
        assert "code" in result.rerun
        assert not _check(result, "verification").passed

    @pytest.mark.unit
    def test_an_empty_channel_without_a_control_is_rerun(self) -> None:
        """
        Given discourse returned nothing and ran no control
        Then it is rerun, because nothing shows it could have found anything
        """
        session = _session(
            ["code", "discourse"],
            [*_clean("code"), _query("discourse", 0)],
            [_finding("code")],
        )
        assert verify_context(session, passes_run=1).rerun == ("discourse",)

    @pytest.mark.unit
    def test_a_productive_channel_without_a_control_passes(self) -> None:
        """
        Given discourse returned findings without a control
        Then it is not rerun: results prove the channel could search
        """
        session = _session(
            ["code", "discourse"],
            [*_clean("code"), _query("discourse", 2)],
            [_finding("code"), _finding("discourse")],
        )
        assert verify_context(session, passes_run=1).rerun == ()


class TestAVenueMismatchIsReformulated:
    @pytest.mark.unit
    def test_mismatch_reformulates_the_empty_channel(self) -> None:
        """
        Given code holds every finding
        And discourse proved it can retrieve and came back empty
        Then CONTINUE, reformulating discourse rather than rerunning it

            Rerunning the same query in the wrong vocabulary returns
            the same nothing. The frontier verdict names this case.
        """
        session = _session(
            ["code", "discourse"],
            [*_clean("code", 9), *_clean("discourse", 0)],
            [_finding("code", i) for i in range(9)],
        )
        result = verify_context(session, passes_run=1)
        assert result.conclusion == CONTINUE
        assert result.reformulate == ("discourse",)
        assert result.rerun == ()
        assert not _check(result, "ambiguity").passed


class TestAThinFieldUsesEveryRetrievalChannel:
    @pytest.mark.unit
    def test_thin_candidate_adds_unplanned_retrieval_channels(self) -> None:
        """
        Given a light plan (code, discourse) came back controlled-empty
        Then CONTINUE, adding academic before a thin field is reported

            OctoTools' verifier asks whether an unused tool could help.
            A thin field claimed without the academic channel ever
            looking is the case where the answer is yes.
        """
        session = _session(
            ["code", "discourse"], [*_clean("code", 0), *_clean("discourse", 0)]
        )
        result = verify_context(session, passes_run=1)
        assert result.conclusion == CONTINUE
        assert result.add == ("academic",)
        assert not _check(result, "unused_channels").passed

    @pytest.mark.unit
    def test_generative_channels_are_never_added(self) -> None:
        """
        Given every retrieval channel ran and came back controlled-empty
        Then nothing is added: triz output cannot testify about absence
        """
        channels = ["code", "discourse", "academic"]
        session = _session(channels, [log for c in channels for log in _clean(c, 0)])
        result = verify_context(session, passes_run=1)
        assert result.add == ()
        assert result.conclusion == STOP


class TestTheBudgetBoundsTheLoop:
    @pytest.mark.unit
    def test_budget_exhausted_stops_with_work_outstanding(self) -> None:
        """
        Given discourse failed
        When verified on the last allowed pass
        Then STOP, still listing discourse so the report can name the gap
        """
        session = _session(
            ["code", "discourse"],
            [
                *_clean("code"),
                _canary("discourse"),
                _query("discourse", 0, "rate_limit"),
            ],
            [_finding("code")],
        )
        result = verify_context(session, passes_run=2, max_passes=2)
        assert result.conclusion == STOP
        assert result.rerun == ("discourse",)
        assert not _check(result, "budget").passed
        assert "discourse" in result.reason

    @pytest.mark.unit
    @pytest.mark.parametrize(("passes_run", "max_passes"), [(0, 2), (1, 0)])
    def test_nonsense_counters_are_refused(
        self, passes_run: int, max_passes: int
    ) -> None:
        """
        Given the verifier runs after a pass, with at least one allowed
        Then zero passes run, or a zero budget, is a caller bug
        """
        session = _session(["code"], _clean("code"), [_finding("code")])
        with pytest.raises(ValueError):
            verify_context(session, passes_run=passes_run, max_passes=max_passes)


class TestADegradedChannelIsRerun:
    @pytest.mark.unit
    def test_a_fallback_answered_channel_is_rerun(self) -> None:
        """
        Given academic had one failed query and one that returned results
        Then it is degraded, not clean, and is rerun

            Its findings are real, but the coverage is not what was
            asked for, and the frontier verdict will not count it.
        """
        session = _session(
            ["code", "academic"],
            [
                *_clean("code"),
                _canary("academic"),
                _query("academic", 0, "source_error"),
                _query("academic", 4),
            ],
            [_finding("code"), _finding("academic")],
        )
        result = verify_context(session, passes_run=1)
        assert result.rerun == ("academic",)
        assert "degraded" in _check(result, "completeness").detail
