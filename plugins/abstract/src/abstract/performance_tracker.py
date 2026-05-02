"""Performance tracker for monitoring skill scores across versions.

Implements the Hyperagents paper's (Zhang et al., 2026) PerformanceTracker
pattern adapted for Claude Code skills. Maps paper "generation" to skill
versions and computes improvement trends via moving average comparison.

Storage: ~/.claude/skills/performance_history.json
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .utils import emit_warn, safe_json_load


def _warn(message: str) -> None:
    """Forward to the shared stderr writer (D-12)."""
    emit_warn("performance_tracker", message)


class PerformanceTracker:
    """Track skill performance across versions (generations).

    Implements the Hyperagents paper's (Zhang et al., 2026)
    PerformanceTracker pattern adapted for Claude Code skills.
    Maps 'generation' to skill versions and computes improvement
    trends via moving average comparison.

    Storage: ~/.claude/skills/performance_history.json
    """

    def __init__(self, tracking_file: Path) -> None:
        self.tracking_file = tracking_file
        self.history: list[dict[str, Any]] = []
        self._load()

    def _load(self) -> None:
        """Load history from disk, creating file if absent."""
        if self.tracking_file.exists():
            data = safe_json_load(self.tracking_file)
            if data is None:
                _warn(f"corrupt tracking file {self.tracking_file}")
                backup = self.tracking_file.with_suffix(".corrupt")
                try:
                    self.tracking_file.rename(backup)
                    _warn(f"backed up corrupt file to {backup}")
                except OSError:
                    pass
                self.history = []
            else:
                self.history = data.get("history", [])
        else:
            self._save()

    def _save(self) -> None:
        """Persist history to disk using atomic write."""
        self.tracking_file.parent.mkdir(parents=True, exist_ok=True)
        tmp_file = self.tracking_file.with_suffix(".tmp")
        try:
            tmp_file.write_text(
                json.dumps(
                    {"history": self.history},
                    indent=2,
                )
            )
            tmp_file.replace(self.tracking_file)
        except OSError as e:
            _warn(f"failed to save history to {self.tracking_file}: {e}")
            if tmp_file.exists():
                tmp_file.unlink(missing_ok=True)

    def record_generation(
        self,
        skill_ref: str,
        version: str,
        score: float,
        domain: str = "general",
        metadata: dict | None = None,
    ) -> None:
        """Record performance for a skill version.

        Each entry stores: skill_ref, version, score (0.0-1.0),
        domain, timestamp, metadata dict.

        Args:
            skill_ref: Skill identifier (e.g., "abstract:skill-auditor").
            version: Skill version string (e.g., "1.0.0").
            score: Performance score in the range 0.0 to 1.0.
            domain: Skill domain category (default: "general").
            metadata: Optional arbitrary metadata dict.

        """
        entry: dict[str, Any] = {
            "skill_ref": skill_ref,
            "version": version,
            "score": score,
            "domain": domain,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": metadata or {},
        }
        self.history.append(entry)
        self._save()

    def get_improvement_trend(
        self,
        skill_ref: str,
        domain: str | None = None,
        window: int = 5,
    ) -> float | None:
        """Calculate improvement trend using moving average.

        Returns positive float if improving, negative if degrading,
        None if insufficient data (need window*2 entries).
        Directly from paper: recent_avg - older_avg.

        Args:
            skill_ref: Skill identifier to analyse.
            domain: Optional domain filter.
            window: Number of entries per averaging window.

        Returns:
            Trend value (recent_avg - older_avg), or None if not enough data.

        """
        entries = [
            e
            for e in self.history
            if e["skill_ref"] == skill_ref and (domain is None or e["domain"] == domain)
        ]

        if len(entries) < window * 2:
            return None

        scores: list[float] = [float(e["score"]) for e in entries]
        older_avg = sum(scores[:window]) / window
        recent_avg = sum(scores[-window:]) / window

        return recent_avg - older_avg

    def get_statistics(
        self,
        skill_ref: str | None = None,
        domain: str | None = None,
    ) -> dict:
        """Get comprehensive statistics.

        Returns: total_generations, best_score, worst_score,
        average_score, improvement_trend.

        Args:
            skill_ref: Optional skill filter.
            domain: Optional domain filter.

        Returns:
            Statistics dict.

        """
        entries = [
            e
            for e in self.history
            if (skill_ref is None or e["skill_ref"] == skill_ref)
            and (domain is None or e["domain"] == domain)
        ]

        if not entries:
            return {
                "total_generations": 0,
                "best_score": None,
                "worst_score": None,
                "average_score": None,
                "improvement_trend": None,
            }

        scores = [e["score"] for e in entries]
        trend: float | None = None
        if skill_ref is not None:
            trend = self.get_improvement_trend(skill_ref, domain=domain)

        return {
            "total_generations": len(entries),
            "best_score": max(scores),
            "worst_score": min(scores),
            "average_score": sum(scores) / len(scores),
            "improvement_trend": trend,
        }

    def get_best_performers(
        self,
        domain: str | None = None,
        top_k: int = 5,
    ) -> list:
        """Get top performing skill versions.

        Returns list of dicts with skill_ref, version, score, domain.
        Sorted by score descending.

        Args:
            domain: Optional domain filter.
            top_k: Maximum number of results.

        Returns:
            List of top-performing entry dicts.

        """
        entries = [e for e in self.history if (domain is None or e["domain"] == domain)]

        sorted_entries = sorted(entries, key=lambda e: e["score"], reverse=True)

        return [
            {
                "skill_ref": e["skill_ref"],
                "version": e["version"],
                "score": e["score"],
                "domain": e["domain"],
            }
            for e in sorted_entries[:top_k]
        ]

    def compare_versions(
        self,
        skill_ref: str,
        v1: str,
        v2: str,
    ) -> dict:
        """Compare two versions of the same skill.

        Returns: v1_scores (list), v2_scores (list),
        v1_avg, v2_avg, improvement (v2_avg - v1_avg),
        improved (bool).

        Args:
            skill_ref: Skill identifier.
            v1: First version string.
            v2: Second version string.

        Returns:
            Comparison dict.

        """
        v1_scores = [
            e["score"]
            for e in self.history
            if e["skill_ref"] == skill_ref and e["version"] == v1
        ]
        v2_scores = [
            e["score"]
            for e in self.history
            if e["skill_ref"] == skill_ref and e["version"] == v2
        ]

        v1_avg = sum(v1_scores) / len(v1_scores) if v1_scores else 0.0
        v2_avg = sum(v2_scores) / len(v2_scores) if v2_scores else 0.0
        improvement = v2_avg - v1_avg

        return {
            "v1_scores": v1_scores,
            "v2_scores": v2_scores,
            "v1_avg": v1_avg,
            "v2_avg": v2_avg,
            "improvement": improvement,
            "improved": improvement > 0,
        }
