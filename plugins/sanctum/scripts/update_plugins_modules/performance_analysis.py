"""Phase 2: Performance & Improvement Analysis module.

Analyzes skill execution metrics from memory-palace logs to identify:
- Unstable skills (stability_gap > 0.3)
- Recent failure patterns
- Low success rates (< 80%)
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


class PerformanceAnalyzer:
    """Analyze skill execution metrics."""

    def __init__(self, log_dir: Path | None = None):
        """Initialize analyzer with optional custom log directory."""
        self.log_dir = log_dir or Path.home() / ".claude" / "skills" / "logs"

    def analyze_plugin(self, plugin_name: str, days: int = 7) -> dict[str, Any]:
        """Analyze performance metrics for a specific plugin.

        Args:
            plugin_name: Name of the plugin to analyze
            days: Number of days to look back for logs (default: 7)

        Returns:
            Dict with unstable_skills, recent_failures, and low_success_rate lists

        """
        performance_data: dict[str, Any] = {
            "unstable_skills": [],
            "recent_failures": [],
            "low_success_rate": [],
        }

        if not self.log_dir.exists():
            return performance_data

        cutoff_date = datetime.now() - timedelta(days=days)
        log_files = list(self.log_dir.glob("*.jsonl"))

        if not log_files:
            return performance_data

        skill_stats = self._aggregate_stats(log_files, plugin_name, cutoff_date)
        return self._analyze_stats(skill_stats)

    def _aggregate_stats(
        self, log_files: list[Path], plugin_name: str, cutoff_date: datetime
    ) -> dict[str, dict[str, Any]]:
        """Aggregate execution statistics from log files."""
        skill_stats: dict[str, dict[str, Any]] = {}

        for log_file in log_files:
            try:
                for line in log_file.read_text(encoding="utf-8").strip().split("\n"):
                    if not line:
                        continue

                    entry = json.loads(line)
                    skill = entry.get("skill", "")

                    if not skill.startswith(f"{plugin_name}:"):
                        continue

                    # Check timestamp
                    timestamp_str = entry.get("timestamp", "")
                    if timestamp_str:
                        try:
                            timestamp = datetime.fromisoformat(
                                timestamp_str.replace("Z", "+00:00")
                            )
                            if timestamp < cutoff_date:
                                continue
                        except ValueError:
                            pass

                    # Initialize stats if needed
                    if skill not in skill_stats:
                        skill_stats[skill] = {
                            "success": 0,
                            "failure": 0,
                            "stability_gaps": [],
                        }

                    # Track outcomes
                    outcome = entry.get("outcome", "unknown")
                    if outcome == "success":
                        skill_stats[skill]["success"] += 1
                    elif outcome in ["failure", "error"]:
                        skill_stats[skill]["failure"] += 1

                    # Track stability gaps
                    metrics = entry.get("metrics", {})
                    if isinstance(metrics, dict) and "stability_gap" in metrics:
                        skill_stats[skill]["stability_gaps"].append(
                            metrics["stability_gap"]
                        )

            except (json.JSONDecodeError, OSError, KeyError):
                continue

        return skill_stats

    def _analyze_stats(self, skill_stats: dict[str, dict[str, Any]]) -> dict[str, Any]:
        """Analyze aggregated statistics and extract issues."""
        performance_data: dict[str, Any] = {
            "unstable_skills": [],
            "recent_failures": [],
            "low_success_rate": [],
        }

        for skill, stats in skill_stats.items():
            total = stats["success"] + stats["failure"]
            if total == 0:
                continue

            success_rate = stats["success"] / total

            # Check unstable skills (stability_gap > 0.3)
            if stats["stability_gaps"]:
                avg_gap = sum(stats["stability_gaps"]) / len(stats["stability_gaps"])
                if avg_gap > 0.3:
                    performance_data["unstable_skills"].append(
                        {"skill": skill, "stability_gap": round(avg_gap, 2)}
                    )

            # Check low success rate
            if success_rate < 0.8:
                performance_data["low_success_rate"].append(
                    {"skill": skill, "success_rate": round(success_rate, 2)}
                )

            # Check recent failures
            if stats["failure"] > 0:
                performance_data["recent_failures"].append(
                    {"skill": skill, "failures": stats["failure"]}
                )

        return performance_data
