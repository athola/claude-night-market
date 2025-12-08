#!/usr/bin/env python3
"""Imbue plugin validation tool for review workflow and evidence management skills."""

import argparse
import json
import re
from pathlib import Path
from typing import TypedDict


class ImbueValidationResult(TypedDict):
    """Result of imbue plugin validation."""

    skills_found: set[str]
    review_workflow_skills: set[str]
    evidence_logging_patterns: set[str]
    issues: list[str]


class ImbueValidator:
    """Validator for imbue plugin review workflow and evidence management skills."""

    def __init__(self, plugin_root: Path):
        """Initialize the imbue validator.

        Args:
            plugin_root: Root directory of the imbue plugin.

        """
        self.plugin_root = plugin_root
        self.skill_files = list(plugin_root.rglob("SKILL.md"))
        self.plugin_config = plugin_root / "plugin.json"

    def scan_review_workflows(self) -> ImbueValidationResult:
        """Scan for review workflow skills and evidence patterns."""
        skills_found: set[str] = set()
        review_workflow_skills: set[str] = set()
        evidence_logging_patterns: set[str] = set()
        issues: list[str] = []

        # Load plugin configuration
        if self.plugin_config.exists():
            try:
                json.loads(self.plugin_config.read_text())
                # Imbue provides review workflow infrastructure to other plugins
                evidence_logging_patterns.add("review-workflows")
                evidence_logging_patterns.add("evidence-logging")
                evidence_logging_patterns.add("structured-output")
                evidence_logging_patterns.add("workflow-orchestration")
            except json.JSONDecodeError:
                issues.append("Invalid plugin.json")

        # Scan skills for review workflow patterns
        for skill_file in self.skill_files:
            skill_name = skill_file.parent.name
            skills_found.add(skill_name)

            content = skill_file.read_text()

            # Check for review workflow patterns
            review_patterns = [
                r"review",
                r"workflow",
                r"evidence",
                r"structured",
                r"output",
                r"orchestrat",
                r"checklist",
                r"deliverable",
            ]

            for pattern in review_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    review_workflow_skills.add(skill_name)
                    break

        return ImbueValidationResult(
            skills_found=skills_found,
            review_workflow_skills=review_workflow_skills,
            evidence_logging_patterns=evidence_logging_patterns,
            issues=issues,
        )

    def validate_review_workflows(self) -> list[str]:
        """Validate that skills follow review workflow patterns."""
        issues: list[str] = []

        for skill_file in self.skill_files:
            content = skill_file.read_text()
            skill_name = skill_file.parent.name

            # Check for review-specific indicators
            if skill_name == "review-core":
                # Core skill with comprehensive review functionality
                review_components = [
                    r"checklist",
                    r"deliverable",
                    r"evidence",
                    r"structured.*output",
                    r"workflow",
                ]

                missing_components = []
                for component in review_components:
                    if not re.search(component, content, re.IGNORECASE):
                        missing_components.append(component)

                if missing_components:
                    missing_str = ", ".join(missing_components)
                issues.append(f"{skill_name}: Missing review components: {missing_str}")

            # Check for evidence logging patterns
            evidence_patterns = [
                r"log",
                r"track",
                r"record",
                r"document",
                r"capture",
                r"evidence",
            ]

            has_evidence = any(
                re.search(pattern, content, re.IGNORECASE)
                for pattern in evidence_patterns
            )

            if not has_evidence and skill_name not in ["review-core"]:
                issues.append(f"{skill_name}: Should have evidence logging patterns")

        return issues

    def generate_report(self) -> str:
        """Generate comprehensive validation report."""
        result = self.scan_review_workflows()
        issues = self.validate_review_workflows()

        report = ["Imbue Plugin Review Workflow Report", "=" * 50]
        report.append(f"\nPlugin Root: {self.plugin_root}")
        report.append(f"Skill Files: {len(self.skill_files)}")

        report.append(
            f"\nReview Workflow Skills: {sorted(result['review_workflow_skills'])}"
        )
        report.append(
            f"Evidence Logging Patterns: {sorted(result['evidence_logging_patterns'])}"
        )

        if issues:
            report.append(f"\nIssues Found ({len(issues)}):")
            for i, issue in enumerate(issues, 1):
                report.append(f"  {i}. {issue}")
        else:
            report.append("\nAll review workflow skills validated successfully!")

        return "\n".join(report)


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Validate imbue plugin review workflow skills"
    )
    parser.add_argument(
        "--root", default="/home/alext/imbue", help="Imbue plugin root directory"
    )
    parser.add_argument("--report", action="store_true", help="Generate full report")
    parser.add_argument(
        "--scan", action="store_true", help="Scan for review workflow patterns"
    )

    args = parser.parse_args()

    validator = ImbueValidator(Path(args.root))

    if args.report:
        print(validator.generate_report())
    elif args.scan:
        result = validator.scan_review_workflows()
        issues = validator.validate_review_workflows()
        print(f"Review workflow skills: {sorted(result['review_workflow_skills'])}")
        if issues:
            print(f"Issues found: {len(issues)}")
        else:
            print("No issues found!")
    else:
        print("Use --report or --scan. Use --help for details.")


if __name__ == "__main__":
    main()
