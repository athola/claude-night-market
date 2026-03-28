"""Pattern improvement suggestions, DSL matching, validation, and
documentation generation.
"""

from __future__ import annotations

import ast
import re
from typing import Any

from ._constants import MIN_REPO_METHODS

__all__ = ["ImprovementsMixin"]


class ImprovementsMixin:
    """DSL matching, improvement suggestions, consistency validation,
    singleton variations, general pattern recognition, documentation,
    and pattern comparison.
    """

    def match_dsl_patterns(self, code: str) -> dict[str, Any]:
        """Match Domain-Specific Language patterns.

        Args:
            code: DSL code to analyze

        Returns:
            Dictionary with DSL pattern analysis
        """
        dsl_patterns: dict[str, bool] = {}
        structures: dict[str, int] = {
            "nested_blocks": 0,
            "route_definitions": 0,
            "validation_rules": 0,
        }

        if not code:
            return {
                "dsl_patterns": dsl_patterns,
                "structures": structures,
            }

        # Configuration DSL
        if re.search(r"\w+\s*\{[^}]*\w+\s*:", code, re.DOTALL):
            dsl_patterns["configuration_dsl"] = True
            structures["nested_blocks"] = len(re.findall(r"\w+\s*\{", code))

        # Routing DSL
        route_matches = re.findall(r'"/[^"]*"\s*->', code)
        if route_matches:
            dsl_patterns["routing_dsl"] = True
            structures["route_definitions"] = len(route_matches)

        # Validation DSL
        validation_matches = re.findall(r"\w+:\s*(required|optional)", code)
        if validation_matches:
            dsl_patterns["validation_dsl"] = True
            structures["validation_rules"] = len(validation_matches)

        return {
            "dsl_patterns": dsl_patterns,
            "structures": structures,
        }

    def suggest_improvements(self, code: str) -> dict[str, Any]:
        """Suggest pattern improvements for code.

        Args:
            code: Code to analyze

        Returns:
            Dictionary with improvement suggestions
        """
        suggestions: list[dict[str, str]] = []

        if not code:
            return {"suggestions": suggestions}

        # Nested loop optimization
        if re.search(r"for\s+\w+.*:\s*\n\s+for\s+\w+", code, re.MULTILINE):
            suggestions.append(
                {
                    "issue": "Nested loops detected (O(n\u00b2))",
                    "improvement": "Use a set for O(1) lookups",
                    "before": "for i in items:\n    for j in items:\n"
                    "        if i == j: ...",
                    "after": "seen = set(items)\nfor i in items:\n"
                    "    if i in seen: ...",
                }
            )

        # Growing list without bounds
        if ".append(" in code and "break" not in code:
            suggestions.append(
                {
                    "issue": "Unbounded list growth",
                    "improvement": ("Consider using a bounded collection or generator"),
                    "before": "results = []\nfor item in items:\n"
                    "    results.append(process(item))",
                    "after": ("results = [process(item) for item in items]"),
                }
            )

        return {"suggestions": suggestions}

    def validate_pattern_consistency(
        self, code: str, _tree: ast.Module | None = None
    ) -> dict[str, Any]:
        """Validate consistency of design patterns used in code.

        Args:
            code: Code to analyze
            _tree: Pre-parsed AST (internal optimisation)

        Returns:
            Dictionary with consistency analysis
        """
        consistency: dict[str, Any] = {
            "mixed_patterns": False,
            "issues": [],
            "recommendations": [],
        }

        if not code:
            return {"consistency_analysis": consistency}

        tree = _tree
        if tree is None:
            tree, err = self._parse_code(code)
            if tree is None:
                return {
                    "consistency_analysis": consistency,
                    **(err or {}),
                }

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = {
                    item.name for item in node.body if isinstance(item, ast.FunctionDef)
                }

                # Check for mixed responsibilities
                has_data = bool(methods & {"add_item", "find_item", "get", "set"})
                has_persistence = bool(
                    methods
                    & {
                        "save_to_database",
                        "load_from_database",
                        "persist",
                    }
                )

                if has_data and has_persistence:
                    consistency["mixed_patterns"] = True
                    consistency["issues"].append("single_responsibility_violation")
                    consistency["recommendations"].append(
                        "Separate data management from persistence"
                    )

        return {"consistency_analysis": consistency}

    # ------------------------------------------------------------------
    # Singleton variation helpers
    # ------------------------------------------------------------------

    def _detect_singleton_variations(
        self,
        code: str,
        variations: dict[str, Any],
        _tree: ast.Module | None = None,
    ) -> None:
        """Detect singleton pattern variations."""
        tree = _tree
        if tree is None:
            tree, _ = self._parse_code(code)
            if tree is None:
                return

        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue

            methods = {
                item.name for item in node.body if isinstance(item, ast.FunctionDef)
            }
            attrs: set[str] = set()
            for item in node.body:
                if isinstance(item, ast.Assign):
                    for target in item.targets:
                        if isinstance(target, ast.Name):
                            attrs.add(target.id)

            self._check_classic_singleton(node, methods, attrs, variations)
            self._check_metaclass_singleton(node, methods, attrs, variations)

    def _check_classic_singleton(
        self,
        node: ast.ClassDef,
        methods: set[str],
        attrs: set[str],
        variations: dict[str, Any],
    ) -> None:
        """Check for classic singleton pattern variants."""
        if "_instance" not in attrs or "__new__" not in methods:
            return
        if "_lock" in attrs:
            variations["thread_safe_singleton"] = {
                "class": node.name,
                "advantages": [
                    "Thread-safe",
                    "Double-checked locking",
                ],
                "disadvantages": [
                    "More complex",
                    "Slight overhead",
                ],
            }
        else:
            variations["classic_singleton"] = {
                "class": node.name,
                "advantages": [
                    "Simple implementation",
                ],
                "disadvantages": [
                    "Not thread-safe",
                ],
            }

    def _check_metaclass_singleton(
        self,
        node: ast.ClassDef,
        methods: set[str],
        attrs: set[str],
        variations: dict[str, Any],
    ) -> None:
        """Check for metaclass singleton pattern."""
        if "__call__" in methods and "_instances" in attrs:
            variations["metaclass_singleton"] = {
                "class": node.name,
                "advantages": [
                    "Reusable across classes",
                    "Clean syntax",
                ],
                "disadvantages": [
                    "Complex metaclass usage",
                ],
            }

    def detect_pattern_variations(
        self,
        code: str,
        pattern_name: str = "",
        _tree: ast.Module | None = None,
    ) -> dict[str, Any]:
        """Detect variations of a specific design pattern.

        Args:
            code: Code to analyze
            pattern_name: Name of the pattern to look for
            _tree: Pre-parsed AST (internal optimisation)

        Returns:
            Dictionary with pattern variation analysis
        """
        variations: dict[str, Any] = {}
        trade_offs: dict[str, Any] = {}

        if not code or not pattern_name:
            return {
                "pattern_variations": variations,
                "trade_offs": trade_offs,
            }

        if pattern_name == "singleton":
            self._detect_singleton_variations(code, variations, _tree=_tree)
            trade_offs = {
                "simple_vs_threadsafe": ("Classic is simpler but not thread-safe"),
            }

        return {
            "pattern_variations": variations,
            "trade_offs": trade_offs,
        }

    # ------------------------------------------------------------------
    # General pattern recognition
    # ------------------------------------------------------------------

    def recognize_patterns(
        self, code: str, _tree: ast.Module | None = None
    ) -> dict[str, Any]:
        """Recognize any patterns in code (general purpose).

        Args:
            code: Code to analyze
            _tree: Pre-parsed AST (internal optimisation)

        Returns:
            Dictionary with recognized patterns
        """
        recognized_patterns: list[str] = []
        confidence = 0.0

        if not code:
            return {
                "recognized_patterns": recognized_patterns,
                "confidence": confidence,
            }

        tree = _tree
        if tree is None:
            tree, err = self._parse_code(code)
            if tree is None:
                return {
                    "recognized_patterns": [],
                    "confidence": 0.0,
                    **(err or {}),
                }

        # Check for class definitions
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                recognized_patterns.append(f"class:{node.name}")
                confidence = max(confidence, 0.6)

        # Check for function definitions
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                recognized_patterns.append(f"function:{node.name}")
                confidence = max(confidence, 0.5)

        return {
            "recognized_patterns": recognized_patterns,
            "confidence": confidence,
        }

    # ------------------------------------------------------------------
    # Documentation and comparison
    # ------------------------------------------------------------------

    def generate_pattern_documentation(
        self, code: str, _tree: ast.Module | None = None
    ) -> dict[str, Any]:
        """Generate documentation for patterns found in code.

        Args:
            code: Code to analyze
            _tree: Pre-parsed AST (internal optimisation)

        Returns:
            Dictionary with pattern documentation
        """
        docs: dict[str, Any] = {}

        if not code:
            return {"documentation": docs}

        tree = _tree
        if tree is None:
            tree, err = self._parse_code(code)
            if tree is None:
                return {"documentation": docs, **(err or {})}

        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue

            methods = {
                item.name for item in node.body if isinstance(item, ast.FunctionDef)
            }

            # Repository pattern
            repo_methods = methods & {
                "save",
                "find_by_id",
                "find",
                "delete",
                "add",
            }
            if "Repository" in node.name or len(repo_methods) >= MIN_REPO_METHODS:
                docs["repository_pattern"] = {
                    "description": "Repository pattern for data access",
                    "usage": (f"Use {node.name} to abstract data persistence"),
                    "benefits": [
                        "Separates domain from data access",
                        "Enables testing with in-memory repositories",
                    ],
                }

            # Service pattern
            if "Service" in node.name:
                docs["service_pattern"] = {
                    "description": "Service pattern for business logic",
                    "usage": (f"Use {node.name} to orchestrate operations"),
                    "benefits": [
                        "Centralizes business logic",
                        "Coordinates between domain objects",
                    ],
                }

        return {"documentation": docs}

    def compare_pattern_alternatives(
        self,
        code: str,
        pattern_type: str = "",
        _tree: ast.Module | None = None,
    ) -> dict[str, Any]:
        """Compare alternative implementations of a pattern.

        Args:
            code: Code containing multiple pattern implementations
            pattern_type: Type of pattern to compare
            _tree: Pre-parsed AST (internal optimisation)

        Returns:
            Dictionary with comparison analysis
        """
        alternatives: list[dict[str, str]] = []
        comparison_matrix: list[dict[str, str]] = []
        recommendations: dict[str, Any] = {}

        if not code:
            return {
                "comparison": {
                    "alternatives": alternatives,
                    "comparison_matrix": comparison_matrix,
                    "recommendations": recommendations,
                }
            }

        tree = _tree
        if tree is None:
            tree, err = self._parse_code(code)
            if tree is None:
                return {
                    "comparison": {
                        "alternatives": [],
                        "comparison_matrix": [],
                        "recommendations": {},
                        **(err or {}),
                    }
                }

        if pattern_type == "factory":
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and (
                    "create" in node.name or "factory" in node.name.lower()
                ):
                    alternatives.append(
                        {
                            "name": node.name,
                            "type": "simple_factory",
                        }
                    )
                    comparison_matrix.append(
                        {
                            "name": node.name,
                            "flexibility": "low",
                            "complexity": "low",
                        }
                    )

                if isinstance(node, ast.ClassDef) and "Factory" in node.name:
                    alternatives.append(
                        {
                            "name": node.name,
                            "type": "abstract_factory",
                        }
                    )
                    comparison_matrix.append(
                        {
                            "name": node.name,
                            "flexibility": "high",
                            "complexity": "medium",
                        }
                    )

            recommendations = {
                "when_to_use": {
                    "simple_factory": ("When you have a small, fixed set of types"),
                    "abstract_factory": ("When you need families of related objects"),
                },
            }

        return {
            "comparison": {
                "alternatives": alternatives,
                "comparison_matrix": comparison_matrix,
                "recommendations": recommendations,
            }
        }
