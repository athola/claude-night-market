"""Tiered audit escalation criteria and analysis helpers.

Provides data structures and logic for determining when
to escalate between audit tiers based on git history
analysis results.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field

# Keywords indicating a commit is fixing a previous commit
FIX_KEYWORDS = re.compile(
    r"\b(fix|revert|patch|hotfix)\b",
    re.IGNORECASE,
)

# Default thresholds
DEFAULT_CHURN_FILE_THRESHOLD = 3
DEFAULT_CHURN_REPEAT_THRESHOLD = 2
DEFAULT_LARGE_DIFF_THRESHOLD = 200
DEFAULT_NEW_FILE_CLUSTER_THRESHOLD = 5


@dataclass
class EscalationFlag:
    """A flag indicating an area warrants deeper review."""

    area: str
    reason: str
    detail: str


@dataclass
class Tier1Results:
    """Aggregated results from Tier 1 git-history analysis."""

    churn_flags: list[EscalationFlag] = field(default_factory=list)
    fix_flags: list[EscalationFlag] = field(default_factory=list)
    large_diff_flags: list[EscalationFlag] = field(default_factory=list)
    new_cluster_flags: list[EscalationFlag] = field(default_factory=list)

    def all_flags(self) -> list[EscalationFlag]:
        """Return all flags across all categories."""
        return (
            self.churn_flags
            + self.fix_flags
            + self.large_diff_flags
            + self.new_cluster_flags
        )

    def escalation_targets(self) -> list[str]:
        """Return deduplicated list of areas to escalate.

        Preserves first-seen order.
        """
        seen: set[str] = set()
        targets: list[str] = []
        for flag in self.all_flags():
            if flag.area not in seen:
                seen.add(flag.area)
                targets.append(flag.area)
        return targets


def _module_from_path(path: str) -> str:
    """Extract the module (top two directory levels) from a file path.

    Examples:
        plugins/imbue/skills/foo.md -> plugins/imbue
        hooks/pre-commit.py -> hooks
        src/main.py -> src
    """
    parts = path.strip("/").split("/")
    if len(parts) >= 2:
        return "/".join(parts[:2])
    return parts[0] if parts else ""


def check_churn_hotspots(
    file_changes: list[str],
    file_threshold: int = DEFAULT_CHURN_FILE_THRESHOLD,
    repeat_threshold: int = DEFAULT_CHURN_REPEAT_THRESHOLD,
) -> list[EscalationFlag]:
    """Identify modules with high file churn.

    Flags a module when it has >= file_threshold unique files
    changed AND at least one file changed > repeat_threshold times.

    Args:
        file_changes: List of file paths (one entry per commit change).
        file_threshold: Minimum unique files in a module to trigger.
        repeat_threshold: Minimum times one file must be changed.

    Returns:
        List of escalation flags for churning modules.

    """
    # Group by module
    module_files: dict[str, Counter[str]] = {}
    for path in file_changes:
        module = _module_from_path(path)
        if module not in module_files:
            module_files[module] = Counter()
        module_files[module][path] += 1

    flags: list[EscalationFlag] = []
    for module, file_counts in module_files.items():
        unique_files = len(file_counts)
        max_changes = max(file_counts.values()) if file_counts else 0

        if unique_files >= file_threshold and max_changes > repeat_threshold:
            most_changed = file_counts.most_common(1)[0]
            flags.append(
                EscalationFlag(
                    area=module,
                    reason="churn",
                    detail=(
                        f"{unique_files} files changed, "
                        f"{most_changed[0]} changed {most_changed[1]}x"
                    ),
                )
            )

    return flags


def check_fix_on_fix(
    commits: list[tuple[str, str]],
) -> list[EscalationFlag]:
    """Identify commits that fix previous commits.

    Args:
        commits: List of (hash, message) tuples.

    Returns:
        List of escalation flags for fix-on-fix patterns.

    """
    return [
        EscalationFlag(
            area="",
            reason="fix-on-fix",
            detail=f"{sha[:7]}: {message}",
        )
        for sha, message in commits
        if FIX_KEYWORDS.search(message)
    ]


def check_large_diffs(
    diff_stats: list[tuple[str, str, int, int]],
    threshold: int = DEFAULT_LARGE_DIFF_THRESHOLD,
) -> list[EscalationFlag]:
    """Identify commits with large diffs.

    Args:
        diff_stats: List of (hash, message, insertions, deletions).
        threshold: Total lines changed to trigger a flag.

    Returns:
        List of escalation flags for large commits.

    """
    return [
        EscalationFlag(
            area="",
            reason="large-diff",
            detail=f"{sha[:7]}: {msg} (+{ins}/-{dels})",
        )
        for sha, msg, ins, dels in diff_stats
        if ins + dels >= threshold
    ]


def check_new_file_clusters(
    new_files: list[str],
    threshold: int = DEFAULT_NEW_FILE_CLUSTER_THRESHOLD,
) -> list[EscalationFlag]:
    """Identify modules with many new files added.

    Args:
        new_files: List of newly added file paths.
        threshold: Minimum new files in a module to trigger.

    Returns:
        List of escalation flags for new file clusters.

    """
    module_counts: Counter[str] = Counter()
    for path in new_files:
        module_counts[_module_from_path(path)] += 1

    return [
        EscalationFlag(
            area=module,
            reason="new-file-cluster",
            detail=f"{count} new files added",
        )
        for module, count in module_counts.items()
        if count >= threshold
    ]


def should_escalate_to_tier2(results: Tier1Results) -> bool:
    """Determine whether Tier 1 results warrant Tier 2 escalation.

    Returns True if ANY flag category has flags.
    """
    return len(results.all_flags()) > 0
