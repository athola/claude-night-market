"""A claim about a thin field requires a channel that proved it can see.

Feature: Frontier verdict, gated on positive controls.

As someone deciding whether a topic is unexplored
I want the verdict to depend on channels that demonstrated they work
So that a broken search cannot masquerade as an empty field

The verdict rule this file pins was revised by research before it was
written. The original gated the strong verdict on a minimum query count
per channel, which counts effort without assessing it: three queries
built from the same wrong root word are one query. Analytical chemistry
supplies the replacement, where a batch is not reportable unless a
positive control demonstrated the instrument could detect what it was
looking for. A canary query whose target is known to be indexed is that
control, and its value is that it is measured independently of how many
results the real query returned. See ADR-0020.

The strongest verdict available is deliberately named
THIN_FIELD_CANDIDATE. It claims the search was well formed enough to
deserve a human look, never that the literature is empty.
"""

from __future__ import annotations

import pytest

from tome.models import Finding, QueryLog, ResearchSession
from tome.synthesis.frontier import (
    CANARY_SOURCE,
    COVERED,
    INCONCLUSIVE,
    MISMATCH_SUSPECTED,
    THIN_CANDIDATE,
    canary_outcomes,
    frontier_verdict,
)
from tome.synthesis.quality import channel_outcomes


def _finding(channel: str, n: int = 0) -> Finding:
    return Finding(
        source="s",
        channel=channel,
        title=f"t{n}",
        url=f"https://example.com/{channel}/{n}",
        relevance=0.5,
        summary="s",
    )


def _canary(channel: str, *, found: bool = True, error: str | None = None) -> QueryLog:
    return QueryLog(
        channel=channel,
        query="a query whose target is known to be indexed",
        source=CANARY_SOURCE,
        result_count=1 if found else 0,
        error=error,
    )


def _session(channels, logs, findings=None) -> ResearchSession:
    return ResearchSession(
        topic="t",
        domain="d",
        triz_depth="light",
        channels=list(channels),
        findings=list(findings or []),
        query_log=list(logs),
    )


class TestCanaryIsNotATopicResult:
    """Feature: A control never counts as a finding about the topic."""

    @pytest.mark.unit
    def test_canary_results_do_not_make_a_channel_ok(self) -> None:
        """Scenario: A passing canary on an empty topic search stays empty.

        Given a channel whose canary retrieved its known target
        And whose topic queries returned nothing
        When the channel outcome is derived
        Then the channel is empty, not ok
        Because the canary proves the instrument works; it says nothing
             about the topic. Counting its hit as a topic result would
             make every working channel look productive and destroy the
             signal the control exists to create.
        """
        session = _session(
            ["code"],
            [_canary("code"), QueryLog("code", "topic", "github", result_count=0)],
        )
        assert channel_outcomes(session)["code"] == "empty"

    @pytest.mark.unit
    def test_failing_canary_does_not_mark_the_topic_search_failed(self) -> None:
        """Scenario: A failed control does not corrupt the topic outcome.

        Given a channel whose canary failed
        And whose topic queries ran cleanly and found nothing
        Then the topic outcome is still empty
        Because the two are separate measurements. The canary's verdict
             is reported through canary_outcomes, and mixing it into the
             topic outcome would collapse the independence that makes a
             control worth running.
        """
        session = _session(
            ["code"],
            [
                _canary("code", found=False),
                QueryLog("code", "topic", "github", result_count=0),
            ],
        )
        assert channel_outcomes(session)["code"] == "empty"


class TestCanaryOutcomes:
    """Feature: Controls report pass, fail, or absent."""

    @pytest.mark.unit
    def test_retrieved_target_passes(self) -> None:
        """Scenario: The channel found what it was known to hold."""
        assert canary_outcomes(_session(["code"], [_canary("code")]))["code"] == "pass"

    @pytest.mark.unit
    def test_missed_target_fails(self) -> None:
        """Scenario: The channel could not find a document it indexes.

        Given a canary that returned nothing
        Then the control fails
        Because a channel that cannot retrieve a document known to be
             in its index is not reporting on the world.
        """
        session = _session(["code"], [_canary("code", found=False)])
        assert canary_outcomes(session)["code"] == "fail"

    @pytest.mark.unit
    def test_no_canary_is_absent_not_pass(self) -> None:
        """Scenario: An unrun control is not a passing one.

        Given a channel with no canary log
        Then the control is absent
        Because treating a missing control as a pass is how an
             uninstrumented run acquires the authority of an
             instrumented one.
        """
        session = _session(["code"], [QueryLog("code", "q", "github", result_count=1)])
        assert canary_outcomes(session)["code"] == "absent"


class TestFrontierVerdict:
    """Feature: The verdict, gated on controls."""

    @pytest.mark.unit
    def test_thin_candidate_requires_two_passing_controls(self) -> None:
        """Scenario: Two proven channels came back empty.

        Given two channels whose canaries passed
        And both searched the topic cleanly and found nothing
        Then the verdict is THIN_FIELD_CANDIDATE
        """
        session = _session(
            ["code", "academic"],
            [
                _canary("code"),
                _canary("academic"),
                QueryLog("code", "q", "github", result_count=0),
                QueryLog("academic", "q", "arxiv", result_count=0),
            ],
        )
        assert frontier_verdict(session).verdict == THIN_CANDIDATE

    @pytest.mark.unit
    def test_absent_control_cannot_support_thin_candidate(self) -> None:
        """Scenario: Uninstrumented emptiness is inconclusive.

        Given two channels that searched cleanly and found nothing
        And neither ran a canary
        Then the verdict is INCONCLUSIVE, not THIN_FIELD_CANDIDATE
        Because this is the whole revision. Without a control there is
             no evidence the channels could have found anything, and
             the count of empty queries cannot supply it.
        """
        session = _session(
            ["code", "academic"],
            [
                QueryLog("code", "q", "github", result_count=0),
                QueryLog("academic", "q", "arxiv", result_count=0),
            ],
        )
        assert frontier_verdict(session).verdict == INCONCLUSIVE

    @pytest.mark.unit
    def test_failing_control_forces_inconclusive(self) -> None:
        """Scenario: A blind channel voids the claim.

        Given one channel whose canary failed
        Then the verdict is INCONCLUSIVE whatever the counts say
        """
        session = _session(
            ["code", "academic"],
            [
                _canary("code"),
                _canary("academic", found=False),
                QueryLog("code", "q", "github", result_count=0),
                QueryLog("academic", "q", "arxiv", result_count=0),
            ],
        )
        assert frontier_verdict(session).verdict == INCONCLUSIVE

    @pytest.mark.unit
    def test_broken_channel_forces_inconclusive(self) -> None:
        """Scenario: An outage voids the claim."""
        session = _session(
            ["code", "academic"],
            [
                _canary("code"),
                _canary("academic"),
                QueryLog("code", "q", "github", result_count=0),
                QueryLog("academic", "q", "arxiv", error="rate_limit"),
            ],
        )
        assert frontier_verdict(session).verdict == INCONCLUSIVE

    @pytest.mark.unit
    def test_legacy_session_is_inconclusive(self) -> None:
        """Scenario: A session with no record claims nothing.

        Given a session persisted before query logging
        Then the verdict is INCONCLUSIVE
        Because unknown channels carry no evidence in either
             direction, and this is the negative control that must
             never yield a claim about a field.
        """
        assert frontier_verdict(_session(["code"], [])).verdict == INCONCLUSIVE

    @pytest.mark.unit
    def test_skew_with_a_proven_empty_channel_suspects_mismatch(self) -> None:
        """Scenario: One channel carried everything, another proved empty.

        Given code holds every finding
        And academic passed its control and found nothing
        Then the verdict is CHANNEL_MISMATCH_SUSPECTED
        Because a topic that lives in one channel and not another is
             more often a vocabulary or venue mismatch than a thin
             field, and the two deserve different next actions.
        """
        session = _session(
            ["code", "academic"],
            [
                _canary("code"),
                _canary("academic"),
                QueryLog("code", "q", "github", result_count=5),
                QueryLog("academic", "q", "arxiv", result_count=0),
            ],
            [_finding("code", n) for n in range(5)],
        )
        assert frontier_verdict(session).verdict == MISMATCH_SUSPECTED

    @pytest.mark.unit
    def test_findings_everywhere_is_covered(self) -> None:
        """Scenario: Both channels produced results."""
        session = _session(
            ["code", "academic"],
            [
                _canary("code"),
                _canary("academic"),
                QueryLog("code", "q", "github", result_count=3),
                QueryLog("academic", "q", "arxiv", result_count=3),
            ],
            [_finding("code", 1), _finding("academic", 2)],
        )
        assert frontier_verdict(session).verdict == COVERED

    @pytest.mark.unit
    def test_verdict_carries_its_reason(self) -> None:
        """Scenario: Every verdict explains itself.

        Given any session
        Then the verdict carries a non-empty reason naming the evidence
        Because a bare label is exactly the confident-looking output
             this work exists to avoid, and a reader who cannot see why
             cannot disagree.
        """
        result = frontier_verdict(_session(["code"], []))
        assert result.reason
        assert result.evidence
