"""Test structure analysis mixin for TestingGuideSkill."""

from __future__ import annotations

import ast
import re
from typing import Any

from ._constants import HEAVY_PARAMETRIZE_THRESHOLD, MIN_FUNCTIONS_FOR_PARAMETRIZE


class TestStructureMixin:
    """AST-based analysis of test structure, coverage, and performance."""

    def _parse_code(self, code: str) -> tuple[ast.Module | None, dict | None]:
        """Parse code into an AST, returning an error dict on failure."""
        try:
            return ast.parse(code), None
        except SyntaxError:
            return None, {"error": "Invalid Python syntax"}

    async def analyze_testing(self, code: str, test_code: str = "") -> dict[str, Any]:
        recommendations: list[dict[str, Any]] = []
        findings: dict[str, Any] = {
            "source_analysis": {},
            "test_analysis": {},
        }

        # Analyze source code
        source_functions, source_classes = self._extract_source_elements(code)
        findings["source_analysis"] = {
            "public_functions": source_functions,
            "classes": source_classes,
        }

        # Analyze test code if provided
        if test_code:
            test_info = self._analyze_test_file(test_code)
            findings["test_analysis"] = test_info
            recommendations.extend(
                self._check_test_recommendations(test_info, source_functions, code)
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

    def analyze_test_structure(
        self, code: str, _tree: ast.Module | None = None
    ) -> dict[str, Any]:
        """Analyze the structure of test code.

        Args:
            code: Test code to analyze
            _tree: Pre-parsed AST (internal optimisation)

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

        tree = _tree
        if tree is None:
            tree, err = self._parse_code(code)
            if tree is None:
                return {"test_structure": structure, **(err or {})}

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
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

    def identify_anti_patterns(
        self, code: str, _tree: ast.Module | None = None
    ) -> dict[str, Any]:
        """Identify testing anti-patterns in test code.

        Args:
            code: Test code to analyze
            _tree: Pre-parsed AST (internal optimisation)

        Returns:
            Dictionary containing identified anti-patterns
        """
        anti_patterns: dict[str, Any] = {"recommendations": []}

        if not code:
            return {"anti_patterns": anti_patterns}

        tree = _tree
        if tree is None:
            tree, err = self._parse_code(code)
            if tree is None:
                return {"anti_patterns": anti_patterns, **(err or {})}

        self._check_direct_instantiation(tree, anti_patterns)
        self._check_private_method_testing(code, anti_patterns)
        self._check_assertions(tree, code, anti_patterns)

        return {"anti_patterns": anti_patterns}

    def _check_direct_instantiation(
        self, tree: ast.AST, anti_patterns: dict[str, Any]
    ) -> None:
        """Check for direct class instantiation without fixtures.

        Args:
            tree: AST tree to analyze
            anti_patterns: Dictionary to update with findings
        """
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                for child in ast.walk(node):
                    if (
                        isinstance(child, ast.Call)
                        and isinstance(child.func, ast.Name)
                        and child.func.id[0].isupper()
                    ):
                        anti_patterns["no_fixture_reuse"] = {
                            "creates_new_instance": True,
                            "class_name": child.func.id,
                        }
                        anti_patterns["recommendations"].append(
                            "Use fixtures for shared setup"
                        )

    def _check_private_method_testing(
        self, code: str, anti_patterns: dict[str, Any]
    ) -> None:
        """Check for testing of private methods.

        Args:
            code: Code to analyze
            anti_patterns: Dictionary to update with findings
        """
        if re.search(r"\._\w+\(", code):
            anti_patterns["testing_private_methods"] = True
            anti_patterns["recommendations"].append(
                "Test public API instead of private methods"
            )

    def _check_assertions(
        self, tree: ast.AST, code: str, anti_patterns: dict[str, Any]
    ) -> None:
        """Check for presence of assertions in test functions.

        Args:
            tree: AST tree to analyze
            code: Original code string
            anti_patterns: Dictionary to update with findings
        """
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                has_assert = False
                for child in ast.walk(node):
                    if isinstance(child, ast.Assert):
                        has_assert = True
                    if (
                        isinstance(child, ast.Call)
                        and isinstance(child.func, ast.Attribute)
                        and child.func.attr.startswith("assert")
                    ):
                        has_assert = True
                source_segment = ast.get_source_segment(code, node)
                if not has_assert and (
                    source_segment is None or "assert" not in source_segment
                ):
                    anti_patterns["no_assertions"] = True
                    anti_patterns["recommendations"].append(
                        "Add assertions to verify behavior"
                    )

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

        source_methods, branch_count = self._extract_source_metrics(source_code)
        tested_methods = self._extract_tested_methods(test_code)

        # Find uncovered methods
        for method in source_methods:
            if method.startswith("_"):
                continue
            if method not in tested_methods and not any(
                method in t for t in tested_methods
            ):
                coverage["uncovered_methods"].append(method)

        # Check for uncovered branches
        tested_branches = self._analyze_branch_coverage(
            branch_count, test_code, source_code, coverage
        )

        # Estimate coverage
        total_items = len(source_methods) + branch_count
        if total_items > 0:
            covered = len(tested_methods) + tested_branches
            coverage["estimated_coverage"] = min(
                100, int((covered / total_items) * 100)
            )

        return {"coverage_analysis": coverage}

    def _extract_source_metrics(
        self,
        source_code: str,
        _tree: ast.Module | None = None,
    ) -> tuple[list[str], int]:
        """Extract methods and branch count from source code.

        Args:
            source_code: Source code to analyze
            _tree: Pre-parsed AST (internal optimisation)

        Returns:
            Tuple of (methods list, branch count)
        """
        source_methods: list[str] = []
        branch_count = 0

        tree = _tree
        if tree is None:
            tree, _ = self._parse_code(source_code)
            if tree is None:
                return source_methods, branch_count

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                source_methods.append(node.name)
            if isinstance(node, ast.If):
                branch_count += 1
            if isinstance(node, ast.ExceptHandler):
                branch_count += 1

        return source_methods, branch_count

    def _extract_tested_methods(
        self, test_code: str, _tree: ast.Module | None = None
    ) -> list[str]:
        """Extract tested method names from test code.

        Args:
            test_code: Test code to analyze
            _tree: Pre-parsed AST (internal optimisation)

        Returns:
            List of tested method names
        """
        tested_methods: list[str] = []

        if not test_code:
            return tested_methods

        tree = _tree
        if tree is None:
            tree, _ = self._parse_code(test_code)
            if tree is None:
                return tested_methods

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                name = node.name.replace("test_", "", 1)
                tested_methods.append(name)

        return tested_methods

    def _analyze_branch_coverage(
        self,
        branch_count: int,
        test_code: str,
        source_code: str,
        coverage: dict[str, Any],
    ) -> int:
        """Analyze branch coverage between source and tests.

        Args:
            branch_count: Total branches in source
            test_code: Test code to check
            source_code: Source code to analyze
            coverage: Coverage dict to update

        Returns:
            Number of tested branches
        """
        tested_branches = 0

        if branch_count > 0:
            # Check if error branches are tested
            if "raises" not in test_code and "Error" in source_code:
                coverage["uncovered_branches"].append("index_error_branch")
            tested_branches = max(0, branch_count - len(coverage["uncovered_branches"]))

        return tested_branches

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
        if param_match and int(param_match.group(1)) > HEAVY_PARAMETRIZE_THRESHOLD:
            performance["issues"]["heavy_parametrize"] = True
            performance["optimizations"].append(
                "Reduce parametrize range or use sampling"
            )

        return {"performance_analysis": performance}

    def _extract_source_elements(
        self, code: str, _tree: ast.Module | None = None
    ) -> tuple[list[str], list[str]]:
        """Extract public functions and classes from source code.

        Args:
            code: Source code to analyze
            _tree: Pre-parsed AST (internal optimisation)

        Returns:
            Tuple of (functions list, classes list)
        """
        source_functions: list[str] = []
        source_classes: list[str] = []

        tree = _tree
        if tree is None:
            tree, _ = self._parse_code(code)
            if tree is None:
                return source_functions, source_classes

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
                source_functions.append(node.name)
            if isinstance(node, ast.ClassDef):
                source_classes.append(node.name)

        return source_functions, source_classes

    def _check_test_recommendations(
        self,
        test_info: dict[str, Any],
        source_functions: list[str],
        code: str,
    ) -> list[dict[str, Any]]:
        """Generate test recommendations based on analysis.

        Args:
            test_info: Test file analysis results
            source_functions: List of public functions in source
            code: Source code to check for I/O operations

        Returns:
            List of recommendation dictionaries
        """
        recommendations: list[dict[str, Any]] = []

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
            and len(source_functions) > MIN_FUNCTIONS_FOR_PARAMETRIZE
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

        return recommendations

    def _analyze_test_file(
        self, test_code: str, _tree: ast.Module | None = None
    ) -> dict[str, Any]:
        info: dict[str, Any] = {
            "tested_functions": [],
            "assertion_types": set(),
            "uses_fixtures": False,
            "uses_parametrize": False,
            "uses_mocks": False,
            "test_count": 0,
        }

        tree = _tree
        if tree is None:
            tree, _ = self._parse_code(test_code)
            if tree is None:
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
