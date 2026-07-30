"""Reporting mixin: recommendations, quality report, multi-file, integration."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any


class ReportingMixin:
    """Generate makefile recommendations, reports, and cross-file analysis."""

    if TYPE_CHECKING:

        def _get_makefile_content(self, context: Any) -> str: ...

    def generate_makefile_recommendations(
        self,
        makefile_analysis: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Generate actionable recommendations from analysis."""
        recommendations = []

        if makefile_analysis.get("structure_issues", 0) > 0:
            recommendations.append(
                {
                    "category": "structure",
                    "priority": "high",
                    "action": "Add .PHONY declarations for non-file targets",
                    "example": ".PHONY: all clean test install",
                    "benefit": "Prevents file conflicts and improves build reliability",
                }
            )

        if makefile_analysis.get("performance_problems", 0) > 0:
            recommendations.append(
                {
                    "category": "performance",
                    "priority": "medium",
                    "action": "Enable parallel builds with independent targets",
                    "example": "make -j$(nproc) all",
                    "benefit": "Significantly reduces build time on multi-core systems",
                }
            )

        if makefile_analysis.get("security_vulnerabilities", 0) > 0:
            recommendations.append(
                {
                    "category": "security",
                    "priority": "high",
                    "action": "Remove sudo and privilege escalation from makefiles",
                    "example": "Use DESTDIR and user-level installation instead",
                    "benefit": "Prevents security vulns and follows least privilege",
                }
            )

        if makefile_analysis.get("portability_issues", 0) > 0:
            recommendations.append(
                {
                    "category": "portability",
                    "priority": "medium",
                    "action": "Use variables for platform-specific commands",
                    "example": "RM ?= rm -f\nclean:\n\t$(RM) *.o",
                    "benefit": "Enables cross-platform builds and easier maintenance",
                }
            )

        return recommendations

    def create_makefile_quality_report(
        self,
        makefile_analysis: dict[str, Any],
    ) -> str:
        """Create a structured quality report from analysis."""
        report_lines: list[str] = []

        report_lines.append("## Makefile Quality Assessment")
        report_lines.append("")
        overall_score = makefile_analysis.get("overall_score", 0.0)
        report_lines.append(f"**Overall Score**: {overall_score}/10")
        report_lines.append("")

        report_lines.append("## Structure Analysis")
        structure_score = makefile_analysis.get("structure_score", 0.0)
        report_lines.append(f"**Score**: {structure_score}/10")
        report_lines.append("")
        total_targets = makefile_analysis.get("total_targets", 0)
        phony_targets = makefile_analysis.get("phony_targets", 0)
        missing_phony = makefile_analysis.get("missing_phony", 0)
        report_lines.append(f"- Total targets: {total_targets}")
        report_lines.append(f"- Declared .PHONY targets: {phony_targets}")
        report_lines.append(f"- Missing .PHONY declarations: {missing_phony}")
        report_lines.append("")

        report_lines.append("## Performance Evaluation")
        performance_score = makefile_analysis.get("performance_score", 0.0)
        report_lines.append(f"**Score**: {performance_score}/10")
        optimization_opportunities = makefile_analysis.get(
            "optimization_opportunities", 0
        )
        report_lines.append(
            f"- Optimization opportunities: {optimization_opportunities}"
        )
        report_lines.append("")

        report_lines.append("## Security Review")
        security_score = makefile_analysis.get("security_score", 0.0)
        report_lines.append(f"**Score**: {security_score}/10")
        security_issues = makefile_analysis.get("security_issues", 0)
        report_lines.append(f"- Security issues found: {security_issues}")
        report_lines.append("")

        report_lines.append("## Portability Assessment")
        portability_score = makefile_analysis.get("portability_score", 0.0)
        report_lines.append(f"**Score**: {portability_score}/10")
        report_lines.append("")

        report_lines.append("## Recommendations")
        report_lines.append("")
        findings = makefile_analysis.get("findings", [])
        for finding in findings[:5]:
            report_lines.append(f"- {finding.get('title', 'Issue')}")
        report_lines.append("")

        return "\n".join(report_lines)

    def analyze_multiple_makefiles(self, context: Any) -> dict[str, Any]:
        """Analyze multiple makefiles for consistency."""
        makefiles = context.get_files()

        consistency_issues: list[str] = []
        variable_conflicts: list[str] = []
        target_naming: list[str] = []
        all_variables: dict[str, str] = {}

        var_pattern = re.compile(r"^([A-Z_]+)\s*=\s*(.+)$", re.MULTILINE)

        for makefile in makefiles:
            content = context.get_file_content(makefile)
            for match in var_pattern.finditer(content):
                var_name = match.group(1)
                var_value = match.group(2).strip()
                if var_name in all_variables:
                    if all_variables[var_name] != var_value:
                        variable_conflicts.append(
                            f"{var_name}: {all_variables[var_name]} vs {var_value}"
                        )
                else:
                    all_variables[var_name] = var_value

        if len({v for k, v in all_variables.items() if k in ["CC", "CFLAGS"]}) > 1:
            consistency_issues.append("Inconsistent compiler settings across makefiles")

        return {
            "consistency_issues": consistency_issues,
            "variable_conflicts": variable_conflicts,
            "target_naming": target_naming,
            "cross_file_dependencies": [],
        }

    def analyze_build_system_integration(self, context: Any) -> dict[str, Any]:
        """Analyze makefile integration with other build systems."""
        files = context.get_files()

        build_system_conflicts: list[str] = []
        ci_integration: list[str] = []
        package_manager_integration: list[str] = []
        tooling_compatibility: list[str] = []

        has_makefile = any("Makefile" in f for f in files)
        has_cmake = any("CMakeLists.txt" in f for f in files)

        if has_makefile and has_cmake:
            build_system_conflicts.append("Both Makefile and CMake detected")

        for file in files:
            if ".github/workflows" in file or ".yml" in file:
                content = context.get_file_content(file)
                if "make" in content:
                    ci_integration.append("GitHub Actions integration detected")

        for file in files:
            if "package.json" in file:
                content = context.get_file_content(file)
                if "make" in content:
                    package_manager_integration.append("npm integration detected")

        return {
            "build_system_conflicts": build_system_conflicts,
            "ci_integration": ci_integration,
            "package_manager_integration": package_manager_integration,
            "tooling_compatibility": tooling_compatibility,
        }
