"""Core data structures for the Insight Engine.

Finding represents a single insight produced by an analyzer
lens. AnalysisContext carries all data a lens needs to run.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Valid insight types and their title prefixes
INSIGHT_TYPES = {
    "Trend": "[Trend]",
    "Pattern": "[Pattern]",
    "Bug Alert": "[Bug Alert]",
    "Optimization": "[Optimization]",
    "Improvement": "[Improvement]",
    "PR Finding": "[PR Finding]",
    "Health Check": "[Health Check]",
}


@dataclass
class Finding:
    """A single insight produced by an analyzer lens."""

    type: str
    severity: str  # "high", "medium", "low", "info"
    skill: str  # affected skill or "" for cross-cutting
    summary: str  # one-line, used in title and hash
    evidence: str  # markdown body with data/metrics
    recommendation: str  # what to do about it
    source: str  # which lens/trigger produced this
    related_files: list[str] = field(default_factory=list)

    def title(self) -> str:
        """Generate a discussion title from this finding."""
        prefix = INSIGHT_TYPES.get(self.type, f"[{self.type}]")
        if self.skill:
            raw = f"{prefix} {self.skill}: {self.summary}"
        else:
            raw = f"{prefix} {self.summary}"
        # GitHub titles are capped at 255 characters
        return raw[:255]


@dataclass
class AnalysisContext:
    """Data available to analyzer lenses during a run."""

    metrics: dict[str, Any]
    previous_snapshot: dict[str, Any] | None
    performance_history: Any  # PerformanceTracker or None
    improvement_memory: Any  # ImprovementMemory or None
    code_paths: list[Path] = field(default_factory=list)
    pr_diff: str | None = None
    trigger: str = "stop"


def finding_hash(finding: Finding) -> str:
    """Compute a deterministic content hash for dedup.

    Hash is based on type, skill, and summary only.
    Evidence and recommendation are excluded so that
    updated data for the same observation gets the
    same hash.
    """
    key = f"{finding.type}:{finding.skill}:{finding.summary}"
    return hashlib.sha256(key.encode()).hexdigest()[:12]
