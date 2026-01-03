"""Orchestrate review skills using a unified review skill."""

from __future__ import annotations

import re
from typing import Any, ClassVar

from .base import AnalysisResult, BaseReviewSkill


def dispatch_agent(skill_name: str, _context: Any) -> str:
    """Dispatch an agent to execute a specific skill.

    Args:
        skill_name: Name of the skill to execute
        _context: Analysis context (unused in placeholder)

    Returns:
        Skill execution result
    """
    import asyncio

    from pensive.workflows.skill_coordinator import (
        dispatch_agent as coordinator_dispatch,
    )

    # Run the async dispatch synchronously
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(coordinator_dispatch(skill_name, _context))


class UnifiedReviewSkill(BaseReviewSkill):
    """Orchestrate review skills for code review."""

    skill_name: ClassVar[str] = "unified-review"
    supported_languages: ClassVar[list[str]] = [
        "python",
        "javascript",
        "typescript",
        "rust",
        "go",
        "java",
    ]

    # File extension to language mapping
    LANGUAGE_MARKERS: ClassVar[dict[str, dict[str, list[str]]]] = {
        "rust": {
            "extensions": [".rs"],
            "config_files": ["Cargo.toml", "Cargo.lock"],
        },
        "python": {
            "extensions": [".py"],
            "config_files": ["setup.py", "requirements.txt", "pyproject.toml"],
            "test_patterns": ["test_*.py", "*_test.py"],
        },
        "javascript": {
            "extensions": [".js", ".mjs"],
            "config_files": ["package.json"],
        },
        "typescript": {
            "extensions": [".ts"],
            "config_files": ["tsconfig.json"],
        },
    }

    # Mathematical library imports to detect
    MATH_IMPORTS: ClassVar[list[str]] = [
        "numpy",
        "scipy",
        "sympy",
        "pandas",
        "sklearn",
        "tensorflow",
        "torch",
        "math",
        "statistics",
    ]

    def detect_languages(self, context: Any) -> dict[str, Any]:
        """Detect programming languages in the codebase.

        Returns:
            Dictionary mapping language names to detection metadata
        """
        files = context.get_files()
        languages: dict[str, Any] = {}

        for lang, markers in self.LANGUAGE_MARKERS.items():
            file_count = 0
            lang_info: dict[str, Any] = {"files": 0}
            extensions = markers["extensions"]

            # Count files by extension
            for file in files:
                if any(file.endswith(ext) for ext in extensions):
                    file_count += 1

            # Check for config files (only count if not already counted by extension)
            for config_file in markers["config_files"]:
                if config_file in files:
                    if config_file == "Cargo.toml":
                        lang_info["cargo_toml"] = True
                    # Only add to count if config file doesn't match the extensions
                    if not any(config_file.endswith(ext) for ext in extensions):
                        file_count += 1

            # Check for test patterns
            if "test_patterns" in markers:
                test_file_count = 0
                for file in files:
                    # Match test patterns like "test_*.py" -> "test_app.py"
                    for pattern in markers["test_patterns"]:
                        if (pattern.startswith("test_") and "test_" in file) or (
                            pattern.endswith("_test.") and "_test." in file
                        ):
                            test_file_count += 1
                            break
                if test_file_count > 0:
                    lang_info["test_files"] = True

            # Add language if we found files
            if file_count > 0:
                lang_info["files"] = file_count
                languages[lang] = lang_info

        return languages

    def detect_build_systems(self, context: Any) -> list[str]:
        """Detect build systems used in the codebase.

        Returns:
            List of detected build system names
        """
        files = context.get_files()
        build_systems = []

        # Check for Makefile
        if "Makefile" in files or "makefile" in files:
            build_systems.extend(["make", "makefile"])

        # Check for other build systems
        if "CMakeLists.txt" in files:
            build_systems.append("cmake")
        if "build.gradle" in files or "build.gradle.kts" in files:
            build_systems.append("gradle")
        if "pom.xml" in files:
            build_systems.append("maven")
        if "Cargo.toml" in files:
            build_systems.append("cargo")

        return build_systems

    def select_review_skills(self, context: Any) -> list[str]:
        """Select appropriate review skills based on codebase.

        Returns:
            List of skill names to execute
        """
        skills = ["code-reviewer"]  # Always include general review
        files = context.get_files()

        # Language-specific skills
        if "Cargo.toml" in files or any(f.endswith(".rs") for f in files):
            skills.append("rust-review")

        if "Makefile" in files or "makefile" in files:
            skills.append("makefile-review")

        # Check for test files
        test_patterns = ["test_", "_test.", "tests/", "test/"]
        has_tests = any(any(pattern in f for pattern in test_patterns) for f in files)
        if has_tests:
            skills.append("test-review")

        # Check for mathematical code
        has_math = False
        for file in files:
            if file.endswith(".py"):
                try:
                    content = context.get_file_content(file)
                    if any(
                        f"import {lib}" in content or f"from {lib}" in content
                        for lib in self.MATH_IMPORTS
                    ):
                        has_math = True
                        break
                except Exception:
                    pass

        if has_math:
            skills.append("math-review")

        return skills

    def prioritize_findings(
        self, findings: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Prioritize findings by severity and impact.

        Args:
            findings: List of finding dictionaries

        Returns:
            Sorted list of findings (high to low severity)
        """
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}

        def get_severity_rank(finding: dict[str, Any]) -> int:
            return severity_order.get(finding.get("severity", "low"), 99)

        return sorted(findings, key=get_severity_rank)

    def consolidate_findings(
        self, findings: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Consolidate duplicate or related findings.

        Args:
            findings: List of finding dictionaries

        Returns:
            Deduplicated list of findings
        """
        seen_ids = set()
        consolidated = []

        for finding in findings:
            finding_id = finding.get("id")
            if finding_id and finding_id not in seen_ids:
                seen_ids.add(finding_id)
                consolidated.append(finding)
            elif not finding_id:
                # Include findings without IDs
                consolidated.append(finding)

        return consolidated

    def generate_summary(self, findings: list[dict[str, Any]]) -> str:
        """Generate a summary of all findings.

        Args:
            findings: List of finding dictionaries

        Returns:
            Markdown-formatted summary
        """
        summary_parts = ["## Summary\n"]

        # Count by severity
        severity_counts: dict[str, int] = {}
        for finding in findings:
            severity = finding.get("severity", "unknown")
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

        summary_parts.append(
            f"Found {len(findings)} total findings: "
            + ", ".join(f"{count} {sev}" for sev, count in severity_counts.items())
        )
        summary_parts.append("\n")

        # Findings section
        summary_parts.append("## Findings\n")
        for finding in findings:
            finding_id = finding.get("id", "UNKNOWN")
            title = finding.get("title", "Untitled")
            location = finding.get("location", "Unknown location")
            severity = finding.get("severity", "unknown")
            issue = finding.get("issue", "No description")

            summary_parts.append(f"### [{finding_id}] {title}\n")
            summary_parts.append(f"- **Location**: {location}\n")
            summary_parts.append(f"- **Severity**: {severity}\n")
            summary_parts.append(f"- **Issue**: {issue}\n\n")

        # Action items
        summary_parts.append("## Action Items\n")
        for finding in findings:
            severity = finding.get("severity", "low")
            finding_id = finding.get("id", "UNKNOWN")
            fix = finding.get("fix", "Review required")
            summary_parts.append(f"- [{severity}] {fix} ({finding_id})\n")

        summary_parts.append("\n")

        # Recommendation
        summary_parts.append("## Recommendation\n")
        summary_parts.append(self.generate_recommendation(findings))

        return "".join(summary_parts)

    def generate_recommendation(self, findings: list[dict[str, Any]]) -> str:
        """Generate recommendations based on findings.

        Args:
            findings: List of finding dictionaries

        Returns:
            Recommendation string
        """
        if not findings:
            return "Approve - No issues found"

        # Check for critical or high severity findings
        has_critical = any(f.get("severity") == "critical" for f in findings)
        has_high = any(f.get("severity") == "high" for f in findings)

        if has_critical:
            return "Block - Critical security/functionality issues must be resolved"
        elif has_high:
            return "Request changes - High severity issues before merging"
        else:
            return "Approve with minor changes - Low/medium issues in follow-up"

    def create_action_items(
        self, findings: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Create actionable items from findings.

        Args:
            findings: List of finding dictionaries

        Returns:
            List of action item dictionaries
        """
        action_items = []

        for finding in findings:
            severity = finding.get("severity", "low")
            finding_id = finding.get("id", "UNKNOWN")
            fix = finding.get("fix", "Review and address this issue")

            # Determine deadline based on severity
            if severity in ["critical", "high"]:
                deadline = "ASAP"
            elif severity == "medium":
                deadline = "This week"
            else:
                deadline = "Next sprint"

            action_items.append(
                {
                    "action": fix,
                    "owner": "Development Team",
                    "deadline": deadline,
                    "severity": severity,
                    "finding_id": finding_id,
                }
            )

        return action_items

    def analyze(self, context: Any, _file_path: str = "") -> AnalysisResult:
        """Run unified analysis across all applicable skills.

        Args:
            context: Analysis context
            _file_path: Optional specific file path (unused)

        Returns:
            Analysis result string
        """
        files = context.get_files()
        if not files:
            return AnalysisResult(warnings=["No code files found in the repository"])

        # Detect languages and skills
        languages = self.detect_languages(context)
        selected_skills = self.select_review_skills(context)

        summary = (
            f"Analyzed {len(files)} files, {len(languages)} languages, "
            f"{len(selected_skills)} skills"
        )
        return AnalysisResult(
            info={
                "summary": summary,
                "files_analyzed": len(files),
                "languages_detected": languages,
                "skills_executed": selected_skills,
            }
        )

    def detect_api_surface(self, context: Any) -> dict[str, Any]:
        """Detect public API surface in the codebase.

        Args:
            context: Analysis context

        Returns:
            Dictionary with API surface metrics
        """
        files = context.get_files()
        api_surface = {"exports": 0, "classes": 0, "functions": 0, "interfaces": 0}

        for file in files:
            if not file.endswith((".ts", ".js", ".py")):
                continue

            try:
                # Handle both callable and direct return mocks
                content = (
                    context.get_file_content(file)
                    if callable(context.get_file_content)
                    else context.get_file_content
                )

                # Count exports (TypeScript/JavaScript)
                export_matches = re.findall(r"^\s*export ", content, re.MULTILINE)
                api_surface["exports"] += len(export_matches)

                # Count classes
                class_matches = re.findall(r"(export\s+)?class\s+\w+", content)
                api_surface["classes"] += len(class_matches)

                # Count functions
                function_matches = re.findall(r"(export\s+)?function\s+\w+", content)
                api_surface["functions"] += len(function_matches)

                # Count interfaces
                interface_matches = re.findall(r"(export\s+)?interface\s+\w+", content)
                api_surface["interfaces"] += len(interface_matches)

            except Exception:
                pass

        return api_surface

    def execute_skills_concurrently(self, skills: list[str], context: Any) -> list[str]:
        """Execute multiple skills concurrently.

        Args:
            skills: List of skill names to execute
            context: Analysis context

        Returns:
            List of skill execution results
        """
        # Use module-level dispatch_agent for testability
        results = []
        for skill in skills:
            result = dispatch_agent(skill, context)
            results.append(result)
        return results

    def calculate_confidence_score(
        self,
        findings: list[dict[str, Any]],
        analysis_data: dict[str, Any] | None = None,
    ) -> float:
        """Calculate confidence score for findings.

        Args:
            findings: List of finding dictionaries
            analysis_data: Optional analysis metadata

        Returns:
            Confidence score between 0 and 100
        """
        if analysis_data is None:
            analysis_data = {}

        base_score = 50.0

        # More findings increase confidence (up to a point)
        finding_bonus = min(len(findings) * 5, 20)

        # Multiple languages detected increases confidence
        languages_detected = analysis_data.get("languages_detected", [])
        if not isinstance(languages_detected, list):
            languages_detected = []
        language_bonus = min(len(languages_detected) * 5, 10)

        # More files analyzed increases confidence
        files_analyzed = analysis_data.get("files_analyzed", 0)
        if not isinstance(files_analyzed, int):
            files_analyzed = 0
        file_bonus = min(files_analyzed * 2, 15)

        # More skills executed increases confidence
        skills_executed = analysis_data.get("skills_executed", 0)
        if not isinstance(skills_executed, int):
            skills_executed = 0
        skill_bonus = min(skills_executed * 5, 15)

        total_score = (
            base_score + finding_bonus + language_bonus + file_bonus + skill_bonus
        )

        # Cap at 100
        return min(total_score, 100.0)

    def format_findings(self, findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Format findings for display.

        Args:
            findings: List of finding dictionaries

        Returns:
            List of formatted finding dictionaries
        """
        formatted = []
        valid_severities = {"critical", "high", "medium", "low"}

        for finding in findings:
            # validate all required fields exist
            formatted_finding = {
                "id": finding.get("id", "UNKNOWN"),
                "title": finding.get("title", "Untitled"),
                "location": finding.get("location", "Unknown"),
                "severity": finding.get("severity", "low"),
                "issue": finding.get("issue", "No description"),
                "fix": finding.get("fix", "Review required"),
            }

            # Normalize severity to allowed values
            if formatted_finding["severity"] not in valid_severities:
                formatted_finding["severity"] = "low"

            formatted.append(formatted_finding)

        return formatted
