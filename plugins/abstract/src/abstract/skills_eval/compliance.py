"""Compliance checking for skills against standards."""

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.abstract.frontmatter import FrontmatterProcessor
from src.abstract.tokens import estimate_tokens

logger = logging.getLogger(__name__)


@dataclass
class ComplianceIssue:
    """A compliance issue found in a skill."""

    severity: str  # critical, high, medium, low
    category: str  # security, structure, metadata, performance, usability
    description: str
    location: str  # file path or line reference
    recommendation: str
    standard: str  # which standard this violates
    auto_fixable: bool = False


@dataclass
class ComplianceReport:
    """Complete compliance report for skills."""

    skill_name: str
    skill_path: str
    overall_compliance: float  # 0-100
    issues: list[ComplianceIssue]
    standards_checked: list[str]
    passed_checks: list[str]
    failed_checks: list[str]


class ComplianceChecker:
    """Core compliance checking functionality."""

    def __init__(self, skill_root: Path, rules_file: Path | None = None) -> None:
        self.skill_root = skill_root
        self.rules_file = rules_file
        self.rules = self._load_rules()

    def _load_rules(self) -> dict[str, Any]:
        """Load compliance rules from file or use defaults."""
        if self.rules_file and self.rules_file.exists():
            with open(self.rules_file) as f:
                return json.load(f)

        # Default rules
        return {
            "required_fields": ["name", "description"],
            "max_tokens": 4000,
            "required_sections": ["Overview", "Quick Start"],
        }

    def check_compliance(self) -> dict[str, Any]:
        """Check compliance of skills in skill_root directory."""
        if not self.skill_root.exists():
            return {
                "compliant": False,
                "issues": [f"Skill root directory does not exist: {self.skill_root}"],
                "warnings": [],
                "total_skills": 0,
            }

        # Count skills
        skill_files = list(self.skill_root.rglob("SKILL.md"))
        total_skills = len(skill_files)

        if total_skills == 0:
            return {
                "compliant": False,
                "issues": ["No SKILL.md files found"],
                "warnings": [],
                "total_skills": 0,
            }

        issues = []
        warnings = []
        compliant_count = 0

        for skill_file in skill_files:
            try:
                with open(skill_file, encoding="utf-8") as f:
                    content = f.read()

                # Check content length first (always check regardless of frontmatter)
                estimated_tokens = estimate_tokens(content)
                if estimated_tokens > self.rules["max_tokens"]:
                    max_tokens = self.rules["max_tokens"]
                    warnings.append(
                        f"{skill_file.parent.name}: Exceeds token limit "
                        f"({estimated_tokens} > {max_tokens})",
                    )

                # Parse frontmatter using centralized processor
                result = FrontmatterProcessor.parse(
                    content,
                    required_fields=self.rules["required_fields"],
                )

                # Check for parse errors (invalid YAML or missing frontmatter)
                if result.parse_error:
                    issues.append(f"{skill_file.parent.name}: {result.parse_error}")
                    continue

                # Check for missing required fields
                if result.missing_fields:
                    skill_name = skill_file.parent.name
                    fields_str = ", ".join(result.missing_fields)
                    issues.append(
                        f"{skill_name}: Missing required fields: {fields_str}",
                    )
                    continue

                compliant_count += 1

            except Exception as e:
                issues.append(f"{skill_file.parent.name}: Error reading file - {e}")

        compliant = compliant_count == total_skills and len(issues) == 0

        return {
            "compliant": compliant,
            "issues": issues,
            "warnings": warnings,
            "total_skills": total_skills,
            "compliant_count": compliant_count,
        }

    def generate_report(self) -> str:
        """Generate a compliance report."""
        results = self.check_compliance()

        lines = [
            f"Compliance Report for {self.skill_root}",
            "=" * 50,
            f"Total Skills: {results['total_skills']}",
            f"Compliant: {'Yes' if results['compliant'] else 'No'}",
            "",
        ]

        if results["issues"]:
            lines.append("Issues:")
            for issue in results["issues"]:
                lines.append(f"  - {issue}")
            lines.append("")

        if results["warnings"]:
            lines.append("Warnings:")
            for warning in results["warnings"]:
                lines.append(f"  - {warning}")
            lines.append("")

        return "\n".join(lines)
