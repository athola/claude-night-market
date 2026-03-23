"""Generate markdown research reports from a ResearchSession."""

from __future__ import annotations

import textwrap

from tome.models import Finding, ResearchSession
from tome.output.citations import generate_bibliography
from tome.synthesis.ranker import compute_relevance_score, group_by_theme

_WRAP = 80

_SECTIONS = [
    ("code", "Code Implementations", "stars"),
    ("discourse", "Community Perspectives", "score"),
    ("academic", "Academic Literature", "citations"),
    ("triz", "Cross-Domain Insights", None),
]


def _wrap(text: str) -> str:
    """Wrap a prose paragraph at _WRAP characters."""
    return textwrap.fill(text, width=_WRAP)


def _section(heading: str, level: int = 2) -> str:
    prefix = "#" * level
    return f"\n{prefix} {heading}\n"


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
