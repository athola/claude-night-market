"""Gang of Four and async pattern recognition."""

from __future__ import annotations

import ast
import re
from typing import Any

from ._constants import _OBSERVER_METHODS, MIN_OBSERVER_METHODS

__all__ = ["GoFPatternMixin"]


def _is_factory(node: ast.ClassDef, methods: set[str]) -> bool:
    """Check if a class matches the Factory pattern."""
    if "Factory" in node.name:
        return True
    has_static_create = (
        any(
            isinstance(dec, ast.Name) and dec.id == "staticmethod"
            for item in node.body
            if isinstance(item, ast.FunctionDef)
            for dec in item.decorator_list
        )
        and "create" in "".join(methods).lower()
    )
    return has_static_create


def _is_observer(node: ast.ClassDef, methods: set[str], bases: list[str]) -> bool:
    """Check if a class matches the Observer pattern."""
    observer_methods = methods & _OBSERVER_METHODS
    return len(observer_methods) >= MIN_OBSERVER_METHODS or (
        "Observer" in node.name and "ABC" in bases
    )


def _is_strategy(node: ast.ClassDef, bases: list[str], strategies: list[str]) -> bool:
    """Check if a class matches the Strategy pattern."""
    return (
        ("ABC" in bases and "Strategy" in node.name)
        or ("Payment" in node.name and "ABC" in bases)
        or any(b in strategies or "Strategy" in b for b in bases)
    )


class GoFPatternMixin:
    """Recognise GoF design patterns and async programming patterns."""

    def recognize_gof_patterns(
        self, code: str, _tree: ast.Module | None = None
    ) -> dict[str, Any]:
        """Recognize Gang of Four design patterns.

        Args:
            code: Code to analyze
            _tree: Pre-parsed AST (internal optimisation)

        Returns:
            Dictionary with GoF pattern analysis
        """
        gof_patterns: dict[str, Any] = {}
        factories: list[str] = []
        observers: list[str] = []
        strategies: list[str] = []

        if not code:
            return {"gof_patterns": gof_patterns}

        tree = _tree
        if tree is None:
            tree, err = self._parse_code(code)
            if tree is None:
                return {"gof_patterns": gof_patterns, **(err or {})}

        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue

            methods = {
                item.name for item in node.body if isinstance(item, ast.FunctionDef)
            }
            bases = [b.id for b in node.bases if isinstance(b, ast.Name)]

            if _is_factory(node, methods):
                factories.append(node.name)
            if _is_observer(node, methods, bases):
                observers.append(node.name)
            if _is_strategy(node, bases, strategies):
                strategies.append(node.name)

        if factories:
            gof_patterns["factory_method"] = True
            gof_patterns["factories"] = factories
        if observers:
            gof_patterns["observer"] = True
            gof_patterns["observers"] = observers
        if strategies:
            gof_patterns["strategy"] = True
            gof_patterns["strategies"] = strategies

        return {"gof_patterns": gof_patterns}

    def recognize_async_patterns(self, code: str) -> dict[str, Any]:
        """Recognize async programming patterns.

        Args:
            code: Code to analyze

        Returns:
            Dictionary with async pattern analysis
        """
        async_patterns: dict[str, bool] = {}
        pattern_instances: list[str] = []

        if not code:
            return {
                "async_patterns": async_patterns,
                "pattern_instances": pattern_instances,
            }

        # Async context manager
        if "__aenter__" in code or "@asynccontextmanager" in code:
            async_patterns["async_context_manager"] = True

        # Retry pattern
        if "retry" in code.lower() or ("for attempt" in code and "await" in code):
            async_patterns["retry_pattern"] = True
            # Find function names with retry
            for match in re.finditer(
                r"async\s+def\s+(\w*retry\w*)", code, re.IGNORECASE
            ):
                pattern_instances.append(match.group(1))
            # Also check for fetch_with_retry style names
            for match in re.finditer(r"async\s+def\s+(fetch_with_\w+)", code):
                if match.group(1) not in pattern_instances:
                    pattern_instances.append(match.group(1))

        # Concurrent processing
        if "asyncio.gather" in code or "create_task" in code:
            async_patterns["concurrent_processing"] = True

        # Batch processing
        if "batch" in code.lower() and "await" in code:
            async_patterns["batch_processing"] = True

        return {
            "async_patterns": async_patterns,
            "pattern_instances": pattern_instances,
        }
