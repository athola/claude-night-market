"""
Feature: Research report formatting

As a researcher reading tome output
I want well-structured markdown reports from a research session
So that I can quickly understand findings and decide on next steps
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from tome.models import Finding, ResearchSession
from tome.output.report import (
    format_brief,
    format_report,
    format_transcript,
    generate_executive_summary,
)


def _make_session(
    findings: list[Finding] | None = None,
    channels: list[str] | None = None,
    topic: str = "async python patterns",
) -> ResearchSession:
    return ResearchSession(
        id="test-session-001",
        topic=topic,
        domain="algorithm",
        triz_depth="medium",
        channels=channels or ["code", "discourse", "academic"],
        findings=findings or [],
        status="complete",
        created_at=datetime(2026, 3, 20, tzinfo=timezone.utc),
    )


def _code_finding(url: str = "https://github.com/example/lib") -> Finding:
    return Finding(
        source="github",
        channel="code",
        title="example/async-lib",
        url=url,
        relevance=0.85,
        summary="Async patterns library with 2.1k stars.",
        metadata={"stars": 2100, "language": "Python"},
    )


def _discourse_finding(url: str = "https://news.ycombinator.com/item?id=99") -> Finding:
    return Finding(
        source="hn",
        channel="discourse",
        title="Why async/await is better",
        url=url,
        relevance=0.72,
        summary="Discussion on async patterns, 200 points.",
        metadata={"score": 200, "comments": 85},
    )


def _academic_finding(url: str = "https://arxiv.org/abs/2301.12345") -> Finding:
    return Finding(
        source="arxiv",
        channel="academic",
        title="A Survey of Asynchronous Programming Models",
        url=url,
        relevance=0.90,
        summary="Survey of async models across languages.",
        metadata={"authors": ["Smith, J.", "Doe, A."], "year": 2023, "citations": 45},
    )


def _triz_finding(url: str = "https://triz-journal.com/article") -> Finding:
    return Finding(
        source="triz",
        channel="triz",
        title="TRIZ Contradiction Matrix Applied to Concurrency",
        url=url,
        relevance=0.78,
        summary="Cross-domain concurrency insights from TRIZ.",
        metadata={},
    )


class TestFormatReport:
    """
    Feature: Full markdown report generation

    As a researcher
    I want a complete, sectioned markdown report
    So that I can read findings organized by channel
    """

    @pytest.mark.unit
    def test_report_includes_topic_in_heading(self) -> None:
        """
        Scenario: Report heading contains the session topic
        Given a session on 'async python patterns'
        When format_report is called
        Then the output contains a level-1 heading with the topic
        """
        session = _make_session()
        report = format_report(session)
        assert "async python patterns" in report
        assert report.strip().startswith("#")

    @pytest.mark.unit
    def test_report_includes_all_channel_sections_for_full_session(self) -> None:
        """
        Scenario: All four channels have findings
        Given a session with code, discourse, academic, and triz findings
        When format_report is called
        Then headings for all four channel sections appear
        """
        session = _make_session(
            findings=[
                _code_finding(),
                _discourse_finding(),
                _academic_finding(),
                _triz_finding(),
            ],
            channels=["code", "discourse", "academic", "triz"],
        )
        report = format_report(session)
        assert "Code" in report or "Implementation" in report
        assert "Community" in report or "Discourse" in report or "Perspective" in report
        assert "Academic" in report or "Literature" in report
        assert "TRIZ" in report or "Cross-Domain" in report or "Insight" in report

    @pytest.mark.unit
    def test_report_omits_code_section_when_no_code_findings(self) -> None:
        """
        Scenario: Session has only discourse findings
        Given a session with one discourse finding and no code findings
        When format_report is called
        Then the code section heading does not appear
        """
        session = _make_session(
            findings=[_discourse_finding()],
            channels=["discourse"],
        )
        report = format_report(session)
        assert "https://github.com/example/lib" not in report

    @pytest.mark.unit
    def test_report_includes_executive_summary_section(self) -> None:
        """
        Scenario: Report always has an executive summary
        Given any session with findings
        When format_report is called
        Then an 'Executive Summary' section heading appears
        """
        session = _make_session(findings=[_code_finding()])
        report = format_report(session)
        assert "Executive Summary" in report

    @pytest.mark.unit
    def test_report_includes_recommendations_section(self) -> None:
        """
        Scenario: Report always has recommendations
        Given any session with findings
        When format_report is called
        Then a 'Recommendations' section heading appears
        """
        session = _make_session(findings=[_code_finding()])
        report = format_report(session)
        assert "Recommendation" in report

    @pytest.mark.unit
    def test_report_includes_citations_section(self) -> None:
        """
        Scenario: Report lists all sources
        Given a session with academic and code findings
        When format_report is called
        Then a citations or sources section appears with the finding URLs
        """
        session = _make_session(
            findings=[_code_finding(), _academic_finding()],
        )
        report = format_report(session)
        assert "Citation" in report or "Source" in report
        assert "https://github.com/example/lib" in report
        assert "https://arxiv.org/abs/2301.12345" in report

    @pytest.mark.unit
    def test_report_finding_urls_appear_in_body(self) -> None:
        """
        Scenario: Each finding URL is referenced in the report body
        Given a code finding with a known URL
        When format_report is called
        Then that URL appears in the output
        """
        session = _make_session(findings=[_code_finding()])
        report = format_report(session)
        assert "https://github.com/example/lib" in report

    @pytest.mark.unit
    def test_report_empty_session_does_not_crash(self) -> None:
        """
        Scenario: Session with no findings
        Given a session that completed with zero findings
        When format_report is called
        Then a report string is returned without raising
        """
        session = _make_session(findings=[])
        report = format_report(session)
        assert isinstance(report, str)
        assert len(report) > 0


class TestFormatBrief:
    """
    Feature: Condensed brief generation

    As a researcher short on time
    I want a compact summary of findings
    So that I can get key takeaways without reading the full report
    """

    @pytest.mark.unit
    def test_brief_is_shorter_than_full_report(self) -> None:
        """
        Scenario: Brief is more compact than full report
        Given a session with multiple findings
        When both format_brief and format_report are called
        Then the brief has fewer characters than the full report
        """
        session = _make_session(
            findings=[
                _code_finding(),
                _discourse_finding(),
                _academic_finding(),
            ]
        )
        brief = format_brief(session)
        report = format_report(session)
        assert len(brief) < len(report)

    @pytest.mark.unit
    def test_brief_includes_key_findings_section(self) -> None:
        """
        Scenario: Brief has a key findings section
        Given a session with findings
        When format_brief is called
        Then 'Key Findings' appears in the output
        """
        session = _make_session(findings=[_code_finding(), _discourse_finding()])
        brief = format_brief(session)
        assert "Key Findings" in brief or "Finding" in brief

    @pytest.mark.unit
    def test_brief_includes_next_steps(self) -> None:
        """
        Scenario: Brief ends with actionable steps
        Given any session with findings
        When format_brief is called
        Then 'Next Steps' or 'Recommended' appears in the output
        """
        session = _make_session(findings=[_academic_finding()])
        brief = format_brief(session)
        assert "Next Step" in brief or "Recommend" in brief

    @pytest.mark.unit
    def test_brief_includes_critical_sources(self) -> None:
        """
        Scenario: Brief references top sources
        Given a session with a code finding
        When format_brief is called
        Then the finding URL appears in the output
        """
        session = _make_session(findings=[_code_finding()])
        brief = format_brief(session)
        assert "https://github.com/example/lib" in brief

    @pytest.mark.unit
    def test_brief_empty_session_does_not_crash(self) -> None:
        """
        Scenario: Empty session brief
        Given a session with no findings
        When format_brief is called
        Then a string is returned without raising
        """
        session = _make_session(findings=[])
        brief = format_brief(session)
        assert isinstance(brief, str)


class TestFormatTranscript:
    """
    Feature: Raw session transcript

    As a researcher debugging a pipeline run
    I want a chronological dump of all findings with metadata
    So that I can audit exactly what was retrieved and from where
    """

    @pytest.mark.unit
    def test_transcript_contains_all_finding_urls(self) -> None:
        """
        Scenario: Every finding URL appears in the transcript
        Given a session with code, discourse, and academic findings
        When format_transcript is called
        Then each finding URL appears in the output
        """
        session = _make_session(
            findings=[
                _code_finding("https://github.com/example/lib"),
                _discourse_finding("https://news.ycombinator.com/item?id=99"),
                _academic_finding("https://arxiv.org/abs/2301.12345"),
            ]
        )
        transcript = format_transcript(session)
        assert "https://github.com/example/lib" in transcript
        assert "https://news.ycombinator.com/item?id=99" in transcript
        assert "https://arxiv.org/abs/2301.12345" in transcript

    @pytest.mark.unit
    def test_transcript_includes_session_metadata(self) -> None:
        """
        Scenario: Transcript header contains session context
        Given a session with a known topic and ID
        When format_transcript is called
        Then the topic and session ID appear in the output
        """
        session = _make_session()
        transcript = format_transcript(session)
        assert "async python patterns" in transcript
        assert "test-session-001" in transcript

    @pytest.mark.unit
    def test_transcript_groups_by_channel(self) -> None:
        """
        Scenario: Channel names appear as section markers
        Given a session with code and discourse findings
        When format_transcript is called
        Then both channel names appear in the transcript
        """
        session = _make_session(
            findings=[_code_finding(), _discourse_finding()],
            channels=["code", "discourse"],
        )
        transcript = format_transcript(session)
        assert "code" in transcript.lower()
        assert "discourse" in transcript.lower()

    @pytest.mark.unit
    def test_transcript_empty_session_does_not_crash(self) -> None:
        """
        Scenario: Empty session transcript
        Given a session with no findings
        When format_transcript is called
        Then a string is returned without raising
        """
        session = _make_session(findings=[])
        transcript = format_transcript(session)
        assert isinstance(transcript, str)


class TestGenerateExecutiveSummary:
    """
    Feature: Executive summary generation

    As a report formatter
    I want a concise multi-sentence summary of all findings
    So that readers get the key takeaway before reading details
    """

    @pytest.mark.unit
    def test_summary_mentions_topic(self) -> None:
        """
        Scenario: Summary references the research topic
        Given findings about 'async python patterns'
        When generate_executive_summary is called
        Then the topic appears in the output
        """
        findings = [_code_finding(), _academic_finding()]
        summary = generate_executive_summary(findings, "async python patterns")
        assert "async python patterns" in summary

    @pytest.mark.unit
    def test_summary_returns_non_empty_string(self) -> None:
        """
        Scenario: Summary is always produced
        Given one finding
        When generate_executive_summary is called
        Then a non-empty string is returned
        """
        findings = [_code_finding()]
        summary = generate_executive_summary(findings, "concurrency")
        assert isinstance(summary, str)
        assert len(summary.strip()) > 0

    @pytest.mark.unit
    def test_summary_empty_findings_does_not_crash(self) -> None:
        """
        Scenario: No findings produces a graceful summary
        Given an empty findings list
        When generate_executive_summary is called
        Then a string is returned without raising
        """
        summary = generate_executive_summary([], "empty topic")
        assert isinstance(summary, str)

    @pytest.mark.unit
    def test_summary_references_channel_counts(self) -> None:
        """
        Scenario: Summary notes how many sources were found
        Given findings from two different channels
        When generate_executive_summary is called
        Then the output reflects the multi-channel nature (mentions count or channels)
        """
        findings = [_code_finding(), _discourse_finding(), _academic_finding()]
        summary = generate_executive_summary(findings, "async python patterns")
        # The summary should mention some quantity signal or channel names
        has_count = any(char.isdigit() for char in summary)
        has_channel = any(
            word in summary.lower()
            for word in ("code", "academic", "discourse", "finding", "source")
        )
        assert has_count or has_channel
