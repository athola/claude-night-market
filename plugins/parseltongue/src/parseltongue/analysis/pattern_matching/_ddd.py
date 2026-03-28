"""Domain-Driven Design pattern recognition."""

from __future__ import annotations

import ast
from typing import Any

from ._constants import MIN_REPO_METHODS

__all__ = ["DDDPatternMixin"]


class DDDPatternMixin:
    """Recognise DDD patterns: Entity, Value Object, Repository, Service."""

    # ------------------------------------------------------------------
    # Classification helpers
    # ------------------------------------------------------------------

    def _check_entity(
        self,
        node: ast.ClassDef,
        methods: set[str],
        decorators: list[str],
    ) -> bool:
        """Check if a class is a DDD Entity."""
        has_id = any(
            arg.arg == "id"
            for item in node.body
            if isinstance(item, ast.FunctionDef) and item.name == "__init__"
            for arg in item.args.args
        ) or (
            "dataclass" in decorators
            and any(
                isinstance(item, ast.AnnAssign)
                and isinstance(item.target, ast.Name)
                and item.target.id == "id"
                for item in node.body
            )
        )
        if not has_id:
            return False
        is_frozen = any(
            "frozen" in str(ast.dump(dec)) and "True" in str(ast.dump(dec))
            for dec in node.decorator_list
            if isinstance(dec, ast.Call)
        )
        return not is_frozen and bool(methods - {"__init__", "__post_init__"})

    def _check_value_object(
        self,
        node: ast.ClassDef,
        decorators: list[str],
    ) -> bool:
        """Check if a class is a DDD Value Object."""
        if "dataclass" not in decorators:
            return False
        for dec in node.decorator_list:
            if isinstance(dec, ast.Call):
                for kw in dec.keywords:
                    if (
                        kw.arg == "frozen"
                        and isinstance(kw.value, ast.Constant)
                        and kw.value.value is True
                    ):
                        return True
        return False

    def _check_repository(
        self,
        node: ast.ClassDef,
        methods: set[str],
        bases: list[str],
    ) -> bool:
        """Check if a class is a DDD Repository."""
        repo_methods = methods & {
            "save",
            "find_by_id",
            "find",
            "delete",
            "add",
            "get",
            "remove",
        }
        return bool(
            (len(repo_methods) >= MIN_REPO_METHODS or "Repository" in node.name)
            and ("Repository" in node.name or ("ABC" in bases and repo_methods))
        )

    def _check_domain_service(
        self,
        node: ast.ClassDef,
        methods: set[str],
    ) -> bool:
        """Check if a class is a DDD Domain Service."""
        if "Service" not in node.name or "__init__" not in methods:
            return False
        for item in node.body:
            if isinstance(item, ast.FunctionDef) and item.name == "__init__":
                for arg in item.args.args:
                    if arg.arg == "repository":
                        return True
        return False

    def _extract_decorators(self, node: ast.ClassDef) -> list[str]:
        """Extract decorator names from a class."""
        decorators = []
        for dec in node.decorator_list:
            if isinstance(dec, ast.Name):
                decorators.append(dec.id)
            elif isinstance(dec, ast.Call) and isinstance(dec.func, ast.Name):
                decorators.append(dec.func.id)
        return decorators

    def _build_ddd_patterns_result(
        self,
        entities: list[str],
        value_objects: list[str],
        repositories: list[str],
        domain_services: list[str],
    ) -> dict[str, Any]:
        """Build the final DDD patterns result dictionary."""
        ddd_patterns: dict[str, Any] = {}
        if entities:
            ddd_patterns["entity"] = True
            ddd_patterns["entities"] = entities
        if value_objects:
            ddd_patterns["value_object"] = True
            ddd_patterns["value_objects"] = value_objects
        if repositories:
            ddd_patterns["repository"] = True
            ddd_patterns["repositories"] = repositories
        if domain_services:
            ddd_patterns["domain_service"] = True
            ddd_patterns["domain_services"] = domain_services
        return ddd_patterns

    # ------------------------------------------------------------------
    # Public method
    # ------------------------------------------------------------------

    def recognize_ddd_patterns(
        self, code: str, _tree: ast.Module | None = None
    ) -> dict[str, Any]:
        """Recognize Domain-Driven Design patterns.

        Args:
            code: Code to analyze
            _tree: Pre-parsed AST (internal optimisation)

        Returns:
            Dictionary with DDD pattern analysis
        """
        if not code:
            return {"ddd_patterns": {}}

        tree = _tree
        if tree is None:
            tree, err = self._parse_code(code)
            if tree is None:
                return {"ddd_patterns": {}, **(err or {})}

        entities: list[str] = []
        value_objects: list[str] = []
        repositories: list[str] = []
        domain_services: list[str] = []

        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue

            methods = {
                item.name for item in node.body if isinstance(item, ast.FunctionDef)
            }
            bases = [b.id if isinstance(b, ast.Name) else "" for b in node.bases]
            decorators = self._extract_decorators(node)

            if self._check_entity(node, methods, decorators):
                entities.append(node.name)

            if self._check_value_object(node, decorators):
                value_objects.append(node.name)

            if self._check_repository(node, methods, bases):
                repositories.append(node.name)

            if self._check_domain_service(node, methods):
                domain_services.append(node.name)

        ddd_patterns = self._build_ddd_patterns_result(
            entities, value_objects, repositories, domain_services
        )
        return {"ddd_patterns": ddd_patterns}
