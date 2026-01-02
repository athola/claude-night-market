"""Improvement suggestion functionality for skills."""

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from abstract.frontmatter import FrontmatterProcessor
from abstract.tokens import estimate_tokens

logger = logging.getLogger(__name__)

# Token thresholds
TOKEN_MAX_EFFICIENT = 2000
TOKEN_LARGE_SKILL = 3000

# Code block thresholds
MIN_CODE_BLOCKS = 2
CODE_BLOCKS_MODULARIZE = 3

# Structure thresholds
MIN_SECTIONS = 5

# Suggestions thresholds
SUGGESTIONS_LOW = 3  # Timeline: 1-2 days
SUGGESTIONS_MEDIUM = 6  # Timeline: 1 week


@dataclass
class Improvement:
    """An improvement suggestion for a skill."""

    category: str  # critical, high, medium, low
    priority: int  # 1-10, where 1 is highest priority
    description: str
    specific_action: str
    code_example: str | None = None
    estimated_effort: str = "medium"  # low, medium, high
    impact: str = "medium"  # low, medium, high
    dependencies: list[str] | None = None

    def __post_init__(self) -> None:
        """Initialize default values for mutable fields."""
        if self.dependencies is None:
            self.dependencies = []


class ImprovementSuggester:
    """Core improvement suggestion functionality."""

    def __init__(self, skills_dir: Path) -> None:
        """Initialize the improvement suggester."""
        self.skills_dir = skills_dir
        self.skills_root = skills_dir  # Add alias for compatibility
        self.skill_root = skills_dir  # Add alias for test compatibility

    def analyze_skill(self, skill_name: str) -> dict[str, Any]:
        """Analyze a specific skill for improvements."""
        skill_path = self.skills_dir / skill_name / "SKILL.md"

        if not skill_path.exists():
            return {
                "name": skill_name,
                "issues": [f"Skill file not found: {skill_path}"],
                "suggestions": ["Create SKILL.md file in skill directory"],
            }

        try:
            with open(skill_path, encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            return {
                "name": skill_name,
                "issues": [f"Error reading skill file: {e}"],
                "suggestions": ["Check file permissions and encoding"],
            }

        issues = []
        suggestions = []

        # Analyze frontmatter using centralized processor
        required_fields = ["name", "description"]
        result = FrontmatterProcessor.parse(content, required_fields=required_fields)

        if not result.is_valid and result.parse_error:
            issues.append("Missing YAML frontmatter")
            suggestions.append("Add YAML frontmatter with metadata")

        # Check for missing required fields
        if result.missing_fields:
            missing = ", ".join(result.missing_fields)
            issues.append(f"Missing required fields: {missing}")
            suggestions.append(f"Add missing fields to frontmatter: {missing}")

        # Check structure
        required_sections = ["## Overview", "## Quick Start"]
        missing_sections = [
            section for section in required_sections if section not in content
        ]

        if missing_sections:
            issues.append(f"Missing required sections: {', '.join(missing_sections)}")
            suggestions.append(
                "Add progressive disclosure structure with Overview "
                "and Quick Start sections",
            )

        # Check examples
        code_blocks_found = len(re.findall(r"```", content))
        if "## Examples" not in content and code_blocks_found < MIN_CODE_BLOCKS:
            suggestions.append("Add practical examples and code blocks")

        # Check token efficiency
        estimated_tokens = estimate_tokens(content)
        if estimated_tokens > TOKEN_LARGE_SKILL:
            suggestions.append(
                "Consider modularization or content optimization "
                "for better token efficiency",
            )

        # Check naming convention
        if "-" not in skill_name or skill_name.islower():
            suggestions.append(
                "Use kebab-case naming (lowercase with hyphens) for better readability",
            )

        return {"name": skill_name, "issues": issues, "suggestions": suggestions}

    def suggest_modularization(self, skill_name: str) -> list[str]:
        """Suggest modularization strategies for a skill."""
        suggestions = []
        skill_path = self.skills_dir / skill_name / "SKILL.md"

        if not skill_path.exists():
            return ["Skill file not found"]

        try:
            with open(skill_path, encoding="utf-8") as f:
                content = f.read()
        except Exception:
            return ["Error reading skill file"]

        # Check content length
        estimated_tokens = estimate_tokens(content)
        if estimated_tokens > TOKEN_MAX_EFFICIENT:
            suggestions.append("Extract large content sections to separate modules")
            suggestions.append("Use tools/ directory for automation scripts")

        # Check code blocks
        code_block_count = len(re.findall(r"```", content)) // 2
        if code_block_count > CODE_BLOCKS_MODULARIZE:
            suggestions.append("Move complex code examples to executable tools")
            suggestions.append("Create reusable scripts for common operations")

        if not suggestions:
            suggestions.append(
                "Skill is well-structured, no major modularization needed",
            )

        return suggestions

    def suggest_improved_structure(self, skill_name: str) -> list[str]:
        """Suggest structural improvements for a skill."""
        suggestions = []
        skill_path = self.skills_dir / skill_name / "SKILL.md"

        if not skill_path.exists():
            return ["Skill file not found"]

        try:
            with open(skill_path, encoding="utf-8") as f:
                content = f.read()
        except Exception:
            return ["Error reading skill file"]

        # Check sections
        required_sections = {
            "Overview": "Add overview section explaining skill purpose",
            "Quick Start": "Add quick start section with basic usage steps",
            "Examples": "Add examples section with concrete use cases",
            "Resources": "Add resources section with detailed information",
        }

        missing_sections = []
        for section, suggestion in required_sections.items():
            if f"## {section}" not in content:
                missing_sections.append(suggestion)

        suggestions.extend(missing_sections)

        # Check organization
        section_count = len(re.findall(r"^#+ ", content, re.MULTILINE))
        if section_count < MIN_SECTIONS:
            suggestions.append(
                "Improve content organization with more structured sections",
            )

        return suggestions

    def generate_improvement_plan(self, skill_name: str) -> dict[str, Any]:
        """Generate a detailed improvement plan for a skill."""
        analysis = self.analyze_skill(skill_name)
        modularization = self.suggest_modularization(skill_name)
        structure = self.suggest_improved_structure(skill_name)

        # Combine all suggestions
        all_suggestions = analysis.get("suggestions", []) + modularization + structure

        # Determine priority
        critical_issues = [
            issue
            for issue in analysis.get("issues", [])
            if "missing" in issue.lower() or "required" in issue.lower()
        ]

        priority = "high" if critical_issues else "medium" if all_suggestions else "low"

        # Estimate timeline
        if len(all_suggestions) <= SUGGESTIONS_LOW:
            timeline = "1-2 days"
        elif len(all_suggestions) <= SUGGESTIONS_MEDIUM:
            timeline = "1 week"
        else:
            timeline = "2 weeks"

        return {
            "skill_name": skill_name,
            "issues_found": analysis.get("issues", []),
            "improvement_steps": all_suggestions,
            "priority": priority,
            "estimated_timeline": timeline,
        }

    def analyze_all_skills(self) -> list[dict[str, Any]]:
        """Analyze all skills in skills directory."""
        skill_directories = [
            d
            for d in self.skills_dir.iterdir()
            if d.is_dir() and (d / "SKILL.md").exists()
        ]

        results = []
        for skill_dir in skill_directories:
            analysis = self.analyze_skill(skill_dir.name)
            results.append(analysis)

        return results

    def prioritize_suggestions(
        self,
        suggestions: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Prioritize suggestions by importance."""
        priority_order = {"high": 0, "medium": 1, "low": 2}

        return sorted(
            suggestions,
            key=lambda x: priority_order.get(x.get("priority", "medium"), 1),
        )
