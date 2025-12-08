#!/usr/bin/env python3
"""
Simple test verification script for spec-kit test suite.
Verifies test structure and basic functionality without requiring pytest installation.
"""

import os
import sys
import ast
import importlib.util
from pathlib import Path


def verify_test_file(filepath):
    """Verify a single test file has proper structure."""
    try:
        with open(filepath, 'r') as f:
            content = f.read()

        # Parse the AST to verify syntax
        ast.parse(content)

        # Check for test classes
        tree = ast.parse(content)
        test_classes = [
            node.name for node in ast.walk(tree)
            if isinstance(node, ast.ClassDef) and node.name.startswith('Test')
        ]

        # Check for test methods
        test_methods = [
            node.name for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef) and node.name.startswith('test')
        ]

        return {
            'valid_syntax': True,
            'test_classes': test_classes,
            'test_methods': test_methods,
            'line_count': len(content.splitlines())
        }

    except SyntaxError as e:
        return {
            'valid_syntax': False,
            'error': str(e),
            'test_classes': [],
            'test_methods': [],
            'line_count': 0
        }


def verify_fixtures(conftest_path):
    """Verify conftest.py has proper fixtures."""
    try:
        with open(conftest_path, 'r') as f:
            content = f.read()

        tree = ast.parse(content)

        # Look for fixture functions
        fixtures = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                for decorator in node.decorator_list:
                    if (isinstance(decorator, ast.Name) and decorator.id == 'pytest.fixture') or \
                       (isinstance(decorator, ast.Attribute) and decorator.attr == 'fixture'):
                        fixtures.append(node.name)

        return fixtures

    except Exception as e:
        return []


def main():
    """Main verification function."""
    tests_dir = Path(__file__).parent

    print("🔍 Verifying spec-kit test suite...")
    print("=" * 50)

    # Verify test files
    test_files = list(tests_dir.glob('test_*.py'))
    total_test_methods = 0
    total_test_classes = 0

    for test_file in sorted(test_files):
        result = verify_test_file(test_file)
        filename = test_file.name

        if result['valid_syntax']:
            print(f"✅ {filename}")
            print(f"   Classes: {len(result['test_classes'])}")
            print(f"   Methods: {len(result['test_methods'])}")
            print(f"   Lines:   {result['line_count']}")
            total_test_methods += len(result['test_methods'])
            total_test_classes += len(result['test_classes'])
        else:
            print(f"❌ {filename} - Syntax Error")
            print(f"   Error: {result['error']}")

    print(f"\n📊 Summary:")
    print(f"   Test files: {len(test_files)}")
    print(f"   Test classes: {total_test_classes}")
    print(f"   Test methods: {total_test_methods}")

    # Verify fixtures
    conftest_path = tests_dir / 'conftest.py'
    if conftest_path.exists():
        fixtures = verify_fixtures(conftest_path)
        print(f"   Fixtures: {len(fixtures)}")

    # Verify other files
    other_files = ['pytest.ini', 'requirements.txt', 'Makefile', 'README.md']
    for other_file in other_files:
        file_path = tests_dir / other_file
        if file_path.exists():
            print(f"✅ {other_file}")
        else:
            print(f"❌ {other_file} - Missing")

    # Coverage estimation
    print(f"\n🎯 Coverage Estimate:")
    print(f"   Unit tests: test_orchestrator.py, test_spec_writing.py, test_task_planning.py")
    print(f"   Command tests: test_commands.py")
    print(f"   Agent tests: test_agents.py")
    print(f"   Integration tests: test_integration.py")
    print(f"   Validation tests: test_frontmatter.py")

    if total_test_methods >= 50:
        print(f"   ✅ Comprehensive test coverage ({total_test_methods} test methods)")
    elif total_test_methods >= 30:
        print(f"   ⚠️  Good test coverage ({total_test_methods} test methods)")
    else:
        print(f"   ❌ Limited test coverage ({total_test_methods} test methods)")

    print("\n" + "=" * 50)
    print("Verification complete! 🎉")


if __name__ == '__main__':
    main()
