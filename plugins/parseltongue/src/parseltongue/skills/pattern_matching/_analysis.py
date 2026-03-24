"""Performance and architectural pattern analysis."""

from __future__ import annotations

import ast
import re
from typing import Any

__all__ = ["AnalysisPatternMixin"]


class AnalysisPatternMixin:
    """Recognise performance patterns, architectural patterns,
    and anti-patterns.
    """

    # ------------------------------------------------------------------
    # Performance helpers
    # ------------------------------------------------------------------

    def _detect_nested_loops(
        self,
        node: ast.FunctionDef,
        anti_patterns: list[str],
        performance_patterns: dict[str, Any],
    ) -> None:
        """Detect nested loops (O(n^2)) in a function."""
        for child in ast.walk(node):
            if isinstance(child, ast.For):
                for grandchild in ast.walk(child):
                    if isinstance(grandchild, ast.For) and grandchild is not child:
                        anti_patterns.append(node.name)
                        performance_patterns["optimization_opportunity"] = True
                        break

    def _detect_set_usage(
        self,
        node: ast.FunctionDef,
        good_patterns: list[str],
    ) -> None:
        """Detect set usage (O(1) lookups) in a function."""
        for child in ast.walk(node):
            if (
                isinstance(child, ast.Call)
                and isinstance(child.func, ast.Name)
                and child.func.id == "set"
            ):
                good_patterns.append(node.name)

    def _detect_generators(
        self,
        node: ast.FunctionDef,
        pattern_instances: list[str],
        performance_patterns: dict[str, Any],
    ) -> None:
        """Detect generators in a function."""
        for child in ast.walk(node):
            if isinstance(child, ast.Yield):
                pattern_instances.append(node.name)
                performance_patterns["memory_efficient"] = True

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    def recognize_performance_patterns(
        self, code: str, _tree: ast.Module | None = None
    ) -> dict[str, Any]:
        """Recognize performance patterns and anti-patterns.

        Args:
            code: Code to analyze
            _tree: Pre-parsed AST (internal optimisation)

        Returns:
            Dictionary with performance pattern analysis
        """
        performance_patterns: dict[str, Any] = {}
        anti_patterns: list[str] = []
        good_patterns: list[str] = []
        pattern_instances: list[str] = []

        if not code:
            return {
                "performance_patterns": performance_patterns,
                "anti_patterns": anti_patterns,
                "good_patterns": good_patterns,
                "pattern_instances": pattern_instances,
            }

        tree = _tree
        if tree is None:
            tree, err = self._parse_code(code)  # type: ignore[attr-defined]
            if tree is None:
                return {
                    "performance_patterns": {},
                    "anti_patterns": [],
                    "good_patterns": [],
                    "pattern_instances": [],
                    **(err or {}),
                }

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                self._detect_nested_loops(node, anti_patterns, performance_patterns)
                self._detect_set_usage(node, good_patterns)
                self._detect_generators(node, pattern_instances, performance_patterns)

        return {
            "performance_patterns": performance_patterns,
            "anti_patterns": anti_patterns,
            "good_patterns": good_patterns,
            "pattern_instances": pattern_instances,
        }

    def recognize_architectural_patterns(self, code: str) -> dict[str, Any]:
        """Recognize architectural patterns (MVC, Repository, etc.).

        Args:
            code: Code to analyze

        Returns:
            Dictionary with architectural pattern analysis
        """
        architectural_patterns: dict[str, bool] = {}
        pattern_instances: list[str] = []

        if not code:
            return {
                "architectural_patterns": architectural_patterns,
                "pattern_instances": pattern_instances,
            }

        # MVC pattern
        has_model = bool(re.search(r"class\s+\w*Model\b", code))
        has_view = bool(re.search(r"class\s+\w*View\b", code))
        has_controller = bool(re.search(r"class\s+\w*Controller\b", code))
        if has_controller and (has_model or has_view):
            architectural_patterns["mvc"] = True
            for match in re.finditer(r"class\s+(\w*Controller)\b", code):
                pattern_instances.append(match.group(1))

        # Repository pattern (class defs or references)
        repo_matches = re.findall(r"(\w*Repository)\b", code)
        if repo_matches:
            architectural_patterns["repository"] = True
            for name in dict.fromkeys(repo_matches):
                pattern_instances.append(name)

        # Unit of Work pattern
        if re.search(r"class\s+\w*UnitOfWork\b", code) or (
            "commit" in code and "register_new" in code
        ):
            architectural_patterns["unit_of_work"] = True

        return {
            "architectural_patterns": architectural_patterns,
            "pattern_instances": pattern_instances,
        }

    def identify_anti_patterns(self, code: str) -> dict[str, Any]:
        """Identify anti-patterns in code.

        Args:
            code: Code to analyze

        Returns:
            Dictionary with anti-pattern analysis
        """
        anti_patterns: list[str] = []
        severity = ""
        description = ""

        if not code:
            return {
                "anti_patterns": anti_patterns,
                "severity": severity,
                "description": description,
            }

        # Nested loops
        if re.search(r"for\s+\w+.*:\s*\n\s+for\s+\w+", code, re.MULTILINE):
            anti_patterns.append("nested_loops")
            severity = "performance_issue"
            description = "O(n\u00b2) nested loop detected"

        # Memory leak (growing collection without cleanup)
        if (
            re.search(r"\.append\(", code)
            and not re.search(r"\.(clear|pop|remove)\(", code)
            and ("cache" in code.lower() or "global" in code.lower())
        ):
            anti_patterns.append("memory_leak")
            description = "growing_collection without cleanup"

        # Blocking in async
        if "time.sleep" in code and "async" in code:
            anti_patterns.append("blocking_async")
            description = "event_loop_blocking with time.sleep"

        return {
            "anti_patterns": anti_patterns,
            "severity": severity,
            "description": description,
        }
