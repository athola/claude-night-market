"""Export research sessions for memory-palace ingestion."""

from __future__ import annotations

from tome.models import ResearchSession


def export_for_memory_palace(session: ResearchSession) -> str:
    """Export a session as memory-palace knowledge-intake markdown.

    Format:
    - YAML frontmatter with topic, domain, date metadata
    - Findings listed with URLs, summaries, relevance
    - Compatible with memory-palace knowledge-intake skill
    """
    created = ""
    if session.created_at:
        created = session.created_at.strftime("%Y-%m-%d")

    # Build YAML frontmatter
    lines = [
        "---",
        f"topic: {session.topic}",
        f"domain: {session.domain}",
        f"session_id: {session.id}",
        f"date: {created}",
        f"finding_count: {len(session.findings)}",
        f"channels: [{', '.join(session.channels)}]",
        "type: research-export",
        "---",
        "",
        f"# Research: {session.topic}",
        "",
    ]

    if not session.findings:
        lines.append("No findings recorded in this session.")
        return "\n".join(lines)

    # Group findings by channel
    by_channel: dict[str, list] = {}
    for f in session.findings:
        by_channel.setdefault(f.channel, []).append(f)

    for channel, findings in by_channel.items():
        lines.append(f"## {channel.title()}")
        lines.append("")
        for f in findings:
            lines.append(f"### {f.title}")
            lines.append("")
            lines.append(f"- **Source**: {f.source}")
            lines.append(f"- **URL**: {f.url}")
            lines.append(f"- **Relevance**: {f.relevance}")
            lines.append(f"- **Summary**: {f.summary}")
            if f.metadata:
                for k, v in f.metadata.items():
                    lines.append(f"- **{k}**: {v}")
            lines.append("")

    return "\n".join(lines)
