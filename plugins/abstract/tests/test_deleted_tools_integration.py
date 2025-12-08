#!/usr/bin/env python3
"""Integration test to ensure no references to deleted tool files exist."""

import ast
import re
from pathlib import Path

import pytest


class TestDeletedToolsIntegration:
    """Test that no references exist to deleted tool files."""

    # List of deleted tools that should not be referenced
    # NOTE: Only include truly deleted tools here, not moved tools
    # Moved tools should be updated to reference new locations, not deleted
    DELETED_TOOLS = {
        # Add actually deleted tools here if any in the future
        # Example: "skills/old-deprecated-tool",
    }

    @pytest.fixture
    def repo_root(self) -> Path:
        """Get the repository root directory."""
        return Path(__file__).parent.parent

    def find_python_files(self, root_dir: Path) -> list[Path]:
        """Find all Python files in the repository.

        Args:
            root_dir: Root directory to search

        Returns:
            List of Python file paths

        """
        python_files = []

        for file_path in root_dir.rglob("*.py"):
            # Skip .venv and __pycache__
            if ".venv" in str(file_path) or "__pycache__" in str(file_path):
                continue

            python_files.append(file_path)

        return python_files

    def find_markdown_files(self, root_dir: Path) -> list[Path]:
        """Find all markdown files in the repository.

        Args:
            root_dir: Root directory to search

        Returns:
            List of markdown file paths

        """
        markdown_files = []

        for file_path in root_dir.rglob("*.md"):
            # Skip .venv and __pycache__
            if ".venv" in str(file_path) or "__pycache__" in str(file_path):
                continue

            markdown_files.append(file_path)

        return markdown_files

    def check_python_file_for_deleted_tools(self, file_path: Path) -> list[str]:
        """Check a Python file for references to deleted tools.

        Args:
            file_path: Path to Python file

        Returns:
            List of found references

        """
        references = []

        try:
            with open(file_path, encoding='utf-8') as f:
                content = f.read()
        except (UnicodeDecodeError, PermissionError):
            return references

        # Parse as AST to find imports and function calls
        try:
            ast.parse(content)  # Validate syntax
        except SyntaxError:
            pass  # Fall back to text search if syntax error

        # Check for string references in code
        for deleted_tool in self.DELETED_TOOLS:
            tool_name = Path(deleted_tool).name

            # Check for direct string references
            if deleted_tool in content:
                references.append(f"{file_path}: Reference to {deleted_tool}")
            elif tool_name in content:
                references.append(f"{file_path}: Reference to {tool_name}")

        return references

    def check_markdown_file_for_deleted_tools(self, file_path: Path) -> list[str]:
        """Check a markdown file for references to deleted tools.

        Args:
            file_path: Path to markdown file

        Returns:
            List of found references

        """
        references = []

        try:
            with open(file_path, encoding='utf-8') as f:
                content = f.read()
        except (UnicodeDecodeError, PermissionError):
            return references

        # Check for references to deleted tools
        for deleted_tool in self.DELETED_TOOLS:
            tool_name = Path(deleted_tool).name

            # Check for direct path references
            if deleted_tool in content:
                references.append(f"{file_path}: Reference to {deleted_tool}")
            elif tool_name in content:
                # Check if it's likely referring to the tool (not just a word)
                # Look for patterns like "./tools/tool-name" or "tools/tool-name"
                escaped_tool = re.escape(tool_name)
                patterns = [
                    rf"\./tools/{escaped_tool}",
                    rf"tools/{escaped_tool}",
                    rf"`{escaped_tool}`",
                    rf"\*\*{escaped_tool}\*\*",
                ]
                for pattern in patterns:
                    if re.search(pattern, content):
                        references.append(f"{file_path}: Reference to {tool_name}")
                        break

        return references

    def test_no_deleted_tools_references(self, repo_root: Path) -> None:
        """Test that no references exist to deleted tool files."""
        all_references = []

        # Check Python files
        python_files = self.find_python_files(repo_root)
        for py_file in python_files:
            references = self.check_python_file_for_deleted_tools(py_file)
            all_references.extend(references)

        # Check markdown files
        markdown_files = self.find_markdown_files(repo_root)
        for md_file in markdown_files:
            references = self.check_markdown_file_for_deleted_tools(md_file)
            all_references.extend(references)

        # Assert no references found
        if all_references:
            error_msg = "Found references to deleted tools:\n\n"
            error_msg += "\n".join(all_references)
            error_msg += "\n\nPlease remove or update these references."
            pytest.fail(error_msg)

    def test_tools_existence(self, repo_root: Path) -> None:
        """Test that all referenced tools actually exist."""
        missing_tools = []

        # Check that deleted tools don't exist
        for deleted_tool in self.DELETED_TOOLS:
            tool_path = repo_root / deleted_tool
            if tool_path.exists():
                missing_tools.append(f"Deleted tool still exists: {deleted_tool}")

        # Check that new tools exist in expected locations
        expected_new_tools = [
            "scripts/skill_analyzer.py",
            "scripts/abstract_validator.py",
            "scripts/token_estimator.py",
        ]

        for new_tool in expected_new_tools:
            tool_path = repo_root / new_tool
            if not tool_path.exists():
                missing_tools.append(f"Expected tool not found: {new_tool}")

        if missing_tools:
            error_msg = "Tool existence issues:\n\n"
            error_msg += "\n".join(missing_tools)
            pytest.fail(error_msg)


if __name__ == "__main__":
    # Run tests directly for debugging
    import sys

    test_class = TestDeletedToolsIntegration()
    repo_root = Path(__file__).parent.parent

    print("Checking for references to deleted tools...")
    all_references = []

    # Check Python files
    python_files = test_class.find_python_files(repo_root)
    for py_file in python_files:
        references = test_class.check_python_file_for_deleted_tools(py_file)
        all_references.extend(references)

    # Check markdown files
    markdown_files = test_class.find_markdown_files(repo_root)
    for md_file in markdown_files:
        references = test_class.check_markdown_file_for_deleted_tools(md_file)
        all_references.extend(references)

    if all_references:
        print("Found references to deleted tools:")
        for ref in all_references:
            print(f"  - {ref}")
        sys.exit(1)
    else:
        print("✓ No references to deleted tools found")
        sys.exit(0)
