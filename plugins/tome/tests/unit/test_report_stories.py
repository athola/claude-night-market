"""A gap the reader cannot triage is a gap that scrolls away.

Feature: The report ends with candidate stories a human can dispose of.

As someone running research across many topics
I want each gap named, evidenced, and offered for a decision
So that I can act on it, defer it to an issue, or decline it on record

``frontier_stories`` was built, tested, and referenced by nothing. The
verdict reached the page and the gaps behind it did not, so every run
produced findings a reader could act on and gaps that survived only as
long as the terminal buffer.

Two properties are tested here rather than the prose around them.

**Dispositions arrive undecided.** The discourse research turned up no
argument against the position that characterizing a field is human
work and a tool should report what it searched. A tool that filed its
own conclusions as decided work would take exactly the step that
position rules out.

**A clean run adds nothing.** A backlog that fills up when nothing is
wrong is a backlog nobody reads, which costs more than the section is
worth.
"""

from __future__ import annotations

from tome.models import Finding, QueryLog, ResearchSession
from tome.output.report import format_report
from tome.synthesis.frontier import ACT, CANARY_SOURCE, DECLINE, DEFER


def _canary(channel: str, *, found: bool = True) -> QueryLog:
    return QueryLog(
        channel=channel,
        query="known-indexed target",
        source=CANARY_SOURCE,
        result_count=1 if found else 0,
    )


def _search(channel: str, count: int = 0) -> QueryLog:
    return QueryLog(
        channel=channel, query="topic terms", source=channel, result_count=count
    )


def _finding(channel: str, title: str) -> Finding:
    return Finding(
        source=channel,
        channel=channel,
        title=title,
        url=f"https://example.invalid/{title}",
        relevance=0.6,
        summary="",
    )


def _session(channels, logs, findings=None) -> ResearchSession:
    return ResearchSession(
        topic="frontier detection in research tooling",
        domain="software",
        triz_depth="none",
        channels=list(channels),
        query_log=list(logs),
        findings=list(findings or []),
    )


class TestGapsReachThePage:
    """Scenario: A run with gaps offers them for triage."""

    def _thin_session(self) -> ResearchSession:
        return _session(
            channels=["academic", "code"],
            logs=[
                _canary("academic"),
                _search("academic"),
                _canary("code"),
                _search("code"),
            ],
        )

    def test_a_thin_result_produces_a_story_section(self) -> None:
        """
        Given two controlled channels that came back empty
        Then the report carries a research stories section
        """
        report = format_report(self._thin_session())
        assert "Research Stories" in report

    def test_the_story_carries_its_evidence_and_next_action(self) -> None:
        """
        Given a story on the page
        Then the evidence and the next action are both printed

            A title alone is a conclusion. The reader disposing of it
            needs to see what it rests on, or the triage decision is
            made on the tool's say-so.
        """
        report = format_report(self._thin_session())
        assert "thin-field-candidate" in report
        assert "reformulated" in report.lower()

    def test_every_disposition_is_offered_to_the_reader(self) -> None:
        """
        Given a story on the page
        Then act, defer and decline are all named as choices

            The story is a question put to a person. Printing it
            without the available answers makes it an announcement.
        """
        report = format_report(self._thin_session())
        for disposition in (ACT, DEFER, DECLINE):
            assert disposition in report, f"{disposition!r} is not offered"

    def test_a_story_arrives_undecided(self) -> None:
        """
        Given a story the tool generated
        Then it is marked undecided rather than pre-triaged

            The tool proposes; a person disposes. A story that arrived
            already marked act would be the tool filing its own
            conclusion as work.
        """
        report = format_report(self._thin_session())
        assert "undecided" in report

    def test_a_broken_channel_is_filed_as_maintenance_not_research(self) -> None:
        """
        Given a channel that failed its positive control
        Then its story is the blind-channel kind

            A broken scraper and a thin field route to different
            people. Filing them under one heading invites a reader to
            take a tooling defect for a finding about the world.
        """
        report = format_report(
            _session(
                channels=["academic", "code"],
                logs=[
                    _canary("academic"),
                    _search("academic"),
                    _canary("code", found=False),
                    _search("code"),
                ],
            )
        )
        assert "blind-channel" in report


class TestAHealthyRunStaysQuiet:
    """Scenario: Nothing missing, nothing filed."""

    def test_a_covered_topic_produces_no_story_section(self) -> None:
        """
        Given every channel controlled, searching cleanly, with findings
        Then no research stories section appears

            The negative control for the whole feature. A section that
            renders on every run trains the reader to skip it, which
            costs exactly the attention the gaps needed.
        """
        report = format_report(
            _session(
                channels=["academic", "code"],
                logs=[
                    _canary("academic"),
                    _search("academic", count=3),
                    _canary("code"),
                    _search("code", count=3),
                ],
                findings=[
                    _finding("academic", "paper-1"),
                    _finding("academic", "paper-2"),
                    _finding("code", "repo-1"),
                    _finding("code", "repo-2"),
                ],
            )
        )
        assert "Research Stories" not in report
