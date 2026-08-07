"""A channel that produced nothing must appear in the report.

Feature: The report shows what was searched, not only what was found.

As someone deciding from a research report
I want a planned channel that returned nothing to say so, and say why
So that I do not read a broken search as a finding about the field

``format_report`` skipped any channel with no findings: no heading, no
note, nothing. The only trace was the planned-channel list in the
metadata line, so a reader had to diff that list against the headings
to notice a gap, and even then could not tell an outage from a thin
topic.

These tests hold the two halves of the fix. A planned channel always
gets a heading, and the note under it distinguishes the outcomes.
"""

from __future__ import annotations

import pytest

from tome.models import Finding, QueryLog, ResearchSession
from tome.output.report import _EMPTY_CHANNEL_NOTES, format_report


def _finding(channel: str = "code") -> Finding:
    return Finding(
        source="github",
        channel=channel,
        title=f"A {channel} result",
        url=f"https://example.com/{channel}",
        relevance=0.8,
        summary="A summary.",
    )


def _session(channels: list[str], logs: list[QueryLog], findings: list[Finding]):
    return ResearchSession(
        topic="a topic",
        domain="software",
        triz_depth="light",
        channels=channels,
        findings=findings,
        query_log=logs,
    )


class TestEmptyChannelIsVisible:
    """Feature: A planned channel that found nothing is still reported."""

    @pytest.mark.unit
    def test_planned_channel_with_no_findings_gets_a_heading(self) -> None:
        """Scenario: An empty academic channel still appears.

        Given academic was planned and returned nothing
        When the report is rendered
        Then the Academic Literature heading is present
        Because a heading that vanishes when a channel fails makes the
             failure invisible; the reader sees a report about code and
             has no way to know academic was ever attempted.
        """
        session = _session(
            ["code", "academic"],
            [
                QueryLog("code", "q", "github", result_count=1),
                QueryLog("academic", "q", "arxiv", result_count=0),
            ],
            [_finding("code")],
        )
        assert "Academic Literature" in format_report(session)

    @pytest.mark.unit
    def test_empty_and_error_notes_differ(self) -> None:
        """Scenario: The reason a channel is empty reaches the page.

        Given one session where academic searched and found nothing
        And another where academic could not be searched at all
        When both reports are rendered
        Then the text under the Academic Literature heading differs
        Because these carry opposite instructions. One is weak evidence
             about the topic; the other is no evidence at all.
        """
        empty = _session(
            ["academic"],
            [QueryLog("academic", "q", "arxiv", result_count=0)],
            [],
        )
        broken = _session(
            ["academic"],
            [QueryLog("academic", "q", "arxiv", error="source_error")],
            [],
        )
        assert format_report(empty) != format_report(broken)

    @pytest.mark.unit
    def test_error_note_refuses_the_absence_reading(self) -> None:
        """Scenario: A failed channel does not license a claim.

        Given a channel whose queries all errored
        When the report is rendered
        Then the note says absence here is not evidence about the field
        Because this is the sentence that stops a reader turning an
             outage into a conclusion, which is the whole defect.
        """
        broken = _session(
            ["academic"],
            [QueryLog("academic", "q", "arxiv", error="source_error")],
            [],
        )
        assert "not evidence" in format_report(broken).lower()

    @pytest.mark.unit
    def test_unknown_channel_does_not_claim_a_thin_field(self) -> None:
        """Scenario: No query record produces no claim about the topic.

        Given a planned channel with no query log at all
        When the report is rendered
        Then the note does not assert the field is thin
        Because a session predating query logging holds no evidence,
             and the report must not invent some.
        """
        legacy = _session(["academic"], [], [])
        text = format_report(legacy).lower()
        assert "no query record" in text
        assert "genuinely thin" not in text


class TestEveryOutcomeIsRenderable:
    """Feature: No channel status can crash the report."""

    @pytest.mark.unit
    def test_ok_channel_whose_findings_all_dropped_renders(self) -> None:
        """Scenario: A channel returned results but none survived.

        Given a channel whose queries returned results
        And no finding for it survived synthesis
        When the report is rendered
        Then it renders rather than raising
        Because cross-channel deduplication keeps one finding per URL,
             so a channel can legitimately lose every finding to a
             sibling that reported the same source first. The status is
             still `ok` because the search worked, and the first version
             of the empty-channel note had no entry for `ok` and died
             with a KeyError on a real path.
        """
        session = _session(
            ["code"], [QueryLog("code", "q", "github", result_count=5)], []
        )
        assert "Code Implementations" in format_report(session)

    @pytest.mark.unit
    def test_every_derivable_status_has_a_note(self) -> None:
        """Scenario: The note table covers the status vocabulary.

        Given the set of statuses channel_outcomes can return
        When the empty-channel note table is checked
        Then every status has an entry
        Because adding a seventh status later would otherwise crash the
             report on the first session that produced it, and the
             crash would land in rendering rather than in derivation.
        """
        derivable = {"ok", "empty", "error", "rate_limited", "degraded", "unknown"}
        assert derivable <= set(_EMPTY_CHANNEL_NOTES)


class TestCoverageSection:
    """Feature: Gap analysis reaches the page it was written for."""

    @pytest.mark.unit
    def test_report_has_a_coverage_section(self) -> None:
        """Scenario: Coverage and Gaps is rendered.

        Given any session
        When the report is rendered
        Then a Coverage and Gaps section is present
        Because identify_gaps has existed and been tested since it was
             written and no caller ever put its output in front of a
             reader.
        """
        session = _session(
            ["code"], [QueryLog("code", "q", "github", result_count=1)], [_finding()]
        )
        assert "Coverage and Gaps" in format_report(session)

    @pytest.mark.unit
    def test_cleanly_empty_channel_is_not_listed_as_unsearchable(self) -> None:
        """Scenario: An empty channel is not called a failed one.

        Given academic searched cleanly and found nothing
        And discourse was rate-limited
        When the coverage summary is rendered
        Then only discourse is named as not cleanly searched
        Because the first version filtered on "not ok", which swept
             `empty` in with the failures. The report then told the
             reader that absence in academic proved nothing, three
             paragraphs above the section correctly calling it weak
             evidence about the topic. The page contradicted itself.
        """
        session = _session(
            ["academic", "discourse"],
            [
                QueryLog("academic", "q", "arxiv", result_count=0),
                QueryLog("discourse", "q", "hn", error="rate_limit"),
            ],
            [],
        )
        summary = format_report(session).split("## Code Implementations")[0]
        unsearchable = [
            line for line in summary.splitlines() if "could not be searched" in line
        ]
        joined = " ".join(unsearchable)
        assert "discourse" in joined
        assert "academic" not in joined

    @pytest.mark.unit
    def test_quality_score_is_not_printed(self) -> None:
        """Scenario: The search-quality score stays out of the report.

        Given a session whose report includes coverage information
        When the report is rendered
        Then no composite quality score appears
        Because that score blends channel coverage, source diversity
             and mean relevance, all properties of the search. Printing
             it beside a statement about the field invites a reader to
             read a bad search as a thin topic, which is the exact
             confusion this section exists to remove.
        """
        session = _session(
            ["code"], [QueryLog("code", "q", "github", result_count=1)], [_finding()]
        )
        assert "quality score" not in format_report(session).lower()
