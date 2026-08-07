"""A frontier finding should land in triage, not evaporate.

Feature: Gaps become candidate research stories a human can dispose of.

As someone running research across many topics
I want each gap surfaced as a story with its evidence
So that I can act on it, defer it to an issue, or decline it on record

A verdict alone tells you about one session and is gone when the report
scrolls past. The gaps a verdict is computed from are the interesting
part: a controlled channel that came back empty is a candidate research
direction, and a channel that failed its control is a maintenance task.
Both deserve to reach a backlog rather than a paragraph.

Dispositions stay `undecided` here on purpose. The discourse research
found no argument against the position that characterizing a field is
human work and a tool should report what it searched. A tool that filed
its own conclusions as decided work would be taking exactly the step
that position rules out. It proposes; a person disposes.
"""

from __future__ import annotations

import pytest

from tome.models import Finding, QueryLog, ResearchSession
from tome.synthesis.frontier import CANARY_SOURCE, UNDECIDED, frontier_stories


def _canary(channel: str, *, found: bool = True) -> QueryLog:
    return QueryLog(
        channel=channel,
        query="known-indexed target",
        source=CANARY_SOURCE,
        result_count=1 if found else 0,
    )


def _session(channels, logs, findings=None) -> ResearchSession:
    return ResearchSession(
        topic="canary queries for retrieval health",
        domain="d",
        triz_depth="light",
        channels=list(channels),
        findings=list(findings or []),
        query_log=list(logs),
    )


class TestStoriesFromGaps:
    """Feature: Each gap kind produces its own candidate story."""

    @pytest.mark.unit
    def test_controlled_empty_channel_becomes_a_research_story(self) -> None:
        """Scenario: A proven-empty channel is a research direction.

        Given a channel that proved it can retrieve and found nothing
        When stories are generated
        Then one story names that channel and carries the topic
        Because this is the only gap kind that points at the world
             rather than at the tooling, which is what makes it worth
             a backlog slot.
        """
        session = _session(
            ["academic"],
            [_canary("academic"), QueryLog("academic", "q", "arxiv", result_count=0)],
        )
        stories = frontier_stories(session)
        assert any(s.kind == "thin-field-candidate" for s in stories)
        assert any("academic" in s.evidence for s in stories)

    @pytest.mark.unit
    def test_failed_control_becomes_a_maintenance_story(self) -> None:
        """Scenario: A blind channel is a tooling task, not a research one.

        Given a channel whose control failed
        Then a story of kind blind-channel exists
        Because filing this beside a research direction would invite
             someone to read a broken scraper as a finding about a
             field, which is the confusion the whole module removes.
        """
        session = _session(
            ["code"],
            [
                _canary("code", found=False),
                QueryLog("code", "q", "github", result_count=0),
            ],
        )
        assert any(s.kind == "blind-channel" for s in frontier_stories(session))

    @pytest.mark.unit
    def test_uncontrolled_channel_becomes_an_instrumentation_story(self) -> None:
        """Scenario: A channel with no control is an instrumentation gap."""
        session = _session(["code"], [QueryLog("code", "q", "github", result_count=0)])
        assert any(s.kind == "uncontrolled-channel" for s in frontier_stories(session))

    @pytest.mark.unit
    def test_covered_topic_produces_no_stories(self) -> None:
        """Scenario: Nothing to triage when nothing is missing.

        Given every channel returned findings under a passing control
        Then no stories are produced
        Because a backlog that fills up on healthy runs is one nobody
             reads.
        """
        session = _session(
            ["code"],
            [_canary("code"), QueryLog("code", "q", "github", result_count=2)],
            [
                Finding(
                    source="s",
                    channel="code",
                    title="t",
                    url="https://example.com/a",
                    relevance=0.5,
                    summary="s",
                )
            ],
        )
        assert frontier_stories(session) == []


class TestDispositionIsTheHumansCall:
    """Feature: The tool proposes; it does not decide."""

    @pytest.mark.unit
    def test_every_story_starts_undecided(self) -> None:
        """Scenario: No story arrives pre-triaged.

        Given any generated story
        Then its disposition is undecided
        Because act, defer and decline are judgments about what is
             worth this project's time, and nothing in a search record
             supports making them.
        """
        session = _session(
            ["academic"],
            [_canary("academic"), QueryLog("academic", "q", "arxiv", result_count=0)],
        )
        assert all(s.disposition == UNDECIDED for s in frontier_stories(session))

    @pytest.mark.unit
    def test_story_carries_a_suggested_next_action(self) -> None:
        """Scenario: A story says what acting on it would mean.

        Given a generated story
        Then it names a concrete next action
        Because "there is a gap here" is not triageable. A reader
             deciding between act, defer and decline needs to know
             what act would cost.
        """
        session = _session(
            ["academic"],
            [_canary("academic"), QueryLog("academic", "q", "arxiv", result_count=0)],
        )
        assert all(s.next_action for s in frontier_stories(session))
