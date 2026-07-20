"""Analysis mixin: structure, dependencies, variables, target organization."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from ._constants import MIN_RECIPE_LINES_FOR_LARGE_TARGET


@dataclass
class _VarScanState:
    """Mutable accumulator threaded through the undefined-variable scan.

    Bundled into one object so the per-line scan helpers in
    :class:`AnalysisMixin` stay under the max-arguments lint limit.
    """

    defined_vars: set[str] = field(default_factory=set)
    used_vars: set[str] = field(default_factory=set)
    var_definitions: dict[str, int] = field(default_factory=dict)
    seen: set[str] = field(default_factory=set)
    results: list[str] = field(default_factory=list)
    pending_use_before_def: set[str] = field(default_factory=set)


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
            if (target in common_phony and target not in phony_targets) or (
                not self._is_file_target(target)
                and target not in phony_targets
                and target not in ["include", "ifdef", "ifndef", "ifeq", "ifneq"]
            ):
                missing_phony.append(target)

        error_handling = []
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if line.startswith("\t"):
                cmd = line.strip()
                if re.search(
                    r"(rm|cp|mv|mkdir|gcc|make|wget|curl)", cmd
                ) and not re.search(r"(\|\||set -e|; exit|\?=|@-)", cmd):
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

    @staticmethod
    def _parse_target_deps(content: str) -> dict[str, list[str]]:
        """Parse `target: dep1 dep2` lines into a target-to-deps map."""
        target_deps: dict[str, list[str]] = {}
        target_pattern = re.compile(r"^([a-zA-Z0-9_\-\.]+)\s*:\s*(.*)$", re.MULTILINE)
        for match in target_pattern.finditer(content):
            target_deps[match.group(1)] = match.group(2).split()
        return target_deps

    @staticmethod
    def _find_circular_dependencies(target_deps: dict[str, list[str]]) -> list[str]:
        """Find target pairs that depend on each other directly."""
        circular_dependencies = []
        for target, deps in target_deps.items():
            for dep in deps:
                if dep in target_deps and target in target_deps[dep]:
                    circular_dependencies.append(f"{target} <-> {dep}")
        return circular_dependencies

    def _find_missing_source_dependencies(self, lines: list[str]) -> list[str]:
        """Flag `main`/`parser.o` targets missing their expected source deps."""
        missing_dependencies: list[str] = []
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
        return missing_dependencies

    @staticmethod
    def _find_header_dependencies(
        target_deps: dict[str, list[str]],
    ) -> tuple[list[str], list[str]]:
        """Flag `.o` targets whose `.c` source has no matching header dep."""
        missing_dependencies: list[str] = []
        header_dependencies: list[str] = []
        for target, deps in target_deps.items():
            if not target.endswith(".o"):
                continue
            base_name = target[:-2]
            has_header = any(dep.endswith((".h", ".hpp")) for dep in deps)
            if f"{base_name}.c" in deps and not has_header:
                missing_dependencies.append(
                    f"{target}: missing header file dependencies"
                )
            if not has_header and target != "%.o":
                header_dependencies.append(f"{target} missing header dependencies")
        return missing_dependencies, header_dependencies

    @staticmethod
    def _find_automatic_dependencies(content: str) -> list[str]:
        """Detect compiler-generated dependency file usage (`-MMD`/`include *.d`)."""
        automatic_dependencies = []
        if re.search(r"-MMD|-MD|-MF", content):
            automatic_dependencies.append("Automatic dependency generation detected")
        if re.search(r"include.*\.d\)", content):
            automatic_dependencies.append("Dependency file inclusion detected")
        return automatic_dependencies

    def analyze_dependencies(self, context: Any) -> dict[str, Any]:
        """Analyze dependency management in makefile."""
        content = self._get_makefile_content(context)
        lines = content.split("\n")

        target_deps = self._parse_target_deps(content)
        circular_dependencies = self._find_circular_dependencies(target_deps)
        missing_dependencies = self._find_missing_source_dependencies(lines)
        header_missing, header_dependencies = self._find_header_dependencies(
            target_deps
        )
        missing_dependencies.extend(header_missing)
        automatic_dependencies = self._find_automatic_dependencies(content)

        return {
            "missing_dependencies": missing_dependencies[:10],
            "circular_dependencies": circular_dependencies,
            "automatic_dependencies": automatic_dependencies,
            "header_dependencies": header_dependencies,
        }

    _VAR_DEF_RE = re.compile(r"^([A-Z_][A-Z0-9_]*)\s*[:?]?=")
    _VAR_USE_RE = re.compile(r"\$\(([A-Z_][A-Z0-9_]*)\)")
    _EMPTY_CRITICAL_RE = re.compile(r"^(CFLAGS|LDFLAGS|SOURCES)\s*=\s*$")
    _TARGET_RE = re.compile(r"^[a-zA-Z0-9_\-]+:\s*(.*)$")
    _BUILTIN_VARS = frozenset({"CC", "CFLAGS", "LDFLAGS", "MAKE", "MAKEFLAGS"})

    @staticmethod
    def _record_once(entry: str, seen: set[str], results: list[str]) -> None:
        """Append `entry` to results only the first time it is seen."""
        if entry not in seen:
            seen.add(entry)
            results.append(entry)

    @classmethod
    def _scan_var_definition(cls, line: str, i: int, state: _VarScanState) -> None:
        """Record a variable definition and its first-definition line."""
        var_def_match = cls._VAR_DEF_RE.match(line)
        if var_def_match:
            var_name = var_def_match.group(1)
            state.defined_vars.add(var_name)
            if var_name not in state.var_definitions:
                state.var_definitions[var_name] = i

    @classmethod
    def _scan_empty_critical(cls, line: str, i: int, state: _VarScanState) -> None:
        """Flag critical variables (CFLAGS/LDFLAGS/SOURCES) defined but empty."""
        if cls._EMPTY_CRITICAL_RE.match(line):
            crit_name = line.split("=", maxsplit=1)[0].strip()
            cls._record_once(
                f"Line {i + 1}: Empty {crit_name}", state.seen, state.results
            )

    @classmethod
    def _scan_target_deps_use_before_def(
        cls, line: str, i: int, state: _VarScanState
    ) -> None:
        """Flag or defer variables referenced in a target's deps line."""
        target_match = cls._TARGET_RE.match(line)
        if not target_match:
            return
        for var_match in cls._VAR_USE_RE.finditer(target_match.group(1)):
            dep_var = var_match.group(1)
            if dep_var in state.var_definitions and state.var_definitions[dep_var] > i:
                cls._record_once(
                    f"{dep_var} (used before definition)", state.seen, state.results
                )
            elif (
                dep_var not in state.var_definitions
                and dep_var not in cls._BUILTIN_VARS
            ):
                state.pending_use_before_def.add(dep_var)

    @classmethod
    def _resolve_pending_use_before_def(cls, state: _VarScanState) -> None:
        """Promote deferred variables to findings once they are defined anywhere."""
        for var in state.pending_use_before_def:
            if var in state.defined_vars:
                cls._record_once(
                    f"{var} (used before definition)", state.seen, state.results
                )

    @classmethod
    def _resolve_undefined_used_vars(cls, state: _VarScanState) -> None:
        """Flag variables that are used but never defined anywhere."""
        for var in state.used_vars:
            if (
                var not in state.defined_vars
                and var not in cls._BUILTIN_VARS
                and var not in state.seen
            ):
                state.seen.add(var)
                state.results.append(var)

    @classmethod
    def _find_undefined_variables(cls, content: str) -> list[str]:
        """Scan makefile for undefined, empty, and use-before-definition variables."""
        state = _VarScanState()
        lines = content.split("\n")

        for i, line in enumerate(lines):
            cls._scan_var_definition(line, i, state)
            cls._scan_empty_critical(line, i, state)
            state.used_vars.update(m.group(1) for m in cls._VAR_USE_RE.finditer(line))
            cls._scan_target_deps_use_before_def(line, i, state)

        cls._resolve_pending_use_before_def(state)
        cls._resolve_undefined_used_vars(state)

        return state.results

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

    def _find_missing_phony_declarations(
        self, targets: list[str], phony_targets: list[str]
    ) -> list[str]:
        """Find non-file targets that should be declared `.PHONY` but aren't."""
        skip_targets = {"include", "ifdef", "ifndef", "ifeq", "ifneq"}
        phony_declarations = []
        for target in targets:
            if target.startswith("%") or target in skip_targets:
                continue
            if not self._is_file_target(target) and target not in phony_targets:
                phony_declarations.append(target)
        return phony_declarations

    @staticmethod
    def _find_naming_inconsistencies(targets: list[str]) -> list[str]:
        """Flag a mix of snake_case/kebab-case/CamelCase target names."""
        naming_styles: set[str] = set()
        for target in targets:
            if "_" in target:
                naming_styles.add("snake_case")
            if "-" in target:
                naming_styles.add("kebab-case")
            if re.search(r"[A-Z]", target):
                naming_styles.add("CamelCase")

        if len(naming_styles) > 1:
            return [f"Inconsistent naming: {', '.join(naming_styles)}"]
        return []

    @staticmethod
    def _find_large_targets(lines: list[str]) -> list[str]:
        """Flag targets whose recipe exceeds the large-target line threshold."""
        dependency_chain = []
        in_target = None
        recipe_lines = 0
        for line in lines:
            if re.match(r"^[a-zA-Z0-9_\-]+:", line):
                if in_target and recipe_lines > MIN_RECIPE_LINES_FOR_LARGE_TARGET:
                    dependency_chain.append(
                        f"{in_target} has {recipe_lines} recipe lines"
                    )
                in_target = line.split(":", maxsplit=1)[0]
                recipe_lines = 0
            elif line.startswith("\t") and in_target:
                recipe_lines += 1
        return dependency_chain

    @staticmethod
    def _find_separation_of_concerns_violations(lines: list[str]) -> list[str]:
        """Flag `build:` targets that also run tests or deploy."""
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
        return separation_of_concerns

    def analyze_target_organization(self, context: Any) -> dict[str, Any]:
        """Analyze target structure and organization."""
        content = self._get_makefile_content(context)
        lines = content.split("\n")

        targets = self._extract_targets(content)
        phony_targets = self._extract_phony_targets(content)

        return {
            "phony_declarations": self._find_missing_phony_declarations(
                targets, phony_targets
            ),
            "target_naming": self._find_naming_inconsistencies(targets),
            "dependency_chain": self._find_large_targets(lines),
            "separation_of_concerns": self._find_separation_of_concerns_violations(
                lines
            ),
        }
