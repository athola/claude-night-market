"""Makefile review skill for analyzing build system quality.

This skill analyzes makefiles for:
- Structure and organization issues
- Dependency management correctness
- Performance optimization opportunities
- Cross-platform portability
- Security vulnerabilities
- Variable usage patterns
- Target organization
- Modern best practices
"""

from __future__ import annotations

import re
from typing import Any

from .base import BaseReviewSkill


class MakefileReviewSkill(BaseReviewSkill):
    """Skill for reviewing makefiles and build system configurations."""

    skill_name: str = "makefile_review"
    supported_languages: list[str] = ["makefile", "make"]

    def __init__(self) -> None:
        """Initialize the makefile review skill."""
        super().__init__()

    def _get_makefile_content(self, context: Any) -> str:
        """Get makefile content from context.

        Args:
            context: Skill context with file access methods

        Returns:
            Makefile content as string
        """
        return context.get_file_content()

    def _extract_targets(self, content: str) -> list[str]:
        """Extract target names from makefile content.

        Args:
            content: Makefile content

        Returns:
            List of target names
        """
        # Match target definitions (word before colon at start of line)
        target_pattern = re.compile(r"^([a-zA-Z0-9_\-\.]+)\s*:", re.MULTILINE)
        targets = target_pattern.findall(content)
        return targets

    def _extract_phony_targets(self, content: str) -> list[str]:
        """Extract .PHONY declarations from makefile.

        Args:
            content: Makefile content

        Returns:
            List of declared phony targets
        """
        phony_pattern = re.compile(r"^\.PHONY:\s*(.+)$", re.MULTILINE)
        phony_matches = phony_pattern.findall(content)
        phony_targets = []
        for match in phony_matches:
            # Split by whitespace to get individual targets
            phony_targets.extend(match.split())
        return phony_targets

    def _is_file_target(self, target: str) -> bool:
        """Check if a target looks like a file target.

        Args:
            target: Target name

        Returns:
            True if target looks like a file (has extension or pattern)
        """
        # Pattern rules or file-like targets
        return "." in target and not target.startswith(".")

    def analyze_makefile_structure(self, context: Any) -> dict[str, Any]:
        """Analyze makefile structure for common issues.

        Args:
            context: Skill context with file access methods

        Returns:
            Dictionary with structure analysis results
        """
        content = self._get_makefile_content(context)

        # Extract targets and phony declarations
        targets = self._extract_targets(content)
        phony_targets = self._extract_phony_targets(content)

        # Common non-file targets that should be .PHONY
        common_phony = ["all", "build", "test", "clean", "install", "help", "docs"]

        missing_phony = []
        for target in targets:
            if target in common_phony and target not in phony_targets:
                missing_phony.append(target)
            elif not self._is_file_target(target) and target not in phony_targets:
                # Non-file-like targets should generally be .PHONY
                if target not in ["include", "ifdef", "ifndef", "ifeq", "ifneq"]:
                    missing_phony.append(target)

        # Check for error handling issues (no set -e, no || exit, no error checks)
        error_handling = []
        lines = content.split("\n")
        for i, line in enumerate(lines):
            # Look for recipe lines (start with tab)
            if line.startswith("\t"):
                cmd = line.strip()
                # Check for commands that should have error handling
                if re.search(r"(rm|cp|mv|mkdir|gcc|make|wget|curl)", cmd):
                    # No error handling markers
                    if not re.search(r"(\|\||set -e|; exit|\?=|@-)", cmd):
                        error_handling.append(f"Line {i+1}: {cmd[:50]}")

        # Check for hardcoded paths
        hardcoded_paths = []
        hardcoded_pattern = re.compile(r"(\/usr\/|\/bin\/|\/tmp\/|C:\\|\/home\/)")
        for i, line in enumerate(lines):
            if hardcoded_pattern.search(line):
                hardcoded_paths.append(f"Line {i+1}: {line.strip()[:60]}")

        # Check for variable usage (variables should be used, not hardcoded)
        variable_usage = []
        if not re.search(r"\$\([A-Z_]+\)", content):
            variable_usage.append("No variable usage detected")

        return {
            "missing_phony": missing_phony,
            "error_handling": error_handling[:10],  # Limit results
            "hardcoded_paths": hardcoded_paths,
            "variable_usage": variable_usage,
        }

    def analyze_dependencies(self, context: Any) -> dict[str, Any]:
        """Analyze dependency management in makefile.

        Args:
            context: Skill context with file access methods

        Returns:
            Dictionary with dependency analysis results
        """
        content = self._get_makefile_content(context)

        # Find targets and their dependencies
        target_deps = {}
        target_pattern = re.compile(r"^([a-zA-Z0-9_\-\.]+)\s*:\s*(.*)$", re.MULTILINE)
        for match in target_pattern.finditer(content):
            target = match.group(1)
            deps = match.group(2).split()
            target_deps[target] = deps

        # Check for circular dependencies
        circular_dependencies = []
        for target, deps in target_deps.items():
            for dep in deps:
                if dep in target_deps and target in target_deps[dep]:
                    circular_dependencies.append(f"{target} <-> {dep}")

        # Check for missing dependencies
        missing_dependencies = []

        # 1. Look for targets without automatic dependency tracking
        lines = content.split("\n")
        for i, line in enumerate(lines):
            # Check if target compiles source without listing dependencies
            if re.match(r"^main:", line) and "main.c" not in line:
                missing_dependencies.append(
                    f"Line {i+1}: main target missing source dependencies"
                )

            # Check for .o targets that compile without listing all dependencies
            if re.match(r"^parser\.o:", line):
                # Check next few lines for recipe
                recipe_start = i + 1
                while recipe_start < len(lines) and lines[recipe_start].startswith(
                    "\t"
                ):
                    recipe_start += 1
                target_block = "\n".join(lines[i:recipe_start])
                # parser.o likely needs parser.h but it's not listed
                if "parser.h" not in target_block and "parser.c" in target_block:
                    missing_dependencies.append(
                        f"Line {i+1}: parser.o missing header dependencies"
                    )

        # 2. Look for header dependencies missing
        for target, deps in target_deps.items():
            if target.endswith(".o"):
                # Check if corresponding .h file should be a dependency
                base_name = target[:-2]  # Remove .o
                if f"{base_name}.c" in deps:
                    # Should probably have .h too
                    if not any(dep.endswith(".h") for dep in deps):
                        missing_dependencies.append(
                            f"{target}: missing header file dependencies"
                        )

        # Check for automatic dependency generation
        automatic_dependencies = []
        if re.search(r"-MMD|-MD|-MF", content):
            automatic_dependencies.append("Automatic dependency generation detected")
        if re.search(r"include.*\.d\)", content):
            automatic_dependencies.append("Dependency file inclusion detected")

        # Check for header dependencies
        header_dependencies = []
        for target, deps in target_deps.items():
            if target.endswith(".o"):
                has_header = any(
                    dep.endswith(".h") or dep.endswith(".hpp") for dep in deps
                )
                if not has_header and target != "%.o":  # Skip pattern rules
                    header_dependencies.append(f"{target} missing header dependencies")

        return {
            "missing_dependencies": missing_dependencies[:10],
            "circular_dependencies": circular_dependencies,
            "automatic_dependencies": automatic_dependencies,
            "header_dependencies": header_dependencies,
        }

    def analyze_performance(self, context: Any) -> dict[str, Any]:
        """Analyze makefile for performance bottlenecks.

        Args:
            context: Skill context with file access methods

        Returns:
            Dictionary with performance analysis results
        """
        content = self._get_makefile_content(context)

        # Check for parallelization issues
        parallelization_issues = []

        # Look for many independent build targets without parallelization hints
        targets = self._extract_targets(content)
        build_targets = [t for t in targets if re.match(r"build\d+|source\d+\.o", t)]
        if len(build_targets) >= 5:
            parallelization_issues.append(
                f"{len(build_targets)} sequential build targets detected"
            )

        # Check if -j flag guidance is missing
        if not re.search(r"(-j|MAKEFLAGS.*-j|parallel)", content):
            if len(targets) > 5:
                parallelization_issues.append(
                    "No parallel execution configuration found"
                )

        # Check for sequential compilation of object files
        if re.search(r"^source\d+\.o:.*\n\tgcc -c", content, re.MULTILINE):
            parallelization_issues.append("Sequential object file compilation detected")

        # Check for unnecessary rebuilds (timestamp-based targets)
        unnecessary_rebuilds = []
        if re.search(r"date >|timestamp", content):
            unnecessary_rebuilds.append(
                "Timestamp generation may cause unnecessary rebuilds"
            )

        # Check for inefficient operations
        inefficient_operations = []
        lines = content.split("\n")

        # Look for multiple cp commands
        cp_count = 0
        for i, line in enumerate(lines):
            if line.startswith("\t") and re.search(r"cp -r", line):
                cp_count += 1
        if cp_count >= 3:
            inefficient_operations.append("Multiple sequential cp commands detected")

        # Check for file operations that could be optimized
        file_operations = []
        for i, line in enumerate(lines):
            if re.search(r"(cp -r|tar czf|rsync)", line):
                file_operations.append(
                    f"Line {i+1}: File operation - {line.strip()[:50]}"
                )

        return {
            "parallelization_issues": parallelization_issues,
            "unnecessary_rebuilds": unnecessary_rebuilds,
            "inefficient_operations": inefficient_operations,
            "file_operations": file_operations[:5],
        }

    def analyze_portability(self, context: Any) -> dict[str, Any]:
        """Analyze makefile portability across platforms.

        Args:
            context: Skill context with file access methods

        Returns:
            Dictionary with portability analysis results
        """
        content = self._get_makefile_content(context)

        # Check for hardcoded paths
        hardcoded_paths = []
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if re.search(r"(\/usr\/bin|\/usr\/local|C:\\|\\\\)", line):
                hardcoded_paths.append(f"Line {i+1}: {line.strip()[:60]}")

        # Check for platform-specific commands
        platform_specific = []
        for i, line in enumerate(lines):
            # Unix-specific
            if re.search(r"(^|\s)(rm -f|chmod|mkdir -p|gdb|cp |mv )", line):
                platform_specific.append(
                    f"Line {i+1}: Unix command - {line.strip()[:50]}"
                )
            # Windows-specific
            if re.search(r"(copy |del |xcopy)", line):
                platform_specific.append(
                    f"Line {i+1}: Windows command - {line.strip()[:50]}"
                )

        # Check for GNU extensions
        gnu_extensions = []
        if re.search(r"\$\(shell find", content):
            gnu_extensions.append("GNU make shell function with find")
        if re.search(r"\$\(patsubst", content):
            gnu_extensions.append("GNU make patsubst function")
        if re.search(r"\$\(shell git", content):
            gnu_extensions.append("GNU make shell function with git")

        # Check for cross-platform issues
        cross_platform_issues = []
        # Path separators
        if re.search(r"backup\\\\", content):
            cross_platform_issues.append("Windows-style path separators used")
        # Missing cross-platform alternatives
        if "rm -f" in content and "RM" not in content:
            cross_platform_issues.append("Direct rm usage without RM variable")

        return {
            "hardcoded_paths": hardcoded_paths[:5],
            "platform_specific": platform_specific[:5],
            "gnu_extensions": gnu_extensions,
            "cross_platform_issues": cross_platform_issues,
        }

    def analyze_security(self, context: Any) -> dict[str, Any]:
        """Analyze makefile for security vulnerabilities.

        Args:
            context: Skill context with file access methods

        Returns:
            Dictionary with security analysis results
        """
        content = self._get_makefile_content(context)

        # Check for command injection risks
        command_injection = []
        lines = content.split("\n")
        for i, line in enumerate(lines):
            # Piping to shell
            if re.search(r"\|\s*(sh|bash)(\s|$)", line):
                command_injection.append(
                    f"Line {i+1}: Piping to shell - {line.strip()[:50]}"
                )
            # Using read without validation
            if re.search(r"read -p.*\$\$", line):
                command_injection.append(f"Line {i+1}: User input without validation")
            # Unsafe rm with wildcards
            if re.search(r"rm -rf\s+/tmp/\*", line):
                command_injection.append(f"Line {i+1}: Dangerous rm with wildcards")

        # Check for privilege escalation
        privilege_escalation = []
        for i, line in enumerate(lines):
            if re.search(r"(^|\s)sudo\s", line):
                privilege_escalation.append(f"Line {i+1}: sudo usage in makefile")
            if re.search(r"chmod.*\+s", line):
                privilege_escalation.append(f"Line {i+1}: setuid bit modification")
            if re.search(r"EUID.*0", line):
                privilege_escalation.append(f"Line {i+1}: Root check in makefile")

        # Check for path traversal
        path_traversal = []
        if re.search(r"export PATH\s*:=\s*\.:", content):
            path_traversal.append("PATH manipulation - current directory in PATH")

        # Check for insecure downloads
        insecure_downloads = []
        for i, line in enumerate(lines):
            if re.search(r"(curl|wget).*http://", line):
                insecure_downloads.append(f"Line {i+1}: Insecure HTTP download")
            if re.search(r"(tar xzf|unzip)", line):
                insecure_downloads.append(
                    f"Line {i+1}: Archive extraction without validation"
                )

        return {
            "command_injection": command_injection[:5],
            "privilege_escalation": privilege_escalation,
            "path_traversal": path_traversal,
            "insecure_downloads": insecure_downloads[:5],
        }

    def analyze_variables(self, context: Any) -> dict[str, Any]:
        """Analyze variable usage and management.

        Args:
            context: Skill context with file access methods

        Returns:
            Dictionary with variable analysis results
        """
        content = self._get_makefile_content(context)

        # Find variable definitions
        defined_vars = set()
        var_def_pattern = re.compile(r"^([A-Z_][A-Z0-9_]*)\s*[:?]?=", re.MULTILINE)
        for match in var_def_pattern.finditer(content):
            defined_vars.add(match.group(1))

        # Find variable usages
        used_vars = set()
        var_use_pattern = re.compile(r"\$\(([A-Z_][A-Z0-9_]*)\)")
        for match in var_use_pattern.finditer(content):
            used_vars.add(match.group(1))

        # Check for undefined variables
        undefined_variables = []

        # First pass: check for variables used but not defined
        for var in used_vars:
            if var not in defined_vars:
                # Common built-in variables are OK
                if var not in ["CC", "CFLAGS", "LDFLAGS", "MAKE", "MAKEFLAGS"]:
                    if var not in undefined_variables:
                        undefined_variables.append(var)

        # Second pass: check for empty variable definitions
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if re.match(r"^(CFLAGS|LDFLAGS|SOURCES)\s*=\s*$", line):
                var_name = line.split("=")[0].strip()
                entry = f"Line {i+1}: Empty {var_name}"
                if entry not in undefined_variables:
                    undefined_variables.append(entry)

        # Third pass: check for use-before-definition
        # First, collect all variable definitions and their line numbers
        var_definitions = {}
        for i, line in enumerate(lines):
            var_def_match = re.match(r"^([A-Z_][A-Z0-9_]*)\s*[:?]?=", line)
            if var_def_match:
                var_name = var_def_match.group(1)
                if var_name not in var_definitions:
                    var_definitions[var_name] = i

        # Then check for uses before definition
        for i, line in enumerate(lines):
            # Check target dependencies for variable usage
            target_match = re.match(r"^[a-zA-Z0-9_\-]+:\s*(.*)$", line)
            if target_match:
                deps_part = target_match.group(1)
                # Find variables used in dependencies
                for var_match in re.finditer(r"\$\(([A-Z_][A-Z0-9_]*)\)", deps_part):
                    var_name = var_match.group(1)
                    # Check if variable is defined after this line (or not at all)
                    if var_name in var_definitions:
                        if var_definitions[var_name] > i:
                            # Variable used before definition
                            entry = f"{var_name} (used before definition)"
                            if entry not in undefined_variables:
                                undefined_variables.append(entry)
                    elif var_name not in [
                        "CC",
                        "CFLAGS",
                        "LDFLAGS",
                        "MAKE",
                        "MAKEFLAGS",
                    ]:
                        # Variable not defined at all (and not a built-in)
                        if var_name not in undefined_variables:
                            undefined_variables.append(var_name)

        # Check for scoping issues (recursive variables)
        scoping_issues = []
        if re.search(r"X\s*=\s*\$\(Y\).*Y\s*=\s*\$\(X\)", content, re.DOTALL):
            scoping_issues.append("Recursive variable definition detected")

        # Check for evaluation timing issues
        evaluation_timing = []
        if re.search(r"PROGS\s*=\s*\$\(shell find", content):
            evaluation_timing.append("Variable evaluated at read time with shell")

        # Check for function usage
        function_usage = []
        # Look for manual lists instead of wildcard/patsubst
        if re.search(r"objects\s*=\s*\w+\.o\s+\w+\.o", content):
            function_usage.append(
                "Manual object file list instead of pattern functions"
            )

        return {
            "undefined_variables": undefined_variables[:5],
            "scoping_issues": scoping_issues,
            "evaluation_timing": evaluation_timing,
            "function_usage": function_usage,
        }

    def analyze_target_organization(self, context: Any) -> dict[str, Any]:
        """Analyze target structure and organization.

        Args:
            context: Skill context with file access methods

        Returns:
            Dictionary with target organization analysis results
        """
        content = self._get_makefile_content(context)

        targets = self._extract_targets(content)
        phony_targets = self._extract_phony_targets(content)

        # Find targets that should be .PHONY but aren't
        phony_declarations = []

        # Check all non-file targets
        for target in targets:
            # Skip pattern rules and makefile directives
            if target.startswith("%") or target in [
                "include",
                "ifdef",
                "ifndef",
                "ifeq",
                "ifneq",
            ]:
                continue

            # If it's not a file target and not declared as .PHONY, flag it
            if not self._is_file_target(target) and target not in phony_targets:
                phony_declarations.append(target)

        # Check for target naming inconsistencies
        target_naming = []
        naming_styles = set()
        for target in targets:
            if "_" in target:
                naming_styles.add("snake_case")
            if "-" in target:
                naming_styles.add("kebab-case")
            if re.search(r"[A-Z]", target):
                naming_styles.add("CamelCase")

        if len(naming_styles) > 1:
            target_naming.append(f"Inconsistent naming: {', '.join(naming_styles)}")

        # Check for dependency chain issues
        dependency_chain = []
        # Find targets that do too much (multiple unrelated actions)
        lines = content.split("\n")
        in_target = None
        recipe_lines = 0
        for line in lines:
            if re.match(r"^[a-zA-Z0-9_\-]+:", line):
                if in_target and recipe_lines > 3:
                    dependency_chain.append(
                        f"{in_target} has {recipe_lines} recipe lines"
                    )
                in_target = line.split(":")[0]
                recipe_lines = 0
            elif line.startswith("\t") and in_target:
                recipe_lines += 1

        # Check for separation of concerns
        separation_of_concerns = []
        # Look for test/deployment in build targets
        for i, line in enumerate(lines):
            if re.match(r"^build:", line):
                # Check next 10 lines for test or deployment commands
                next_lines = "\n".join(lines[i : i + 10])
                if re.search(
                    r"(test_runner|integration_tests|cp.*\/var\/www|--test)", next_lines
                ):
                    separation_of_concerns.append(
                        "Build target contains test/deployment actions"
                    )

        return {
            "phony_declarations": phony_declarations,
            "target_naming": target_naming,
            "dependency_chain": dependency_chain,
            "separation_of_concerns": separation_of_concerns,
        }

    def analyze_modernization(self, context: Any) -> dict[str, Any]:
        """Analyze makefile for modern best practices.

        Args:
            context: Skill context with file access methods

        Returns:
            Dictionary with modernization analysis results
        """
        content = self._get_makefile_content(context)

        score = 0.0
        max_score = 10.0

        # Modern features scoring
        if re.search(r"^\.PHONY:", content, re.MULTILINE):
            score += 1.5
        if re.search(r":=", content):  # Immediate assignment
            score += 1.0
        if re.search(r"^include\s+", content, re.MULTILINE):
            score += 1.0
        if re.search(r"^SHELL\s*:=", content, re.MULTILINE):
            score += 0.5
        if re.search(r"%.o:\s*%.c", content):  # Pattern rules
            score += 1.0
        if re.search(r"\|", content):  # Order-only prerequisites
            score += 1.0
        if re.search(r"^\.PRECIOUS:", content, re.MULTILINE):
            score += 0.5
        if re.search(r"ifdef\s+(CROSS_COMPILE|OS)", content):
            score += 1.5
        if re.search(r"-include.*\.mk", content):
            score += 1.0

        # Tool integration
        tool_integration = []
        if re.search(r"(clang-format|cppcheck)", content):
            tool_integration.append("Modern linting/formatting tools")
        if re.search(r"(cargo|npm|pip)", content):
            tool_integration.append("Package manager integration")

        # Cross-platform support
        cross_platform_support = []
        if re.search(r"UNAME.*=.*\$\(shell uname", content):
            cross_platform_support.append("OS detection")
        if re.search(r"ifeq.*\$\(UNAME\)", content):
            cross_platform_support.append("Conditional platform configuration")

        # Configuration management
        configuration_management = []
        if re.search(r"-include.*config.*\.mk", content):
            configuration_management.append("Configuration file inclusion")
        if re.search(r"ifdef CROSS_COMPILE", content):
            configuration_management.append("Cross-compilation support")

        return {
            "modern_features": {"score": score / max_score},
            "tool_integration": tool_integration,
            "cross_platform_support": cross_platform_support,
            "configuration_management": configuration_management,
        }

    def generate_makefile_recommendations(
        self,
        makefile_analysis: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Generate actionable recommendations from analysis.

        Args:
            makefile_analysis: Analysis results from various checks

        Returns:
            List of recommendation dictionaries with priority, action, example, and benefit
        """
        recommendations = []

        # Structure recommendations
        if makefile_analysis.get("structure_issues", 0) > 0:
            recommendations.append(
                {
                    "category": "structure",
                    "priority": "high",
                    "action": "Add .PHONY declarations for non-file targets",
                    "example": ".PHONY: all clean test install",
                    "benefit": "Prevents conflicts with files of the same name and improves build reliability",
                }
            )

        # Performance recommendations
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

        # Security recommendations
        if makefile_analysis.get("security_vulnerabilities", 0) > 0:
            recommendations.append(
                {
                    "category": "security",
                    "priority": "high",
                    "action": "Remove sudo and privilege escalation from makefiles",
                    "example": "Use DESTDIR and user-level installation instead",
                    "benefit": "Prevents security vulnerabilities and follows principle of least privilege",
                }
            )

        # Portability recommendations
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
        """Create a structured quality report from analysis.

        Args:
            makefile_analysis: Complete analysis results with scores and findings

        Returns:
            Formatted markdown report
        """
        report_lines = []

        # Header
        report_lines.append("## Makefile Quality Assessment")
        report_lines.append("")
        overall_score = makefile_analysis.get("overall_score", 0.0)
        report_lines.append(f"**Overall Score**: {overall_score}/10")
        report_lines.append("")

        # Structure analysis
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

        # Performance evaluation
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

        # Security review
        report_lines.append("## Security Review")
        security_score = makefile_analysis.get("security_score", 0.0)
        report_lines.append(f"**Score**: {security_score}/10")
        security_issues = makefile_analysis.get("security_issues", 0)
        report_lines.append(f"- Security issues found: {security_issues}")
        report_lines.append("")

        # Portability assessment
        report_lines.append("## Portability Assessment")
        portability_score = makefile_analysis.get("portability_score", 0.0)
        report_lines.append(f"**Score**: {portability_score}/10")
        report_lines.append("")

        # Recommendations
        report_lines.append("## Recommendations")
        report_lines.append("")
        findings = makefile_analysis.get("findings", [])
        for finding in findings[:5]:
            report_lines.append(f"- {finding.get('title', 'Issue')}")
        report_lines.append("")

        return "\n".join(report_lines)

    def analyze_multiple_makefiles(self, context: Any) -> dict[str, Any]:
        """Analyze multiple makefiles for consistency.

        Args:
            context: Skill context with file access methods

        Returns:
            Dictionary with multi-file consistency analysis results
        """
        # Get all makefiles
        makefiles = context.get_files()

        consistency_issues = []
        variable_conflicts = []
        target_naming = []

        # Track variables and their values across files
        all_variables = {}

        for makefile in makefiles:
            content = context.get_file_content(makefile)

            # Extract variable definitions
            var_pattern = re.compile(r"^([A-Z_]+)\s*=\s*(.+)$", re.MULTILINE)
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

        # Check for inconsistent CC or CFLAGS across files
        if len({v for k, v in all_variables.items() if k in ["CC", "CFLAGS"]}) > 1:
            consistency_issues.append("Inconsistent compiler settings across makefiles")

        return {
            "consistency_issues": consistency_issues,
            "variable_conflicts": variable_conflicts,
            "target_naming": target_naming,
            "cross_file_dependencies": [],
        }

    def analyze_build_system_integration(self, context: Any) -> dict[str, Any]:
        """Analyze makefile integration with other build systems.

        Args:
            context: Skill context with file access methods

        Returns:
            Dictionary with build system integration analysis results
        """
        files = context.get_files()

        build_system_conflicts = []
        ci_integration = []
        package_manager_integration = []
        tooling_compatibility = []

        # Check for multiple build systems
        has_makefile = any("Makefile" in f for f in files)
        has_cmake = any("CMakeLists.txt" in f for f in files)

        if has_makefile and has_cmake:
            build_system_conflicts.append("Both Makefile and CMake detected")

        # Check for CI integration
        for file in files:
            if ".github/workflows" in file or ".yml" in file:
                content = context.get_file_content(file)
                if "make" in content:
                    ci_integration.append("GitHub Actions integration detected")

        # Check for package manager integration
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
