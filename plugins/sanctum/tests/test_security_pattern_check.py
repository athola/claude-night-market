# ruff: noqa: D101,D102,D103,PLR2004,E501
"""Tests for security_pattern_check hook.

Tests context-aware security pattern detection that distinguishes
between actual code and documentation examples.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

HOOK_PATH = Path(__file__).resolve().parents[1] / "hooks" / "security_pattern_check.py"

# Pattern builders to construct test strings without triggering hooks
# These are used to test security detection, NOT to bypass it
PATTERNS = {
    "eval_call": lambda: "ev" + "al(user_input)",
    "exec_call": lambda: "ex" + "ec(code_string)",
    "os_system": lambda: "os.sys" + "tem(command)",
    "shell_mode": lambda: "she" + "ll=True",
    "pkl_load": lambda: "pi" + "ckle.load(file)",
    "eval_upper": lambda: "EV" + "AL(user_input)",
    "eval_js": lambda: "ev" + "al(userCode)",
}


def run_hook(tool_name: str, tool_input: dict) -> tuple[int, str, str]:
    """Run the security pattern check hook and return results."""
    input_data = json.dumps({"tool_name": tool_name, "tool_input": tool_input})
    result = subprocess.run(
        [sys.executable, str(HOOK_PATH)],
        input=input_data,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode, result.stdout, result.stderr


class TestSecurityPatternCheck:
    """Test suite for security pattern detection."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_detects_eval_in_python_code(self) -> None:
        """Given dynamic code evaluation in Python file, returns security warning."""
        content = f"result = {PATTERNS['eval_call']()}"
        returncode, _, stderr = run_hook(
            "Write", {"file_path": "app.py", "content": content}
        )
        assert returncode == 2
        assert "dynamic_code_evaluation" in stderr

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_detects_exec_in_python_code(self) -> None:
        """Given dynamic code execution in Python file, returns security warning."""
        content = PATTERNS["exec_call"]()
        returncode, _, stderr = run_hook(
            "Write", {"file_path": "runner.py", "content": content}
        )
        assert returncode == 2
        assert "dynamic_code_execution" in stderr

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_detects_os_system_in_python(self) -> None:
        """Given system call in Python file, returns security warning."""
        content = PATTERNS["os_system"]()
        returncode, _, stderr = run_hook(
            "Write", {"file_path": "util.py", "content": content}
        )
        assert returncode == 2
        assert "os_system_call" in stderr

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_detects_shell_true_in_subprocess(self) -> None:
        """Given subprocess with unsafe mode, returns warning."""
        content = f"subprocess.run(cmd, {PATTERNS['shell_mode']()})"
        returncode, _, stderr = run_hook(
            "Write", {"file_path": "executor.py", "content": content}
        )
        assert returncode == 2
        assert "subprocess_shell_mode" in stderr

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_detects_deserialization_pattern(self) -> None:
        """Given unsafe deserialization, returns security warning."""
        content = f"data = {PATTERNS['pkl_load']()}"
        returncode, _, stderr = run_hook(
            "Write", {"file_path": "loader.py", "content": content}
        )
        assert returncode == 2
        assert "deserialization" in stderr

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_allows_pattern_in_docs_with_warning_context(self) -> None:
        """Given pattern in docs with warning context, allows it."""
        ev = PATTERNS["eval_call"]()
        content = f"## Security Warning\nDo not use {ev} as it is unsafe.\n# BAD"
        returncode, _, _ = run_hook(
            "Write", {"file_path": "docs/security.md", "content": content}
        )
        assert returncode == 0

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_allows_pattern_with_avoid_context(self) -> None:
        """Given pattern near 'avoid' keyword, allows it in docs."""
        pattern = PATTERNS["os_system"]()
        content = f"Avoid using {pattern} as it is vulnerable to injection."
        returncode, _, _ = run_hook(
            "Write", {"file_path": "README.md", "content": content}
        )
        assert returncode == 0

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_allows_pattern_with_bad_example_context(self) -> None:
        """Given pattern in 'bad' example context, allows it in docs."""
        pattern = PATTERNS["os_system"]()
        content = f"# Bad example - never do this:\n```python\n{pattern}\n```"
        returncode, _, _ = run_hook(
            "Write", {"file_path": "examples/unsafe.md", "content": content}
        )
        assert returncode == 0

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_allows_pattern_with_dont_context(self) -> None:
        """Given pattern with "don't" nearby, allows it in docs."""
        pattern = PATTERNS["shell_mode"]()
        content = f"Don't use {pattern} when accepting user input."
        returncode, _, _ = run_hook(
            "Write", {"file_path": "guide.md", "content": content}
        )
        assert returncode == 0

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_ignores_pattern_in_wrong_file_type(self) -> None:
        """Given Python pattern in non-Python file, ignores it."""
        content = f"subprocess.run(cmd, {PATTERNS['shell_mode']()})"
        returncode, _, _ = run_hook(
            "Write", {"file_path": "config.yaml", "content": content}
        )
        assert returncode == 0

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_detects_eval_in_javascript(self) -> None:
        """Given dynamic code in JS file, returns security warning."""
        content = f"const result = {PATTERNS['eval_js']()};"
        returncode, _, stderr = run_hook(
            "Write", {"file_path": "script.js", "content": content}
        )
        assert returncode == 2
        assert "dynamic_code_evaluation" in stderr

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_checks_edit_new_string(self) -> None:
        """Given Edit tool with unsafe pattern, returns warning."""
        pattern = PATTERNS["exec_call"]()
        tool_input = {
            "file_path": "script.py",
            "old_string": "pass",
            "new_string": pattern,
        }
        returncode, _, stderr = run_hook("Edit", tool_input)
        assert returncode == 2
        assert "dynamic_code_execution" in stderr

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_allows_safe_edit(self) -> None:
        """Given Edit tool with safe pattern, allows it."""
        tool_input = {
            "file_path": "script.py",
            "old_string": "pass",
            "new_string": "print('hello')",
        }
        returncode, _, _ = run_hook("Edit", tool_input)
        assert returncode == 0

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_checks_multi_edit_combined(self) -> None:
        """Given MultiEdit with unsafe pattern, returns warning."""
        pattern = PATTERNS["eval_call"]()
        tool_input = {
            "file_path": "app.py",
            "edits": [
                {"old_string": "a", "new_string": "b"},
                {"old_string": "c", "new_string": pattern},
            ],
        }
        returncode, _, stderr = run_hook("MultiEdit", tool_input)
        assert returncode == 2
        assert "dynamic_code_evaluation" in stderr

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_allows_safe_multi_edit(self) -> None:
        """Given MultiEdit with safe patterns, allows it."""
        tool_input = {
            "file_path": "app.py",
            "edits": [
                {"old_string": "a", "new_string": "b"},
                {"old_string": "c", "new_string": "d"},
            ],
        }
        returncode, _, _ = run_hook("MultiEdit", tool_input)
        assert returncode == 0

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_ignores_non_write_tools(self) -> None:
        """Given Read tool, exits cleanly without checking."""
        returncode, _, _ = run_hook("Read", {"file_path": "app.py"})
        assert returncode == 0

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_handles_empty_content(self) -> None:
        """Given empty content, exits cleanly."""
        returncode, _, _ = run_hook("Write", {"file_path": "empty.py", "content": ""})
        assert returncode == 0

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_handles_missing_file_path(self) -> None:
        """Given missing file_path, exits cleanly."""
        pattern = PATTERNS["eval_call"]()
        returncode, _, _ = run_hook("Write", {"content": pattern})
        assert returncode == 0

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_handles_invalid_json_input(self) -> None:
        """Given invalid JSON input, exits cleanly."""
        result = subprocess.run(
            [sys.executable, str(HOOK_PATH)],
            input="not valid json",
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_case_insensitive_pattern_matching(self) -> None:
        """Given mixed case pattern, still detects it."""
        content = f"result = {PATTERNS['eval_upper']()}"
        returncode, _, stderr = run_hook(
            "Write", {"file_path": "app.py", "content": content}
        )
        assert returncode == 2
        assert "dynamic_code_evaluation" in stderr


class TestDocumentationFileDetection:
    """Test the is_documentation_file helper logic."""

    @pytest.mark.unit
    def test_recognizes_markdown_files(self) -> None:
        """Given .md file with negative context, treats as documentation."""
        pattern = PATTERNS["eval_call"]()
        content = f"Never use {pattern}"
        returncode, _, _ = run_hook(
            "Write", {"file_path": "notes.md", "content": content}
        )
        assert returncode == 0

    @pytest.mark.unit
    def test_recognizes_rst_files(self) -> None:
        """Given .rst file with negative context, treats as documentation."""
        pattern = PATTERNS["eval_call"]()
        content = f"Warning: avoid using {pattern}"
        returncode, _, _ = run_hook(
            "Write", {"file_path": "guide.rst", "content": content}
        )
        assert returncode == 0

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_recognizes_docs_directory(self) -> None:
        """Given file in docs directory with negative context, allows it."""
        pattern = PATTERNS["eval_call"]()
        content = f"This is insecure: {pattern}"
        returncode, _, _ = run_hook(
            "Write", {"file_path": "docs/api.py", "content": content}
        )
        assert returncode == 0

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_recognizes_examples_directory(self) -> None:
        """Given file in examples directory with negative context, allows it."""
        pattern = PATTERNS["os_system"]()
        content = f"# bad example: {pattern}"
        returncode, _, _ = run_hook(
            "Write", {"file_path": "examples/demo.py", "content": content}
        )
        assert returncode == 0


class TestCodeBlockHandling:
    """Test code block detection in markdown."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_pattern_in_code_block_with_context_allowed(self) -> None:
        """Given pattern in code block with negative context, allows it."""
        pattern = PATTERNS["os_system"]()
        content = f"## Bad Practice\nThis is an unsafe pattern to avoid:\n```python\n{pattern}\n```"
        returncode, _, _ = run_hook(
            "Write", {"file_path": "guide.md", "content": content}
        )
        assert returncode == 0

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_pattern_in_code_block_without_context_flags(self) -> None:
        """Given pattern in code block without negative context, may flag."""
        pattern = "os.sys" + 'tem("ls -la")'
        content = f"## Example\nHere is how:\n```python\n{pattern}\n```"
        returncode, _, _ = run_hook(
            "Write", {"file_path": "tutorial.md", "content": content}
        )
        assert returncode == 2
