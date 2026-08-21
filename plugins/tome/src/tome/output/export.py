"""Export research sessions for memory-palace ingestion."""

from __future__ import annotations

import yaml

from tome.models import ResearchSession
from tome.synthesis.ranker import group_by_theme


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

    # Frontmatter goes through the YAML writer rather than hand-rolled
    # quoting: a topic starting with "-", "[" or "%", or one that is bare
    # yes/no/null, re-parses as the wrong type when emitted unquoted, and
    # memory-palace then cannot ingest it.
    front = {
        "topic": session.topic,
        "domain": session.domain,
        "session_id": session.id,
        "date": created,
        "finding_count": len(session.findings),
        "channels": list(session.channels),
        "type": "research-export",
    }
    lines = [
        "---",
        yaml.safe_dump(front, sort_keys=False, allow_unicode=True).rstrip(),
        "---",
        "",
        f"# Research: {session.topic}",
        "",
    ]

    if not session.findings:
        lines.append("No findings recorded in this session.")
        return "\n".join(lines)

    # Group findings by channel
    by_channel = group_by_theme(session.findings)

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
