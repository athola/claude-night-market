#!/usr/bin/env python3
"""Test Generation Tool.

Generates test scaffolding following TDD/BDD principles.
Part of the test-updates skill tooling suite.

Usage:
    python test_generator.py --source /path/to/source.py
    python test_generator.py --module my_module
    python test_generator.py --template bdd --output test_new_feature.py
"""

from __future__ import annotations

import argparse
import ast
import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class TestStyle(Enum):
    """BDD test styles."""

    PYTEST_BDD = "pytest_bdd"
    DOCSTRING_BDD = "docstring_bdd"
    GHERKIN = "gherkin"


@dataclass
class TestConfig:
    """Configuration for test generation."""

    style: TestStyle
    output_path: Path | None = None
    include_fixtures: bool = True
    include_edge_cases: bool = True
    include_error_cases: bool = True


class TestGenerator:
    """Generates test scaffolding from source code analysis."""

    def __init__(self, config: TestConfig) -> None:
        """Initialize the test generator."""
        self.config = config

    def generate_from_source(self, source_path: Path) -> str:
        """Generate test scaffolding from source file."""
        with open(source_path) as f:
            source_code = f.read()

        tree = ast.parse(source_code)
        module_name = source_path.stem

        # Extract functions and classes
        functions = self._extract_functions(tree)
        classes = self._extract_classes(tree)

        # Generate test content
        test_content = self._generate_test_header(module_name)

        if self.config.include_fixtures:
            test_content += self._generate_fixtures()

        # Generate function tests
        for func in functions:
            test_content += self._generate_function_test(func)

        # Generate class tests
        for cls in classes:
            test_content += self._generate_class_test(cls)

        return test_content

    def _extract_functions(self, tree: ast.AST) -> list[ast.FunctionDef]:
        """Extract function definitions from AST."""
        return [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef) and not node.name.startswith("_")
        ]

    def _extract_classes(self, tree: ast.AST) -> list[ast.ClassDef]:
        """Extract class definitions from AST."""
        return [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]

    def _generate_test_header(self, module_name: str) -> str:
        """Generate test file header."""
        if self.config.style == TestStyle.PYTEST_BDD:
            return f'''"""
BDD-style tests for {module_name} module.

Generated using test-updates skill following TDD principles.
"""

import pytest
from {module_name} import *

'''
        if self.config.style == TestStyle.DOCSTRING_BDD:
            return f'''"""
Tests for {module_name} module.

Generated using test-updates skill following BDD principles.
"""

from {module_name} import *

'''
        # GHERKIN
        return f'''"""
Feature: {module_name} functionality

Generated using test-updates skill following BDD principles.
"""

from behave import given, when, then
from {module_name} import *

'''

    def _generate_fixtures(self) -> str:
        """Generate common test fixtures."""
        if self.config.style == TestStyle.GHERKIN:
            return '''
@given('a configured context')
def step_given_configured_context(context):
    """Setup test context."""
    context.configured = True

@when('an action is performed')
def step_when_action_performed(context):
    """Perform the test action."""
    context.result = perform_action(context)

@then('the expected outcome occurs')
def step_then_expected_outcome(context):
    """Verify the outcome."""
    assert context.result is not None
'''

        return '''
@pytest.fixture
def test_context():
    """Common test context fixture."""
    return {{"setup": True, "data": {}}}

'''

    def _generate_function_test(self, func: ast.FunctionDef) -> str:
        """Generate test for a function."""
        params = self._extract_function_params(func)

        if self.config.style == TestStyle.PYTEST_BDD:
            return self._generate_pytest_bdd_test(func.name, params)
        if self.config.style == TestStyle.DOCSTRING_BDD:
            return self._generate_docstring_test(func.name, params)
        # GHERKIN
        return self._generate_gherkin_scenario(func.name, params)

    def _generate_class_test(self, cls: ast.ClassDef) -> str:
        """Generate test for a class."""
        methods = [
            node
            for node in cls.body
            if isinstance(node, ast.FunctionDef) and not node.name.startswith("_")
        ]

        test_content = f"\n\nclass Test{cls.name}:\n"
        test_content += f'    """BDD-style tests for {cls.name} class."""\n'

        if self.config.include_fixtures:
            test_content += '''
    def setup_method(self):
        """Setup test instance."""
        self.instance = CLASS_NAME()
'''.replace("CLASS_NAME", cls.name)

        for method in methods:
            test_content += f"\n    {self._generate_method_test(method, cls.name)}"

        return test_content

    def _generate_method_test(self, method: ast.FunctionDef, class_name: str) -> str:
        """Generate test for class method."""
        method_name = method.name

        if self.config.style == TestStyle.PYTEST_BDD:
            return f'''@pytest.mark.bdd
    def test_{method_name}_behavior(self):
        """
        GIVEN a configured {class_name.lower()} instance
        WHEN calling {method_name}()
        THEN it should behave as expected
        """
        # TODO: Arrange - Setup test context
        instance = {class_name}()

        # TODO: Act - Call the method
        result = instance.{method_name}()

        # TODO: Assert - Verify the outcome
        assert result is not None
'''

        if self.config.style == TestStyle.DOCSTRING_BDD:
            return f'''def test_{method_name}_behavior(self):
        """Test {method_name} method behavior.

        GIVEN a configured {class_name.lower()} instance
        WHEN calling {method_name}()
        THEN it should behave as expected
        """
        # TODO: Implement test
        pass
'''

        # GHERKIN style placeholder
        return f"# Scenario: {method_name} behavior\n"

    def _extract_function_params(self, func: ast.FunctionDef) -> list[str]:
        """Extract parameter names from function."""
        return [arg.arg for arg in func.args.args]

    def _generate_pytest_bdd_test(self, func_name: str, params: list[str]) -> str:
        """Generate pytest BDD-style test."""
        param_str = ", ".join(params) if params else ""
        setup_code = ""

        if params:
            setup_code = "\n        # TODO: Setup test parameters\n"
            for param in params:
                setup_code += (
                    f'        {param} = "test_{param}"  # TODO: Provide test value\n'
                )

        error_section = ""
        if self.config.include_error_cases:
            error_section = f"""
@pytest.mark.bdd
def test_{func_name}_with_invalid_input():
    \"""
    GIVEN invalid input parameters
    WHEN calling {func_name}({param_str})
    THEN it should raise a ValueError
    \"""{setup_code}
    with pytest.raises(ValueError):
        {func_name}({param_str})

"""

        return (
            f'''
@pytest.mark.bdd
def test_{func_name}_with_valid_input():
    """
    GIVEN valid input parameters
    WHEN calling {func_name}({param_str})
    THEN it should return the expected result
    """{setup_code}
    # TODO: Act - Call the function
    result = {func_name}({param_str})

    # TODO: Assert - Verify the outcome
    assert result is not None

'''
            + error_section
        )

    def _generate_docstring_test(self, func_name: str, params: list[str]) -> str:
        """Generate docstring BDD-style test."""
        param_str = ", ".join(params) if params else ""

        return f'''
def test_{func_name}_behavior():
    """Test {func_name} function behavior.

    GIVEN valid input parameters
    WHEN calling {func_name}({param_str})
    THEN it should return the expected result
    AND handle edge cases appropriately
    """
    # TODO: Arrange - Setup test data
    test_params = {{
        # TODO: Define test parameters
    }}

    # TODO: Act - Execute function
    result = {func_name}({param_str})

    # TODO: Assert - Verify results
    assert result is not None

'''

    def _generate_gherkin_scenario(self, func_name: str, params: list[str]) -> str:
        """Generate Gherkin scenario."""
        param_desc = " and ".join(params) if params else "required parameters"

        return f"""
  Scenario: {func_name} with valid {param_desc}
    Given a configured context with {param_desc}
    When {func_name} is called
    Then the result should be successful

"""

    def save_test_file(self, test_content: str, source_path: Path) -> Path:
        """Save generated test to appropriate location."""
        if self.config.output_path:
            output_path = self.config.output_path
        else:
            # Determine test file path
            test_dir = source_path.parent / "tests"
            test_dir.mkdir(exist_ok=True)
            output_path = test_dir / f"test_{source_path.stem}.py"

        with open(output_path, "w") as f:
            f.write(test_content)

        return output_path


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Generate test scaffolding")
    parser.add_argument("--source", type=str, help="Source file to generate tests for")
    parser.add_argument("--module", type=str, help="Module name to generate tests for")
    parser.add_argument("--output", type=str, help="Output test file path")
    parser.add_argument(
        "--style",
        choices=["pytest_bdd", "docstring_bdd", "gherkin"],
        default="pytest_bdd",
        help="Test style to generate",
    )
    parser.add_argument(
        "--no-fixtures",
        action="store_true",
        help="Skip fixture generation",
    )
    parser.add_argument(
        "--no-edge-cases",
        action="store_true",
        help="Skip edge case generation",
    )
    parser.add_argument(
        "--no-error-cases",
        action="store_true",
        help="Skip error case generation",
    )
    parser.add_argument(
        "--output-json",
        action="store_true",
        help="Output results as JSON for programmatic use",
    )

    args = parser.parse_args()

    try:
        config = TestConfig(
            style=TestStyle(args.style),
            output_path=Path(args.output) if args.output else None,
            include_fixtures=not args.no_fixtures,
            include_edge_cases=not args.no_edge_cases,
            include_error_cases=not args.no_error_cases,
        )

        generator = TestGenerator(config)

        if args.source:
            source_path = Path(args.source)
            if not source_path.exists():
                output_error(f"Source file not found: {source_path}", args)
                return

            test_content = generator.generate_from_source(source_path)
            output_path = generator.save_test_file(test_content, source_path)

            result = {
                "test_file": str(output_path),
                "source_file": str(source_path),
                "style": args.style,
                "fixtures_included": config.include_fixtures,
                "edge_cases_included": config.include_edge_cases,
                "error_cases_included": config.include_error_cases,
            }
            output_result(result, args)

        elif args.module:
            output_error("Module generation not yet implemented", args)
        else:
            parser.print_help()

    except Exception as e:
        output_error(f"Error generating tests: {e}", args)


def output_result(result: dict, args) -> None:
    """Output result in requested format."""
    if args.output_json:
        print(
            json.dumps(
                {
                    "success": True,
                    "data": result,
                },
                indent=2,
            )
        )
    else:
        print(f"Generated test file: {result.get('test_file')}")
        print(f"Style: {result.get('style')}")


def output_error(message: str, args) -> None:
    """Output error in requested format."""
    if args.output_json:
        print(
            json.dumps(
                {
                    "success": False,
                    "error": message,
                },
                indent=2,
            )
        )
    else:
        print(f"Error: {message}")


if __name__ == "__main__":
    main()
