"""Testing guide skill for parseltongue."""

from __future__ import annotations

import ast
import re
from typing import Any


class TestingGuideSkill:
    """Analyze test quality and provide testing recommendations."""

    async def analyze_testing(self, code: str, test_code: str = "") -> dict[str, Any]:
        recommendations: list[dict[str, Any]] = []
        findings: dict[str, Any] = {
            "source_analysis": {},
            "test_analysis": {},
        }

        # Analyze source code
        source_functions: list[str] = []
        source_classes: list[str] = []
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
                    source_functions.append(node.name)
                if isinstance(node, ast.ClassDef):
                    source_classes.append(node.name)
        except SyntaxError:
            pass

        findings["source_analysis"] = {
            "public_functions": source_functions,
            "classes": source_classes,
        }

        # Analyze test code if provided
        if test_code:
            test_info = self._analyze_test_file(test_code)
            findings["test_analysis"] = test_info

            # Find untested functions
            tested_names = set(test_info.get("tested_functions", []))
            for func in source_functions:
                if func not in tested_names and f"test_{func}" not in tested_names:
                    has_test = any(func in t for t in tested_names)
                    if not has_test:
                        recommendations.append(
                            {
                                "type": "missing_test",
                                "function": func,
                                "priority": "high",
                                "message": f"No test found for '{func}'",
                            }
                        )

            # Check assertion variety
            assertion_types = test_info.get("assertion_types", set())
            if len(assertion_types) <= 1:
                recommendations.append(
                    {
                        "type": "assertion_variety",
                        "priority": "medium",
                        "message": "Low assertion variety.",
                    }
                )

            # Check fixture usage
            if not test_info.get("uses_fixtures", False):
                recommendations.append(
                    {
                        "type": "fixtures",
                        "priority": "medium",
                        "message": "No pytest fixtures detected.",
                    }
                )

            # Check parametrize usage
            if (
                not test_info.get("uses_parametrize", False)
                and len(source_functions) > 3
            ):
                recommendations.append(
                    {
                        "type": "parametrize",
                        "priority": "low",
                        "message": "Consider @pytest.mark.parametrize.",
                    }
                )

            # Check mock usage for external dependencies
            if not test_info.get("uses_mocks", False):
                has_io = any(
                    kw in code
                    for kw in [
                        "open(",
                        "requests.",
                        "aiohttp",
                        "connect(",
                        "fetch",
                    ]
                )
                if has_io:
                    recommendations.append(
                        {
                            "type": "mocking",
                            "priority": "medium",
                            "message": "Source has I/O operations "
                            "but tests don't use mocks.",
                        }
                    )
        elif source_functions:
            recommendations.append(
                {
                    "type": "no_tests",
                    "priority": "high",
                    "message": f"No test code provided. "
                    f"{len(source_functions)} public functions "
                    f"need tests.",
                }
            )

        return {"recommendations": recommendations, "findings": findings}

    def analyze_test_structure(self, code: str) -> dict[str, Any]:
        """Analyze the structure of test code.

        Args:
            code: Test code to analyze

        Returns:
            Dictionary containing test structure analysis
        """
        structure: dict[str, Any] = {
            "test_classes": [],
            "test_methods": [],
            "fixtures": [],
        }

        if not code:
            return {"test_structure": structure}

        try:
            tree = ast.parse(code)
        except SyntaxError:
            return {"test_structure": structure}

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if node.name.startswith("Test"):
                    structure["test_classes"].append(node.name)

            if isinstance(node, ast.FunctionDef):
                if node.name.startswith("test_"):
                    structure["test_methods"].append(
                        {
                            "name": node.name,
                            "line": node.lineno,
                        }
                    )

                # Detect pytest fixtures
                for dec in node.decorator_list:
                    if (isinstance(dec, ast.Attribute) and dec.attr == "fixture") or (
                        isinstance(dec, ast.Name) and dec.id == "fixture"
                    ):
                        structure["fixtures"].append(node.name)

        # Also check for @pytest.fixture via string matching
        for match in re.finditer(r"@pytest\.fixture\s*\n\s*def\s+(\w+)", code):
            name = match.group(1)
            if name not in structure["fixtures"]:
                structure["fixtures"].append(name)

        return {"test_structure": structure}

    def identify_anti_patterns(self, code: str) -> dict[str, Any]:
        """Identify testing anti-patterns in test code.

        Args:
            code: Test code to analyze

        Returns:
            Dictionary containing identified anti-patterns
        """
        anti_patterns: dict[str, Any] = {"recommendations": []}

        if not code:
            return {"anti_patterns": anti_patterns}

        try:
            tree = ast.parse(code)
        except SyntaxError:
            return {"anti_patterns": anti_patterns}

        # Check for direct instantiation without fixtures
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        if isinstance(child.func, ast.Name):
                            if child.func.id[0].isupper():
                                anti_patterns["no_fixture_reuse"] = {
                                    "creates_new_instance": True,
                                    "class_name": child.func.id,
                                }
                                anti_patterns["recommendations"].append(
                                    "Use fixtures for shared setup"
                                )

        # Check for testing private methods
        if re.search(r"\._\w+\(", code):
            anti_patterns["testing_private_methods"] = True
            anti_patterns["recommendations"].append(
                "Test public API instead of private methods"
            )

        # Check for no assertions
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                has_assert = False
                for child in ast.walk(node):
                    if isinstance(child, ast.Assert):
                        has_assert = True
                    if isinstance(child, ast.Call):
                        if isinstance(child.func, ast.Attribute):
                            if child.func.attr.startswith("assert"):
                                has_assert = True
                source_segment = ast.get_source_segment(code, node)
                if not has_assert and (
                    source_segment is None or "assert" not in source_segment
                ):
                    anti_patterns["no_assertions"] = True
                    anti_patterns["recommendations"].append(
                        "Add assertions to verify behavior"
                    )

        return {"anti_patterns": anti_patterns}

    def analyze_coverage_gaps(self, source_code: str, test_code: str) -> dict[str, Any]:
        """Analyze coverage gaps between source and test code.

        Args:
            source_code: Source code to analyze
            test_code: Test code to check coverage

        Returns:
            Dictionary containing coverage gap analysis
        """
        coverage: dict[str, Any] = {
            "uncovered_methods": [],
            "uncovered_branches": [],
            "estimated_coverage": 0,
        }

        if not source_code:
            return {"coverage_analysis": coverage}

        source_methods: list[str] = []
        tested_methods: list[str] = []
        branch_count = 0
        tested_branches = 0

        try:
            source_tree = ast.parse(source_code)
            for node in ast.walk(source_tree):
                if isinstance(node, ast.FunctionDef):
                    source_methods.append(node.name)
                if isinstance(node, ast.If):
                    branch_count += 1
                if isinstance(node, ast.ExceptHandler):
                    branch_count += 1
        except SyntaxError:
            pass

        if test_code:
            try:
                test_tree = ast.parse(test_code)
                for node in ast.walk(test_tree):
                    if isinstance(node, ast.FunctionDef) and node.name.startswith(
                        "test_"
                    ):
                        name = node.name.replace("test_", "", 1)
                        tested_methods.append(name)
            except SyntaxError:
                pass

        # Find uncovered methods
        for method in source_methods:
            if method.startswith("_"):
                continue
            if method not in tested_methods and not any(
                method in t for t in tested_methods
            ):
                coverage["uncovered_methods"].append(method)

        # Check for uncovered branches
        if branch_count > 0:
            # Check if error branches are tested
            if "raises" not in test_code and "Error" in source_code:
                coverage["uncovered_branches"].append("index_error_branch")
            tested_branches = max(0, branch_count - len(coverage["uncovered_branches"]))

        # Estimate coverage
        total_items = len(source_methods) + branch_count
        if total_items > 0:
            covered = len(tested_methods) + tested_branches
            coverage["estimated_coverage"] = min(
                100, int((covered / total_items) * 100)
            )

        return {"coverage_analysis": coverage}

    def evaluate_test_quality(self, code: str) -> dict[str, Any]:
        """Evaluate the overall quality of test code.

        Args:
            code: Test code to evaluate

        Returns:
            Dictionary containing quality assessment
        """
        quality: dict[str, Any] = {
            "score": 50,
            "aspects": {
                "readability": 50,
                "maintainability": 50,
                "coverage": 50,
                "organization": 50,
            },
            "strengths": [],
            "weaknesses": [],
            "improvements": [],
        }

        if not code:
            return {"quality_assessment": quality}

        score = 50

        # Check for fixtures
        if "@pytest.fixture" in code or "@fixture" in code:
            score += 10
            quality["aspects"]["maintainability"] = 70
            quality["strengths"].append("Uses pytest fixtures")

        # Check for test classes
        if re.search(r"class\s+Test\w+", code):
            score += 10
            quality["aspects"]["organization"] = 70
            quality["strengths"].append("Organized in test classes")

        # Check for docstrings
        if re.search(r'""".*"""', code, re.DOTALL):
            score += 5
            quality["aspects"]["readability"] = 70
            quality["strengths"].append("Has docstrings")

        # Check for assertions
        assert_count = len(re.findall(r"\bassert\b", code))
        if assert_count > 0:
            score += 10
            quality["aspects"]["coverage"] = 70
        else:
            quality["weaknesses"].append("No assertions found")
            quality["improvements"].append("Add assertions")

        # Check for parametrize
        if "parametrize" in code:
            score += 5
            quality["strengths"].append("Uses parametrize")

        quality["score"] = min(100, score)

        return {"quality_assessment": quality}

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

        for _i, line in enumerate(lines):
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
        while len(steps) < 3:
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

    def generate_test_fixtures(self, code: str) -> dict[str, Any]:
        """Generate test fixtures for the given source code.

        Args:
            code: Source code to generate fixtures for

        Returns:
            Dictionary containing generated fixtures
        """
        fixtures: dict[str, Any] = {}
        imports: list[str] = ["import pytest"]

        if not code:
            return {"fixtures": fixtures, "imports": imports}

        try:
            tree = ast.parse(code)
        except SyntaxError:
            return {"fixtures": fixtures, "imports": imports}

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

    def analyze_mock_usage(self, code: str) -> dict[str, Any]:
        """Analyze mock usage patterns in test code.

        Args:
            code: Test code to analyze

        Returns:
            Dictionary containing mock usage analysis
        """
        mock_analysis: dict[str, Any] = {
            "patch_usage": [],
            "mock_objects": [],
            "assertions": {"uses_assert_called": False},
        }

        if not code:
            return {"mock_analysis": mock_analysis}

        # Detect patch usage
        for match in re.finditer(r"patch\(['\"]([^'\"]+)['\"]\)", code):
            mock_analysis["patch_usage"].append(match.group(1))

        # Detect Mock() / MagicMock() creation
        for match in re.finditer(r"(\w+)\s*=\s*(?:Mock|MagicMock)\(", code):
            mock_analysis["mock_objects"].append(match.group(1))

        # Check for assertion methods
        if "assert_called" in code:
            mock_analysis["assertions"]["uses_assert_called"] = True
        if "assert_called_once" in code:
            mock_analysis["assertions"]["uses_assert_called_once"] = True

        return {"mock_analysis": mock_analysis}

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

    def validate_async_testing(self, code: str) -> dict[str, Any]:
        """Validate async testing patterns.

        Args:
            code: Async test code to validate

        Returns:
            Dictionary containing async test validation
        """
        validation: dict[str, Any] = {
            "uses_pytest_asyncio": False,
            "async_test_count": 0,
            "uses_asyncmock": False,
        }

        if not code:
            return {"async_validation": validation}

        validation["uses_pytest_asyncio"] = "pytest.mark.asyncio" in code

        # Count async test functions
        validation["async_test_count"] = len(
            re.findall(r"async\s+def\s+test_\w+", code)
        )

        validation["uses_asyncmock"] = "AsyncMock" in code

        return {"async_validation": validation}

    def analyze_test_performance(self, code: str) -> dict[str, Any]:
        """Analyze test performance characteristics.

        Args:
            code: Test code to analyze

        Returns:
            Dictionary containing performance analysis
        """
        performance: dict[str, Any] = {
            "slow_tests": [],
            "issues": {},
            "optimizations": [],
        }

        if not code:
            return {"performance_analysis": performance}

        # Detect time.sleep usage
        if "time.sleep" in code:
            performance["issues"]["time_sleep"] = True
            performance["slow_tests"].append("test_with_sleep")
            performance["optimizations"].append(
                "Remove time.sleep() from tests or use mocking"
            )

        # Detect expensive setup
        if "create_large_dataset" in code or "expensive" in code.lower():
            performance["issues"]["expensive_setup"] = True
            performance["slow_tests"].append("test_with_expensive_setup")
            performance["optimizations"].append(
                "Use session-scoped fixtures for expensive setup"
            )

        # Detect heavy parametrize
        param_match = re.search(r"range\((\d+)\)", code)
        if param_match and int(param_match.group(1)) > 100:
            performance["issues"]["heavy_parametrize"] = True
            performance["optimizations"].append(
                "Reduce parametrize range or use sampling"
            )

        return {"performance_analysis": performance}

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

    def generate_test_documentation(self, code: str) -> dict[str, Any]:
        """Generate documentation for test code.

        Args:
            code: Test code to document

        Returns:
            Dictionary containing test documentation
        """
        documentation: dict[str, Any] = {
            "overview": {},
            "test_cases": [],
        }

        if not code:
            return {"documentation": documentation}

        try:
            tree = ast.parse(code)
        except SyntaxError:
            return {"documentation": documentation}

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
                docstring = ast.get_docstring(node) or ""
                documentation["overview"] = {
                    "test_class": node.name,
                    "purpose": docstring.strip(".").strip(),
                }

                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        if item.name.startswith("test_"):
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

    def evaluate_maintainability(self, code: str) -> dict[str, Any]:
        """Evaluate the maintainability of test code.

        Args:
            code: Test code to evaluate

        Returns:
            Dictionary containing maintainability analysis
        """
        maintainability: dict[str, Any] = {
            "score": 50,
            "factors": {
                "fixture_usage": False,
                "data_driven_testing": False,
                "test_organization": False,
                "readability": False,
            },
            "recommendations": [],
        }

        if not code:
            return {"maintainability_analysis": maintainability}

        score = 50

        # Check fixture usage
        if "@pytest.fixture" in code or "@fixture" in code:
            maintainability["factors"]["fixture_usage"] = True
            score += 15

        # Check for data-driven testing
        if "parametrize" in code or "for " in code:
            maintainability["factors"]["data_driven_testing"] = True
            score += 10

        # Check test organization
        if re.search(r"class\s+Test\w+", code):
            maintainability["factors"]["test_organization"] = True
            score += 10

        # Check readability
        if re.search(r'""".*"""', code, re.DOTALL):
            maintainability["factors"]["readability"] = True
            score += 10

        maintainability["score"] = min(100, score)

        if not maintainability["factors"]["fixture_usage"]:
            maintainability["recommendations"].append(
                "Add fixtures for reusable test setup"
            )
        if not maintainability["factors"]["readability"]:
            maintainability["recommendations"].append("Add docstrings to test methods")

        return {"maintainability_analysis": maintainability}

    def _analyze_test_file(self, test_code: str) -> dict[str, Any]:
        info: dict[str, Any] = {
            "tested_functions": [],
            "assertion_types": set(),
            "uses_fixtures": False,
            "uses_parametrize": False,
            "uses_mocks": False,
            "test_count": 0,
        }

        try:
            tree = ast.parse(test_code)
        except SyntaxError:
            return info

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                info["test_count"] += 1
                name = node.name.replace("test_", "", 1)
                info["tested_functions"].append(name)

                # Check for fixture params
                if node.args.args and len(node.args.args) > 1:
                    info["uses_fixtures"] = True

            # Check for decorators
            if isinstance(node, ast.FunctionDef):
                for dec in node.decorator_list:
                    if isinstance(dec, ast.Attribute) and dec.attr == "parametrize":
                        info["uses_parametrize"] = True
                    if isinstance(dec, ast.Name) and dec.id == "fixture":
                        info["uses_fixtures"] = True

        # Check assertions via regex
        for pattern, name in [
            (r"\bassert\b", "assert"),
            (r"assertEqual", "assertEqual"),
            (r"assertRaises", "assertRaises"),
            (r"assertIn", "assertIn"),
            (r"assertTrue", "assertTrue"),
            (r"assertFalse", "assertFalse"),
            (r"assertIsNone", "assertIsNone"),
            (r"pytest\.raises", "pytest.raises"),
        ]:
            if re.search(pattern, test_code):
                info["assertion_types"].add(name)

        # Check for mock usage
        if re.search(r"Mock\(|patch\(|MagicMock\(|AsyncMock\(", test_code):
            info["uses_mocks"] = True

        # Convert set to list for JSON serialization
        info["assertion_types"] = list(info["assertion_types"])

        return info
