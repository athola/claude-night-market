"""Token usage tracking and analysis for skills."""

import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from ..frontmatter import FrontmatterProcessor
from ..tokens import estimate_tokens

logger = logging.getLogger(__name__)


class TokenUsageTracker:
    """Core token usage tracking functionality."""

    # Default thresholds for token limits
    DEFAULT_OPTIMAL_LIMIT = 1000
    DEFAULT_MAX_LIMIT = 4000

    def __init__(
        self,
        skills_dir: Path,
        optimal_limit: int | None = None,
        max_limit: int | None = None,
    ):
        self.skills_dir = skills_dir
        self.skills_root = skills_dir  # Add alias for compatibility
        self.optimal_limit = (
            optimal_limit if optimal_limit is not None else self.DEFAULT_OPTIMAL_LIMIT
        )
        self.max_limit = max_limit if max_limit is not None else self.DEFAULT_MAX_LIMIT
        self.usage_history: list[dict[str, Any]] = []

    def analyze_skill_tokens(self, skill_name: str) -> dict[str, Any]:
        """Analyze tokens for a single skill."""
        skill_path = self.skills_dir / skill_name / "SKILL.md"
        if not skill_path.exists():
            return {
                "name": skill_name,
                "error": f"Skill not found: {skill_name}",
                "total_tokens": 0,
                "frontmatter_tokens": 0,
                "content_tokens": 0,
                "sections": [],
                "needs_modularization": False,
            }

        try:
            with open(skill_path, encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            return {
                "name": skill_name,
                "error": str(e),
                "total_tokens": 0,
                "frontmatter_tokens": 0,
                "content_tokens": 0,
                "sections": [],
                "needs_modularization": False,
            }

        total_tokens = estimate_tokens(content)
        frontmatter_tokens = self._calculate_frontmatter_tokens(content)
        content_tokens = total_tokens - frontmatter_tokens

        # Extract sections
        sections = re.findall(r"^##\s+(.+)$", content, re.MULTILINE)

        return {
            "name": skill_name,
            "total_tokens": total_tokens,
            "frontmatter_tokens": frontmatter_tokens,
            "content_tokens": content_tokens,
            "sections": sections,
            "needs_modularization": total_tokens > self.optimal_limit,
        }

    def analyze_all_skills(self) -> dict[str, Any]:
        """Analyze tokens for all skills in directory."""
        skill_files = list(self.skills_dir.rglob("SKILL.md"))
        skills = []
        total_tokens = 0

        for skill_file in skill_files:
            skill_name = skill_file.parent.name
            analysis = self.analyze_skill_tokens(skill_name)
            skills.append(analysis)
            total_tokens += analysis.get("total_tokens", 0)

        return {
            "total_skills": len(skills),
            "skills": skills,
            "summary": {
                "total_tokens": total_tokens,
                "average_tokens": total_tokens // len(skills) if skills else 0,
                "skills_needing_modularization": len(
                    [s for s in skills if s.get("needs_modularization")]
                ),
            },
        }

    def calculate_token_efficiency(self) -> dict[str, Any]:
        """Calculate token efficiency metrics."""
        all_analysis = self.analyze_all_skills()
        skill_efficiencies = {}
        optimization_opportunities = []

        for skill in all_analysis.get("skills", []):
            name = skill.get("name", "unknown")
            tokens = skill.get("total_tokens", 0)
            efficiency = min(100, (self.optimal_limit / max(tokens, 1)) * 100)
            skill_efficiencies[name] = efficiency

            if tokens > self.optimal_limit:
                optimization_opportunities.append(
                    {
                        "skill": name,
                        "current_tokens": tokens,
                        "target_tokens": self.optimal_limit,
                        "potential_savings": tokens - self.optimal_limit,
                    }
                )

        avg_efficiency = (
            sum(skill_efficiencies.values()) / len(skill_efficiencies)
            if skill_efficiencies
            else 0
        )

        return {
            "overall_efficiency": avg_efficiency,
            "skill_efficiencies": skill_efficiencies,
            "optimization_opportunities": optimization_opportunities,
        }

    def suggest_modularization(self) -> list[dict[str, Any]]:
        """Suggest modularization strategies for large skills."""
        all_analysis = self.analyze_all_skills()
        suggestions = []

        for skill in all_analysis.get("skills", []):
            if skill.get("needs_modularization"):
                sections = skill.get("sections", [])
                suggested_modules = [
                    f"modules/{s.lower().replace(' ', '-')}.md" for s in sections
                ]
                suggestions.append(
                    {
                        "skill": skill.get("name"),
                        "current_tokens": skill.get("total_tokens", 0),
                        "suggested_modules": suggested_modules[:5],
                        "reason": "Skill exceeds optimal token limit",
                    }
                )

        return suggestions

    def record_usage(self, usage_record: dict[str, Any]) -> None:
        """Record a usage entry in history."""
        self.usage_history.append(usage_record)

    def generate_usage_report(self, analysis: dict[str, Any]) -> str:
        """Generate a formatted usage report from analysis."""
        lines = [
            "# Token Usage Report",
            "",
            "## Summary Statistics",
            f"- **Total Skills:** {analysis.get('total_skills', 0)}",
        ]

        summary = analysis.get("summary", {})
        if summary:
            lines.extend(
                [
                    f"- **Total Tokens:** {summary.get('total_tokens', 0):,}",
                    f"- **Average Tokens:** {summary.get('average_tokens', 0):,}",
                ]
            )

        lines.append("")
        lines.append("## Individual Skills")

        for skill in analysis.get("skills", []):
            name = skill.get("name", "unknown")
            tokens = skill.get("total_tokens", 0)
            lines.append(f"- **{name}**: {tokens:,} tokens")

        return "\n".join(lines)

    def identify_optimization_opportunities(self) -> list[dict[str, Any]]:
        """Identify optimization opportunities for skills."""
        all_analysis = self.analyze_all_skills()
        opportunities = []

        for skill in all_analysis.get("skills", []):
            tokens = skill.get("total_tokens", 0)
            if tokens > self.optimal_limit:
                opportunities.append(
                    {
                        "skill": skill.get("name"),
                        "type": "token_reduction",
                        "potential_savings": tokens - self.optimal_limit,
                        "action": "Consider modularizing or compressing content",
                    }
                )

        return opportunities

    def calculate_dependency_impact(self) -> dict[str, Any]:
        """Calculate token impact from skill dependencies."""
        all_analysis = self.analyze_all_skills()
        skills_data = []
        dependency_chains: list[list[str]] = []

        for skill in all_analysis.get("skills", []):
            skill_name = skill.get("name", "unknown")
            direct_tokens = skill.get("total_tokens", 0)
            # Simplified: no actual dependency tracking yet
            skills_data.append(
                {
                    "name": skill_name,
                    "direct_tokens": direct_tokens,
                    "dependency_tokens": 0,
                    "total_impact": direct_tokens,
                }
            )

        return {
            "skills": skills_data,
            "dependency_chains": dependency_chains,
        }

    def export_analysis(self, analysis: dict[str, Any], export_path: Path) -> None:
        """Export analysis to a JSON file."""
        with open(export_path, "w") as f:
            json.dump(analysis, f, indent=2, default=str)

    def compare_skills(self, skill_names: list[str]) -> dict[str, Any]:
        """Compare token usage between specified skills."""
        comparison_table = []
        for name in skill_names:
            analysis = self.analyze_skill_tokens(name)
            comparison_table.append(
                {
                    "name": name,
                    "total_tokens": analysis.get("total_tokens", 0),
                    "sections": len(analysis.get("sections", [])),
                }
            )

        # Sort by token count
        comparison_table.sort(key=lambda x: x["total_tokens"])

        return {
            "comparison_table": comparison_table,
            "analysis": {
                "smallest": comparison_table[0]["name"] if comparison_table else None,
                "largest": comparison_table[-1]["name"] if comparison_table else None,
            },
            "recommendations": self._build_recommendations(comparison_table),
        }

    def _build_recommendations(self, comparison_table: list) -> list[str]:
        """Build recommendations for skill comparison."""
        if not comparison_table:
            return []
        largest = comparison_table[-1]
        if largest["total_tokens"] > self.optimal_limit:
            return [f"Consider modularizing {largest['name']}"]
        return []

    def monitor_budgets(self, budget: int) -> dict[str, Any]:
        """Monitor token budgets and generate alerts."""
        all_analysis = self.analyze_all_skills()
        total_tokens = all_analysis.get("summary", {}).get("total_tokens", 0)
        exceeded = total_tokens > budget

        recommendations = []
        if exceeded:
            overage = total_tokens - budget
            recommendations.append(
                f"Budget exceeded by {overage} tokens. Consider optimization."
            )
            # Find skills to optimize
            for skill in all_analysis.get("skills", []):
                if skill.get("total_tokens", 0) > self.optimal_limit:
                    recommendations.append(
                        f"Optimize {skill.get('name')} to reduce tokens"
                    )

        return {
            "budget": budget,
            "usage": total_tokens,
            "exceeded": exceeded,
            "recommendations": recommendations,
        }

    def track_usage(self, skill_path: Path = None):
        """Track token usage for a single skill."""
        if skill_path is None:
            # Find first skill if none specified
            skill_files = list(self.skills_dir.rglob("SKILL.md"))
            if not skill_files:
                return None
            skill_path = skill_files[0]

        if skill_path.is_dir():
            skill_path = skill_path / "SKILL.md"

        if not skill_path.exists():
            raise FileNotFoundError(f"Skill file not found: {skill_path}")

        try:
            with open(skill_path, encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            raise OSError(f"Error reading skill file {skill_path}: {e}") from e

        # Calculate tokens
        total_tokens = estimate_tokens(content)
        frontmatter_tokens = self._calculate_frontmatter_tokens(content)
        content_tokens = total_tokens - frontmatter_tokens

        entry = {
            "skill_name": skill_path.parent.name,
            "file_path": str(skill_path),
            "token_count": total_tokens,
            "frontmatter_tokens": frontmatter_tokens,
            "content_tokens": content_tokens,
            "timestamp": datetime.now(),
        }

        return entry

    def get_usage_statistics(self):
        """Get comprehensive usage statistics."""
        # Track all skills first
        skill_files = list(self.skills_dir.rglob("SKILL.md"))
        entries = []

        for skill_file in skill_files:
            try:
                entry = self.track_usage(skill_file)
                if entry:
                    entries.append(entry)
            except (OSError, ValueError) as e:
                # Log the error if needed, but continue processing other files
                logger.debug(f"Error processing skill file {skill_file}: {e}")
                continue

        if not entries:
            return {
                "total_skills": 0,
                "total_tokens": 0,
                "average_tokens": 0,
                "min_tokens": 0,
                "max_tokens": 0,
                "skills_over_limit": 0,
                "optimal_usage_count": 0,
            }

        token_counts = [entry["token_count"] for entry in entries]
        total_tokens = sum(token_counts)
        skills_over_limit = len([t for t in token_counts if t > self.optimal_limit])
        optimal_usage_count = len([t for t in token_counts if t <= self.optimal_limit])

        return {
            "total_skills": len(entries),
            "total_tokens": total_tokens,
            "average_tokens": total_tokens // len(entries) if entries else 0,
            "min_tokens": min(token_counts) if token_counts else 0,
            "max_tokens": max(token_counts) if token_counts else 0,
            "skills_over_limit": skills_over_limit,
            "optimal_usage_count": optimal_usage_count,
        }

    def get_usage_report(self):
        """Generate formatted usage report."""
        stats = self.get_usage_statistics()

        lines = [
            "# Token Usage Report",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Skills Directory:** {self.skills_dir}",
            "",
            "## Summary",
            f"- **Total Skills:** {stats['total_skills']}",
            f"- **Total Tokens:** {stats['total_tokens']:,}",
            f"- **Average Tokens:** {stats['average_tokens']:,}",
            f"- **Min Tokens:** {stats['min_tokens']:,}",
            f"- **Max Tokens:** {stats['max_tokens']:,}",
            f"- **Skills Over Limit ({self.optimal_limit}):** "
            f"{stats['skills_over_limit']}",
            f"- **Optimal Usage (≤{self.optimal_limit}):** "
            f"{stats['optimal_usage_count']}",
            "",
        ]

        return "\n".join(lines)

    def optimize_suggestions(self, skill_name: str = None):
        """Generate optimization suggestions for skills."""
        if skill_name:
            # Single skill suggestions
            skill_path = self.skills_dir / skill_name / "SKILL.md"
            if not skill_path.exists():
                return ["Skill not found"]

            try:
                with open(skill_path, encoding="utf-8") as f:
                    content = f.read()
            except Exception:
                return ["Error reading skill file"]

            total_tokens = estimate_tokens(content)
            if total_tokens > self.optimal_limit:
                return ["Reduce content size for better performance"]
            elif total_tokens > self.max_limit:
                return ["CRITICAL: Skill exceeds maximum token limit"]
            else:
                return ["Token usage is optimal"]
        else:
            # General suggestions
            stats = self.get_usage_statistics()
            suggestions = []

            if stats["skills_over_limit"] > 0:
                suggestions.append(
                    f"{stats['skills_over_limit']} skills exceed optimal token limit"
                )

            if stats["average_tokens"] > self.optimal_limit:
                suggestions.append(
                    "Average token usage is high, consider content optimization"
                )

            if not suggestions:
                suggestions.append("Token usage is within optimal limits")

            return suggestions

    def _calculate_frontmatter_tokens(self, content: str) -> int:
        """Calculate tokens used in frontmatter."""
        frontmatter, _ = FrontmatterProcessor.extract_raw(content)
        return estimate_tokens(frontmatter)
