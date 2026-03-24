"""Core pattern detection: AST parsing, class-level and factory patterns."""

from __future__ import annotations

import ast
import re
from typing import Any

from ._constants import (
    _OBSERVER_METHODS,
    MIN_FACTORY_RETURN_CLASSES,
    MIN_OBSERVER_METHODS,
)

__all__ = ["PatternMatchingCoreMixin"]


class PatternMatchingCoreMixin:
    """AST parsing and structural pattern detection (singleton, observer,
    strategy, factory, decorator).
    """

    def _parse_code(self, code: str) -> tuple[ast.Module | None, dict | None]:
        """Parse code into an AST, returning an error dict on failure."""
        try:
            return ast.parse(code), None
        except SyntaxError:
            return None, {"error": "Invalid Python syntax"}

    # ------------------------------------------------------------------
    # Class-level pattern helpers
    # ------------------------------------------------------------------

    def _detect_class_patterns(
        self,
        tree: ast.Module,
        patterns: list[dict[str, Any]],
    ) -> None:
        """Detect class-level design patterns."""
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue

            methods = {
                item.name
                for item in node.body
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
            }
            attrs: set[str] = set()
            for item in node.body:
                if isinstance(item, ast.Assign):
                    for target in item.targets:
                        if isinstance(target, ast.Name):
                            attrs.add(target.id)
                        elif isinstance(target, ast.Attribute):
                            attrs.add(target.attr)

            self._check_singleton_pattern(node, methods, attrs, patterns)
            self._check_observer_pattern(node, methods, patterns)
            self._check_strategy_pattern(node, methods, patterns)

    def _check_singleton_pattern(
        self,
        node: ast.ClassDef,
        methods: set[str],
        attrs: set[str],
        patterns: list[dict[str, Any]],
    ) -> None:
        """Check for singleton pattern in class."""
        if "_instance" in attrs and ("__new__" in methods or "get_instance" in methods):
            patterns.append(
                {
                    "pattern": "singleton",
                    "class": node.name,
                    "line": node.lineno,
                    "evidence": "_instance attribute with __new__/get_instance",
                }
            )

    def _check_observer_pattern(
        self,
        node: ast.ClassDef,
        methods: set[str],
        patterns: list[dict[str, Any]],
    ) -> None:
        """Check for observer pattern in class."""
        observer_methods = methods & _OBSERVER_METHODS
        if len(observer_methods) >= MIN_OBSERVER_METHODS:
            patterns.append(
                {
                    "pattern": "observer",
                    "class": node.name,
                    "line": node.lineno,
                    "evidence": f"Methods: {', '.join(sorted(observer_methods))}",
                }
            )

    def _check_strategy_pattern(
        self,
        node: ast.ClassDef,
        methods: set[str],
        patterns: list[dict[str, Any]],
    ) -> None:
        """Check for strategy pattern in class."""
        if "__init__" not in methods:
            return
        for item in node.body:
            if isinstance(item, ast.FunctionDef) and item.name == "__init__":
                for arg in item.args.args:
                    if (
                        arg.annotation
                        and isinstance(arg.annotation, ast.Name)
                        and arg.annotation.id
                        in (
                            "Callable",
                            "Protocol",
                            "Strategy",
                        )
                    ):
                        patterns.append(
                            {
                                "pattern": "strategy",
                                "class": node.name,
                                "line": node.lineno,
                                "evidence": f"Parameter "
                                f"'{arg.arg}' typed as "
                                f"{arg.annotation.id}",
                            }
                        )

    # ------------------------------------------------------------------
    # Function-level pattern helpers
    # ------------------------------------------------------------------

    def _detect_factory_patterns(
        self,
        tree: ast.Module,
        patterns: list[dict[str, Any]],
    ) -> None:
        """Detect factory pattern in functions."""
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef):
                continue
            return_classes: set[str] = set()
            has_conditional = False
            for child in ast.walk(node):
                if isinstance(child, (ast.If, ast.IfExp)):
                    has_conditional = True
                if (
                    isinstance(child, ast.Return)
                    and child.value
                    and isinstance(child.value, ast.Call)
                    and isinstance(child.value.func, ast.Name)
                ):
                    name = child.value.func.id
                    if name[0].isupper():
                        return_classes.add(name)
            if has_conditional and len(return_classes) >= MIN_FACTORY_RETURN_CLASSES:
                patterns.append(
                    {
                        "pattern": "factory",
                        "function": node.name,
                        "line": node.lineno,
                        "evidence": "Returns different classes: "
                        + ", ".join(sorted(return_classes)),
                    }
                )

    def _detect_decorator_patterns(
        self,
        tree: ast.Module,
        patterns: list[dict[str, Any]],
    ) -> None:
        """Detect decorator pattern in functions."""
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef):
                continue
            uses_wraps = False
            for child in ast.walk(node):
                if isinstance(child, ast.Attribute) and child.attr == "wraps":
                    uses_wraps = True
                if isinstance(child, ast.Name) and child.id == "wraps":
                    uses_wraps = True
            if uses_wraps:
                patterns.append(
                    {
                        "pattern": "decorator",
                        "function": node.name,
                        "line": node.lineno,
                        "evidence": "Uses @wraps, function decorator pattern",
                    }
                )

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    async def find_patterns(
        self,
        code: str,
        language: str = "python",
        _tree: ast.Module | None = None,
    ) -> dict[str, Any]:
        """Find design patterns in code.

        Args:
            code: Code to analyze
            language: Programming language
            _tree: Pre-parsed AST (internal optimisation)

        Returns:
            Dictionary with patterns found
        """
        if language != "python":
            return {
                "patterns": [],
                "optimization_suggestions": [],
                "note": f"Only Python supported, got {language}",
            }

        if not code:
            return {"patterns": [], "optimization_suggestions": []}

        tree = _tree
        if tree is None:
            tree, err = self._parse_code(code)
            if tree is None:
                return {
                    "patterns": [],
                    "optimization_suggestions": [],
                    **(err or {}),
                }

        patterns: list[dict[str, Any]] = []

        self._detect_class_patterns(tree, patterns)
        self._detect_factory_patterns(tree, patterns)
        self._detect_decorator_patterns(tree, patterns)

        return {"patterns": patterns, "optimization_suggestions": []}

    def match_patterns(self, code: str, _language: str = "python") -> dict[str, Any]:
        """Match patterns in code with confidence scoring.

        Args:
            code: Code to analyze
            _language: Programming language (reserved for future use)

        Returns:
            Dictionary with patterns and confidence
        """
        patterns: list[str] = []
        confidence = 0.5

        if not code:
            return {"patterns": [], "confidence": 0.0}

        # Detect nested loops
        if re.search(r"for\s+\w+\s+in\s+.*:\s*\n\s+for\s+\w+\s+in", code):
            patterns.append("nested_loop")
            confidence = 0.8

        # Detect list comprehensions
        if re.search(r"\[.*for\s+\w+\s+in\s+.*\]", code):
            patterns.append("list_comprehension")
            confidence = max(confidence, 0.7)

        return {"patterns": patterns, "confidence": confidence}
