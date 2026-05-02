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
from typing import Any

try:
    import yaml as _yaml  # type: ignore[import-untyped]  # PyYAML ships no type stubs in dev deps
except ImportError:  # pragma: no cover - PyYAML is in dev deps
    _yaml = None  # type: ignore[assignment]  # None sentinel; callers branch on `_yaml is None`

# Matches Skill(plugin:name) and Skill(name) inside backticks or bare.
# Backtick form: `Skill(plugin:name)` or `Skill(name)`
# Bare form: Skill(plugin:name) -- captured anywhere.
_SKILL_REF_RE = re.compile(r"Skill\(\s*([a-zA-Z0-9_-]+)(?::([a-zA-Z0-9_-]+))?\s*\)")

# Matches a kebab-case bare skill name (no path separators, no extension).
_BARE_SKILL_NAME_RE = re.compile(r"^[a-z][a-z0-9_-]*$")

# Frontmatter array fields whose entries are skill references.
#
# `dependencies:` lists sibling skill references; bare names resolve to the
# same-plugin skill (the canonical declaration used by hubs like
# archetypes:architecture-paradigms and tome:research).
#
# `modules:` lists local module file basenames within the skill's own
# directory (e.g. `modules/tdd-methodology.md`). Bare names are NEVER
# skill references in this field; only fully-qualified `plugin:name`
# entries count, which is rare but legal.
_FRONTMATTER_DEP_FIELDS_QUALIFIED_ONLY = ("modules",)
_FRONTMATTER_DEP_FIELDS_ANY = ("dependencies",)

# Valid values for the `role:` frontmatter field, per the taxonomy in
# docs/skill-integration-guide.md#skill-role-taxonomy.
VALID_ROLES = frozenset({"entrypoint", "library", "hook-target"})

# Expected number of path components for plugins/<plugin>/skills/<name>/SKILL.md
_SKILL_PATH_PARTS = 4


@dataclass(frozen=True)
class SkillNode:
    """A skill in the marketplace graph.

    `role` reflects the taxonomy in
    docs/skill-integration-guide.md#skill-role-taxonomy:
    `entrypoint` (user-invoked), `library` (loaded by other skills),
    or `hook-target` (invoked by hooks). Empty string means unset --
    legacy skills that predate the role: convention.
    """

    plugin: str
    name: str
    path: Path
    description: str = ""
    role: str = ""

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


_FRONTMATTER_BLOCK_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def _parse_frontmatter(text: str) -> dict[str, Any]:
    """Parse a SKILL.md YAML frontmatter block to a dict.

    Returns {} on missing or malformed frontmatter so callers can treat
    absence and parse failure uniformly. PyYAML is required (declared in
    plugins/abstract/scripts deps); the import-time fallback path keeps
    the script importable in environments without it.
    """
    m = _FRONTMATTER_BLOCK_RE.match(text)
    if not m:
        return {}
    if _yaml is None:
        return {}
    try:
        data = _yaml.safe_load(m.group(1))
    except _yaml.YAMLError:
        return {}
    return data if isinstance(data, dict) else {}


def _is_local_module_path(item: str) -> bool:
    """True if a frontmatter list entry is a local file path, not a skill ref.

    `modules:` entries like `modules/usage.md` are local files; they must
    not produce phantom edges. Anything containing a path separator or a
    file extension qualifies.
    """
    return "/" in item or item.endswith(".md")


def _resolve_dep_to_skill_ref(
    item: Any, default_plugin: str, *, allow_bare: bool
) -> tuple[str, str] | None:
    """Map a frontmatter dep entry to a (plugin, name) tuple, or None.

    Accepts Any because YAML frontmatter can produce non-string list
    entries (ints, nested dicts) when authors mistype. The function
    coerces gracefully rather than raising.

    `allow_bare` distinguishes how to interpret bare-name entries:
    - True (used for `dependencies:`): bare name -> (default_plugin, name)
      -- the canonical sibling-skill declaration.
    - False (used for `modules:`): bare names refer to local module files,
      not skills. Only fully-qualified `plugin:name` entries count.

    Rules:
    - `plugin:name` form -> (plugin, name) regardless of allow_bare
    - bare kebab-case name -> (default_plugin, name) iff allow_bare
    - file-path-shaped entry -> None (local module file, not a skill)
    - anything else (non-string, whitespace, malformed) -> None
    """
    # Reject early for non-string, empty, or path-shaped entries.
    if not isinstance(item, str):
        return None
    stripped = item.strip()
    if not stripped or _is_local_module_path(stripped):
        return None
    # Qualified plugin:name form takes precedence and works in any field.
    if ":" in stripped:
        plugin, _, name = stripped.partition(":")
        plugin, name = plugin.strip(), name.strip()
        return (plugin, name) if (plugin and name) else None
    # Bare names only count where the field's semantics permit them.
    if allow_bare and _BARE_SKILL_NAME_RE.match(stripped):
        return (default_plugin, stripped)
    return None


def extract_frontmatter_skill_refs(
    skill_md: Path, default_plugin: str
) -> set[tuple[str, str]]:
    """Extract skill references declared in frontmatter dep arrays.

    Two fields contribute, with different bare-name semantics:

    - `dependencies:` -- bare names resolve to same-plugin sibling skills
      (the canonical hub-loads-sibling pattern).
    - `modules:` -- bare names refer to local module file basenames in
      the skill's own ``modules/`` directory and are NOT skill refs.
      Only fully-qualified ``plugin:name`` entries in this field
      contribute edges.

    File-path entries (e.g. ``modules/usage.md``) are filtered out
    everywhere.
    """
    text = skill_md.read_text(encoding="utf-8", errors="replace")
    fm = _parse_frontmatter(text)
    refs: set[tuple[str, str]] = set()
    for field_name, allow_bare in (
        *((f, True) for f in _FRONTMATTER_DEP_FIELDS_ANY),
        *((f, False) for f in _FRONTMATTER_DEP_FIELDS_QUALIFIED_ONLY),
    ):
        items = fm.get(field_name) or []
        if not isinstance(items, list):
            continue
        for item in items:
            resolved = _resolve_dep_to_skill_ref(
                item, default_plugin, allow_bare=allow_bare
            )
            if resolved is not None:
                refs.add(resolved)
    return refs


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
        role = _parse_frontmatter_field(text, "role")
        if role and role not in VALID_ROLES:
            role = ""  # ignore unknown role values rather than error
        nodes.append(
            SkillNode(
                plugin=plugin,
                name=fm_name,
                path=skill_md,
                description=description,
                role=role,
            )
        )
    return nodes


def build_graph(plugins_root: Path) -> SkillGraph:
    """Build the skill graph from a plugins root directory.

    Edges come from two sources:

    1. Inline `Skill(plugin:name)` invocations in SKILL.md prose (the
       canonical runtime call site).
    2. Frontmatter `dependencies:` and `modules:` arrays (the canonical
       declarative dependency, used by hubs that load siblings without
       inline calls).

    Both forms produce the same edge shape; consumers (hubs, isolates,
    dangling-ref classification) do not need to distinguish them.
    """
    graph = SkillGraph()
    nodes = _discover_skills(plugins_root)
    for node in nodes:
        graph.nodes[str(node)] = node

    for node in nodes:
        src_key = str(node)
        # Inline Skill() refs.
        inline_refs = extract_skill_references(node.path)
        # Frontmatter declarative deps; bare names resolve to same-plugin.
        fm_refs = extract_frontmatter_skill_refs(node.path, default_plugin=node.plugin)
        # Merge: inline refs may have None plugin (unqualified, ignored
        # below); frontmatter refs always have a concrete plugin.
        all_refs: set[tuple[str | None, str]] = set(inline_refs)
        all_refs.update(fm_refs)
        for plugin, name in all_refs:
            if plugin is None:
                continue  # skip unqualified inline refs
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
    """Return skills with no entry path of any kind.

    Per the taxonomy in
    docs/skill-integration-guide.md#skill-role-taxonomy, an isolate is a
    skill with zero inbound, zero outbound, AND no declared role. Skills
    that declare role: library / entrypoint / hook-target have a known
    entry path and are reported in their own bins (uncalled_libraries
    and classify_by_role) rather than conflated with genuine orphans.

    Sorted alphabetically for deterministic output.
    """
    isolates = []
    for key, node in graph.nodes.items():
        if node.role:
            continue  # role-declared skills are not legacy isolates
        if not graph.inbound.get(key) and not graph.outbound.get(key):
            isolates.append(key)
    return sorted(isolates)


def detect_uncalled_libraries(graph: SkillGraph) -> list[str]:
    """Return library skills (`role: library`) with zero inbound edges.

    A library exists to be loaded by other skills. Zero inbound is a
    legitimate smell signal -- either the library is genuinely dead,
    or its callers load it through a path the audit cannot see (in
    which case the caller should declare the dep in frontmatter).

    Sorted alphabetically for deterministic output.
    """
    uncalled = [
        key
        for key, node in graph.nodes.items()
        if node.role == "library" and not graph.inbound.get(key)
    ]
    return sorted(uncalled)


def classify_by_role(graph: SkillGraph) -> dict[str, list[str]]:
    """Bin skills by declared role, with `unset` for legacy skills.

    Returns a dict with keys `entrypoint`, `library`, `hook-target`, and
    `unset`. Each value is an alphabetically-sorted list of skill keys.
    Useful for role-specific quality thresholds and per-role reporting.
    """
    bins: dict[str, list[str]] = {role: [] for role in VALID_ROLES}
    bins["unset"] = []
    for key, node in graph.nodes.items():
        bin_key = node.role if node.role in VALID_ROLES else "unset"
        bins[bin_key].append(key)
    for skills in bins.values():
        skills.sort()
    return bins


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
    by_role = classify_by_role(graph)
    uncalled_libs = detect_uncalled_libraries(graph)
    return {
        "marketplace": str(plugins_root),
        "totals": {
            "skills": len(graph.nodes),
            "edges": len(graph.edges),
            "isolates": len(detect_isolates(graph)),
            "uncalled_libraries": len(uncalled_libs),
            "dangling_bugs": len(classified["bugs"]),
            "dangling_external": len(classified["external"]),
            "dangling_placeholders": len(classified["placeholders"]),
            "role_entrypoint": len(by_role["entrypoint"]),
            "role_library": len(by_role["library"]),
            "role_hook_target": len(by_role["hook-target"]),
            "role_unset": len(by_role["unset"]),
        },
        "hubs": [{"skill": k, "inbound": n} for k, n in rank_hubs(graph, top_n)],
        "orchestrators": [
            {"skill": k, "outbound": n} for k, n in rank_orchestrators(graph, top_n)
        ],
        "isolates": detect_isolates(graph),
        "uncalled_libraries": uncalled_libs,
        "by_role": by_role,
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
        f"Uncalled libraries: {t['uncalled_libraries']} | "
        f"Dangling: {t['dangling_bugs']} bugs, "
        f"{t['dangling_external']} external, "
        f"{t['dangling_placeholders']} placeholders"
    )
    lines.append(
        f"  Roles: {t['role_entrypoint']} entrypoint | "
        f"{t['role_library']} library | "
        f"{t['role_hook_target']} hook-target | "
        f"{t['role_unset']} unset"
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
        lines.append(f"Isolates -- no entry path ({len(report['isolates'])}):")
        for i in report["isolates"]:
            lines.append(f"  {i}")
    if report["uncalled_libraries"]:
        lines.append("")
        lines.append(
            f"Uncalled libraries -- role: library, zero inbound "
            f"({len(report['uncalled_libraries'])}):"
        )
        for u in report["uncalled_libraries"]:
            lines.append(f"  {u}")
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
