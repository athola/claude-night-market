#!/usr/bin/env python3
"""Aggregate skill execution logs into LEARNINGS.md.

Analyzes skill execution logs from ~/.claude/skills/logs/ and generates
a consolidated LEARNINGS.md file with:
- High-impact issues (failure patterns, slow skills)
- Performance metrics (avg duration, success rate)
- Qualitative insights (common friction, improvement suggestions)

Part of Issue #69 Phase 3: Log Aggregation & Pattern Detection
"""

from __future__ import annotations

import json
import statistics
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

# Optional Hyperagents modules (may not be installed)
_src = Path(__file__).resolve().parent.parent / "src"
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

from abstract.utils import get_log_directory  # noqa: E402 - import after sys.path setup

try:
    from abstract.improvement_memory import ImprovementMemory

    _HAS_IMPROVEMENT_MEMORY = True
except ImportError:
    _HAS_IMPROVEMENT_MEMORY = False
try:
    from abstract.performance_tracker import PerformanceTracker

    _HAS_PERFORMANCE_TRACKER = True
except ImportError:
    _HAS_PERFORMANCE_TRACKER = False

# Analysis thresholds
MIN_EXECUTIONS_FOR_FAILURE_ANALYSIS = 5
HIGH_FAILURE_THRESHOLD_PERCENT = 70  # Success rate below this is concerning
LOW_RATING_THRESHOLD = 3.0  # Ratings below this need attention
EXCESSIVE_FAILURES_THRESHOLD = 10  # Total failures above this is concerning
SLOW_EXECUTION_THRESHOLD_MS = 10000  # 10 seconds
LOW_USER_RATING_THRESHOLD = 3.5  # For detection in aggregate view


@dataclass
class SkillLogSummary:
    """Metrics for a single skill."""

    skill: str
    plugin: str
    skill_name: str
    total_executions: int
    success_count: int
    failure_count: int
    partial_count: int
    avg_duration_ms: float
    max_duration_ms: int
    success_rate: float
    avg_rating: float | None
    common_friction: list[str]
    improvement_suggestions: list[str]
    recent_errors: list[str]


@dataclass
class AggregationResult:
    """Result of log aggregation."""

    timestamp: datetime
    skills_analyzed: int
    total_executions: int
    high_impact_issues: list[dict[str, Any]]
    slow_skills: list[dict[str, Any]]
    low_rated_skills: list[dict[str, Any]]
    metrics_by_skill: dict[str, SkillLogSummary]


def get_learnings_path() -> Path:
    """Get path to LEARNINGS.md file."""
    claude_home = Path.home() / ".claude"
    return claude_home / "skills" / "LEARNINGS.md"


# Session-id prefixes used by tests, dogfood runs, and other synthetic
# harnesses. Production session ids are UUID-shaped, so a startswith
# match on these prefixes is a reliable filter without false positives.
_SYNTHETIC_SESSION_PREFIXES: tuple[str, ...] = (
    "test-",
    "dogfood-",
    "fixture-",
)


def _is_synthetic_session(entry: dict[str, Any]) -> bool:
    """Return True if a log entry is from a synthetic harness.

    Filters out test runs and dogfood data so production aggregation
    reflects real usage. Missing or empty session_id is treated as
    real (we never want to silently drop unfamiliar production
    formats).
    """
    session_id = entry.get("context", {}).get("session_id", "")
    if not session_id:
        return False
    return any(session_id.startswith(p) for p in _SYNTHETIC_SESSION_PREFIXES)


def load_log_entries(
    log_dir: Path, days_back: int = 30, *, include_synthetic: bool = False
) -> dict[str, list[dict[str, Any]]]:
    """Load all log entries from the last N days.

    Args:
        log_dir: Base log directory
        days_back: Number of days to look back
        include_synthetic: If True, keep entries from synthetic harnesses
            (test-session, dogfood-*). Default False so production
            aggregation stays clean.

    Returns:
        Dict mapping skill name to list of log entries

    """
    entries_by_skill: dict[str, list[dict[str, Any]]] = defaultdict(list)
    cutoff = datetime.now(timezone.utc) - timedelta(days=days_back)

    # Traverse plugin/skill directory structure
    for plugin_dir in log_dir.iterdir():
        if not plugin_dir.is_dir():
            continue

        for skill_dir in plugin_dir.iterdir():
            if not skill_dir.is_dir():
                continue

            skill_key = f"{plugin_dir.name}:{skill_dir.name}"

            # Load all JSONL files in skill directory
            for log_file in skill_dir.glob("*.jsonl"):
                try:
                    with open(log_file) as f:
                        for line in f:
                            if not line.strip():
                                continue

                            try:
                                entry = json.loads(line)
                                # Filter by date
                                entry_time = datetime.fromisoformat(entry["timestamp"])
                                if entry_time < cutoff:
                                    continue
                                if not include_synthetic and _is_synthetic_session(
                                    entry
                                ):
                                    continue
                                entries_by_skill[skill_key].append(entry)
                            except (
                                json.JSONDecodeError,
                                KeyError,
                                ValueError,
                            ):
                                # Skip individual bad entries, not the whole file
                                continue
                except OSError as e:
                    print(f"Warning: Could not read {log_file}: {e}")
                    continue

    return dict(entries_by_skill)


def calculate_skill_metrics(
    skill: str, entries: list[dict[str, Any]]
) -> SkillLogSummary:
    """Calculate metrics for a single skill.

    Args:
        skill: Skill name (plugin:skill-name)
        entries: List of log entries for this skill

    Returns:
        SkillLogSummary object

    """
    plugin, skill_name = skill.split(":", 1)

    # Count outcomes
    outcome_counts = Counter(e["outcome"] for e in entries)
    success_count = outcome_counts["success"]
    failure_count = outcome_counts["failure"]
    partial_count = outcome_counts["partial"]

    # Duration stats
    durations = [e["duration_ms"] for e in entries if "duration_ms" in e]
    avg_duration = statistics.mean(durations) if durations else 0.0
    max_duration = max(durations) if durations else 0

    # Success rate
    total = len(entries)
    success_rate = (success_count / total * 100) if total > 0 else 0.0

    # Qualitative evaluation data
    evaluations = [
        e["qualitative_evaluation"]
        for e in entries
        if e.get("qualitative_evaluation") is not None
    ]

    # Average rating
    ratings = [ev["rating"] for ev in evaluations if "rating" in ev]
    avg_rating = statistics.mean(ratings) if ratings else None

    # Common friction points (aggregate across evaluations)
    friction_points: list[str] = []
    for ev in evaluations:
        friction_points.extend(ev.get("friction_points", []))

    # Count friction frequency
    friction_counts: dict[str, int] = defaultdict(int)
    for point in friction_points:
        friction_counts[point] += 1

    # Top 5 most common friction points
    common_friction = sorted(friction_counts.items(), key=lambda x: x[1], reverse=True)[
        :5
    ]

    # Improvement suggestions (aggregate)
    suggestions: list[str] = []
    for ev in evaluations:
        suggestions.extend(ev.get("improvement_suggestions", []))

    # Recent errors (last 5 failures)
    recent_errors = [
        e.get("error", "Unknown error") for e in entries if e["outcome"] == "failure"
    ][-5:]

    return SkillLogSummary(
        skill=skill,
        plugin=plugin,
        skill_name=skill_name,
        total_executions=total,
        success_count=success_count,
        failure_count=failure_count,
        partial_count=partial_count,
        avg_duration_ms=avg_duration,
        max_duration_ms=max_duration,
        success_rate=success_rate,
        avg_rating=avg_rating,
        common_friction=[f for f, _ in common_friction],
        improvement_suggestions=list(set(suggestions)),  # Unique suggestions
        recent_errors=recent_errors,
    )


def detect_high_impact_issues(
    metrics_by_skill: dict[str, SkillLogSummary],
) -> list[dict[str, Any]]:
    """Detect high-impact issues across all skills.

    Args:
        metrics_by_skill: Metrics for each skill

    Returns:
        List of high-impact issues with severity and details

    """
    issues: list[dict[str, Any]] = []

    for skill, metrics in metrics_by_skill.items():
        # High failure rate (>30%)
        if (
            metrics.total_executions >= MIN_EXECUTIONS_FOR_FAILURE_ANALYSIS
            and metrics.success_rate < HIGH_FAILURE_THRESHOLD_PERCENT
        ):
            issues.append(
                {
                    "skill": skill,
                    "type": "high_failure_rate",
                    "severity": "high",
                    "metric": f"{metrics.success_rate:.1f}% success rate",
                    "detail": (
                        f"{metrics.failure_count}/{metrics.total_executions} failures"
                    ),
                    "errors": metrics.recent_errors[:3],  # Top 3 errors
                }
            )

        # Low rating (<3.0)
        if metrics.avg_rating is not None and metrics.avg_rating < LOW_RATING_THRESHOLD:
            issues.append(
                {
                    "skill": skill,
                    "type": "low_rating",
                    "severity": "medium",
                    "metric": f"{metrics.avg_rating:.1f}/5.0 rating",
                    "detail": "User evaluations indicate poor effectiveness",
                    "friction": metrics.common_friction[:3],  # Top 3 friction points
                }
            )

        # Excessive failures (>10 in analysis period)
        if metrics.failure_count > EXCESSIVE_FAILURES_THRESHOLD:
            issues.append(
                {
                    "skill": skill,
                    "type": "excessive_failures",
                    "severity": "high",
                    "metric": f"{metrics.failure_count} failures",
                    "detail": "Failing frequently across many sessions",
                    "errors": metrics.recent_errors[:3],
                }
            )

    _ORDER = {"high": 0, "medium": 1, "low": 2}
    return sorted(issues, key=lambda x: _ORDER.get(x["severity"], 2))


def detect_slow_skills(
    metrics_by_skill: dict[str, SkillLogSummary],
    threshold_ms: int = SLOW_EXECUTION_THRESHOLD_MS,
) -> list[dict[str, Any]]:
    """Detect skills with slow execution times.

    Args:
        metrics_by_skill: Metrics for each skill
        threshold_ms: Duration threshold in milliseconds

    Returns:
        List of slow skills with performance data

    """
    slow: list[dict[str, Any]] = []

    for skill, metrics in metrics_by_skill.items():
        if metrics.avg_duration_ms > threshold_ms:
            slow.append(
                {
                    "skill": skill,
                    "avg_duration_ms": metrics.avg_duration_ms,
                    "max_duration_ms": metrics.max_duration_ms,
                    "executions": metrics.total_executions,
                }
            )

    return sorted(slow, key=lambda x: x["avg_duration_ms"], reverse=True)


def detect_low_rated_skills(
    metrics_by_skill: dict[str, SkillLogSummary],
    threshold: float = LOW_USER_RATING_THRESHOLD,
) -> list[dict[str, Any]]:
    """Detect skills with low user ratings.

    Args:
        metrics_by_skill: Metrics for each skill
        threshold: Rating threshold (1-5 scale)

    Returns:
        List of low-rated skills with feedback

    """
    low_rated: list[dict[str, Any]] = []

    for skill, metrics in metrics_by_skill.items():
        if metrics.avg_rating is not None and metrics.avg_rating < threshold:
            low_rated.append(
                {
                    "skill": skill,
                    "rating": metrics.avg_rating,
                    "friction": metrics.common_friction,
                    "suggestions": metrics.improvement_suggestions,
                }
            )

    return sorted(low_rated, key=lambda x: x["rating"])


def aggregate_logs(days_back: int = 30) -> AggregationResult:
    """Aggregate skill execution logs.

    Args:
        days_back: Number of days to analyze

    Returns:
        AggregationResult with all metrics and insights

    """
    log_dir = get_log_directory()
    entries_by_skill = load_log_entries(log_dir, days_back)

    # Calculate metrics for each skill
    metrics_by_skill = {
        skill: calculate_skill_metrics(skill, entries)
        for skill, entries in entries_by_skill.items()
    }

    # Detect issues and patterns
    high_impact_issues = detect_high_impact_issues(metrics_by_skill)
    slow_skills = detect_slow_skills(metrics_by_skill)
    low_rated_skills = detect_low_rated_skills(metrics_by_skill)

    # Calculate totals
    total_executions = sum(m.total_executions for m in metrics_by_skill.values())

    return AggregationResult(
        timestamp=datetime.now(timezone.utc),
        skills_analyzed=len(metrics_by_skill),
        total_executions=total_executions,
        high_impact_issues=high_impact_issues,
        slow_skills=slow_skills,
        low_rated_skills=low_rated_skills,
        metrics_by_skill=metrics_by_skill,
    )


def format_high_impact_issues(issues: list[dict[str, Any]]) -> list[str]:
    """Format high-impact issues section."""
    lines = [
        "## High-Impact Issues",
        "",
        "Skills with significant problems requiring immediate attention.",
        "",
    ]

    for issue in issues[:10]:  # Top 10
        lines.append(f"### {issue['skill']}")
        lines.append(f"**Type**: {issue['type']}")
        lines.append(f"**Severity**: {issue['severity']}")
        lines.append(f"**Metric**: {issue['metric']}")
        lines.append(f"**Detail**: {issue['detail']}")

        if "errors" in issue and issue["errors"]:
            lines.append("**Recent Errors**:")
            for error in issue["errors"]:
                lines.append(f"- {error[:100]}...")  # Truncate

        if "friction" in issue and issue["friction"]:
            lines.append("**Common Friction**:")
            for friction in issue["friction"]:
                lines.append(f"- {friction}")

        lines.append("")

    lines.extend(["---", ""])
    return lines


def format_slow_skills(slow_skills: list[dict[str, Any]]) -> list[str]:
    """Format slow skills section."""
    lines = [
        "## Slow Execution",
        "",
        "Skills exceeding 10s average execution time.",
        "",
        "| Skill | Avg Duration | Max Duration | Executions |",
        "|-------|--------------|--------------|------------|",
    ]

    for slow in slow_skills[:10]:
        avg_sec = slow["avg_duration_ms"] / 1000
        max_sec = slow["max_duration_ms"] / 1000
        skill_name = slow["skill"]
        executions = slow["executions"]
        lines.append(
            f"| `{skill_name}` | {avg_sec:.1f}s | {max_sec:.1f}s | {executions} |"
        )

    lines.extend(["", "---", ""])
    return lines


def format_low_rated_skills(low_rated: list[dict[str, Any]]) -> list[str]:
    """Format low-rated skills section."""
    lines = [
        "## Low User Ratings",
        "",
        "Skills with < 3.5/5.0 average rating from evaluations.",
        "",
    ]

    for low in low_rated:
        lines.append(f"### {low['skill']} - {low['rating']:.1f}/5.0")

        if low["friction"]:
            lines.append("**Common Friction**:")
            for friction in low["friction"][:5]:
                lines.append(f"- {friction}")

        if low["suggestions"]:
            lines.append("**Improvement Suggestions**:")
            for suggestion in low["suggestions"][:5]:
                lines.append(f"- {suggestion}")

        lines.append("")

    lines.extend(["---", ""])
    return lines


def format_skill_summary(metrics_by_skill: dict[str, SkillLogSummary]) -> list[str]:
    """Format skill performance summary table."""
    lines = [
        "## Skill Performance Summary",
        "",
        "| Skill | Executions | Success Rate | Avg Duration | Rating |",
        "|-------|------------|--------------|--------------|--------|",
    ]

    sorted_skills = sorted(
        metrics_by_skill.items(), key=lambda x: x[1].total_executions, reverse=True
    )[:20]  # Top 20 most-used

    for skill, metrics in sorted_skills:
        rating_str = f"{metrics.avg_rating:.1f}/5.0" if metrics.avg_rating else "N/A"
        duration_sec = metrics.avg_duration_ms / 1000
        lines.append(
            f"| `{skill}` | {metrics.total_executions} | "
            f"{metrics.success_rate:.1f}% | {duration_sec:.1f}s | {rating_str} |"
        )

    return lines


def extract_pinned_section(content: str) -> str:
    """Extract the Pinned Learnings section from existing content.

    Returns the section content (without header) or empty
    string if not found.
    """
    if "## Pinned Learnings" not in content:
        return ""

    start = content.index("## Pinned Learnings")
    after_header = content[start + len("## Pinned Learnings") :]
    next_section = after_header.find("\n## ")
    if next_section == -1:
        section = after_header.strip()
    else:
        section = after_header[:next_section].strip()

    return section


def _format_hyperagents_section() -> list[str]:  # noqa: PLR0912 - report section requires many conditional formatting branches
    """Format Hyperagents performance trends and meta-insights.

    Best-effort: returns empty list if modules unavailable.
    """
    lines: list[str] = []
    _max_trend_skills = 20

    # Performance trends from PerformanceTracker
    if _HAS_PERFORMANCE_TRACKER:
        try:
            tracker_file = (
                Path.home() / ".claude" / "skills" / "performance_history.json"
            )
            if tracker_file.exists():
                tracker = PerformanceTracker(tracker_file)
                if tracker.history:
                    lines.extend(["", "## Performance Trends (Hyperagents)", ""])
                    seen: set[str] = set()
                    for entry in tracker.history:
                        ref = entry.get("skill_ref")
                        if not ref or ref in seen:
                            continue
                        seen.add(ref)
                        trend = tracker.get_improvement_trend(ref)
                        if trend is not None:
                            direction = "improving" if trend > 0 else "degrading"
                            lines.append(
                                f"- `{ref}`: {direction} (trend: {trend:+.3f})"
                            )
                        if len(seen) >= _max_trend_skills:
                            break
                    lines.append("")
        except (OSError, KeyError) as e:
            sys.stderr.write(
                f"aggregate_skill_logs: PerformanceTracker section skipped: {e}\n"
            )

    # Meta-insights from ImprovementMemory
    if _HAS_IMPROVEMENT_MEMORY:
        try:
            mem_file = Path.home() / ".claude" / "skills" / "improvement_memory.json"
            if mem_file.exists():
                mem = ImprovementMemory(mem_file)
                effective = mem.get_effective_strategies()
                failed = mem.get_failed_strategies()
                if effective or failed:
                    lines.extend(["## Meta-Insights (Hyperagents)", ""])
                    total = len(effective) + len(failed)
                    rate = len(effective) / total if total else 0
                    lines.append(
                        f"Improvement effectiveness: {rate:.0%}"
                        f" ({len(effective)}/{total})"
                    )
                    lines.append("")
                    if effective:
                        best = effective[0]
                        lines.append(
                            f"Best strategy: {best.get('change_summary', 'N/A')}"
                            f" (+{best.get('improvement', 0):.3f})"
                        )
                    if failed:
                        worst = failed[0]
                        lines.append(
                            f"Avoid: {worst.get('change_summary', 'N/A')}"
                            f" ({worst.get('improvement', 0):+.3f})"
                        )
                    lines.append("")
        except (OSError, KeyError) as e:
            sys.stderr.write(
                f"aggregate_skill_logs: ImprovementMemory section skipped: {e}\n"
            )

    return lines


def generate_learnings_md(result: AggregationResult, existing_pinned: str = "") -> str:
    """Generate LEARNINGS.md content from aggregation result.

    Args:
        result: Aggregation result
        existing_pinned: Content from an existing Pinned Learnings
            section to preserve across regeneration

    Returns:
        Markdown content for LEARNINGS.md

    """
    lines = [
        "# Skill Performance Learnings",
        "",
        f"**Last Updated**: {result.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}",
        "**Analysis Period**: Last 30 days",
        f"**Skills Analyzed**: {result.skills_analyzed}",
        f"**Total Executions**: {result.total_executions}",
        "",
        "---",
        "",
    ]

    # Pinned section (preserved across regenerations)
    if existing_pinned:
        lines.append("## Pinned Learnings")
        lines.append("")
        lines.append(existing_pinned)
        lines.append("")
        lines.extend(["---", ""])

    # Add sections using helper functions
    if result.high_impact_issues:
        lines.extend(format_high_impact_issues(result.high_impact_issues))

    if result.slow_skills:
        lines.extend(format_slow_skills(result.slow_skills))

    if result.low_rated_skills:
        lines.extend(format_low_rated_skills(result.low_rated_skills))

    # Skill performance summary
    lines.extend(format_skill_summary(result.metrics_by_skill))

    # Hyperagents: Include performance trends and meta-insights
    lines.extend(_format_hyperagents_section())

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("*Generated by aggregate_skill_logs.py (Issue #69 Phase 3)*")

    return "\n".join(lines)


def main() -> None:
    """Main entry point."""
    # Parse command-line arguments
    days_back = 30
    if len(sys.argv) > 1:
        try:
            days_back = int(sys.argv[1])
        except ValueError:
            print(f"Usage: {sys.argv[0]} [days_back]", file=sys.stderr)
            sys.exit(1)

    # Run aggregation
    print(f"Aggregating logs from last {days_back} days...")
    result = aggregate_logs(days_back)

    # Preserve existing pinned learnings across regeneration
    learnings_path = get_learnings_path()
    existing_pinned = ""
    if learnings_path.exists():
        existing_pinned = extract_pinned_section(learnings_path.read_text())

    # Generate LEARNINGS.md
    learnings_content = generate_learnings_md(result, existing_pinned=existing_pinned)

    # Write to file
    learnings_path.parent.mkdir(parents=True, exist_ok=True)
    learnings_path.write_text(learnings_content)

    # Print summary
    print(f"\n✅ LEARNINGS.md generated: {learnings_path}")
    print("\nSummary:")
    print(f"  Skills Analyzed: {result.skills_analyzed}")
    print(f"  Total Executions: {result.total_executions}")
    print(f"  High-Impact Issues: {len(result.high_impact_issues)}")
    print(f"  Slow Skills: {len(result.slow_skills)}")
    print(f"  Low-Rated Skills: {len(result.low_rated_skills)}")


if __name__ == "__main__":
    main()
