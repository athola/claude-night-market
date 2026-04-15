"""Markdown, JSON, wiki, and blast radius rendering."""

from __future__ import annotations

import copy
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from .models import (
    BlastResult,
    Dependency,
    RouteInfo,
    ScanResult,
    TruncatedList,
)

# ---------------------------------------------------------------------------
# Display limit constants (PLR2004)
# ---------------------------------------------------------------------------
_MAX_DISPLAY_FILES = 20
_MAX_DISPLAY_ROUTES = 15
_MAX_DISPLAY_HOT_FILES = 8
_MAX_DISPLAY_ENV_VARS = 12
_MAX_DISPLAY_SCHEMAS = 8
_MAX_DISPLAY_CONFIGS = 6
_MAX_DISPLAY_SECTION_ITEMS = 12
_MAX_DISPLAY_SECTION_HOT_FILES = 15
_MAX_DISPLAY_SECTION_ROUTES = 20
_ROUND_THRESHOLD = 100

# ---------------------------------------------------------------------------
# T005: Strategic Summarizer
# ---------------------------------------------------------------------------


def summarize(
    result: ScanResult,
    max_dirs: int = 8,
    max_deps: int = 8,
    max_frameworks: int = 6,
    max_entry_points: int = 5,
) -> ScanResult:
    """Apply truncation limits to scan result in-place."""
    if len(result.directories) > max_dirs:
        result.truncated_dirs = len(result.directories) - max_dirs
        result.directories = result.directories[:max_dirs]

    for eco in result.ecosystems:
        if len(eco.dependencies) > max_deps:
            eco.dependencies = eco.dependencies[:max_deps]
        if len(eco.frameworks) > max_frameworks:
            eco.frameworks = eco.frameworks[:max_frameworks]
        if len(eco.entry_points) > max_entry_points:
            eco.entry_points = eco.entry_points[:max_entry_points]

    return result


def summarize_dependencies(deps: list[Dependency], max_items: int = 8) -> TruncatedList:
    """Truncate a dependency list with remaining count."""
    if len(deps) <= max_items:
        return TruncatedList(shown=deps, remaining=0)
    return TruncatedList(shown=deps[:max_items], remaining=len(deps) - max_items)


# ---------------------------------------------------------------------------
# Wiki Knowledge Articles
# ---------------------------------------------------------------------------

_TOPIC_PATTERNS: list[tuple[str, str, list[str], list[str]]] = [
    (
        "auth",
        "Authentication & Authorization",
        ["auth", "login", "session", "permission", "jwt", "oauth", "token"],
        ["jwt", "oauth", "passlib", "bcrypt", "flask_login", "authlib"],
    ),
    (
        "database",
        "Database & Models",
        ["model", "schema", "migration", "orm", "database", "db"],
        [
            "sqlalchemy",
            "django.db",
            "prisma",
            "sqlx",
            "diesel",
            "gorm",
            "drizzle",
            "mongoose",
            "sequelize",
            "typeorm",
        ],
    ),
    (
        "api",
        "API Routes & Endpoints",
        ["route", "endpoint", "handler", "controller", "view", "api"],
        [],
    ),
    (
        "config",
        "Configuration & Environment",
        ["config", "setting", "env", ".env"],
        ["dotenv", "pydantic_settings", "decouple", "environ"],
    ),
    (
        "testing",
        "Testing",
        ["test", "spec", "fixture", "conftest", "factory"],
        ["pytest", "unittest", "jest", "vitest", "mocha"],
    ),
]


def classify_topics(  # noqa: PLR0912 - topic classification naturally branches per topic type
    result: ScanResult,
) -> dict[str, list[str]]:
    """Classify project files into topic clusters."""
    topics: dict[str, list[str]] = defaultdict(list)

    # Classify files by route presence
    route_files = {r.file for r in result.routes}
    for rf in route_files:
        topics["api"].append(rf)

    # Classify files by env var presence
    env_files = {v.file for v in result.env_vars}
    for ef in env_files:
        if ef not in topics["config"]:
            topics["config"].append(ef)

    # Classify by middleware
    for mw in result.middleware:
        if mw.kind in ("auth", "session"):
            topics["auth"].append(mw.file)
        elif mw.kind == "logging":
            topics["config"].append(mw.file)

    # Classify schemas
    for s in getattr(result, "schemas", []):
        if s.file not in topics["database"]:
            topics["database"].append(s.file)

    # Classify hot files by path patterns
    for hf in result.hot_files:
        hf_lower = hf.lower()
        for topic, _title, path_pats, _imp_pats in _TOPIC_PATTERNS:
            if any(pat in hf_lower for pat in path_pats):
                if hf not in topics[topic]:
                    topics[topic].append(hf)

    # Deduplicate and sort
    for topic, files in topics.items():
        topics[topic] = sorted(set(files))

    # Remove empty topics
    return {k: v for k, v in topics.items() if v}


def _render_wiki_article(
    topic: str, title: str, files: list[str], result: ScanResult
) -> str:
    """Render a single wiki article as markdown."""
    lines = [f"# {title}", ""]

    if topic == "api" and result.routes:
        by_file: dict[str, list[RouteInfo]] = defaultdict(list)
        for r in result.routes:
            by_file[r.file].append(r)
        for rfile, routes in sorted(by_file.items()):
            lines.append(f"## {rfile}")
            for r in routes:
                lines.append(f"  {r.method:<7} {r.path}")
            lines.append("")
    elif topic == "database" and getattr(result, "schemas", []):
        for s in result.schemas:
            fields = f" ({s.field_count} fields)" if s.field_count else ""
            lines.append(f"  - {s.name}: {s.file}{fields}")
        lines.append("")

    if topic == "config" and result.env_vars:
        lines.append("## Environment Variables")
        for v in result.env_vars[:_MAX_DISPLAY_FILES]:
            default = " (has default)" if v.has_default else " (required)"
            lines.append(f"  - {v.name}{default}")
        if len(result.env_vars) > _MAX_DISPLAY_FILES:
            lines.append(f"  ...{len(result.env_vars) - _MAX_DISPLAY_FILES} more")
        lines.append("")

    lines.append("## Related Files")
    lines.append("")
    for f in files[:_MAX_DISPLAY_FILES]:
        lines.append(f"  - {f}")
    if len(files) > _MAX_DISPLAY_FILES:
        lines.append(f"  ...{len(files) - _MAX_DISPLAY_FILES} more")
    lines.append("")

    return "\n".join(lines)


def generate_wiki(root: Path, result: ScanResult) -> None:
    """Generate .codesight/ wiki directory with per-topic articles."""
    root = root.resolve()
    topics = classify_topics(result)

    if not topics:
        return

    wiki_dir = root / ".codesight"
    wiki_dir.mkdir(exist_ok=True)

    generated: list[tuple[str, str]] = []
    for topic, files in sorted(topics.items()):
        title = topic
        for t_name, t_title, _pats, _imps in _TOPIC_PATTERNS:
            if t_name == topic:
                title = t_title
                break
        content = _render_wiki_article(topic, title, files, result)
        article_path = wiki_dir / f"{topic}.md"
        article_path.write_text(content)
        generated.append((topic, title))

    index_lines = [
        f"# Context Wiki: {result.project_name}",
        f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        "## Topics",
        "",
    ]
    for topic, title in generated:
        count = len(topics[topic])
        index_lines.append(f"  - [{title}]({topic}.md) ({count} files)")
    index_lines.append("")

    (wiki_dir / "INDEX.md").write_text("\n".join(index_lines))


# ---------------------------------------------------------------------------
# T006: Markdown and JSON Renderers
# ---------------------------------------------------------------------------


def render_markdown(  # noqa: PLR0912, PLR0915 - rendering many optional sections requires branches and statements
    result: ScanResult,
    max_dirs: int = 8,
    max_deps: int = 8,
    include_timestamp: bool = True,
) -> str:
    """Render scan result as markdown context map."""
    result = summarize(result, max_dirs=max_dirs, max_deps=max_deps)

    lines: list[str] = []
    ts = (
        datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        if include_timestamp
        else ""
    )
    header_parts = [f"# Context Map: {result.project_name}"]
    meta_parts = []
    if ts:
        meta_parts.append(f"Generated: {ts}")
    meta_parts.append(f"Files: {result.total_files}")
    if meta_parts:
        header_parts.append(" | ".join(meta_parts))
    lines.extend(header_parts)
    lines.append("")

    # Structure section
    if result.directories:
        lines.append("## Structure")
        lines.append("")
        for d in result.directories:
            lang = f" ({d.primary_language})" if d.primary_language else ""
            lines.append(f"  {d.path:<20s} {d.file_count:>4d} files{lang}")
        if result.truncated_dirs > 0:
            lines.append(f"  ...{result.truncated_dirs} more directories")
        lines.append("")

    # Ecosystems
    for eco in result.ecosystems:
        if eco.name == "Generic":
            continue
        # Dependencies
        if eco.dependencies:
            lines.append(f"## Dependencies ({eco.name})")
            if eco.package_manager:
                lines.append(f"Package manager: {eco.package_manager}")
            lines.append("")
            shown_deps = summarize_dependencies(eco.dependencies, max_items=max_deps)
            for dep in shown_deps.shown:
                ver = f" {dep.version}" if dep.version else ""
                cat = " (dev)" if dep.category == "dev" else ""
                lines.append(f"  - {dep.name}{ver}{cat}")
            if shown_deps.remaining > 0:
                lines.append(f"  ...{shown_deps.remaining} more")
            lines.append("")

    # Frameworks (combined across ecosystems)
    all_frameworks = result.all_frameworks
    if all_frameworks:
        lines.append("## Frameworks Detected")
        lines.append("")
        seen = set()
        for fw in all_frameworks:
            if fw.name not in seen:
                seen.add(fw.name)
                lines.append(f"  - {fw.name}")
        lines.append("")

    # Entry points (combined)
    all_eps = result.all_entry_points
    if all_eps:
        lines.append("## Entry Points")
        lines.append("")
        for ep in all_eps:
            lines.append(f"  - {ep.path} ({ep.kind})")
        lines.append("")

    # Routes
    if result.routes:
        lines.append("## Routes")
        lines.append("")
        for r in result.routes[:_MAX_DISPLAY_ROUTES]:
            lines.append(f"  {r.method:<6s} {r.path}  ({r.file})")
        if len(result.routes) > _MAX_DISPLAY_ROUTES:
            lines.append(f"  ...{len(result.routes) - _MAX_DISPLAY_ROUTES} more")
        lines.append("")

    # Hot files
    if result.hot_files:
        lines.append("## Hot Files (high blast radius)")
        lines.append("")
        graph = result.import_graph
        for hf in result.hot_files[:_MAX_DISPLAY_HOT_FILES]:
            if graph and hf in graph.imported_by:
                count = len(graph.imported_by[hf])
            else:
                count = result.hot_file_counts.get(hf, 0)
            lines.append(f"  - {hf} ({count} importers)")
        if len(result.hot_files) > _MAX_DISPLAY_HOT_FILES:
            lines.append(f"  ...{len(result.hot_files) - _MAX_DISPLAY_HOT_FILES} more")
        lines.append("")

    # Environment variables
    if result.env_vars:
        lines.append("## Environment Variables")
        lines.append("")
        for ev in result.env_vars[:_MAX_DISPLAY_ENV_VARS]:
            default_mark = " (has default)" if ev.has_default else " (required)"
            lines.append(f"  - {ev.name}{default_mark}")
        if len(result.env_vars) > _MAX_DISPLAY_ENV_VARS:
            lines.append(f"  ...{len(result.env_vars) - _MAX_DISPLAY_ENV_VARS} more")
        lines.append("")

    # Middleware
    if result.middleware:
        lines.append("## Middleware")
        lines.append("")
        for mw in result.middleware:
            lines.append(f"  - {mw.name} ({mw.file})")
        lines.append("")

    # Schemas section
    if result.schemas:
        lines.append("## Models/Schemas")
        lines.append("")
        shown = result.schemas[:_MAX_DISPLAY_SCHEMAS]
        for s in shown:
            fields = f"({s.field_count} fields)" if s.field_count else ""
            lines.append(f"  {s.name:<16} {s.file} {fields}")
        if len(result.schemas) > _MAX_DISPLAY_SCHEMAS:
            lines.append(f"  ...{len(result.schemas) - _MAX_DISPLAY_SCHEMAS} more")
        lines.append("")

    # Config files
    if result.config_files:
        lines.append("## Configuration")
        lines.append("")
        for cf in result.config_files[:_MAX_DISPLAY_CONFIGS]:
            lines.append(f"  - {cf}")
        if len(result.config_files) > _MAX_DISPLAY_CONFIGS:
            lines.append(f"  ...{len(result.config_files) - _MAX_DISPLAY_CONFIGS} more")
        lines.append("")

    # Token savings estimate
    if result.token_estimate and result.token_estimate.total > 0:
        est = result.token_estimate
        lines.append(f"## Token Savings: ~{_round_tokens(est.total)} tokens saved")
        lines.append("")
        if est.route_tokens:
            lines.append(f"  Routes: ~{_round_tokens(est.route_tokens)}")
        if est.hot_file_tokens:
            lines.append(f"  Hot files: ~{_round_tokens(est.hot_file_tokens)}")
        if est.env_var_tokens:
            lines.append(f"  Env vars: ~{_round_tokens(est.env_var_tokens)}")
        if est.file_scan_tokens:
            lines.append(f"  File scanning: ~{_round_tokens(est.file_scan_tokens)}")
        lines.append("")

    output = "\n".join(lines)

    # Replace token estimate in header
    output_tokens = len(output) // 4
    output = output.replace("~calculating", f"~{_round_tokens(output_tokens)} tokens")

    return output


def _round_tokens(n: int) -> str:
    """Round token count to nearest 100 for stable output."""
    if n < _ROUND_THRESHOLD:
        return str(n)
    rounded = round(n / _ROUND_THRESHOLD) * _ROUND_THRESHOLD
    return f"{rounded:,}"


def _copy_result(result: ScanResult) -> ScanResult:
    """Deep copy to prevent mutation of nested lists during rendering."""
    return copy.deepcopy(result)


def render_json(result: ScanResult) -> str:
    """Render scan result as JSON."""
    data = {
        "project_name": result.project_name,
        "total_files": result.total_files,
        "directories": [
            {
                "path": d.path,
                "file_count": d.file_count,
                "primary_language": d.primary_language,
            }
            for d in result.directories
        ],
        "ecosystems": [
            {
                "name": eco.name,
                "package_manager": eco.package_manager,
                "dependencies": [
                    {"name": d.name, "version": d.version, "category": d.category}
                    for d in eco.dependencies
                ],
                "frameworks": [{"name": f.name} for f in eco.frameworks],
                "entry_points": [
                    {"path": e.path, "kind": e.kind} for e in eco.entry_points
                ],
            }
            for eco in result.ecosystems
        ],
        "config_files": result.config_files,
        "routes": [
            {"method": r.method, "path": r.path, "file": r.file} for r in result.routes
        ],
        "hot_files": result.hot_files,
        "hot_file_counts": result.hot_file_counts,
        "env_vars": [
            {"name": v.name, "file": v.file, "has_default": v.has_default}
            for v in result.env_vars
        ],
        "middleware": [
            {"name": m.name, "kind": m.kind, "file": m.file} for m in result.middleware
        ],
        "schemas": [
            {
                "name": s.name,
                "file": s.file,
                "field_count": s.field_count,
                "framework": s.framework,
            }
            for s in result.schemas
        ],
        "token_savings": {
            "route_tokens": result.token_estimate.route_tokens
            if result.token_estimate
            else 0,
            "hot_file_tokens": result.token_estimate.hot_file_tokens
            if result.token_estimate
            else 0,
            "env_var_tokens": result.token_estimate.env_var_tokens
            if result.token_estimate
            else 0,
            "file_scan_tokens": result.token_estimate.file_scan_tokens
            if result.token_estimate
            else 0,
            "total": result.token_estimate.total if result.token_estimate else 0,
        },
        "estimated_tokens": len(
            render_markdown(
                _copy_result(result),
                include_timestamp=False,
            )
        )
        // 4,
    }
    return json.dumps(data, indent=2)


def render_blast_radius(result: BlastResult) -> str:
    """Render blast radius result as markdown."""
    lines = [
        f"# Blast Radius: {result.target}",
        f"Direct dependents: {len(result.direct)}"
        f" | Transitive: {len(result.transitive)}",
        "",
    ]

    if result.direct:
        lines.append("## Direct (imported by)")
        for f in result.direct:
            lines.append(f"  {f}")
        lines.append("")

    if result.transitive:
        lines.append("## Transitive (2nd+ degree)")
        for f, via in result.transitive:
            lines.append(f"  {f} (via {via})")
        lines.append("")

    if result.total_affected == 0:
        lines.append("No dependents found.")

    return "\n".join(lines)


_VALID_SECTIONS = {
    "structure",
    "deps",
    "routes",
    "hot-files",
    "env",
    "middleware",
    "models",
    "frameworks",
}


def render_section(result: ScanResult, section: str) -> str | None:  # noqa: PLR0912 - one branch per section type is the clearest structure
    """Render a single section of the context map.

    Returns None if the section name is invalid.
    """
    if section not in _VALID_SECTIONS:
        return None

    lines: list[str] = []

    if section == "structure":
        for d in result.directories[:_MAX_DISPLAY_SECTION_ITEMS]:
            lang = f" ({d.primary_language})" if d.primary_language else ""
            lines.append(f"  {d.path:<20} {d.file_count} files{lang}")
        if result.truncated_dirs:
            lines.append(f"  ...{result.truncated_dirs} more directories")

    elif section == "deps":
        for eco in result.ecosystems:
            pm = f" ({eco.package_manager})" if eco.package_manager else ""
            lines.append(f"## {eco.name}{pm}")
            for dep in eco.dependencies[:_MAX_DISPLAY_SECTION_ITEMS]:
                ver = f" {dep.version}" if dep.version else ""
                lines.append(f"  - {dep.name}{ver}")
            remaining = len(eco.dependencies) - _MAX_DISPLAY_SECTION_ITEMS
            if remaining > 0:
                lines.append(f"  ...{remaining} more")
            lines.append("")

    elif section == "routes":
        for r in result.routes[:_MAX_DISPLAY_SECTION_ROUTES]:
            lines.append(f"  {r.method:<7} {r.path:<30} ({r.file})")
        if len(result.routes) > _MAX_DISPLAY_SECTION_ROUTES:
            extra = len(result.routes) - _MAX_DISPLAY_SECTION_ROUTES
            lines.append(f"  ...{extra} more")

    elif section == "hot-files":
        graph = result.import_graph
        for hf in result.hot_files[:_MAX_DISPLAY_SECTION_HOT_FILES]:
            if graph and hf in graph.imported_by:
                count = len(graph.imported_by[hf])
            else:
                count = result.hot_file_counts.get(hf, 0)
            lines.append(f"  - {hf} ({count} importers)")
        if len(result.hot_files) > _MAX_DISPLAY_SECTION_HOT_FILES:
            extra = len(result.hot_files) - _MAX_DISPLAY_SECTION_HOT_FILES
            lines.append(f"  ...{extra} more")

    elif section == "env":
        for v in result.env_vars[:_MAX_DISPLAY_FILES]:
            default = " (has default)" if v.has_default else " (required)"
            lines.append(f"  - {v.name}{default}")
        if len(result.env_vars) > _MAX_DISPLAY_FILES:
            lines.append(f"  ...{len(result.env_vars) - _MAX_DISPLAY_FILES} more")

    elif section == "middleware":
        for m in result.middleware:
            lines.append(f"  - {m.name} [{m.kind}] ({m.file})")

    elif section == "models":
        schemas = getattr(result, "schemas", [])
        for s in schemas[:_MAX_DISPLAY_SECTION_ITEMS]:
            fields = f" ({s.field_count} fields)" if s.field_count else ""
            lines.append(f"  {s.name:<16} {s.file}{fields}")
        if len(schemas) > _MAX_DISPLAY_SECTION_ITEMS:
            lines.append(f"  ...{len(schemas) - _MAX_DISPLAY_SECTION_ITEMS} more")

    elif section == "frameworks":
        for fw in result.all_frameworks:
            locs = ", ".join(fw.locations[:3])
            lines.append(f"  - {fw.name} ({locs})")

    return "\n".join(lines) if lines else "(empty)"
