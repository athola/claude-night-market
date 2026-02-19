#!/usr/bin/env python3
"""TDD/BDD Gate: Enforce test-first development before implementation.

This hook implements the Iron Law: NO IMPLEMENTATION WITHOUT A FAILING TEST FIRST

It fires on PreToolUse for Write/Edit operations and checks:
1. Is this an implementation file (skill, module, Python code)?
2. Does a corresponding test file exist?
3. If not, inject a reminder to write tests first

This prevents "Cargo Cult TDD" where tests are written after implementation
to validate pre-conceived solutions rather than drive design.

BDD (Behavior-Driven Development) is enforced alongside TDD:
- Tests should describe behavior in Given/When/Then format
- Test classes should have Feature docstrings
- Test methods should have Scenario docstrings
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# File type classification
# Only executable code types are gated. Markdown modules/commands are agent
# instructions validated by abstract:skills-eval, not pytest.
SKILL_FILE = "skill"
PYTHON_FILE = "python"


def _find_plugin_root(path: Path) -> Path:
    """Find the plugin root by looking for pyproject.toml or .claude-plugin."""
    plugin_root = path.parent
    while plugin_root != plugin_root.parent:
        has_pyproject = (plugin_root / "pyproject.toml").exists()
        has_plugin = (plugin_root / ".claude-plugin").exists()
        if has_pyproject or has_plugin:
            break
        plugin_root = plugin_root.parent
    return plugin_root


def _check_python_file(path: Path) -> tuple[bool, str | None]:
    """Check if a Python file is an implementation file."""
    # Exclude test files
    if path.name.startswith("test_") or path.name.endswith("_test.py"):
        return False, None
    # Exclude conftest and __init__
    if path.name in ("conftest.py", "__init__.py"):
        return False, None
    # Exclude files in tests directory
    if "tests" in path.parts:
        return False, None
    return True, PYTHON_FILE


def is_implementation_file(file_path: str) -> tuple[bool, str | None]:
    """Check if the file is an implementation file that requires tests.

    Markdown files (.md) in modules/ and commands/ directories are excluded
    because they are agent instruction documents, not executable code testable
    by pytest. Use abstract:skills-eval or abstract:test-skill for those.
    SKILL.md files are still gated as they define core skill behavior.
    """
    path = Path(file_path)

    # Skill files (SKILL.md defines core behavior — keep gated)
    if path.name == "SKILL.md":
        return True, SKILL_FILE

    # Python implementation files (in modules/, commands/, or elsewhere)
    if path.suffix == ".py":
        return _check_python_file(path)

    return False, None


def _find_skill_test(path: Path, tests_dir: Path) -> Path:
    """Find test file for a skill."""
    skill_name = path.parent.name.replace("-", "_")  # Convert hyphens to underscores
    candidates = [
        tests_dir / "unit" / "skills" / f"test_{skill_name}.py",
        tests_dir / "unit" / f"test_{skill_name}_skill.py",
        tests_dir / f"test_{skill_name}.py",
    ]
    return next((t for t in candidates if t.exists()), candidates[0])


def _find_python_test(path: Path, tests_dir: Path) -> Path:
    """Find test file for a Python implementation."""
    impl_name = path.stem
    candidates = [
        tests_dir / "unit" / f"test_{impl_name}.py",
        path.parent / f"test_{impl_name}.py",
        tests_dir / f"test_{impl_name}.py",
    ]
    return next((t for t in candidates if t.exists()), candidates[0])


def find_test_file(impl_path: str, impl_type: str) -> Path | None:
    """Find the corresponding test file for an implementation file."""
    path = Path(impl_path)
    plugin_root = _find_plugin_root(path)
    tests_dir = plugin_root / "tests"

    finders = {
        SKILL_FILE: _find_skill_test,
        PYTHON_FILE: _find_python_test,
    }

    finder = finders.get(impl_type)
    if finder:
        return finder(path, tests_dir)
    return None


def is_new_file(file_path: str) -> bool:
    """Check if the file doesn't exist yet (new implementation)."""
    return not Path(file_path).exists()


def format_tdd_bdd_reminder(impl_path: str, impl_type: str, test_path: Path) -> str:
    """Generate a TDD/BDD reminder message."""
    type_names = {
        SKILL_FILE: "skill",
        PYTHON_FILE: "Python implementation",
    }

    bdd_template = """
## BDD Test Template

```python
import pytest

class TestFeatureName:
    \"\"\"
    Feature: [Feature description]

    As a [stakeholder]
    I want [capability]
    So that [benefit]
    \"\"\"

    @pytest.mark.unit
    def test_scenario_describes_behavior(self):
        \"\"\"
        Scenario: [Clear scenario description]
        Given [initial context]
        When [action occurs]
        Then [expected outcome]
        \"\"\"
        # Arrange
        # Act
        # Assert
        pass
```
"""
    test_status = "Yes" if test_path.exists() else "NO - Write tests first!"
    template = bdd_template if not test_path.exists() else ""

    return f"""IRON LAW + BDD REMINDER

You are about to create/modify a {type_names.get(impl_type, "file")}: {impl_path}

The Iron Law states: NO IMPLEMENTATION WITHOUT A FAILING TEST FIRST

Expected test file: {test_path}
Test file exists: {test_status}

REQUIRED BEFORE IMPLEMENTATION:
1. Write a failing BDD-style test that describes the BEHAVIOR you want
2. Run the test to confirm it fails (RED phase)
3. Then write minimal implementation to make it pass (GREEN phase)
4. Refactor while keeping tests green (REFACTOR phase)
{template}
TDD/BDD Quick Reference:
- TDD: Test drives design through RED-GREEN-REFACTOR cycle
- BDD: Tests describe behavior with Given/When/Then scenarios
- Iron Law: Prevents "Cargo Cult TDD" where tests validate pre-conceived code

If tests already exist and you're extending functionality:
- Add a NEW failing test for the new behavior first
- Then implement to make it pass"""


def main():
    """Run the TDD/BDD gate check."""
    try:
        raw_input = sys.stdin.read()
        input_data = json.loads(raw_input)
    except json.JSONDecodeError:
        sys.exit(0)

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})

    # Only check Write and Edit operations
    if tool_name not in ["Write", "Edit", "MultiEdit"]:
        sys.exit(0)

    file_path = tool_input.get("file_path", "")
    if not file_path:
        sys.exit(0)

    # Check if this is an implementation file
    is_impl, impl_type = is_implementation_file(file_path)
    if not is_impl or impl_type is None:
        sys.exit(0)

    # Find corresponding test file
    test_path = find_test_file(file_path, impl_type)
    if test_path is None:
        sys.exit(0)

    # Check if test exists
    test_exists = test_path.exists()
    is_new = is_new_file(file_path)

    # If creating new implementation without tests, inject reminder
    if is_new and not test_exists:
        reminder = format_tdd_bdd_reminder(file_path, impl_type, test_path)
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "additionalContext": reminder,
            }
        }
        print(json.dumps(output))
        # Log warning
        print(
            f"[TDD/BDD Gate] New {impl_type} without tests: {file_path}",
            file=sys.stderr,
        )
        print(f"[TDD/BDD Gate] Expected test at: {test_path}", file=sys.stderr)
        sys.exit(2)  # Continue but with warning

    # If modifying existing file, still remind about TDD
    if not test_exists:
        msg = f"TDD/BDD Reminder: No test file found at {test_path}. Consider tests."
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "additionalContext": msg,
            }
        }
        print(json.dumps(output))
        sys.exit(2)

    # Tests exist - allow operation
    sys.exit(0)


if __name__ == "__main__":
    main()
