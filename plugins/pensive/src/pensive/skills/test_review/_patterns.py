"""Patterns mixin: anti-patterns, data management, mock usage."""

from __future__ import annotations

import ast
import re
from typing import Any

from ._constants import MIN_COMPLEX_ASSERTIONS, MIN_EDGE_CASES


class PatternsMixin:
    """Detect test anti-patterns, analyze data management and mock usage."""

    def identify_test_anti_patterns(
        self, context: Any, file_path: str = ""
    ) -> list[dict[str, Any]]:
        """Identify common test anti-patterns."""
        content = context.get_file_content(file_path)
        anti_patterns: list[dict[str, Any]] = []

        anti_patterns.extend(self._check_external_dependencies(content))
        anti_patterns.extend(self._check_shared_state(content))
        anti_patterns.extend(self._check_magic_numbers(content))
        anti_patterns.extend(self._check_slow_tests(content))
        anti_patterns.extend(self._check_assertion_quality(content))
        anti_patterns.extend(self._check_bare_excepts(content))

        return anti_patterns

    @staticmethod
    def _check_external_dependencies(content: str) -> list[dict[str, Any]]:
        """Detect tests that make real HTTP requests."""
        results: list[dict[str, Any]] = []
        for match in re.finditer(r"requests\.(get|post|put|delete)", content):
            results.append(
                {
                    "type": "external_dependency",
                    "message": "Test depends on external HTTP requests",
                    "line": content[: match.start()].count("\n") + 1,
                }
            )
        return results

    @staticmethod
    def _check_shared_state(content: str) -> list[dict[str, Any]]:
        """Detect module-level mutable assignments using AST."""
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return []
        results: list[dict[str, Any]] = []
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and not target.id.startswith("_"):
                        results.append(
                            {
                                "type": "shared_state",
                                "message": (
                                    f"Global '{target.id}' may cause state issues"
                                ),
                                "variable": target.id,
                                "line": node.lineno,
                            }
                        )
        return results

    @staticmethod
    def _check_magic_numbers(content: str) -> list[dict[str, Any]]:
        """Detect hardcoded magic numbers in assertions."""
        results: list[dict[str, Any]] = []
        for match in re.finditer(
            r"assert\s+\w+\s*==\s*(\d+)\s*(?:#.*)?$", content, re.MULTILINE
        ):
            if not re.search(r"#.*(?:explain|why)", match.group(0)):
                results.append(
                    {
                        "type": "hardcoded_values",
                        "message": "Magic number without explanation",
                        "value": match.group(1),
                    }
                )
        return results

    @staticmethod
    def _check_slow_tests(content: str) -> list[dict[str, Any]]:
        """Detect sleep calls that slow down tests."""
        results: list[dict[str, Any]] = []
        for match in re.finditer(r"time\.sleep\((\d+(?:\.\d+)?)\)", content):
            delay = float(match.group(1))
            if delay > 1.0:
                results.append(
                    {
                        "type": "slow_test",
                        "message": f"Unnecessary delay of {delay}s found",
                        "duration": delay,
                    }
                )
        return results

    @staticmethod
    def _check_assertion_quality(content: str) -> list[dict[str, Any]]:
        """Detect tests without assertions and tests with too many assertions."""
        results: list[dict[str, Any]] = []
        test_funcs = list(
            re.finditer(
                r"def\s+(test_\w+)\s*\([^)]*\):(.*?)(?=\ndef|\Z)", content, re.DOTALL
            )
        )
        for match in test_funcs:
            func_name = match.group(1)
            func_body = match.group(2)
            if not re.search(r"\bassert\b|\.assert_", func_body):
                results.append(
                    {
                        "type": "no_assertions",
                        "message": f"Test '{func_name}' has no assertions",
                        "function": func_name,
                    }
                )
            else:
                assert_count = len(re.findall(r"\bassert\b", func_body))
                if assert_count > MIN_EDGE_CASES:
                    results.append(
                        {
                            "type": "multiple_concerns",
                            "message": (
                                f"Test has {assert_count} assertions - too many"
                            ),
                            "assertion_count": assert_count,
                        }
                    )
        return results

    @staticmethod
    def _check_bare_excepts(content: str) -> list[dict[str, Any]]:
        """Detect bare except clauses that swallow all exceptions."""
        if re.search(r"except\s*:", content):
            return [
                {
                    "type": "exception_swallowing",
                    "message": "Bare except clause catches all exceptions",
                }
            ]
        return []

    def analyze_test_data_management(
        self, context: Any, file_path: str = ""
    ) -> dict[str, Any]:
        """Analyze test data setup and management patterns."""
        content = context.get_file_content(file_path)

        fixture_count = len(re.findall(r"@pytest\.fixture", content))
        fixtures_with_docs = len(
            re.findall(
                r'@pytest\.fixture.*?\n\s*def\s+\w+.*?:\s*"""',
                content,
                re.DOTALL,
            )
        )
        fixtures_with_cleanup = len(
            re.findall(r"yield.*?(?:cleanup|close|teardown)", content, re.DOTALL)
        )

        fixture_quality = {
            "total_fixtures": fixture_count,
            "documented": fixtures_with_docs,
            "with_cleanup": fixtures_with_cleanup,
            "quality_score": (fixtures_with_docs + fixtures_with_cleanup)
            / (fixture_count * 2)
            if fixture_count > 0
            else 0.0,
        }

        factory_usage = bool(
            re.search(r"Factory\.(create|build|create_batch)", content)
        )

        hardcoded_data = []
        test_funcs = re.finditer(r"def\s+test_\w+.*?(?=\ndef|\Z)", content, re.DOTALL)
        for match in test_funcs:
            func_body = match.group(0)
            dict_literals = re.finditer(r"\{[^}]{50,}\}", func_body, re.DOTALL)
            for dict_match in dict_literals:
                if dict_match.group(0).count(":") >= MIN_COMPLEX_ASSERTIONS:
                    hardcoded_data.append(
                        {
                            "type": "dict_literal",
                            "size": dict_match.group(0).count(":"),
                        }
                    )

        has_database_fixture = bool(
            re.search(r"@pytest\.fixture.*?database", content, re.DOTALL)
        )
        has_cleanup = bool(re.search(r"\bcleanup\b|\bdrop\b|\bdelete\b", content))

        return {
            "fixture_quality": fixture_quality,
            "factory_usage": factory_usage,
            "hardcoded_data": hardcoded_data,
            "data_isolation": {
                "has_database_fixtures": has_database_fixture,
                "has_cleanup": has_cleanup,
            },
        }

    def analyze_mock_usage(self, context: Any, file_path: str = "") -> dict[str, Any]:
        """Analyze mock and stub usage patterns."""
        content = context.get_file_content(file_path)

        mock_patterns = []
        if re.search(r"Mock\(\)", content):
            mock_patterns.append("unittest.mock")
        if re.search(r"@patch", content):
            mock_patterns.append("patch_decorator")
        if re.search(r"MagicMock", content):
            mock_patterns.append("magic_mock")

        over_mocking = []
        test_funcs = re.finditer(
            r"def\s+(test_\w+)\s*\([^)]*\):(.*?)(?=\ndef|\Z)",
            content,
            re.DOTALL,
        )
        for match in test_funcs:
            func_name = match.group(1)
            func_full = match.group(0)
            patch_matches = re.findall(r"patch\(['\"][\w.]+['\"]", func_full)
            patch_count = len(patch_matches)
            if patch_count >= MIN_COMPLEX_ASSERTIONS:
                over_mocking.append(
                    {
                        "function": func_name,
                        "patch_count": patch_count,
                    }
                )

        mock_verifications = len(
            re.findall(r"\.assert_called|\.assert_not_called", content)
        )
        mock_creation = len(re.findall(r"Mock\(|MagicMock\(|@patch", content))
        verification_ratio = (
            mock_verifications / mock_creation if mock_creation > 0 else 0.0
        )

        spy_usage = bool(re.search(r"patch\.object", content))

        return {
            "mock_patterns": mock_patterns,
            "over_mocking": over_mocking,
            "verification_quality": {
                "verification_count": mock_verifications,
                "mock_count": mock_creation,
                "ratio": verification_ratio,
            },
            "spy_usage": spy_usage,
        }
