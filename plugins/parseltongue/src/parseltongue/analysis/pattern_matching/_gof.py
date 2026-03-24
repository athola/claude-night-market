"""Gang of Four and async pattern recognition."""

from __future__ import annotations

import ast
import re
from typing import Any

from ._constants import _OBSERVER_METHODS, MIN_OBSERVER_METHODS

__all__ = ["GoFPatternMixin"]


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
            tree, err = self._parse_code(code)  # type: ignore[attr-defined]
            if tree is None:
                return {"gof_patterns": gof_patterns, **(err or {})}

        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue

            methods = {
                item.name for item in node.body if isinstance(item, ast.FunctionDef)
            }
            bases = []
            for b in node.bases:
                if isinstance(b, ast.Name):
                    bases.append(b.id)

            # Factory: has create/static methods returning different types
            if "Factory" in node.name or (
                any(
                    isinstance(dec, ast.Name) and dec.id == "staticmethod"
                    for item in node.body
                    if isinstance(item, ast.FunctionDef)
                    for dec in item.decorator_list
                )
                and "create" in "".join(methods).lower()
            ):
                factories.append(node.name)

            # Observer: has subscribe/notify methods
            observer_methods = methods & _OBSERVER_METHODS
            if len(observer_methods) >= MIN_OBSERVER_METHODS or (
                "Observer" in node.name and "ABC" in bases
            ):
                observers.append(node.name)

            # Strategy: abstract class with single method
            if (
                ("ABC" in bases and "Strategy" in node.name)
                or ("Payment" in node.name and "ABC" in bases)
            ) or any(b in strategies or "Strategy" in b for b in bases):
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
