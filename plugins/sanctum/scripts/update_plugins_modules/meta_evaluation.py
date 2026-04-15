"""Phase 3: Meta-Evaluation Check module.

Validates recursive quality of evaluation-related skills:
- Checks for Table of Contents in long skills
- Validates verification steps are documented
- Ensures test references exist
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


class MetaEvaluator:
    """Validate recursive quality of evaluation-related skills."""

    # Keywords that indicate a skill is evaluation-related
    EVAL_KEYWORDS = [
        "review",
        "audit",
        "validate",
        "check",
        "eval",
        "test",
        "verify",
        "inspect",
    ]

    def check_plugin(self, plugin_path: Path) -> dict[str, Any]:
        """Check meta-evaluation quality for a plugin's skills.

        Args:
            plugin_path: Path to the plugin directory

        Returns:
            Dict with missing_toc, missing_verification, and missing_tests lists

        """
        issues: dict[str, Any] = {
            "missing_toc": [],
            "missing_verification": [],
            "missing_tests": [],
        }

        skills_dir = plugin_path / "skills"
        if not skills_dir.exists():
            return issues

        for skill_dir in skills_dir.iterdir():
            if not skill_dir.is_dir():
                continue

            skill_name = skill_dir.name
            skill_file = skill_dir / "SKILL.md"
            if not skill_file.exists():
                continue

            # Only check evaluation-related skills
            if not self._is_eval_skill(skill_name):
                continue

            try:
                content = skill_file.read_text(encoding="utf-8")
                skill_issues = self._check_skill_quality(skill_name, content)
                for category, category_list in issues.items():
                    category_list.extend(skill_issues.get(category, []))
            except OSError:
                continue

        return issues

    def _is_eval_skill(self, skill_name: str) -> bool:
        """Check if a skill name indicates it's evaluation-related."""
        return any(keyword in skill_name.lower() for keyword in self.EVAL_KEYWORDS)

    def _check_skill_quality(self, skill_name: str, content: str) -> dict[str, Any]:
        """Check quality of a single skill file."""
        issues: dict[str, Any] = {
            "missing_toc": [],
            "missing_verification": [],
            "missing_tests": [],
        }

        # ToC check disabled: ToC sections were removed ecosystem-wide
        # per the 2026-04-08 plugin audit.  Skills loaded into model
        # context don't benefit from HTML anchor links.

        # Check for verification steps
        has_verification = bool(
            re.search(
                r"verification|validate|check.*work|test.*correctness",
                content,
                re.IGNORECASE,
            )
        )
        if not has_verification:
            issues["missing_verification"].append(skill_name)

        # Check for test references
        has_tests = bool(re.search(r"test|spec", content, re.IGNORECASE))
        if not has_tests:
            issues["missing_tests"].append(skill_name)

        return issues
