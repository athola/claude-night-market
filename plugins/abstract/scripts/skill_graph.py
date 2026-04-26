"""Skill graph extractor for the claude-night-market marketplace.

Builds a directed graph of `Skill(plugin:name)` references across all SKILL.md
files in a plugins tree. Surfaces hubs (high inbound), orchestrators (high
outbound), and isolates (zero degree).

Used by:
- abstract:skill-graph-audit (skill wrapper)
- docs/quality-gates.md generation
- audit reports
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

# Matches Skill(plugin:name) and Skill(name) inside backticks or bare.
# Backtick form: `Skill(plugin:name)` or `Skill(name)`
# Bare form: Skill(plugin:name) -- captured anywhere.
_SKILL_REF_RE = re.compile(r"Skill\(\s*([a-zA-Z0-9_-]+)(?::([a-zA-Z0-9_-]+))?\s*\)")

# Expected number of path components for plugins/<plugin>/skills/<name>/SKILL.md
_SKILL_PATH_PARTS = 4


@dataclass(frozen=True)
class SkillNode:
    """A skill in the marketplace graph."""

    plugin: str
    name: str
    path: Path
    description: str = ""

    def __str__(self) -> str:
        """Return the canonical 'plugin:name' identifier."""
        return f"{self.plugin}:{self.name}"


@dataclass
class SkillGraph:
    """Directed graph of skills and their Skill() references."""

    nodes: dict[str, SkillNode] = field(default_factory=dict)
    edges: set[tuple[str, str]] = field(default_factory=set)
    # outbound[src] -> set of dst node keys
    outbound: dict[str, set[str]] = field(default_factory=lambda: defaultdict(set))
    # inbound[dst] -> set of src node keys
    inbound: dict[str, set[str]] = field(default_factory=lambda: defaultdict(set))


def extract_skill_references(skill_md: Path) -> set[tuple[str | None, str]]:
    """Extract all Skill() references from a SKILL.md file.

    Returns a set of (plugin, name) tuples. plugin is None for unqualified refs.
    Self-references (a skill referencing itself in examples) are not filtered
    here; the caller decides.
    """
    text = skill_md.read_text(encoding="utf-8", errors="replace")
    refs: set[tuple[str | None, str]] = set()
    for match in _SKILL_REF_RE.finditer(text):
        first, second = match.group(1), match.group(2)
        if second:
            # plugin:name form
            refs.add((first, second))
        else:
            # unqualified form
            refs.add((None, first))
    return refs


def _parse_frontmatter_field(text: str, field: str) -> str:
    """Best-effort extraction of a top-level frontmatter scalar."""
    pattern = re.compile(rf"^{field}:\s*(.*)$", re.MULTILINE)
    m = pattern.search(text)
    if not m:
        return ""
    val = m.group(1).strip()
    # Strip surrounding quotes
    if val.startswith(("'", '"')) and val.endswith(("'", '"')):
        val = val[1:-1]
    return val


def _discover_skills(plugins_root: Path) -> list[SkillNode]:
    """Find all SKILL.md files under plugins_root and build SkillNodes."""
    nodes: list[SkillNode] = []
    for skill_md in plugins_root.glob("*/skills/*/SKILL.md"):
        # path: plugins/<plugin>/skills/<name>/SKILL.md
        try:
            parts = skill_md.relative_to(plugins_root).parts
            # parts = (<plugin>, "skills", <name>, "SKILL.md")
            if len(parts) < _SKILL_PATH_PARTS or parts[1] != "skills":
                continue
            plugin = parts[0]
            name = parts[2]
        except ValueError:
            continue
        text = skill_md.read_text(encoding="utf-8", errors="replace")
        # frontmatter name overrides directory name if present
        fm_name = _parse_frontmatter_field(text, "name") or name
        description = _parse_frontmatter_field(text, "description")
        nodes.append(
            SkillNode(
                plugin=plugin, name=fm_name, path=skill_md, description=description
            )
        )
    return nodes


def build_graph(plugins_root: Path) -> SkillGraph:
    """Build the skill graph from a plugins root directory."""
    graph = SkillGraph()
    nodes = _discover_skills(plugins_root)
    for node in nodes:
        graph.nodes[str(node)] = node

    for node in nodes:
        src_key = str(node)
        refs = extract_skill_references(node.path)
        for plugin, name in refs:
            if plugin is None:
                continue  # skip unqualified refs in graph edges
            dst_key = f"{plugin}:{name}"
            if dst_key == src_key:
                continue  # skip self-references
            graph.edges.add((src_key, dst_key))
            graph.outbound[src_key].add(dst_key)
            graph.inbound[dst_key].add(src_key)
    return graph


def rank_hubs(graph: SkillGraph, top_n: int = 10) -> list[tuple[str, int]]:
    """Return top-N skills by inbound reference count, descending."""
    counts = [(key, len(srcs)) for key, srcs in graph.inbound.items()]
    counts.sort(key=lambda x: (-x[1], x[0]))
    return counts[:top_n]


def rank_orchestrators(graph: SkillGraph, top_n: int = 10) -> list[tuple[str, int]]:
    """Return top-N skills by outbound reference count, descending."""
    counts = [(key, len(dsts)) for key, dsts in graph.outbound.items()]
    counts.sort(key=lambda x: (-x[1], x[0]))
    return counts[:top_n]


def detect_isolates(graph: SkillGraph) -> list[str]:
    """Return skills with zero inbound and zero outbound references.

    Sorted alphabetically for deterministic output.
    """
    isolates = []
    for key in graph.nodes:
        if not graph.inbound.get(key) and not graph.outbound.get(key):
            isolates.append(key)
    return sorted(isolates)


# Plugins that exist in the marketplace ecosystem but are not in this repo.
# References to these are external and should not be flagged as bugs.
KNOWN_EXTERNAL_PLUGINS = frozenset(
    {
        "superpowers",
        "superpowers-chrome",
        "superpowers-developing-for-claude-code",
        "superpowers-lab",
        "elements-of-style",
        "claude-md-management",
        "code-review-mode",
        "code-simplifier",
        "documentation-mode",
        "feature-dev",
        "frontend-design",
        "interface-design",
        "minister",
        "plugin-developer",
        "pr-review-toolkit",
        "ralph-wiggum",
    }
)

# Patterns indicating template placeholder text (not a real reference).
# Matches both suffix forms (`-NAME`) and bare placeholder words (`name`).
_PLACEHOLDER_RE = re.compile(
    r"(?:-(NAME|FOO|BAR|XXX|TODO|EXAMPLE)$)|^(name|skill-name|plugin-name)$"
)


def _is_placeholder(plugin: str, name: str) -> bool:
    """True if either side of the reference looks like template text."""
    if _PLACEHOLDER_RE.search(name):
        return True
    if _PLACEHOLDER_RE.search(plugin):
        return True
    if plugin.lower() in {"plugin", "your-plugin"}:
        return True
    return False


def classify_dangling_refs(
    graph: SkillGraph,
) -> dict[str, list[tuple[str, str]]]:
    """Classify dangling references into bug, external, or placeholder.

    Returns a dict with keys 'bugs', 'external', 'placeholders'.
    """
    bugs: list[tuple[str, str]] = []
    external: list[tuple[str, str]] = []
    placeholders: list[tuple[str, str]] = []
    for src, dst in sorted(graph.edges):
        if dst in graph.nodes:
            continue
        plugin, _, name = dst.partition(":")
        if _is_placeholder(plugin, name):
            placeholders.append((src, dst))
        elif plugin in KNOWN_EXTERNAL_PLUGINS:
            external.append((src, dst))
        else:
            bugs.append((src, dst))
    return {"bugs": bugs, "external": external, "placeholders": placeholders}


def detect_dangling_refs(graph: SkillGraph) -> list[tuple[str, str]]:
    """Return only true bug-class dangling refs (typos / retired skills).

    External plugin references and template placeholders are excluded.
    For the full classification, use ``classify_dangling_refs``.
    """
    return classify_dangling_refs(graph)["bugs"]


def generate_report(plugins_root: Path, top_n: int = 10) -> dict:
    """Generate a report dict suitable for JSON serialization."""
    graph = build_graph(plugins_root)
    classified = classify_dangling_refs(graph)
    return {
        "marketplace": str(plugins_root),
        "totals": {
            "skills": len(graph.nodes),
            "edges": len(graph.edges),
            "isolates": len(detect_isolates(graph)),
            "dangling_bugs": len(classified["bugs"]),
            "dangling_external": len(classified["external"]),
            "dangling_placeholders": len(classified["placeholders"]),
        },
        "hubs": [{"skill": k, "inbound": n} for k, n in rank_hubs(graph, top_n)],
        "orchestrators": [
            {"skill": k, "outbound": n} for k, n in rank_orchestrators(graph, top_n)
        ],
        "isolates": detect_isolates(graph),
        "dangling_refs": {
            "bugs": [{"source": s, "target": t} for s, t in classified["bugs"]],
            "external": [{"source": s, "target": t} for s, t in classified["external"]],
            "placeholders": [
                {"source": s, "target": t} for s, t in classified["placeholders"]
            ],
        },
    }


def _format_text_report(report: dict) -> str:
    """Render a JSON-shaped report as a human-readable text block."""
    lines: list[str] = []
    t = report["totals"]
    lines.append(f"Marketplace: {report['marketplace']}")
    lines.append(
        f"  Skills: {t['skills']} | Edges: {t['edges']} | "
        f"Isolates: {t['isolates']} | "
        f"Dangling: {t['dangling_bugs']} bugs, "
        f"{t['dangling_external']} external, "
        f"{t['dangling_placeholders']} placeholders"
    )
    lines.append("")
    lines.append("Top hubs (inbound references):")
    for h in report["hubs"]:
        lines.append(f"  {h['skill']:50s} <- {h['inbound']}")
    lines.append("")
    lines.append("Top orchestrators (outbound references):")
    for o in report["orchestrators"]:
        lines.append(f"  {o['skill']:50s} -> {o['outbound']}")
    if report["isolates"]:
        lines.append("")
        lines.append(f"Isolates ({len(report['isolates'])}):")
        for i in report["isolates"]:
            lines.append(f"  {i}")
    bugs = report["dangling_refs"]["bugs"]
    if bugs:
        lines.append("")
        lines.append(f"Dangling references -- BUGS ({len(bugs)}):")
        for d in bugs:
            lines.append(f"  {d['source']} -> {d['target']}")
    ext = report["dangling_refs"]["external"]
    if ext:
        lines.append("")
        lines.append(f"Dangling references -- external plugins ({len(ext)}):")
        for d in ext:
            lines.append(f"  {d['source']} -> {d['target']}")
    return "\n".join(lines)


def main() -> int:
    """CLI entry point: emit a graph report for a plugins tree."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--plugins-root",
        type=Path,
        default=Path("plugins"),
        help="Root directory containing plugin folders (default: plugins)",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=10,
        help="Top N for hubs/orchestrators (default: 10)",
    )
    parser.add_argument(
        "--format",
        choices=["json", "text"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument("--output", type=Path, help="Write to file instead of stdout")
    args = parser.parse_args()

    report = generate_report(args.plugins_root, top_n=args.top_n)

    if args.format == "json":
        out = json.dumps(report, indent=2, default=str)
    else:
        out = _format_text_report(report)

    if args.output:
        args.output.write_text(out)
    else:
        print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
