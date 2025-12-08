"""Skills auditing functionality."""

import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..frontmatter import FrontmatterProcessor
from ..tokens import estimate_tokens

logger = logging.getLogger(__name__)

# Score thresholds
SCORE_EXCELLENT = 90
SCORE_GOOD = 75
SCORE_ACCEPTABLE = 70
SCORE_WELL_STRUCTURED = 80

# Code block thresholds
MIN_CODE_BLOCKS = 2
MIN_CODE_BLOCKS_EXCELLENT = 3
MIN_NUMBERED_LISTS = 2
MIN_NUMBERED_LISTS_GOOD = 3
MIN_NUMBERED_STEPS = 2  # Minimum numbered steps for instructions

# Structure thresholds
MIN_HEADINGS = 4
MIN_SECTIONS = 5
MIN_SECTION_COUNT = 6


@dataclass
class SkillMetrics:
    """Metrics for a single skill."""

    name: str
    path: str
    score: float
    issues: list[str]
    strengths: list[str]
    token_count: int
    completeness_score: float
    structure_score: float
    documentation_score: float


class SkillsAuditor:
    """Core skills auditing functionality."""

    def __init__(self, skills_dir: Path):
        self.skills_dir = skills_dir
        self.skills_root = skills_dir  # Add alias for compatibility
        self.audit_metrics = self._load_audit_metrics()

    @property
    def skill_files(self) -> list[Path]:
        """Return list of skill files in directory."""
        return list(self.skills_dir.rglob("SKILL.md"))

    def _load_audit_metrics(self) -> dict[str, Any]:
        """Load audit criteria and scoring metrics."""
        return {
            "scoring_weights": {
                "completeness": 0.3,
                "structure": 0.25,
                "documentation": 0.25,
                "token_efficiency": 0.2,
            },
            "required_fields": ["name", "description"],
            "recommended_fields": ["category", "tags", "dependencies"],
            "required_sections": ["Overview", "Quick Start"],
            "recommended_sections": ["Examples", "Resources", "Troubleshooting"],
            "token_optimal": 1500,
            "token_acceptable": 2500,
            "structure_indicators": ["## Overview", "## Quick Start", "## Examples"],
            "documentation_indicators": ["code blocks", "step-by-step", "examples"],
        }

    def audit_skills(self) -> dict[str, Any]:
        """Perform comprehensive audit of skills in directory."""
        skill_files = list(self.skills_dir.rglob("SKILL.md"))
        if not skill_files:
            return {
                "total_skills": 0,
                "average_score": 0.0,
                "well_structured": 0,
                "needs_improvement": 0,
                "recommendations": ["No skills found to audit"],
            }

        skills_metrics = []
        total_score = 0

        for skill_file in skill_files:
            metrics = self._analyze_skill_file(skill_file)
            skills_metrics.append(metrics)
            total_score += metrics.score

        average_score = total_score / len(skills_metrics) if skills_metrics else 0
        well_structured = len(
            [m for m in skills_metrics if m.score >= SCORE_WELL_STRUCTURED]
        )
        needs_improvement = len(
            [m for m in skills_metrics if m.score < SCORE_ACCEPTABLE]
        )
        recommendations = self._generate_recommendations(skills_metrics)

        return {
            "total_skills": len(skills_metrics),
            "average_score": average_score,
            "well_structured": well_structured,
            "needs_improvement": needs_improvement,
            "recommendations": recommendations,
            "skill_metrics": skills_metrics,
        }

    def _analyze_skill_file(self, skill_file: Path) -> SkillMetrics:
        """Analyze a single skill file and generate metrics."""
        try:
            with open(skill_file, encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            return SkillMetrics(
                name=skill_file.parent.name,
                path=str(skill_file),
                score=0.0,
                issues=[f"Error reading file: {e}"],
                strengths=[],
                token_count=0,
                completeness_score=0.0,
                structure_score=0.0,
                documentation_score=0.0,
            )

        # Parse frontmatter
        frontmatter = self._parse_frontmatter(content)

        # Calculate scores
        completeness_score = self._calculate_completeness_score(frontmatter, content)
        structure_score = self._calculate_structure_score(content)
        documentation_score = self._calculate_documentation_score(content)
        token_count = estimate_tokens(content)

        # Calculate overall score
        weights = self.audit_metrics["scoring_weights"]
        overall_score = (
            completeness_score * weights["completeness"]
            + structure_score * weights["structure"]
            + documentation_score * weights["documentation"]
            + self._calculate_token_score(token_count) * weights["token_efficiency"]
        )

        # Generate issues and strengths
        issues = self._generate_issues(frontmatter, content, token_count)
        strengths = self._generate_strengths(
            completeness_score,
            structure_score,
            documentation_score,
            token_count,
        )

        return SkillMetrics(
            name=frontmatter.get("name", skill_file.parent.name),
            path=str(skill_file),
            score=overall_score,
            issues=issues,
            strengths=strengths,
            token_count=token_count,
            completeness_score=completeness_score,
            structure_score=structure_score,
            documentation_score=documentation_score,
        )

    def _parse_frontmatter(self, content: str) -> dict[str, Any]:
        """Parse YAML frontmatter from content."""
        result = FrontmatterProcessor.parse(content, required_fields=[])
        return result.parsed

    def _calculate_completeness_score(
        self, frontmatter: dict[str, Any], content: str
    ) -> float:
        """Calculate frontmatter completeness score."""
        required = self.audit_metrics["required_fields"]
        recommended = self.audit_metrics["recommended_fields"]

        score = 0.0
        total_possible = len(required) + len(recommended) * 0.5

        # Required fields
        for field in required:
            # Check if field exists and is not None (empty lists/strings are valid)
            if field in frontmatter and frontmatter[field] is not None:
                score += 1.0

        # Recommended fields
        for field in recommended:
            # Check if field exists and is not None (empty lists/strings are valid)
            if field in frontmatter and frontmatter[field] is not None:
                score += 0.5

        return (score / total_possible) * 100 if total_possible > 0 else 0

    def _calculate_structure_score(self, content: str) -> float:
        """Calculate content structure score."""
        required = self.audit_metrics["required_sections"]
        recommended = self.audit_metrics["recommended_sections"]

        score = 0.0
        total_possible = len(required) + len(recommended) * 0.5

        # Required sections
        for section in required:
            if f"## {section}" in content:
                score += 1.0

        # Recommended sections
        for section in recommended:
            if f"## {section}" in content:
                score += 0.5

        # Additional structure factors
        headings = len(re.findall(r"^#+ ", content, re.MULTILINE))
        if headings >= MIN_HEADINGS:
            score += 0.5

        return (score / (total_possible + 0.5)) * 100 if total_possible > 0 else 0

    def _calculate_documentation_score(self, content: str) -> float:
        """Calculate documentation quality score."""
        score = 0.0

        # Code blocks
        code_block_count = len(re.findall(r"```", content)) // 2
        if code_block_count >= 1:
            score += 25
        if code_block_count >= MIN_CODE_BLOCKS_EXCELLENT:
            score += 25

        # Step-by-step instructions
        numbered_lists = len(re.findall(r"^\d+\.", content, re.MULTILINE))
        if numbered_lists >= 1:
            score += 25
        if numbered_lists >= MIN_NUMBERED_LISTS_GOOD:
            score += 25

        # Examples
        if "## Examples" in content or "example" in content.lower():
            score += 25

        return min(score, 100)

    def _calculate_token_score(self, token_count: int) -> float:
        """Calculate token efficiency score."""
        optimal = self.audit_metrics["token_optimal"]
        acceptable = self.audit_metrics["token_acceptable"]

        if token_count <= optimal:
            return 100
        elif token_count <= acceptable:
            return 80
        else:
            return max(20, 100 - (token_count - acceptable) * 0.02)

    def _generate_issues(
        self,
        frontmatter: dict[str, Any],
        content: str,
        token_count: int,
    ) -> list[str]:
        """Generate list of issues found in skill."""
        issues = []

        # Frontmatter issues
        if not content.startswith("---\n"):
            issues.append("Missing YAML frontmatter")
        else:
            for field in self.audit_metrics["required_fields"]:
                if not frontmatter.get(field):
                    issues.append(f"Missing required field: {field}")

            for field in self.audit_metrics["recommended_fields"]:
                if not frontmatter.get(field):
                    issues.append(f"Missing recommended field: {field}")

        # Structure issues
        for section in self.audit_metrics["required_sections"]:
            if f"## {section}" not in content:
                issues.append(f"Missing required section: {section}")

        # Documentation issues
        if len(re.findall(r"```", content)) < MIN_CODE_BLOCKS:
            issues.append("Missing code examples")

        if len(re.findall(r"^\d+\.", content, re.MULTILINE)) < MIN_NUMBERED_STEPS:
            issues.append("Missing step-by-step instructions")

        # Token efficiency
        if token_count > self.audit_metrics["token_acceptable"]:
            target = self.audit_metrics["token_optimal"]
            issues.append(f"High token usage: {token_count} (target: <{target})")

        return issues

    def _generate_strengths(
        self,
        completeness: float,
        structure: float,
        documentation: float,
        token_count: int,
    ) -> list[str]:
        """Generate list of strengths found in skill."""
        strengths = []

        if completeness >= SCORE_EXCELLENT:
            strengths.append("Excellent frontmatter completeness")
        elif completeness >= SCORE_GOOD:
            strengths.append("Good frontmatter completeness")

        if structure >= SCORE_EXCELLENT:
            strengths.append("Excellent content structure")
        elif structure >= SCORE_GOOD:
            strengths.append("Good content structure")

        if documentation >= SCORE_EXCELLENT:
            strengths.append("Excellent documentation")
        elif documentation >= SCORE_GOOD:
            strengths.append("Good documentation")

        if token_count <= self.audit_metrics["token_optimal"]:
            strengths.append("Excellent token efficiency")
        elif token_count <= self.audit_metrics["token_acceptable"]:
            strengths.append("Acceptable token usage")

        return strengths

    def _generate_recommendations(self, skill_metrics: list[SkillMetrics]) -> list[str]:
        """Generate overall recommendations based on audit results."""
        recommendations = []

        if not skill_metrics:
            return recommendations

        avg_completeness = sum(m.completeness_score for m in skill_metrics) / len(
            skill_metrics
        )
        avg_structure = sum(m.structure_score for m in skill_metrics) / len(
            skill_metrics
        )
        avg_documentation = sum(m.documentation_score for m in skill_metrics) / len(
            skill_metrics
        )

        if avg_completeness < SCORE_GOOD:
            recommendations.append(
                "Add required frontmatter fields (name, description) to all skills"
            )
            recommendations.append(
                "Consider adding recommended fields (category, tags) "
                "for better organization"
            )

        if avg_structure < SCORE_GOOD:
            recommendations.append(
                "Implement progressive disclosure structure with "
                "Overview and Quick Start sections"
            )
            recommendations.append(
                "Add more detailed sections to improve content organization"
            )

        if avg_documentation < SCORE_GOOD:
            recommendations.append(
                "Add practical examples and code blocks to demonstrate skill usage"
            )
            recommendations.append(
                "Include step-by-step instructions for common workflows"
            )

        avg_tokens = sum(m.token_count for m in skill_metrics) / len(skill_metrics)
        if avg_tokens > self.audit_metrics["token_acceptable"]:
            recommendations.append("Optimize content for better token efficiency")
            recommendations.append(
                "Consider moving detailed content to separate files or tools"
            )

        return recommendations

    # Legacy method names for compatibility
    def audit_all_skills(self) -> dict[str, Any]:
        """Return audit results with skills list and summary."""
        base_result = self.audit_skills()
        skill_metrics = base_result.get("skill_metrics", [])

        # Convert SkillMetrics to dicts for compatibility
        skills = []
        for m in skill_metrics:
            skills.append(
                {
                    "name": m.name,
                    "path": m.path,
                    "overall_score": m.score,
                    "completeness_score": m.completeness_score,
                    "structure_score": m.structure_score,
                    "documentation_score": m.documentation_score,
                    "token_count": m.token_count,
                    "issues": [
                        {
                            "type": i.split(":")[0].strip().lower().replace(" ", "_"),
                            "description": i,
                        }
                        for i in m.issues
                    ],
                    "recommendations": [
                        {"action": r, "priority": "medium"} for r in m.strengths
                    ],
                }
            )

        # Calculate summary
        if skills:
            skill_count = len(skills)
            avg_completeness = (
                sum(s["completeness_score"] for s in skills) / skill_count
            )
            avg_structure = sum(s["structure_score"] for s in skills) / skill_count
            avg_overall = sum(s["overall_score"] for s in skills) / skill_count
            needs_improvement = len(
                [s for s in skills if s["overall_score"] < SCORE_ACCEPTABLE]
            )
            high_priority = len([s for s in skills if s["issues"]])
        else:
            avg_completeness = avg_structure = avg_overall = 0.0
            needs_improvement = high_priority = 0

        return {
            "total_skills": base_result["total_skills"],
            "skill_metrics": skill_metrics,
            "skills": skills,
            "summary": {
                "average_completeness": avg_completeness,
                "average_structure": avg_structure,
                "average_overall": avg_overall,
                "skills_needing_improvement": needs_improvement,
                "high_priority_issues": high_priority,
            },
            "recommendations": base_result.get("recommendations", []),
        }

    def audit_skill(self, skill_name: str) -> dict[str, Any]:
        """Audit a single skill by name."""
        skill_path = self.skills_dir / skill_name / "SKILL.md"
        if not skill_path.exists():
            return {
                "name": skill_name,
                "error": f"Skill not found: {skill_name}",
                "completeness_score": 0,
                "structure_score": 0,
                "overall_score": 0,
                "issues": [],
                "recommendations": [],
            }

        metrics = self._analyze_skill_file(skill_path)

        # Convert issues to typed dicts
        typed_issues = []
        for issue in metrics.issues:
            issue_lower = issue.lower()
            if "missing" in issue_lower and "description" in issue_lower:
                issue_type = "missing_description"
            elif "high token" in issue_lower or "token usage" in issue_lower:
                issue_type = "size_large"
            elif "missing" in issue_lower:
                issue_type = "missing_" + issue_lower.split(":")[-1].strip().replace(
                    " ", "_"
                )
            else:
                issue_type = issue_lower.replace(" ", "_")[:20]
            typed_issues.append({"type": issue_type, "description": issue})

        # Convert strengths to recommendations
        recommendations = [
            {"action": s, "priority": "medium"} for s in metrics.strengths
        ]

        return {
            "name": metrics.name,
            "path": metrics.path,
            "completeness_score": metrics.completeness_score,
            "structure_score": metrics.structure_score,
            "documentation_score": metrics.documentation_score,
            "overall_score": metrics.score,
            "token_count": metrics.token_count,
            "issues": typed_issues,
            "recommendations": recommendations,
        }

    def generate_report(self, audit_results: dict[str, Any]) -> str:
        """Generate a formatted audit report."""
        lines = [
            "# Skills Audit Report",
            "",
            "## Summary",
            f"- **Total Skills:** {audit_results['total_skills']}",
        ]

        if "summary" in audit_results:
            summary = audit_results["summary"]
            completeness = summary["average_completeness"]
            structure = summary["average_structure"]
            overall = summary["average_overall"]
            needs_improve = summary["skills_needing_improvement"]
            lines.extend(
                [
                    f"- **Average Completeness:** {completeness:.1f}%",
                    f"- **Average Structure:** {structure:.1f}%",
                    f"- **Average Overall:** {overall:.1f}%",
                    f"- **Skills Needing Improvement:** {needs_improve}",
                ]
            )

        lines.append("")
        lines.append("## Skills")

        for skill in audit_results.get("skills", []):
            lines.append(f"\n### {skill['name']}")
            lines.append(f"- Overall Score: {skill['overall_score']:.1f}")
            lines.append(f"- Completeness: {skill['completeness_score']:.1f}")
            lines.append(f"- Structure: {skill['structure_score']:.1f}")

        return "\n".join(lines)

    def export_results(self, audit_results: dict[str, Any], export_path: Path) -> None:
        """Export audit results to a JSON file."""
        # Remove non-serializable SkillMetrics if present
        export_data = {
            "total_skills": audit_results["total_skills"],
            "skills": audit_results.get("skills", []),
            "summary": audit_results.get("summary", {}),
            "recommendations": audit_results.get("recommendations", []),
        }
        with open(export_path, "w") as f:
            json.dump(export_data, f, indent=2)

    def filter_skills(
        self,
        audit_results: dict[str, Any],
        min_overall_score: float | None = None,
        has_high_priority_issues: bool | None = None,
    ) -> dict[str, Any]:
        """Filter skills by criteria."""
        skills = audit_results.get("skills", [])
        filtered = []

        for skill in skills:
            if min_overall_score is not None:
                if skill["overall_score"] < min_overall_score:
                    continue
            if has_high_priority_issues is not None:
                has_issues = len(skill.get("issues", [])) > 0
                if has_high_priority_issues and not has_issues:
                    continue
                if not has_high_priority_issues and has_issues:
                    continue
            filtered.append(skill)

        return {"skills": filtered, "total_skills": len(filtered)}

    def discover_skills(self) -> list[str]:
        """Discover skill names in directory."""
        skill_files = list(self.skills_dir.rglob("SKILL.md"))
        return [f.parent.name for f in skill_files]
