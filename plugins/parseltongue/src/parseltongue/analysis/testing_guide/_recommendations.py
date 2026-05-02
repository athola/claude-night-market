"""Test recommendation mixin for TestingGuideSkill."""

from __future__ import annotations

import ast
import re
from typing import Any

from ._constants import MIN_FUNCTIONS_FOR_PARAMETRIZE, parse_code


class TestRecommendationMixin:
    """Workflow, fixture, tooling, and documentation recommendations."""

    def recommend_tdd_workflow(self, code: str) -> dict[str, Any]:
        """Recommend a TDD workflow for the given feature description.

        Args:
            code: Feature description or code to analyze

        Returns:
            Dictionary containing TDD workflow recommendation
        """
        steps: list[dict[str, Any]] = []

        if not code:
            return {"tdd_workflow": {"steps": steps}}

        # Extract feature requirements from the description
        lines = [
            line.strip()
            for line in code.split("\n")
            if line.strip() and line.strip().startswith("-")
        ]

        for line in lines:
            requirement = line.lstrip("- ").strip()
            test_name = (
                "test_"
                + re.sub(r"[^a-z0-9_]", "_", requirement.lower()).strip("_")[:50]
            )

            step: dict[str, Any] = {
                "description": f"Implement: {requirement}",
                "test_name": test_name,
                "implementation_hint": f"Start with the simplest "
                f"implementation for: {requirement}",
                "test_cases": [
                    f"test_{requirement.split()[0].lower()}_success",
                    f"test_{requirement.split()[0].lower()}_failure",
                ],
            }
            steps.append(step)

        # Ensure at least 3 steps
        while len(steps) < MIN_FUNCTIONS_FOR_PARAMETRIZE:
            steps.append(
                {
                    "description": "Refactor and improve",
                    "test_name": f"test_refactor_step_{len(steps)}",
                    "implementation_hint": "Improve code quality",
                    "test_cases": ["test_edge_cases", "test_integration"],
                }
            )

        return {"tdd_workflow": {"steps": steps}}

    def suggest_improvements(self, code: str) -> dict[str, Any]:
        """Suggest improvements for test code.

        Args:
            code: Test code to analyze

        Returns:
            Dictionary containing improvement suggestions
        """
        suggestions: list[dict[str, str]] = []

        if not code:
            return {"suggestions": suggestions}

        # Check for testing private methods
        if re.search(r"\._\w+\(", code):
            suggestions.append(
                {
                    "issue": "private_method testing detected",
                    "improvement": "Test public API instead",
                    "example": "def test_public_method(): ...",
                    "rationale": "Private methods are implementation "
                    "details that may change",
                }
            )

        # Check for no assertions
        if "assert" not in code:
            suggestions.append(
                {
                    "issue": "No assertions found",
                    "improvement": "Add assertions to verify behavior",
                    "example": "assert result == expected",
                    "rationale": "Assertions verify the code works correctly",
                }
            )

        # Check for no fixtures
        if "fixture" not in code and "setUp" not in code:
            suggestions.append(
                {
                    "issue": "No fixture or setup usage",
                    "improvement": "Use fixtures for shared setup",
                    "example": "@pytest.fixture\ndef service():\n    "
                    "return UserService()",
                    "rationale": "Fixtures reduce duplication and "
                    "improve maintainability",
                }
            )

        return {"suggestions": suggestions}

    def generate_test_fixtures(
        self, code: str, _tree: ast.Module | None = None
    ) -> dict[str, Any]:
        """Generate test fixtures for the given source code.

        Args:
            code: Source code to generate fixtures for
            _tree: Pre-parsed AST (internal optimisation)

        Returns:
            Dictionary containing generated fixtures
        """
        fixtures: dict[str, Any] = {}
        imports: list[str] = ["import pytest"]

        if not code:
            return {"fixtures": fixtures, "imports": imports}

        tree = _tree
        if tree is None:
            tree, err = parse_code(code)
            if tree is None:
                return {"fixtures": fixtures, "imports": imports, **(err or {})}

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_name = node.name
                fixture_key = f"{class_name.lower()}_fixture"

                # Find __init__ params
                init_params: list[str] = []
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) and item.name == "__init__":
                        init_params = [
                            arg.arg for arg in item.args.args if arg.arg != "self"
                        ]

                fixtures[fixture_key] = {
                    "minimal_fixture": f"@pytest.fixture\n"
                    f"def {class_name.lower()}():\n"
                    f"    return {class_name}("
                    + ", ".join(f'"{p}"' if p != "id" else "1" for p in init_params)
                    + ")",
                    "complete_fixture": f"@pytest.fixture\n"
                    f"def {class_name.lower()}_full():\n"
                    f"    return {class_name}("
                    + ", ".join(
                        f'{p}="{p}_value"' if p != "id" else "id=1" for p in init_params
                    )
                    + ")",
                    "edge_case_fixture": f"@pytest.fixture\n"
                    f"def {class_name.lower()}_edge():\n"
                    f"    return {class_name}("
                    + ", ".join(f'{p}=""' if p != "id" else "id=0" for p in init_params)
                    + ")",
                }

        return {"fixtures": fixtures, "imports": imports}

    def recommend_test_types(self, code: str) -> dict[str, Any]:
        """Recommend types of tests for the given code structure.

        Args:
            code: Code structure description or actual code

        Returns:
            Dictionary containing test type recommendations
        """
        recommendations: dict[str, Any] = {
            "unit_tests": {},
            "integration_tests": {},
            "test_structure": {"conftest_py": True},
        }

        if not code:
            return {"test_recommendations": recommendations}

        # Parse module structure from code/description
        # Support both "user/models.py # desc" and tree-formatted
        # "├── models.py  # desc" styles
        modules = re.findall(r"(\w+)/(\w+)\.py\s*#?\s*(.*)", code)

        # Also parse tree-formatted directory listings
        current_dir = ""
        for line in code.split("\n"):
            # Detect directory lines like "├── user/" or "user/"
            dir_match = re.search(r"[├└│─\s]*(\w+)/\s*$", line)
            if dir_match:
                current_dir = dir_match.group(1)
                continue

            # Detect file lines like "├── models.py  # description"
            file_match = re.search(r"[├└│─\s]*(\w+)\.py\s*#?\s*(.*)", line)
            if file_match and current_dir:
                module_name = file_match.group(1)
                description = file_match.group(2).strip()
                if module_name == "__init__":
                    continue
                modules.append((current_dir, module_name, description))

        for module_dir, module_name, description in modules:
            test_key = f"{module_dir}_{module_name}_test"
            if (
                "model" in module_name.lower()
                or "service" in module_name.lower()
                or "middleware" in module_name.lower()
            ):
                recommendations["unit_tests"][test_key] = {
                    "description": description.strip() or f"Tests for {module_name}",
                }

        # Recommend integration tests for auth flows
        if "auth" in code.lower():
            recommendations["integration_tests"]["auth_flow_test"] = {
                "description": "End-to-end authentication flow",
            }

        return {"test_recommendations": recommendations}

    def recommend_testing_tools(self, code: Any) -> dict[str, Any]:
        """Recommend testing tools based on project context.

        Args:
            code: Project context (dict or string)

        Returns:
            Dictionary containing tool recommendations
        """
        recommendations: dict[str, Any] = {
            "testing_framework": "pytest",
            "async_testing": {"tools": ["pytest-asyncio"]},
            "api_testing": {"tools": ["httpx", "aiohttp"]},
            "database_testing": {"tools": ["factory_boy", "pytest-postgresql"]},
        }

        if isinstance(code, dict):
            context = code
            if context.get("async"):
                recommendations["async_testing"]["tools"].append("anyio")
            if context.get("framework") == "fastapi":
                recommendations["api_testing"]["tools"].append("starlette.testclient")

        return {"tool_recommendations": recommendations}

    def generate_test_documentation(
        self, code: str, _tree: ast.Module | None = None
    ) -> dict[str, Any]:
        """Generate documentation for test code.

        Args:
            code: Test code to document
            _tree: Pre-parsed AST (internal optimisation)

        Returns:
            Dictionary containing test documentation
        """
        documentation: dict[str, Any] = {
            "overview": {},
            "test_cases": [],
        }

        if not code:
            return {"documentation": documentation}

        tree = _tree
        if tree is None:
            tree, err = parse_code(code)
            if tree is None:
                return {"documentation": documentation, **(err or {})}

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
                docstring = ast.get_docstring(node) or ""
                documentation["overview"] = {
                    "test_class": node.name,
                    "purpose": docstring.strip(".").strip(),
                }

                for item in node.body:
                    if isinstance(item, ast.FunctionDef) and item.name.startswith(
                        "test_"
                    ):
                        test_doc = ast.get_docstring(item) or ""
                        has_fixture = len(item.args.args) > 1
                        has_assert = any(
                            isinstance(c, ast.Assert) for c in ast.walk(item)
                        )

                        documentation["test_cases"].append(
                            {
                                "name": item.name,
                                "description": test_doc.strip(".").strip(),
                                "setup": "fixture" if has_fixture else "inline",
                                "assertions": has_assert,
                            }
                        )

        return {"documentation": documentation}
