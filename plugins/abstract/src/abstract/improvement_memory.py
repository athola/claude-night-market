"""Persistent improvement memory for the Hyperagents self-improvement loop.

Implements the persistent memory pattern from Zhang et al. (2026):
stores synthesized insights, causal hypotheses, and forward-looking
strategies so improvement compounds across runs rather than restarting
from scratch each time LEARNINGS.md is regenerated.

Storage: ~/.claude/skills/improvement_memory.json
Consumed by: skill-improver for data-driven improvement decisions.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .utils import safe_json_load


def _warn(message: str) -> None:
    """Write a warning message to stderr."""
    sys.stderr.write(f"improvement_memory: {message}\n")


class ImprovementMemory:
    """Persistent memory for improvement insights.

    Implements the Hyperagents paper's (Zhang et al., 2026) persistent
    memory pattern. Stores synthesized insights beyond raw metrics:
    causal hypotheses about what improvements worked and why,
    best-performer analysis, and forward-looking strategies.

    Survives LEARNINGS.md regeneration. Consumed by skill-improver
    for data-driven improvement decisions.

    Storage: ~/.claude/skills/improvement_memory.json
    """

    CATEGORIES = (
        "strategy_success",
        "strategy_failure",
        "causal_hypothesis",
        "best_performer_analysis",
        "regression_diagnosis",
    )

    MAX_INSIGHTS_PER_SKILL = 50
    MAX_OUTCOMES_PER_SKILL = 100

    def __init__(self, memory_file: Path) -> None:
        self.memory_file = memory_file
        self.insights: dict[str, list[dict[str, Any]]] = {}
        self.outcomes: dict[str, list[dict[str, Any]]] = {}
        self._load()

    def _load(self) -> None:
        """Load memory from disk, creating if absent."""
        if self.memory_file.exists():
            data = safe_json_load(self.memory_file)
            if data is None:
                _warn(f"corrupt memory file {self.memory_file}")
                backup = self.memory_file.with_suffix(".corrupt")
                try:
                    self.memory_file.rename(backup)
                    _warn(f"backed up corrupt file to {backup}")
                except OSError:
                    pass
                self.insights = {}
                self.outcomes = {}
            else:
                self.insights = data.get("insights", {})
                self.outcomes = data.get("outcomes", {})
        else:
            self._save()

    def _save(self) -> None:
        """Persist memory to disk using atomic write."""
        self.memory_file.parent.mkdir(parents=True, exist_ok=True)
        tmp_file = self.memory_file.with_suffix(".tmp")
        try:
            tmp_file.write_text(
                json.dumps(
                    {"insights": self.insights, "outcomes": self.outcomes},
                    indent=2,
                )
            )
            tmp_file.replace(self.memory_file)
        except OSError as e:
            _warn(f"failed to save memory to {self.memory_file}: {e}")
            if tmp_file.exists():
                tmp_file.unlink(missing_ok=True)

    def _prune_insights(self, skill_ref: str) -> None:
        """Keep only the most recent MAX_INSIGHTS_PER_SKILL entries."""
        entries = self.insights.get(skill_ref, [])
        if len(entries) > self.MAX_INSIGHTS_PER_SKILL:
            self.insights[skill_ref] = entries[-self.MAX_INSIGHTS_PER_SKILL :]

    def _prune_outcomes(self, skill_ref: str) -> None:
        """Keep only the most recent MAX_OUTCOMES_PER_SKILL entries."""
        entries = self.outcomes.get(skill_ref, [])
        if len(entries) > self.MAX_OUTCOMES_PER_SKILL:
            self.outcomes[skill_ref] = entries[-self.MAX_OUTCOMES_PER_SKILL :]

    def record_insight(
        self,
        skill_ref: str,
        category: str,
        insight: str,
        evidence: list | None = None,
    ) -> bool:
        """Record a synthesized insight about a skill.

        Categories: strategy_success, strategy_failure,
        causal_hypothesis, best_performer_analysis, regression_diagnosis.

        Returns True if recorded, False if invalid category.
        """
        if category not in self.CATEGORIES:
            _warn(f"unknown insight category {category!r} for skill {skill_ref!r}")
            return False

        entry: dict[str, Any] = {
            "category": category,
            "insight": insight,
            "evidence": evidence or [],
            "timestamp": datetime.now(timezone.utc).isoformat(),  # noqa: UP017
        }

        skill_insights = self.insights.setdefault(skill_ref, [])
        skill_insights.append(entry)
        self._prune_insights(skill_ref)
        self._save()
        return True

    def record_improvement_outcome(  # noqa: PLR0913
        self,
        skill_ref: str,
        version: str,
        change_summary: str,
        before_score: float,
        after_score: float,
        hypothesis: str | None = None,
    ) -> None:
        """Record the outcome of an improvement attempt.

        Stores before/after scores, the change summary, and the causal
        hypothesis for why it worked or failed. Auto-classifies as
        success (after > before), failure (after < before), or neutral.
        """
        improvement = after_score - before_score
        if improvement > 0:
            outcome_type = "success"
        elif improvement < 0:
            outcome_type = "failure"
        else:
            outcome_type = "neutral"

        entry: dict[str, Any] = {
            "version": version,
            "change_summary": change_summary,
            "before_score": before_score,
            "after_score": after_score,
            "improvement": improvement,
            "hypothesis": hypothesis,
            "timestamp": datetime.now(timezone.utc).isoformat(),  # noqa: UP017
            "outcome_type": outcome_type,
        }

        skill_outcomes = self.outcomes.setdefault(skill_ref, [])
        skill_outcomes.append(entry)
        self._prune_outcomes(skill_ref)
        self._save()

    def get_effective_strategies(
        self,
        skill_ref: str | None = None,
        min_improvement: float = 0.1,
    ) -> list:
        """Get improvement strategies that demonstrably worked.

        Returns outcomes where after_score - before_score >= min_improvement,
        sorted by improvement magnitude descending.
        """
        candidates = self._collect_outcomes(skill_ref)
        effective = [o for o in candidates if o["improvement"] >= min_improvement]
        effective.sort(key=lambda o: o["improvement"], reverse=True)
        return effective

    def get_failed_strategies(
        self,
        skill_ref: str | None = None,
    ) -> list:
        """Get improvement strategies that caused regression.

        Returns outcomes where after_score < before_score.
        """
        candidates = self._collect_outcomes(skill_ref)
        return [o for o in candidates if o["improvement"] < 0]

    def get_causal_hypotheses(self, skill_ref: str) -> list:
        """Get all causal hypotheses for a skill.

        Returns insights with category 'causal_hypothesis', sorted by
        timestamp (most recent first).
        """
        entries = self.insights.get(skill_ref, [])
        hypotheses = [e for e in entries if e["category"] == "causal_hypothesis"]
        hypotheses.sort(key=lambda e: e["timestamp"], reverse=True)
        return hypotheses

    def get_insights_by_category(
        self,
        category: str,
        skill_ref: str | None = None,
    ) -> list:
        """Get all insights of a given category.

        If skill_ref is given, scoped to that skill. Otherwise returns
        matching insights across all skills.
        """
        if skill_ref is not None:
            entries = self.insights.get(skill_ref, [])
        else:
            entries = []
            for skill_entries in self.insights.values():
                entries.extend(skill_entries)
        return [e for e in entries if e["category"] == category]

    def synthesize_forward_plan(self, skill_ref: str) -> dict:
        """Synthesize a forward-looking improvement plan.

        Based on the Hyperagents persistent memory pattern:
        - What worked (effective strategies)
        - What failed (avoid these)
        - Current hypotheses
        - Recommended next steps

        Returns dict with keys: effective_strategies, failed_strategies,
        hypotheses, recommended_approach.

        Deterministic: filters and organizes existing data only,
        no LLM calls.
        """
        effective = self.get_effective_strategies(skill_ref=skill_ref)
        failed = self.get_failed_strategies(skill_ref=skill_ref)
        hypotheses = self.get_causal_hypotheses(skill_ref)

        if effective:
            best = effective[0]
            recommended_approach = (
                f"Repeat or build on: {best['change_summary']}"
                f" (+{best['improvement']:.3f} improvement)"
            )
        elif hypotheses:
            recommended_approach = f"Test hypothesis: {hypotheses[0]['insight']}"
        else:
            recommended_approach = (
                "No prior data. Start with a targeted, measurable change"
                " and record the hypothesis before applying it."
            )

        return {
            "effective_strategies": effective,
            "failed_strategies": failed,
            "hypotheses": hypotheses,
            "recommended_approach": recommended_approach,
        }

    # Internal helpers

    def _collect_outcomes(self, skill_ref: str | None) -> list[dict[str, Any]]:
        """Collect outcomes for one skill or all skills."""
        if skill_ref is not None:
            return list(self.outcomes.get(skill_ref, []))
        result: list[dict[str, Any]] = []
        for skill_outcomes in self.outcomes.values():
            result.extend(skill_outcomes)
        return result
