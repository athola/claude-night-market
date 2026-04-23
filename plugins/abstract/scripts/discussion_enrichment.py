#!/usr/bin/env python3
"""Enrichment functions for Phase 6a Collective Intelligence posts.

Surfaces data the previous discussion poster threw away, runs the
existing analysis lenses to embed real recommendations, and clusters
errors into named failure modes. Every function is pure (no I/O
beyond reading the LEARNINGS.md or log directory the caller passes
in) so tests can pin behavior with synthetic fixtures.

Composition entry point: build_enriched_sections() returns a list
of section strings that post_learnings_to_discussions.py joins into
the final body.

Issue #69 follow-up.
"""

from __future__ import annotations

import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from insight_types import (  # noqa: E402 - sys.path adjusted above to discover sibling scripts
    AnalysisContext,
    Finding,
)

# Failure-mode clustering thresholds
_MIN_ERRORS_FOR_CLUSTER = 2
_CLUSTER_TERM_OVERLAP = 0.4
_STOP_WORDS = frozenset(
    {
        "the",
        "a",
        "an",
        "in",
        "on",
        "at",
        "to",
        "for",
        "of",
        "is",
        "was",
        "and",
        "or",
        "but",
        "with",
        "by",
        "as",
        "this",
        "that",
        "it",
        "from",
        "error",
        "failed",
        "failure",
        "exception",
    }
)
_MIN_TERM_LENGTH = 4

# Severity weight for ranking findings
_SEVERITY_RANK = {"high": 3, "medium": 2, "low": 1, "info": 0}

# Trend-noise thresholds (changes below these are not interesting)
_MIN_RATE_DELTA_PP = 5  # percentage points
_MIN_EXEC_DELTA = 5  # absolute run count

# Persistence detection minimum (must be >=2 to mean anything)
_MIN_PERSISTENCE_THRESHOLD = 2


@dataclass
class FailureMode:
    """A clustered group of similar errors."""

    name: str
    skills: list[str]
    sample_error: str
    occurrences: int


@dataclass
class EnrichedIssue:
    """High-impact issue with full surfaced detail."""

    skill: str
    issue_type: str
    severity: str
    metric: str
    detail: str
    recent_errors: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Parsers (read LEARNINGS.md, return structured data)
# ---------------------------------------------------------------------------


def parse_enriched_issues(content: str) -> list[EnrichedIssue]:
    """Parse High-Impact Issues including Detail and Recent Errors.

    The previous parser captured Type/Severity/Metric only and
    dropped Detail and Recent Errors. This version keeps everything.
    """
    section = _extract_section(content, "## High-Impact Issues")
    if not section:
        return []

    issues: list[EnrichedIssue] = []
    pattern = re.compile(
        r"### (?P<skill>.+?)\n(?P<body>.*?)(?=\n### |\n## |\n---|\Z)", re.DOTALL
    )
    for match in pattern.finditer(section):
        skill = match.group("skill").strip()
        body = match.group("body")
        issues.append(
            EnrichedIssue(
                skill=skill,
                issue_type=_field(body, "Type"),
                severity=_field(body, "Severity"),
                metric=_field(body, "Metric"),
                detail=_field(body, "Detail"),
                recent_errors=_recent_errors(body),
            )
        )
    return issues


def parse_perf_summary(content: str) -> list[dict[str, str]]:
    """Parse the Skill Performance Summary table into row dicts."""
    section = _extract_section(content, "## Skill Performance Summary")
    if not section:
        return []

    rows: list[dict[str, str]] = []
    row_re = re.compile(
        r"\|\s*`(?P<skill>[^`]+)`\s*\|\s*(?P<exec>\d+)\s*\|\s*(?P<rate>[^\|]+?)\s*\|"
        r"\s*(?P<dur>[^\|]+?)\s*\|\s*(?P<rating>[^\|]+?)\s*\|"
    )
    for m in row_re.finditer(section):
        rows.append(
            {
                "skill": m.group("skill").strip(),
                "executions": m.group("exec").strip(),
                "success_rate": m.group("rate").strip(),
                "avg_duration": m.group("dur").strip(),
                "rating": m.group("rating").strip(),
            }
        )
    return rows


def _extract_section(content: str, heading: str) -> str | None:
    pattern = re.escape(heading) + r"\n(.*?)(?=\n## |\n---|\Z)"
    m = re.search(pattern, content, re.DOTALL)
    return m.group(1).strip() if m else None


def _field(body: str, name: str) -> str:
    m = re.search(rf"\*\*{re.escape(name)}\*\*:\s*(.+)", body)
    return m.group(1).strip() if m else ""


def _recent_errors(body: str) -> list[str]:
    """Extract Recent Errors bullets from a section body."""
    errors_block = re.search(
        r"\*\*Recent Errors\*\*:\s*\n(.*?)(?=\n\*\*|\n### |\n## |\Z)",
        body,
        re.DOTALL,
    )
    if not errors_block:
        return []
    bullets = re.findall(r"^\s*-\s*(.+)$", errors_block.group(1), re.MULTILINE)
    return [b.strip().rstrip(".") for b in bullets if b.strip()]


# ---------------------------------------------------------------------------
# Failure-mode clustering
# ---------------------------------------------------------------------------


def cluster_failure_modes(
    errors_by_skill: dict[str, list[str]],
) -> list[FailureMode]:
    """Group similar errors across skills into named failure modes.

    Two errors cluster together when they share at least
    _CLUSTER_TERM_OVERLAP fraction of significant terms. The cluster
    name comes from the most common significant term in the group.
    """
    entries: list[tuple[str, str, set[str]]] = []
    for skill, errors in errors_by_skill.items():
        for err in errors:
            terms = _extract_terms(err)
            if terms:
                entries.append((skill, err, terms))

    used: set[int] = set()
    modes: list[FailureMode] = []
    for i, (skill_i, err_i, terms_i) in enumerate(entries):
        if i in used:
            continue
        group = [(skill_i, err_i, terms_i)]
        used.add(i)
        for j in range(i + 1, len(entries)):
            if j in used:
                continue
            _, _, terms_j = entries[j]
            if _jaccard(terms_i, terms_j) >= _CLUSTER_TERM_OVERLAP:
                group.append(entries[j])
                used.add(j)
        if len(group) >= _MIN_ERRORS_FOR_CLUSTER:
            modes.append(_name_mode(group))
    return modes


def _extract_terms(text: str) -> set[str]:
    words = re.findall(r"[A-Za-z][A-Za-z0-9_]+", text)
    return {
        w.lower()
        for w in words
        if len(w) >= _MIN_TERM_LENGTH and w.lower() not in _STOP_WORDS
    }


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _name_mode(
    group: list[tuple[str, str, set[str]]],
) -> FailureMode:
    counter: Counter[str] = Counter()
    for _, _, terms in group:
        counter.update(terms)
    name = counter.most_common(1)[0][0] if counter else "unknown"
    skills = sorted({skill for skill, _, _ in group})
    return FailureMode(
        name=name,
        skills=skills,
        sample_error=group[0][1][:140],
        occurrences=len(group),
    )


# ---------------------------------------------------------------------------
# Lens runner (uses existing pattern/delta/health/trend lenses)
# ---------------------------------------------------------------------------


def run_lenses(
    metrics_by_skill: dict[str, Any],
    previous_snapshot: dict[str, Any] | None = None,
) -> list[Finding]:
    """Invoke registered analysis lenses and return all Findings."""
    context = AnalysisContext(
        metrics=metrics_by_skill,
        previous_snapshot=previous_snapshot,
        performance_history=None,
        improvement_memory=None,
        trigger="discussion-post",
    )
    findings: list[Finding] = []
    for module_name in (
        "lenses.pattern_lens",
        "lenses.delta_lens",
        "lenses.health_lens",
        "lenses.trend_lens",
    ):
        try:
            module = __import__(module_name, fromlist=["analyze"])
        except ImportError:
            continue
        if not hasattr(module, "analyze"):
            continue
        try:
            findings.extend(module.analyze(context))
        except (AttributeError, KeyError, TypeError, ValueError) as exc:
            # Lens failure must not block posting.
            print(
                f"Warning: lens {module_name} raised {type(exc).__name__}: {exc}",
                file=sys.stderr,
            )
    return findings


def rank_findings(findings: list[Finding]) -> list[Finding]:
    """Order findings by severity (high first), then by source."""
    return sorted(
        findings,
        key=lambda f: (-_SEVERITY_RANK.get(f.severity, 0), f.source, f.summary),
    )


# ---------------------------------------------------------------------------
# Trend deltas
# ---------------------------------------------------------------------------


def compute_trend_deltas(
    current: dict[str, dict[str, Any]],
    previous: dict[str, dict[str, Any]] | None,
) -> dict[str, Any]:
    """Compute changes between two skill-metric snapshots.

    Inputs are dicts of skill -> {success_rate, total_executions}.
    Returns deltas plus lists of new and resolved skills.
    """
    if not previous:
        return {
            "new_skills": sorted(current.keys()),
            "resolved_skills": [],
            "rate_changes": [],
            "exec_changes": [],
        }

    cur_keys = set(current.keys())
    prev_keys = set(previous.keys())
    new_skills = sorted(cur_keys - prev_keys)
    resolved_skills = sorted(prev_keys - cur_keys)

    rate_changes: list[dict[str, Any]] = []
    exec_changes: list[dict[str, Any]] = []
    for skill in sorted(cur_keys & prev_keys):
        cur = current[skill]
        prv = previous[skill]
        d_rate = cur.get("success_rate", 0) - prv.get("success_rate", 0)
        d_exec = cur.get("total_executions", 0) - prv.get("total_executions", 0)
        if abs(d_rate) >= _MIN_RATE_DELTA_PP:
            rate_changes.append(
                {
                    "skill": skill,
                    "delta": round(d_rate, 1),
                    "now": cur.get("success_rate"),
                }
            )
        if abs(d_exec) >= _MIN_EXEC_DELTA:
            exec_changes.append(
                {"skill": skill, "delta": d_exec, "now": cur.get("total_executions")}
            )
    return {
        "new_skills": new_skills,
        "resolved_skills": resolved_skills,
        "rate_changes": rate_changes,
        "exec_changes": exec_changes,
    }


# ---------------------------------------------------------------------------
# Action items + persistence tracking
# ---------------------------------------------------------------------------


def generate_action_items(
    findings: list[Finding],
    persistent: list[dict[str, Any]] | None = None,
) -> list[str]:
    """Build a GitHub-flavored task list from findings + persistence state."""
    items: list[str] = []
    for f in rank_findings(findings)[:5]:
        if f.skill:
            items.append(
                f"- [ ] **{f.skill}**: {f.recommendation.splitlines()[0]} "
                f"_(from {f.source})_"
            )
        else:
            items.append(
                f"- [ ] {f.recommendation.splitlines()[0]} _(from {f.source})_"
            )

    for entry in persistent or []:
        skill = entry.get("skill", "(cross-cutting)")
        streak = entry.get("streak", 0)
        items.append(
            f"- [ ] File a tracking issue for **{skill}** "
            f"(unchanged for {streak} consecutive posts)"
        )

    if not items:
        items.append("- [ ] No high-priority actions this period. Continue monitoring.")
    return items


def track_issue_persistence(
    current_issues: list[EnrichedIssue],
    history: list[list[str]],
    threshold: int = 3,
) -> list[dict[str, Any]]:
    """Detect issues that have appeared in N consecutive posts.

    `history` is a list of prior post fingerprint lists, oldest first.
    A fingerprint is "{skill}|{issue_type}". When the current issue
    matches across `threshold-1` recent history entries (so it has
    actually appeared `threshold` times including today), flag it.
    """
    if threshold < _MIN_PERSISTENCE_THRESHOLD:
        return []

    persistent: list[dict[str, Any]] = []
    needed = threshold - 1
    if len(history) < needed:
        return persistent

    recent = history[-needed:]
    for issue in current_issues:
        fingerprint = f"{issue.skill}|{issue.issue_type}"
        if all(fingerprint in past for past in recent):
            persistent.append(
                {
                    "skill": issue.skill,
                    "issue_type": issue.issue_type,
                    "streak": threshold,
                }
            )
    return persistent


# ---------------------------------------------------------------------------
# Section formatters
# ---------------------------------------------------------------------------


def format_enriched_issues(issues: list[EnrichedIssue]) -> str:
    """Render High-Impact Issues with Detail + Recent Errors restored."""
    if not issues:
        return ""

    lines = ["## Top Issues", ""]
    for issue in issues[:5]:
        lines.append(f"### {issue.skill} [{issue.severity}]")
        lines.append("")
        lines.append(f"- **Type**: {issue.issue_type}")
        lines.append(f"- **Metric**: {issue.metric}")
        if issue.detail:
            lines.append(f"- **Detail**: {issue.detail}")
        if issue.recent_errors:
            lines.append("- **Recent Errors**:")
            for err in issue.recent_errors[:3]:
                lines.append(f"  - `{err}`")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def format_perf_summary(rows: list[dict[str, str]]) -> str:
    """Render the Skill Performance Summary table."""
    if not rows:
        return ""
    lines = [
        "## Performance Summary",
        "",
        "| Skill | Executions | Success Rate | Avg Duration | Rating |",
        "|-------|------------|--------------|--------------|--------|",
    ]
    for r in rows[:10]:
        lines.append(
            f"| `{r['skill']}` | {r['executions']} | {r['success_rate']} "
            f"| {r['avg_duration']} | {r['rating']} |"
        )
    lines.append("")
    return "\n".join(lines)


def format_failure_modes(modes: list[FailureMode]) -> str:
    """Render named failure-mode clusters with affected skills + sample."""
    if not modes:
        return ""
    lines = ["## Named Failure Modes", ""]
    for mode in modes[:5]:
        skills_str = ", ".join(f"`{s}`" for s in mode.skills)
        n_skills = len(mode.skills)
        lines.append(
            f"### `{mode.name}` "
            f"({mode.occurrences} occurrences across {n_skills} skill(s))"
        )
        lines.append("")
        lines.append(f"**Affected**: {skills_str}")
        lines.append("")
        lines.append(f"**Sample**: `{mode.sample_error}`")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def format_lens_findings(findings: list[Finding]) -> str:
    """Render lens-driven Findings with severity, source, evidence, recommendation."""
    if not findings:
        return ""
    ranked = rank_findings(findings)
    lines = ["## Insights & Recommendations", ""]
    for f in ranked[:6]:
        skill_str = f" ({f.skill})" if f.skill else ""
        lines.append(f"### [{f.type}] {f.summary}{skill_str}")
        lines.append("")
        lines.append(f"**Severity**: {f.severity}  |  **Source**: `{f.source}`")
        lines.append("")
        if f.evidence:
            lines.append("**Evidence:**")
            lines.append("")
            for ln in f.evidence.splitlines():
                lines.append(f"> {ln}")
            lines.append("")
        if f.recommendation:
            lines.append(f"**Recommendation**: {f.recommendation}")
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def format_trends(deltas: dict[str, Any]) -> str:
    """Render rate/exec changes and new/resolved skill lists."""
    parts = []
    if deltas.get("rate_changes"):
        parts.append("**Success rate changes (>=5pp):**")
        for c in deltas["rate_changes"][:5]:
            arrow = "+" if c["delta"] > 0 else ""
            parts.append(f"- `{c['skill']}`: {arrow}{c['delta']}pp (now {c['now']}%)")
    if deltas.get("exec_changes"):
        parts.append("")
        parts.append("**Execution volume changes (>=5):**")
        for c in deltas["exec_changes"][:5]:
            arrow = "+" if c["delta"] > 0 else ""
            parts.append(f"- `{c['skill']}`: {arrow}{c['delta']} runs (now {c['now']})")
    if deltas.get("new_skills"):
        parts.append("")
        parts.append(
            "**New this period**: "
            + ", ".join(f"`{s}`" for s in deltas["new_skills"][:5])
        )
    if deltas.get("resolved_skills"):
        parts.append(
            "**Resolved/quiet**: "
            + ", ".join(f"`{s}`" for s in deltas["resolved_skills"][:5])
        )
    if not parts:
        return ""
    return "## Trends vs Previous Snapshot\n\n" + "\n".join(parts).rstrip() + "\n"


def format_action_items(items: list[str]) -> str:
    """Wrap a list of pre-rendered action lines in the Action Items section."""
    if not items:
        return ""
    return "## Action Items\n\n" + "\n".join(items) + "\n"


def format_persistence_callout(persistent: list[dict[str, Any]]) -> str:
    """Render the persistent-issues callout that suggests filing real Issues."""
    if not persistent:
        return ""
    lines = ["## Persistent Issues (consider filing GitHub Issues)", ""]
    for entry in persistent[:5]:
        lines.append(
            f"- **{entry.get('skill')}** [{entry.get('issue_type')}] "
            f"persisted across {entry.get('streak')} consecutive posts."
        )
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Composition entry point
# ---------------------------------------------------------------------------


def errors_by_skill_from_issues(
    issues: list[EnrichedIssue],
) -> dict[str, list[str]]:
    """Pivot EnrichedIssue list into the {skill: [errors]} shape lenses expect."""
    out: dict[str, list[str]] = defaultdict(list)
    for issue in issues:
        out[issue.skill].extend(issue.recent_errors)
    return dict(out)
