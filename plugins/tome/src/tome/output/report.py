"""Generate markdown research reports from a ResearchSession."""

from __future__ import annotations

import textwrap

from tome.models import Finding, ResearchSession
from tome.output.citations import generate_bibliography
from tome.synthesis.frontier import (
    ACT,
    DECLINE,
    DEFER,
    ResearchStory,
    frontier_stories,
    frontier_verdict,
)
from tome.synthesis.quality import channel_outcomes, identify_gaps
from tome.synthesis.ranker import compute_relevance_score, group_by_theme

_WRAP = 80

_SECTIONS = [
    ("code", "Code Implementations", "stars"),
    ("discourse", "Community Perspectives", "score"),
    ("academic", "Academic Literature", "citations"),
    ("triz", "Cross-Domain Insights", None),
]

# What to say under a planned channel that produced no findings.
#
# These sentences carry the whole point of recording channel outcome, so
# they are written to be read rather than skimmed. The difference that
# matters is between "this is weak evidence about the topic" and "this
# is no evidence at all", and only `empty` is the former.
#
# Every status channel_outcomes can return needs an entry here, including
# `ok`: deduplication keeps one finding per URL, so a channel whose
# queries all succeeded can still contribute nothing to the report. A
# test holds the two vocabularies in step.
_EMPTY_CHANNEL_NOTES = {
    "ok": (
        "Returned results, none of which survived synthesis. "
        "Deduplication keeps one finding per URL, so everything this "
        "channel found was already reported by another. The search "
        "worked; the channel added no new sources."
    ),
    "empty": (
        "Searched, and found nothing. Every query for this channel "
        "completed, so this is the one outcome here that says something "
        "about the topic rather than about the search. It remains weak "
        "evidence: a field published under different words looks exactly "
        "like this."
    ),
    "error": (
        "Could not be searched. Every query failed, so absence here is "
        "not evidence about the field, only about the run. Re-run before "
        "concluding anything from this gap."
    ),
    "rate_limited": (
        "Rate-limited before returning anything. The source refused us "
        "for volume, not for want of content, so this gap is not "
        "evidence about the field. Re-run this channel."
    ),
    "degraded": (
        "Partially searched. Some queries failed and any findings above "
        "came through a fallback, so coverage is thinner than planned "
        "and this channel is not a clean probe either way."
    ),
    "unknown": (
        "No query record. This session predates outcome tracking, or the "
        "agent returned no envelope, so nothing can be concluded about "
        "this channel in either direction."
    ),
}


def _wrap(text: str) -> str:
    """Wrap a prose paragraph at _WRAP characters."""
    return textwrap.fill(text, width=_WRAP)


def _section(heading: str, level: int = 2) -> str:
    prefix = "#" * level
    return f"\n{prefix} {heading}\n"


def _format_coverage(session: ResearchSession, outcomes: dict[str, str]) -> str:
    """Render what each planned channel did, and the gaps that follow.

    `compute_quality_score` is deliberately absent. It blends channel
    coverage, source diversity and mean relevance, every one of which
    describes the search rather than the field. Printing that number
    beside statements about the topic invites the reader to treat a bad
    search as a thin field, which is the confusion this section exists
    to remove.
    """
    result = frontier_verdict(session)
    lines = [
        _wrap(f"Verdict: {result.verdict}"),
        "",
        _wrap(result.reason),
        "",
        _wrap(
            "What each planned channel did. A channel that returned "
            "nothing is only informative about the topic when its "
            "queries actually ran."
        ),
        "",
        "| Channel | Outcome | Findings |",
        "| --- | --- | --- |",
    ]
    counts: dict[str, int] = {}
    for f in session.findings:
        counts[f.channel] = counts.get(f.channel, 0) + 1
    for channel in session.channels:
        status = outcomes.get(channel, "unknown")
        lines.append(f"| {channel} | {status} | {counts.get(channel, 0)} |")

    gaps = identify_gaps(session.findings, session.channels)
    notes: list[str] = []
    if gaps["source_diversity_warning"]:
        notes.append(
            "One channel holds most of the findings, so the result rests "
            "on a single source's coverage."
        )
    if gaps["recency_gap"]:
        notes.append(
            "Every dated finding is several years old, which may reflect "
            "the field or may reflect the queries."
        )
    # `empty` belongs with `ok`, not with the failures. Its queries ran;
    # it is the one outcome whose silence is informative. Filtering on
    # `!= "ok"` put it here once, and the report then told the reader
    # that absence in a cleanly-searched channel proved nothing, three
    # paragraphs above the section saying it was weak evidence.
    unproven = [
        c for c in session.channels if outcomes.get(c, "unknown") not in ("ok", "empty")
    ]
    if unproven:
        notes.append(
            "Channels that could not be searched cleanly: "
            + ", ".join(f"{c} ({outcomes.get(c, 'unknown')})" for c in unproven)
            + ". Absence in these is not evidence about the field, only "
            "about the run."
        )
    if notes:
        lines.append("")
        lines.extend(_wrap(n) for n in notes)
    return "\n".join(lines)


def _format_stories(stories: list[ResearchStory]) -> str:
    """Render this session's gaps as questions put to a person.

    Each story prints its evidence and its next action, because a bare
    title is a conclusion and a reader cannot disagree with a
    conclusion whose basis is off the page.

    The dispositions are printed as offered choices rather than
    inferred. Nothing in a search record supports deciding what is
    worth this project's time, so every story arrives ``undecided``
    and a person moves it.
    """
    lines: list[str] = [
        _wrap(
            "Gaps this run turned up, for triage. A verdict describes one "
            "session and then scrolls away, but these outlive it. Mark each "
            f"one {ACT} (worth doing now), {DEFER} (file it as an issue and "
            f"come back), or {DECLINE} (not worth this project's time). "
            "They arrive undecided because nothing in a search record "
            "says which one is right."
        ),
        "",
    ]
    for story in stories:
        lines.extend(
            [
                _section(f"{story.title} [{story.kind}]", level=3),
                _wrap(story.evidence),
                "",
                _wrap(f"Next: {story.next_action}"),
                "",
                _wrap(
                    f"Disposition: {story.disposition} ({ACT} / {DEFER} / {DECLINE})"
                ),
                "",
            ]
        )
    return "\n".join(lines)


def format_report(session: ResearchSession) -> str:
    """Generate a full markdown research report."""
    groups = group_by_theme(session.findings)
    date_str = (
        session.created_at.strftime("%Y-%m-%d") if session.created_at else "Unknown"
    )
    channels_str = ", ".join(session.channels) if session.channels else "none"

    parts: list[str] = []

    # --- Header ---
    parts.append(f"# Research Report: {session.topic}\n")
    parts.append(
        _wrap(
            f"Date: {date_str} | Domain: {session.domain} | "
            f"Channels: {channels_str} | "
            f"Findings: {len(session.findings)}"
        )
    )

    # --- Executive Summary ---
    parts.append(_section("Executive Summary"))
    parts.append(_wrap(generate_executive_summary(session.findings, session.topic)))

    # --- Coverage and Gaps ---
    outcomes = channel_outcomes(session)
    parts.append(_section("Coverage and Gaps"))
    parts.append(_format_coverage(session, outcomes))

    # --- Channel sections (data-driven) ---
    for group_key, heading, show_key in _SECTIONS:
        section_findings = groups.get(group_key, [])
        if section_findings:
            parts.append(_section(heading))
            for f in section_findings:
                if show_key:
                    parts.append(_finding_block(f, show_key=show_key))
                else:
                    parts.append(_finding_block(f))
        elif group_key in session.channels:
            # Planned, produced nothing. Rendering the heading anyway is
            # the point: a section that disappears when its channel
            # fails hides the failure, and the reader sees a report that
            # looks complete.
            parts.append(_section(heading))
            parts.append(
                _wrap(_EMPTY_CHANNEL_NOTES[outcomes.get(group_key, "unknown")])
            )

    # --- Research Stories ---
    stories = frontier_stories(session)
    if stories:
        parts.append(_section("Research Stories"))
        parts.append(_format_stories(stories))

    # --- Recommendations ---
    parts.append(_section("Recommendations"))
    parts.append(_generate_recommendations(session.findings, session.topic))

    # --- Citations ---
    parts.append(_section("Citations"))
    bib = generate_bibliography(session.findings)
    parts.append(bib if bib else "_No sources recorded._")

    return "\n".join(parts)


def format_brief(session: ResearchSession) -> str:
    """Generate a condensed 1-2 page brief."""
    ranked = sorted(session.findings, key=compute_relevance_score, reverse=True)
    top_sources = ranked[:5]

    parts: list[str] = []

    parts.append(f"# Brief: {session.topic}\n")

    # Key Findings
    parts.append(_section("Key Findings"))
    if session.findings:
        groups = group_by_theme(session.findings)
        for channel, findings in groups.items():
            top = max(findings, key=compute_relevance_score)
            parts.append(f"- **{channel.capitalize()}**: {top.summary}")
    else:
        parts.append("- No findings recorded.")

    # Recommended Approach
    parts.append(_section("Recommended Approach"))
    parts.append(
        _wrap(
            f"Based on {len(session.findings)} findings across "
            f"{len(session.channels)} channels, the research on "
            f"'{session.topic}' suggests focusing on the highest-relevance "
            "sources identified below before drawing conclusions."
        )
    )

    # Critical Sources
    parts.append(_section("Critical Sources"))
    for f in top_sources:
        score = compute_relevance_score(f)
        parts.append(f"- [{f.title}]({f.url}) (relevance: {score:.2f})")

    # Next Steps
    parts.append(_section("Next Steps"))
    parts.append(_generate_next_steps(session.findings, session.topic))

    return "\n".join(parts)


def format_transcript(session: ResearchSession) -> str:
    """Generate a raw session transcript."""
    date_str = session.created_at.isoformat() if session.created_at else "Unknown"
    parts: list[str] = []

    # Session header
    parts.append("# Session Transcript\n")
    parts.append(f"- **Session ID**: {session.id}")
    parts.append(f"- **Topic**: {session.topic}")
    parts.append(f"- **Domain**: {session.domain}")
    parts.append(f"- **Status**: {session.status}")
    parts.append(f"- **Created**: {date_str}")
    parts.append(f"- **Total findings**: {len(session.findings)}")

    # Findings grouped by channel
    groups = group_by_theme(session.findings)
    for channel, findings in groups.items():
        parts.append(f"\n## Channel: {channel}\n")
        for i, f in enumerate(findings, start=1):
            parts.append(f"### [{i}] {f.title}")
            parts.append(f"- **URL**: {f.url}")
            parts.append(f"- **Source**: {f.source}")
            parts.append(f"- **Relevance**: {f.relevance:.2f}")
            parts.append(f"- **Summary**: {f.summary}")
            if f.metadata:
                meta_pairs = ", ".join(f"{k}={v}" for k, v in f.metadata.items())
                parts.append(f"- **Metadata**: {meta_pairs}")

    if not session.findings:
        parts.append("\n_No findings recorded._")

    return "\n".join(parts)


def generate_executive_summary(findings: list[Finding], topic: str) -> str:
    """Generate a 3-5 sentence executive summary.

    Strategy: count findings per channel, note top finding per channel,
    synthesize into prose.
    """
    if not findings:
        return _wrap(
            f"No findings were collected for the topic '{topic}'. "
            "Consider expanding the search channels or adjusting the query."
        )

    groups = group_by_theme(findings)

    total = len(findings)
    channel_count = len(groups)

    # Build a summary sentence per channel.
    channel_sentences: list[str] = []
    for channel, channel_findings in groups.items():
        top = max(channel_findings, key=lambda f: f.relevance)
        channel_sentences.append(
            f"The {channel} channel yielded {len(channel_findings)} finding(s), "
            f"with the top result being '{top.title}'."
        )

    intro = f"Research on '{topic}' produced {total} finding(s) across {channel_count} channel(s)."
    body = " ".join(channel_sentences)
    conclusion = "Review the sections below for full details and ranked source lists."

    return _wrap(f"{intro} {body} {conclusion}")


# --- Internal helpers ---


def _finding_block(finding: Finding, show_key: str | None = None) -> str:
    lines: list[str] = []
    lines.append(f"**[{finding.title}]({finding.url})**")
    lines.append(_wrap(finding.summary))
    if show_key and show_key in finding.metadata:
        val = finding.metadata[show_key]
        lines.append(f"_{show_key}: {val}_")
    return "\n".join(lines) + "\n"


def _generate_recommendations(findings: list[Finding], topic: str) -> str:
    if not findings:
        return (
            "1. Broaden the search scope and retry with additional channels.\n"
            "2. Verify the topic query covers the intended domain.\n"
            "3. Consult domain experts directly."
        )
    top = max(findings, key=compute_relevance_score)
    unique_channels = len({f.channel for f in findings})
    lines = [
        f"1. Start with the highest-ranked source: [{top.title}]({top.url}).",
        f"2. Cross-reference findings across all {unique_channels} "
        f"channel(s) to identify convergent insights on '{topic}'.",
        "3. Validate academic findings against active code implementations "
        "before making architectural decisions.",
    ]
    return "\n".join(lines)


def _generate_next_steps(findings: list[Finding], topic: str) -> str:
    if not findings:
        return "- Expand search channels.\n- Refine the research query.\n- Consult domain experts."
    top = max(findings, key=compute_relevance_score)
    return (
        f"- Review the top-ranked source on '{topic}': "
        f"[{top.title}]({top.url}).\n"
        "- Compare code implementations against community recommendations.\n"
        "- Define success criteria before beginning implementation."
    )
