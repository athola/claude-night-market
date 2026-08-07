"""A generated analogy is not evidence that a field is well published.

Feature: Only channels that retrieve may testify about what exists.

As someone asking whether a topic is thin
I want the verdict computed from channels that searched an index
So that invented cross-domain analogies cannot vote on the literature

Three of tome's channels probe an external index: ``academic`` reads
arXiv and Semantic Scholar, ``code`` reads GitHub, ``discourse`` reads
Hacker News and friends. Their silence is a fact about the world, once
a control proves they were not blind.

``triz`` is different in kind. It generates cross-domain analogies with
open-web search; its findings are proposals, not retrieved records of
prior work. Counting them alongside retrieved ones lets the tool
manufacture the evidence that a field is covered. Three invented
analogies are enough to push a genuinely thin topic past the sparsity
threshold, and the resulting ``COVERED`` reads exactly like one earned
by finding eight real papers.

The same asymmetry applies to controls. A positive control asks whether
a channel can retrieve a document known to be in its index. ``triz``
has no index, so the question is not merely unanswered for it, it is
malformed. Demanding one would pin every session to ``INCONCLUSIVE``
for a reason that says nothing about coverage.
"""

from __future__ import annotations

from tome.models import Finding, QueryLog, ResearchSession
from tome.synthesis.frontier import (
    CANARY_SOURCE,
    INCONCLUSIVE,
    THIN_CANDIDATE,
    frontier_verdict,
)


def _canary(channel: str, *, found: bool = True) -> QueryLog:
    return QueryLog(
        channel=channel,
        query="known-indexed target",
        source=CANARY_SOURCE,
        result_count=1 if found else 0,
    )


def _empty_search(channel: str) -> QueryLog:
    return QueryLog(channel=channel, query="topic terms", source=channel)


def _finding(channel: str, title: str) -> Finding:
    return Finding(
        title=title,
        url=f"https://example.invalid/{title}",
        channel=channel,
        source=channel,
        summary="",
        relevance=0.5,
    )


def _session(channels, logs, findings=None) -> ResearchSession:
    return ResearchSession(
        topic="a topic nobody has written about",
        domain="software",
        triz_depth="none",
        channels=list(channels),
        query_log=list(logs),
        findings=list(findings or []),
    )


class TestGeneratedFindingsDoNotVoteOnCoverage:
    """Scenario: TRIZ analogies must not mask a thin field."""

    def test_triz_findings_do_not_suppress_a_thin_field_verdict(self) -> None:
        """
        Given two retrieval channels that passed controls and found nothing
        And four TRIZ analogies, enough to exceed the sparsity threshold
        Then the verdict is still THIN_FIELD_CANDIDATE

            The retrieval evidence is unchanged by how many analogies
            the generative channel produced. If four invented bridges
            can flip this verdict, the tool is grading the field on
            output it wrote itself.
        """
        session = _session(
            channels=["academic", "code", "triz"],
            logs=[
                _canary("academic"),
                _empty_search("academic"),
                _canary("code"),
                _empty_search("code"),
                QueryLog(
                    channel="triz",
                    query="cross-domain bridges",
                    source="triz",
                    result_count=4,
                ),
            ],
            findings=[_finding("triz", f"bridge-{i}") for i in range(4)],
        )

        assert frontier_verdict(session).verdict == THIN_CANDIDATE

    def test_triz_present_but_silent_does_not_force_inconclusive(self) -> None:
        """
        Given two controlled retrieval channels that came back empty
        And TRIZ planned but with no query record at all
        Then the verdict is THIN_FIELD_CANDIDATE

            A planned channel with no record reads ``unknown``, which
            is grounds for INCONCLUSIVE when the channel was supposed
            to search an index. TRIZ was not, so a missing record from
            it is not missing retrieval evidence.
        """
        session = _session(
            channels=["academic", "code", "triz"],
            logs=[
                _canary("academic"),
                _empty_search("academic"),
                _canary("code"),
                _empty_search("code"),
            ],
        )

        assert frontier_verdict(session).verdict == THIN_CANDIDATE

    def test_retrieved_findings_still_suppress_a_thin_field_verdict(self) -> None:
        """
        Given the same two controlled channels
        And four findings retrieved by one of them
        Then the verdict is not THIN_FIELD_CANDIDATE

            The negative half of the pair. Discounting TRIZ must not
            become discounting evidence in general, or the verdict
            reaches THIN_FIELD_CANDIDATE for well-covered topics.
        """
        session = _session(
            channels=["academic", "code", "triz"],
            logs=[
                _canary("academic"),
                QueryLog(
                    channel="academic",
                    query="topic terms",
                    source="academic",
                    result_count=4,
                ),
                _canary("code"),
                _empty_search("code"),
            ],
            findings=[_finding("academic", f"paper-{i}") for i in range(4)],
        )

        assert frontier_verdict(session).verdict != THIN_CANDIDATE


class TestControlsAreOnlyDemandedOfRetrievalChannels:
    """Scenario: A channel with no index cannot fail an index probe."""

    def test_triz_without_a_control_does_not_force_inconclusive(self) -> None:
        """
        Given two retrieval channels with passing controls and no results
        And TRIZ present, with no control and nothing to show
        Then the verdict is THIN_FIELD_CANDIDATE, not INCONCLUSIVE

            TRIZ has no index to probe, so its missing control is not a
            gap in the evidence. Treating it as one would make every
            session inconclusive for a reason unrelated to coverage.
        """
        session = _session(
            channels=["academic", "code", "triz"],
            logs=[
                _canary("academic"),
                _empty_search("academic"),
                _canary("code"),
                _empty_search("code"),
                _empty_search("triz"),
            ],
        )

        assert frontier_verdict(session).verdict == THIN_CANDIDATE

    def test_a_retrieval_channel_without_a_control_still_forces_inconclusive(
        self,
    ) -> None:
        """
        Given one controlled channel and one retrieval channel with no control
        And both came back empty
        Then the verdict is INCONCLUSIVE

            The negative half. Exempting TRIZ must not leak into
            exempting channels that do have an index, which is the
            uncontrolled-channel hole the control mechanism closed.
        """
        session = _session(
            channels=["academic", "discourse"],
            logs=[
                _canary("academic"),
                _empty_search("academic"),
                _empty_search("discourse"),
            ],
        )

        assert frontier_verdict(session).verdict == INCONCLUSIVE
