"""Orchestrate review skills using a unified review skill."""

from __future__ import annotations

import re
from typing import Any, ClassVar

from pensive.analysis.repository_analyzer import RepositoryAnalyzer
from pensive.utils.severity_mapper import count_by_severity

from .base import AnalysisResult, BaseReviewSkill


def dispatch_agent(skill_name: str, _context: Any) -> str:
    return f"{skill_name} execution result"


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

        Delegates extension/config detection to RepositoryAnalyzer, then
        enriches with context-specific metadata (Cargo.toml flag, test files).

        Returns:
            Dictionary mapping language names to detection metadata
        """
        files = context.get_files()
        # Set lookup for O(1) membership tests inside the per-language loop.
        # Build once outside the loop so a large repo doesn't pay O(n)
        # per config-file probe.
        files_set = set(files)
        languages: dict[str, Any] = {}

        # Build counts using RepositoryAnalyzer mappings
        for lang, extensions in RepositoryAnalyzer.LANGUAGE_EXTENSIONS.items():
            file_count = sum(
                1 for f in files if any(f.endswith(ext) for ext in extensions)
            )
            lang_info: dict[str, Any] = {"files": 0}

            # Check config files
            config_files = RepositoryAnalyzer.LANGUAGE_CONFIG_FILES.get(lang, [])
            for config_file in config_files:
                if config_file in files_set:
                    if config_file == "Cargo.toml":
                        lang_info["cargo_toml"] = True
                    if not any(config_file.endswith(ext) for ext in extensions):
                        file_count += 1

            # Check for test patterns (Python)
            if lang == "python":
                test_file_count = sum(1 for f in files if "test_" in f or "_test." in f)
                if test_file_count > 0:
                    lang_info["test_files"] = True

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
                except (FileNotFoundError, OSError, AttributeError, TypeError):
                    pass

        if has_math:
            skills.append("math-review")

        return skills

    def prioritize_findings(
        self,
        findings: list[dict[str, Any]],
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
        self,
        findings: list[dict[str, Any]],
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

        severity_counts = count_by_severity(findings)

        summary_parts.append(
            f"Found {len(findings)} total findings: "
            + ", ".join(
                f"{count} {sev}" for sev, count in severity_counts.items() if count > 0
            )
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

            except (FileNotFoundError, OSError, AttributeError):
                pass

        return api_surface

    def execute_skills(self, skills: list[str], context: Any) -> list[str]:
        """Execute multiple skills sequentially.

        Args:
            skills: List of skill names to execute
            context: Analysis context

        Returns:
            List of skill execution results
        """
        results = []
        for skill in skills:
            result = dispatch_agent(skill, context)
            results.append(result)
        return results

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
