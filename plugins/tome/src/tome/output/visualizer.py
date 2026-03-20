"""Domain-specific visualization for research findings."""

from __future__ import annotations

from tome.models import Finding


def generate_visualization(findings: list[Finding], domain: str) -> str:
    """Generate domain-appropriate visualization.

    Routes to the right format based on domain:
    - architecture: mermaid diagram
    - algorithm/data-structure: comparison table
    - financial/scientific: metrics table
    - general/other: numbered ranked list
    """
    if not findings:
        return ""

    if domain == "architecture":
        return _mermaid_diagram(findings)
    elif domain in ("algorithm", "data-structure"):
        return _comparison_table(findings)
    elif domain in ("financial", "scientific"):
        return _metrics_table(findings, domain)
    else:
        return _ranked_list(findings)


def _mermaid_diagram(findings: list[Finding]) -> str:
    """Generate a mermaid flowchart from findings."""
    lines = ["```mermaid", "graph TD"]
    for i, f in enumerate(findings[:8]):
        node_id = f"N{i}"
        label = f.title.replace('"', "'")[:40]
        lines.append(f'    {node_id}["{label}"]')
    # Connect nodes sequentially as a simple flow
    for i in range(len(findings[:8]) - 1):
        lines.append(f"    N{i} --> N{i + 1}")
    lines.append("```")
    return "\n".join(lines)


def _comparison_table(findings: list[Finding]) -> str:
    """Generate a comparison table for algorithm/data-structure findings."""
    lines = [
        "| Finding | Source | Relevance | Summary |",
        "|---------|--------|-----------|---------|",
    ]
    for f in findings[:10]:
        title = f.title[:30]
        source = f.source
        rel = f"{f.relevance:.2f}"
        summary = f.summary[:50]
        lines.append(f"| {title} | {source} | {rel} | {summary} |")
    return "\n".join(lines)


def _metrics_table(findings: list[Finding], domain: str) -> str:
    """Generate a metrics table for financial/scientific findings."""
    if domain == "financial":
        header = "| Finding | Source | Relevance | Stars/Score |"
        sep = "|---------|--------|-----------|-------------|"
    else:
        header = "| Finding | Source | Relevance | Citations |"
        sep = "|---------|--------|-----------|-----------|"

    lines = [header, sep]
    for f in findings[:10]:
        title = f.title[:30]
        source = f.source
        rel = f"{f.relevance:.2f}"
        metric = f.metadata.get(
            "citations", f.metadata.get("stars", f.metadata.get("score", "-"))
        )
        lines.append(f"| {title} | {source} | {rel} | {metric} |")
    return "\n".join(lines)


def _ranked_list(findings: list[Finding]) -> str:
    """Generate a numbered ranked list."""
    lines = []
    for i, f in enumerate(findings[:10], 1):
        lines.append(f"{i}. **{f.title}** ({f.source}) - {f.summary[:60]}")
    return "\n".join(lines)
