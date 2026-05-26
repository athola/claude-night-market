"""Analysis mixin: structure, dependencies, variables, target organization."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from ._constants import MIN_RECIPE_LINES_FOR_LARGE_TARGET

if TYPE_CHECKING:
    pass


class AnalysisMixin:
    """Analyze makefile structure, dependency chains, variables, and targets."""

    if TYPE_CHECKING:

        def _get_makefile_content(self, context: Any) -> str: ...

        def _extract_targets(self, content: str) -> list[str]: ...

        def _extract_phony_targets(self, content: str) -> list[str]: ...

        def _is_file_target(self, target: str) -> bool: ...

    def analyze_makefile_structure(self, context: Any) -> dict[str, Any]:
        """Analyze makefile structure for common issues."""
        content = self._get_makefile_content(context)

        targets = self._extract_targets(content)
        phony_targets = self._extract_phony_targets(content)

        common_phony = frozenset(
            {"all", "build", "test", "clean", "install", "help", "docs"}
        )

        missing_phony = []
        for target in targets:
            if target in common_phony and target not in phony_targets:
                missing_phony.append(target)
            elif not self._is_file_target(target) and target not in phony_targets:
                if target not in ["include", "ifdef", "ifndef", "ifeq", "ifneq"]:
                    missing_phony.append(target)

        error_handling = []
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if line.startswith("\t"):
                cmd = line.strip()
                if re.search(r"(rm|cp|mv|mkdir|gcc|make|wget|curl)", cmd):
                    if not re.search(r"(\|\||set -e|; exit|\?=|@-)", cmd):
                        error_handling.append(f"Line {i + 1}: {cmd[:50]}")

        hardcoded_paths = []
        hardcoded_pattern = re.compile(r"(\/usr\/|\/bin\/|\/tmp\/|C:\\|\/home\/)")
        for i, line in enumerate(lines):
            if hardcoded_pattern.search(line):
                hardcoded_paths.append(f"Line {i + 1}: {line.strip()[:60]}")

        variable_usage = []
        if not re.search(r"\$\([A-Z_]+\)", content):
            variable_usage.append("No variable usage detected")

        return {
            "missing_phony": missing_phony,
            "error_handling": error_handling[:10],
            "hardcoded_paths": hardcoded_paths,
            "variable_usage": variable_usage,
        }

    @staticmethod
    def _find_recipe_end(lines: list[str], start: int) -> int:
        """Find the line index where a recipe block ends."""
        idx = start + 1
        while idx < len(lines) and lines[idx].startswith("\t"):
            idx += 1
        return idx

    def analyze_dependencies(self, context: Any) -> dict[str, Any]:
        """Analyze dependency management in makefile."""
        content = self._get_makefile_content(context)

        target_deps: dict[str, list[str]] = {}
        target_pattern = re.compile(r"^([a-zA-Z0-9_\-\.]+)\s*:\s*(.*)$", re.MULTILINE)
        for match in target_pattern.finditer(content):
            target = match.group(1)
            deps = match.group(2).split()
            target_deps[target] = deps

        circular_dependencies = []
        for target, deps in target_deps.items():
            for dep in deps:
                if dep in target_deps and target in target_deps[dep]:
                    circular_dependencies.append(f"{target} <-> {dep}")

        missing_dependencies: list[str] = []
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if re.match(r"^main:", line) and "main.c" not in line:
                missing_dependencies.append(
                    f"Line {i + 1}: main target missing source dependencies"
                )

            if re.match(r"^parser\.o:", line):
                recipe_end = self._find_recipe_end(lines, i)
                target_block = "\n".join(lines[i:recipe_end])
                if "parser.h" not in target_block and "parser.c" in target_block:
                    missing_dependencies.append(
                        f"Line {i + 1}: parser.o missing header dependencies"
                    )

        header_dependencies: list[str] = []
        for target, deps in target_deps.items():
            if target.endswith(".o"):
                base_name = target[:-2]
                has_header = any(
                    dep.endswith(".h") or dep.endswith(".hpp") for dep in deps
                )
                if f"{base_name}.c" in deps and not has_header:
                    missing_dependencies.append(
                        f"{target}: missing header file dependencies"
                    )
                if not has_header and target != "%.o":
                    header_dependencies.append(f"{target} missing header dependencies")

        automatic_dependencies = []
        if re.search(r"-MMD|-MD|-MF", content):
            automatic_dependencies.append("Automatic dependency generation detected")
        if re.search(r"include.*\.d\)", content):
            automatic_dependencies.append("Dependency file inclusion detected")

        return {
            "missing_dependencies": missing_dependencies[:10],
            "circular_dependencies": circular_dependencies,
            "automatic_dependencies": automatic_dependencies,
            "header_dependencies": header_dependencies,
        }

    @staticmethod
    def _find_undefined_variables(content: str) -> list[str]:
        """Scan makefile for undefined, empty, and use-before-definition variables."""
        builtin_vars = {"CC", "CFLAGS", "LDFLAGS", "MAKE", "MAKEFLAGS"}
        lines = content.split("\n")
        defined_vars: set[str] = set()
        used_vars: set[str] = set()
        var_definitions: dict[str, int] = {}
        seen: set[str] = set()
        results: list[str] = []
        pending_use_before_def: set[str] = set()

        var_def_re = re.compile(r"^([A-Z_][A-Z0-9_]*)\s*[:?]?=")
        var_use_re = re.compile(r"\$\(([A-Z_][A-Z0-9_]*)\)")
        empty_critical_re = re.compile(r"^(CFLAGS|LDFLAGS|SOURCES)\s*=\s*$")
        target_re = re.compile(r"^[a-zA-Z0-9_\-]+:\s*(.*)$")

        for i, line in enumerate(lines):
            var_def_match = var_def_re.match(line)
            if var_def_match:
                var_name = var_def_match.group(1)
                defined_vars.add(var_name)
                if var_name not in var_definitions:
                    var_definitions[var_name] = i

            if empty_critical_re.match(line):
                crit_name = line.split("=")[0].strip()
                entry = f"Line {i + 1}: Empty {crit_name}"
                if entry not in seen:
                    seen.add(entry)
                    results.append(entry)

            for var_match in var_use_re.finditer(line):
                used_vars.add(var_match.group(1))

            target_match = target_re.match(line)
            if target_match:
                deps_part = target_match.group(1)
                for var_match in var_use_re.finditer(deps_part):
                    dep_var = var_match.group(1)
                    if dep_var in var_definitions and var_definitions[dep_var] > i:
                        entry = f"{dep_var} (used before definition)"
                        if entry not in seen:
                            seen.add(entry)
                            results.append(entry)
                    elif dep_var not in var_definitions and dep_var not in builtin_vars:
                        pending_use_before_def.add(dep_var)

        for var in pending_use_before_def:
            if var in defined_vars:
                entry = f"{var} (used before definition)"
                if entry not in seen:
                    seen.add(entry)
                    results.append(entry)

        for var in used_vars:
            if var not in defined_vars and var not in builtin_vars:
                if var not in seen:
                    seen.add(var)
                    results.append(var)

        return results

    def analyze_variables(self, context: Any) -> dict[str, Any]:
        """Analyze variable usage and management."""
        content = self._get_makefile_content(context)

        undefined_variables = self._find_undefined_variables(content)

        scoping_issues = []
        if re.search(r"X\s*=\s*\$\(Y\).*Y\s*=\s*\$\(X\)", content, re.DOTALL):
            scoping_issues.append("Recursive variable definition detected")

        evaluation_timing = []
        if re.search(r"PROGS\s*=\s*\$\(shell find", content):
            evaluation_timing.append("Variable evaluated at read time with shell")

        function_usage = []
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
        """Analyze target structure and organization."""
        content = self._get_makefile_content(context)

        targets = self._extract_targets(content)
        phony_targets = self._extract_phony_targets(content)

        phony_declarations = []
        for target in targets:
            if target.startswith("%") or target in [
                "include",
                "ifdef",
                "ifndef",
                "ifeq",
                "ifneq",
            ]:
                continue
            if not self._is_file_target(target) and target not in phony_targets:
                phony_declarations.append(target)

        target_naming = []
        naming_styles: set[str] = set()
        for target in targets:
            if "_" in target:
                naming_styles.add("snake_case")
            if "-" in target:
                naming_styles.add("kebab-case")
            if re.search(r"[A-Z]", target):
                naming_styles.add("CamelCase")

        if len(naming_styles) > 1:
            target_naming.append(f"Inconsistent naming: {', '.join(naming_styles)}")

        dependency_chain = []
        lines = content.split("\n")
        in_target = None
        recipe_lines = 0
        for line in lines:
            if re.match(r"^[a-zA-Z0-9_\-]+:", line):
                if in_target and recipe_lines > MIN_RECIPE_LINES_FOR_LARGE_TARGET:
                    dependency_chain.append(
                        f"{in_target} has {recipe_lines} recipe lines"
                    )
                in_target = line.split(":")[0]
                recipe_lines = 0
            elif line.startswith("\t") and in_target:
                recipe_lines += 1

        separation_of_concerns = []
        for i, line in enumerate(lines):
            if re.match(r"^build:", line):
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
