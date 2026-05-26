"""Quality mixin: performance, portability, security, modernization."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from ._constants import (
    _SCORE_CROSS_COMPILE,
    _SCORE_IMMEDIATE_ASSIGN,
    _SCORE_INCLUDE,
    _SCORE_MK_INCLUDE,
    _SCORE_ORDER_PREREQS,
    _SCORE_PATTERN_RULES,
    _SCORE_PHONY,
    _SCORE_PRECIOUS,
    _SCORE_SHELL_OVERRIDE,
    MIN_CP_OPERATIONS_FOR_WARNING,
    MIN_TARGETS_FOR_PARALLEL,
)

if TYPE_CHECKING:
    pass


class QualityMixin:
    """Analyze makefile performance, portability, security, and modernization."""

    if TYPE_CHECKING:

        def _get_makefile_content(self, context: Any) -> str: ...

        def _extract_targets(self, content: str) -> list[str]: ...

    def analyze_performance(self, context: Any) -> dict[str, Any]:
        """Analyze makefile for performance bottlenecks."""
        content = self._get_makefile_content(context)

        parallelization_issues = []
        targets = self._extract_targets(content)
        build_targets = [t for t in targets if re.match(r"build\d+|source\d+\.o", t)]
        if len(build_targets) >= MIN_TARGETS_FOR_PARALLEL:
            parallelization_issues.append(
                f"{len(build_targets)} sequential build targets detected"
            )

        if not re.search(r"(-j|MAKEFLAGS.*-j|parallel)", content):
            if len(targets) > MIN_TARGETS_FOR_PARALLEL:
                parallelization_issues.append(
                    "No parallel execution configuration found"
                )

        if re.search(r"^source\d+\.o:.*\n\tgcc -c", content, re.MULTILINE):
            parallelization_issues.append("Sequential object file compilation detected")

        unnecessary_rebuilds = []
        if re.search(r"date >|timestamp", content):
            unnecessary_rebuilds.append(
                "Timestamp generation may cause unnecessary rebuilds"
            )

        inefficient_operations = []
        lines = content.split("\n")
        cp_count = 0
        for line in lines:
            if line.startswith("\t") and re.search(r"cp -r", line):
                cp_count += 1
        if cp_count >= MIN_CP_OPERATIONS_FOR_WARNING:
            inefficient_operations.append("Multiple sequential cp commands detected")

        file_operations = []
        for i, line in enumerate(lines):
            if re.search(r"(cp -r|tar czf|rsync)", line):
                file_operations.append(
                    f"Line {i + 1}: File operation - {line.strip()[:50]}"
                )

        return {
            "parallelization_issues": parallelization_issues,
            "unnecessary_rebuilds": unnecessary_rebuilds,
            "inefficient_operations": inefficient_operations,
            "file_operations": file_operations[:5],
        }

    def analyze_portability(self, context: Any) -> dict[str, Any]:
        """Analyze makefile portability across platforms."""
        content = self._get_makefile_content(context)

        hardcoded_paths = []
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if re.search(r"(\/usr\/bin|\/usr\/local|C:\\|\\\\)", line):
                hardcoded_paths.append(f"Line {i + 1}: {line.strip()[:60]}")

        platform_specific = []
        for i, line in enumerate(lines):
            if re.search(r"(^|\s)(rm -f|chmod|mkdir -p|gdb|cp |mv )", line):
                platform_specific.append(
                    f"Line {i + 1}: Unix command - {line.strip()[:50]}"
                )
            if re.search(r"(copy |del |xcopy)", line):
                platform_specific.append(
                    f"Line {i + 1}: Windows command - {line.strip()[:50]}"
                )

        gnu_extensions = []
        if re.search(r"\$\(shell find", content):
            gnu_extensions.append("GNU make shell function with find")
        if re.search(r"\$\(patsubst", content):
            gnu_extensions.append("GNU make patsubst function")
        if re.search(r"\$\(shell git", content):
            gnu_extensions.append("GNU make shell function with git")

        cross_platform_issues = []
        if re.search(r"backup\\\\", content):
            cross_platform_issues.append("Windows-style path separators used")
        if "rm -f" in content and "RM" not in content:
            cross_platform_issues.append("Direct rm usage without RM variable")

        return {
            "hardcoded_paths": hardcoded_paths[:5],
            "platform_specific": platform_specific[:5],
            "gnu_extensions": gnu_extensions,
            "cross_platform_issues": cross_platform_issues,
        }

    def analyze_security(self, context: Any) -> dict[str, Any]:
        """Analyze makefile for security vulnerabilities."""
        content = self._get_makefile_content(context)

        command_injection = []
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if re.search(r"\|\s*(sh|bash)(\s|$)", line):
                command_injection.append(
                    f"Line {i + 1}: Piping to shell - {line.strip()[:50]}"
                )
            if re.search(r"read -p.*\$\$", line):
                command_injection.append(f"Line {i + 1}: User input without validation")
            if re.search(r"rm -rf\s+/tmp/\*", line):
                command_injection.append(f"Line {i + 1}: Dangerous rm with wildcards")

        privilege_escalation = []
        for i, line in enumerate(lines):
            if re.search(r"(^|\s)sudo\s", line):
                privilege_escalation.append(f"Line {i + 1}: sudo usage in makefile")
            if re.search(r"chmod.*\+s", line):
                privilege_escalation.append(f"Line {i + 1}: setuid bit modification")
            if re.search(r"EUID.*0", line):
                privilege_escalation.append(f"Line {i + 1}: Root check in makefile")

        path_traversal = []
        if re.search(r"export PATH\s*:=\s*\.:", content):
            path_traversal.append("PATH manipulation - current directory in PATH")

        insecure_downloads = []
        for i, line in enumerate(lines):
            if re.search(r"(curl|wget).*http://", line):
                insecure_downloads.append(f"Line {i + 1}: Insecure HTTP download")
            if re.search(r"(tar xzf|unzip)", line):
                insecure_downloads.append(
                    f"Line {i + 1}: Archive extraction without validation"
                )

        return {
            "command_injection": command_injection[:5],
            "privilege_escalation": privilege_escalation,
            "path_traversal": path_traversal,
            "insecure_downloads": insecure_downloads[:5],
        }

    def analyze_modernization(self, context: Any) -> dict[str, Any]:
        """Analyze makefile for modern best practices."""
        content = self._get_makefile_content(context)

        score = 0.0
        max_score = 10.0

        if re.search(r"^\.PHONY:", content, re.MULTILINE):
            score += _SCORE_PHONY
        if re.search(r":=", content):
            score += _SCORE_IMMEDIATE_ASSIGN
        if re.search(r"^include\s+", content, re.MULTILINE):
            score += _SCORE_INCLUDE
        if re.search(r"^SHELL\s*:=", content, re.MULTILINE):
            score += _SCORE_SHELL_OVERRIDE
        if re.search(r"%.o:\s*%.c", content):
            score += _SCORE_PATTERN_RULES
        if re.search(r"\|", content):
            score += _SCORE_ORDER_PREREQS
        if re.search(r"^\.PRECIOUS:", content, re.MULTILINE):
            score += _SCORE_PRECIOUS
        if re.search(r"ifdef\s+(CROSS_COMPILE|OS)", content):
            score += _SCORE_CROSS_COMPILE
        if re.search(r"-include.*\.mk", content):
            score += _SCORE_MK_INCLUDE

        tool_integration = []
        if re.search(r"(clang-format|cppcheck)", content):
            tool_integration.append("Modern linting/formatting tools")
        if re.search(r"(cargo|npm|pip)", content):
            tool_integration.append("Package manager integration")

        cross_platform_support = []
        if re.search(r"UNAME.*=.*\$\(shell uname", content):
            cross_platform_support.append("OS detection")
        if re.search(r"ifeq.*\$\(UNAME\)", content):
            cross_platform_support.append("Conditional platform configuration")

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
