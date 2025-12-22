"""Compliance checking for skills against standards."""

import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.abstract.frontmatter import FrontmatterProcessor
from src.abstract.tokens import estimate_tokens

logger = logging.getLogger(__name__)


# Patterns for trigger isolation checks
TRIGGER_PATTERNS = {
    "triggers": re.compile(r"Triggers?:\s*", re.IGNORECASE),
    "use_when": re.compile(r"Use when:\s*", re.IGNORECASE),
    "not_use_when": re.compile(r"DO NOT use when:\s*", re.IGNORECASE),
}

# Patterns that indicate trigger logic in body (violations)
BODY_TRIGGER_PATTERNS = {
    "when_to_use": re.compile(r"^##?\s*When to Use", re.MULTILINE | re.IGNORECASE),
    "perfect_for": re.compile(r"Perfect for:", re.IGNORECASE),
    "dont_use_when": re.compile(r"Don'?t use when:", re.IGNORECASE),
}

# Enforcement language intensity patterns
ENFORCEMENT_PATTERNS = {
    "maximum": [
        re.compile(r"YOU MUST", re.IGNORECASE),
        re.compile(r"NON-NEGOTIABLE", re.IGNORECASE),
        re.compile(r"NEVER skip", re.IGNORECASE),
    ],
    "high": [
        re.compile(r"Use.*BEFORE", re.IGNORECASE),
        re.compile(r"Check even if", re.IGNORECASE),
    ],
    "medium": [
        re.compile(r"Use when", re.IGNORECASE),
        re.compile(r"Consider.*when", re.IGNORECASE),
    ],
    "low": [
        re.compile(r"Available for", re.IGNORECASE),
        re.compile(r"Consult when", re.IGNORECASE),
    ],
}


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


@dataclass
class TriggerIsolationResult:
    """Result of trigger isolation analysis."""

    has_triggers: bool
    has_use_when: bool
    has_not_use_when: bool
    body_has_when_to_use: bool
    body_has_duplicates: bool
    score: int  # 0-10
    issues: list[str]


def check_trigger_isolation(description: str, body: str) -> TriggerIsolationResult:
    """Check if trigger logic is properly isolated in description.

    Args:
        description: The skill's description field from frontmatter.
        body: The skill's markdown body (after frontmatter).

    Returns:
        TriggerIsolationResult with analysis details.

    """
    # Handle None inputs gracefully
    description = description or ""
    body = body or ""

    issues = []

    # Check description for required trigger patterns
    has_triggers = bool(TRIGGER_PATTERNS["triggers"].search(description))
    has_use_when = bool(TRIGGER_PATTERNS["use_when"].search(description))
    has_not_use_when = bool(TRIGGER_PATTERNS["not_use_when"].search(description))

    # Check body for patterns that should be in description
    body_has_when_to_use = bool(BODY_TRIGGER_PATTERNS["when_to_use"].search(body))
    body_has_duplicates = bool(
        BODY_TRIGGER_PATTERNS["perfect_for"].search(body)
        or BODY_TRIGGER_PATTERNS["dont_use_when"].search(body)
    )

    # Calculate score (10 points max)
    score = 0

    if has_triggers:
        score += 2
    else:
        issues.append("Missing 'Triggers:' in description")

    if has_use_when:
        score += 3
    else:
        issues.append("Missing 'Use when:' in description")

    if has_not_use_when:
        score += 3
    else:
        issues.append("Missing 'DO NOT use when:' in description")

    if not body_has_when_to_use:
        score += 1
    else:
        issues.append("Body contains 'When to Use' section (should be in description)")

    if not body_has_duplicates:
        score += 1
    else:
        issues.append("Body contains trigger patterns that duplicate description")

    return TriggerIsolationResult(
        has_triggers=has_triggers,
        has_use_when=has_use_when,
        has_not_use_when=has_not_use_when,
        body_has_when_to_use=body_has_when_to_use,
        body_has_duplicates=body_has_duplicates,
        score=score,
        issues=issues,
    )


def detect_enforcement_level(description: str) -> str:
    """Detect the enforcement language intensity in a description.

    Args:
        description: The skill's description field.

    Returns:
        Enforcement level: 'maximum', 'high', 'medium', 'low', or 'none'.

    """
    # Handle None input gracefully
    if not description:
        return "none"

    for level in ["maximum", "high", "medium", "low"]:
        for pattern in ENFORCEMENT_PATTERNS[level]:
            if pattern.search(description):
                return level
    return "none"


class ComplianceChecker:
    """Core compliance checking functionality."""

    def __init__(self, skill_root: Path, rules_file: Path | None = None) -> None:
        """Initialize the compliance checker."""
        self.skill_root = skill_root
        self.rules_file = rules_file
        self.rules = self._load_rules()

    def _load_rules(self) -> dict[str, Any]:
        """Load compliance rules from file or use defaults."""
        if self.rules_file and self.rules_file.exists():
            try:
                with open(self.rules_file, encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                logger.error("Failed to load rules from %s: %s", self.rules_file, e)
                # Fall through to defaults

        # Default rules
        return {
            "required_fields": ["name", "description"],
            "max_tokens": 4000,
            "required_sections": ["Overview", "Quick Start"],
            # Trigger isolation settings
            "check_trigger_isolation": True,
            "min_trigger_isolation_score": 7,  # Out of 10
            "require_negative_triggers": True,
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

                skill_name = skill_file.parent.name

                # Check trigger isolation if enabled
                if self.rules.get("check_trigger_isolation", True):
                    description = result.parsed.get("description", "")
                    trigger_result = check_trigger_isolation(description, result.body)

                    # Report trigger isolation issues as warnings
                    # Skip "DO NOT use when" issues if require_negative_triggers
                    # is True, since we handle that separately below
                    min_score = self.rules.get("min_trigger_isolation_score", 7)
                    require_negative = self.rules.get("require_negative_triggers", True)
                    if trigger_result.score < min_score:
                        filtered = (
                            i
                            for i in trigger_result.issues
                            if not (require_negative and "DO NOT use when" in i)
                        )
                        warnings.extend(f"{skill_name}: {i}" for i in filtered)

                    # Missing negative triggers is a more serious issue
                    if require_negative and not trigger_result.has_not_use_when:
                        warnings.append(
                            f"{skill_name}: Missing 'DO NOT use when:' "
                            "(negative triggers required)"
                        )

                    # Body containing "When to Use" is a compliance issue
                    if trigger_result.body_has_when_to_use:
                        issues.append(
                            f"{skill_name}: Body contains 'When to Use' section "
                            "(trigger logic should be in description only)"
                        )
                        continue

                compliant_count += 1

            except (
                FileNotFoundError,
                PermissionError,
                UnicodeDecodeError,
                OSError,
            ) as e:
                issues.append(f"{skill_file.parent.name}: {e}")

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
