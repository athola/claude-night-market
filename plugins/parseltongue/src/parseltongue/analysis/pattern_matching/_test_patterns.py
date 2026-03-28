"""Test pattern recognition (pytest fixtures, test classes, lifecycle)."""

from __future__ import annotations

import ast
import re
from typing import Any

__all__ = ["TestPatternMixin"]


class TestPatternMixin:
    """Recognise testing patterns in code."""

    def recognize_test_patterns(
        self, code: str, _tree: ast.Module | None = None
    ) -> dict[str, Any]:
        """Recognize testing patterns in code.

        Args:
            code: Test code to analyze
            _tree: Pre-parsed AST (internal optimisation)

        Returns:
            Dictionary with recognized testing patterns
        """
        recognized_patterns: list[str] = []
        pytest_patterns: list[str] = []
        structures: list[str] = []
        test_classes: list[str] = []
        lifecycle_methods: list[str] = []
        confidence = 0.0

        if not code:
            return {
                "recognized_patterns": recognized_patterns,
                "confidence": 0.0,
                "patterns": {"pytest": pytest_patterns},
                "structures": structures,
                "test_classes": test_classes,
                "lifecycle_methods": lifecycle_methods,
            }

        tree = _tree
        if tree is None:
            tree, _ = self._parse_code(code)
            if tree is None:
                return {
                    "recognized_patterns": [],
                    "confidence": 0.0,
                    "patterns": {"pytest": []},
                    "structures": [],
                    "test_classes": [],
                    "lifecycle_methods": [],
                }

        # Detect pytest fixtures
        if "@pytest.fixture" in code or "@fixture" in code:
            pytest_patterns.append("fixture")
            recognized_patterns.append("test_pattern")

        # Detect test classes
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if node.name.startswith("Test"):
                    structures.append("test_class")
                    test_classes.append(node.name)
                    confidence = max(confidence, 0.9)

                # Check for lifecycle methods
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) and item.name in (
                        "setup_method",
                        "teardown_method",
                        "setup_class",
                        "teardown_class",
                        "setUp",
                        "tearDown",
                    ):
                        lifecycle_methods.append(item.name)

        # Detect test functions
        if re.search(r"def test_\w+", code):
            recognized_patterns.append("test_pattern")
            confidence = max(confidence, 0.85)

        return {
            "recognized_patterns": recognized_patterns,
            "confidence": confidence,
            "patterns": {"pytest": pytest_patterns},
            "structures": structures,
            "test_classes": test_classes,
            "lifecycle_methods": lifecycle_methods,
        }
