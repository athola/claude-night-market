#!/usr/bin/env python3
"""Tests for the lint_suppression_guard PreToolUse hook.

Feature: Block inline lint suppression directives

As a codebase maintainer
I want to prevent inline lint suppression comments from being added
So that suppressions are configured in project config files
(pyproject.toml, .eslintrc, Cargo.toml) rather than hidden inline.
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

# Load the hook module dynamically
_HOOK_PATH = Path(__file__).parents[3] / "hooks" / "noqa_guard.py"
_spec = importlib.util.spec_from_file_location("noqa_guard", _HOOK_PATH)
assert _spec is not None
assert _spec.loader is not None
_mod = importlib.util.module_from_spec(_spec)
sys.modules["noqa_guard"] = _mod
_spec.loader.exec_module(_mod)

check_for_suppressions = _mod.check_for_suppressions


class TestPythonSuppressions:
    """Detect Python-specific lint suppression patterns."""

    @pytest.mark.unit
    def test_detects_bare_noqa(self) -> None:
        """Scenario: bare # noqa is detected."""
        hits = check_for_suppressions("x = 1  # noqa\n")
        assert len(hits) == 1
        assert "noqa" in hits[0].lower()

    @pytest.mark.unit
    def test_detects_noqa_with_codes(self) -> None:
        """Scenario: # noqa: E501 is detected."""
        hits = check_for_suppressions("long_line = 1  # noqa: E501, S101\n")
        assert len(hits) == 1

    @pytest.mark.unit
    def test_detects_type_ignore(self) -> None:
        """Scenario: # type: ignore is detected."""
        hits = check_for_suppressions('x: int = "bad"  # type: ignore\n')
        assert len(hits) == 1
        assert "type: ignore" in hits[0].lower()

    @pytest.mark.unit
    def test_detects_type_ignore_with_codes(self) -> None:
        """Scenario: # type: ignore[assignment] is detected."""
        hits = check_for_suppressions('x: int = "bad"  # type: ignore[assignment]\n')
        assert len(hits) == 1

    @pytest.mark.unit
    def test_detects_pylint_disable(self) -> None:
        """Scenario: # pylint: disable is detected."""
        hits = check_for_suppressions("x = 1  # pylint: disable=C0114\n")
        assert len(hits) == 1
        assert "pylint" in hits[0].lower()


class TestRustSuppressions:
    """Detect Rust-specific lint suppression patterns."""

    @pytest.mark.unit
    def test_detects_allow_attribute(self) -> None:
        """Scenario: #[allow(unused)] is detected."""
        hits = check_for_suppressions("#[allow(unused_variables)]\nlet x = 1;\n")
        assert len(hits) == 1
        assert "allow" in hits[0].lower()

    @pytest.mark.unit
    def test_detects_clippy_allow(self) -> None:
        """Scenario: #[allow(clippy::...)] is detected."""
        hits = check_for_suppressions("#[allow(clippy::needless_return)]\n")
        assert len(hits) == 1


class TestJavaScriptSuppressions:
    """Detect JavaScript/TypeScript lint suppression patterns."""

    @pytest.mark.unit
    def test_detects_eslint_disable_next_line(self) -> None:
        """Scenario: // eslint-disable-next-line is detected."""
        hits = check_for_suppressions(
            "// eslint-disable-next-line no-console\nconsole.log(x);\n"
        )
        assert len(hits) == 1
        assert "eslint" in hits[0].lower()

    @pytest.mark.unit
    def test_detects_eslint_disable_line(self) -> None:
        """Scenario: inline eslint-disable comment is detected."""
        hits = check_for_suppressions(
            "console.log(x); // eslint-disable-line no-console\n"
        )
        assert len(hits) == 1

    @pytest.mark.unit
    def test_detects_ts_ignore(self) -> None:
        """Scenario: @ts-ignore is detected."""
        hits = check_for_suppressions("// @ts-ignore\nconst x: number = 'bad';\n")
        assert len(hits) == 1

    @pytest.mark.unit
    def test_detects_ts_expect_error(self) -> None:
        """Scenario: @ts-expect-error is detected."""
        hits = check_for_suppressions("// @ts-expect-error\nconst x: number = 'bad';\n")
        assert len(hits) == 1


class TestGoSuppressions:
    """Detect Go lint suppression patterns."""

    @pytest.mark.unit
    def test_detects_nolint(self) -> None:
        """Scenario: //nolint is detected."""
        hits = check_for_suppressions("func main() {} //nolint:errcheck\n")
        assert len(hits) == 1
        assert "nolint" in hits[0].lower()


class TestCleanCode:
    """Verify that clean code passes without false positives."""

    @pytest.mark.unit
    def test_clean_python_passes(self) -> None:
        """Scenario: normal Python code passes."""
        code = "x = 1\ny = 2\nz = x + y\n"
        hits = check_for_suppressions(code)
        assert hits == []

    @pytest.mark.unit
    def test_clean_rust_passes(self) -> None:
        """Scenario: normal Rust code passes."""
        code = "fn main() {\n    let x = 1;\n}\n"
        hits = check_for_suppressions(code)
        assert hits == []

    @pytest.mark.unit
    def test_clean_js_passes(self) -> None:
        """Scenario: normal JavaScript code passes."""
        code = "const x = 1;\nfunction foo() { return x; }\n"
        hits = check_for_suppressions(code)
        assert hits == []

    @pytest.mark.unit
    def test_multiple_suppressions(self) -> None:
        """Scenario: multiple different suppressions are all found."""
        code = 'a = 1  # noqa: E501\nb = 2\nc: int = "x"  # type: ignore\n'
        hits = check_for_suppressions(code)
        assert len(hits) == 2


class TestHookIntegration:
    """Integration tests running the hook as a subprocess."""

    @pytest.mark.unit
    def test_blocks_edit_with_noqa(self) -> None:
        """Scenario: Edit with noqa is blocked."""
        env = {
            **os.environ,
            "CLAUDE_TOOL_NAME": "Edit",
            "CLAUDE_TOOL_INPUT": json.dumps(
                {
                    "file_path": "/tmp/test.py",  # noqa: S108
                    "old_string": "x = 1",
                    "new_string": "x = 1  # noqa: E501",
                }
            ),
        }
        result = subprocess.run(
            [sys.executable, str(_HOOK_PATH)],
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert output["hookSpecificOutput"]["permissionDecision"] == "deny"

    @pytest.mark.unit
    def test_blocks_edit_with_type_ignore(self) -> None:
        """Scenario: Edit with type: ignore is blocked."""
        env = {
            **os.environ,
            "CLAUDE_TOOL_NAME": "Edit",
            "CLAUDE_TOOL_INPUT": json.dumps(
                {
                    "file_path": "/tmp/test.py",  # noqa: S108
                    "old_string": "x = 1",
                    "new_string": 'x: int = "bad"  # type: ignore',
                }
            ),
        }
        result = subprocess.run(
            [sys.executable, str(_HOOK_PATH)],
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert output["hookSpecificOutput"]["permissionDecision"] == "deny"

    @pytest.mark.unit
    def test_allows_clean_edit(self) -> None:
        """Scenario: clean Edit passes."""
        env = {
            **os.environ,
            "CLAUDE_TOOL_NAME": "Edit",
            "CLAUDE_TOOL_INPUT": json.dumps(
                {
                    "file_path": "/tmp/test.py",  # noqa: S108
                    "old_string": "x = 1",
                    "new_string": "x = 2",
                }
            ),
        }
        result = subprocess.run(
            [sys.executable, str(_HOOK_PATH)],
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert output == {}

    @pytest.mark.unit
    def test_blocks_write_with_suppression(self) -> None:
        """Scenario: Write with lint suppression is blocked."""
        env = {
            **os.environ,
            "CLAUDE_TOOL_NAME": "Write",
            "CLAUDE_TOOL_INPUT": json.dumps(
                {
                    "file_path": "/tmp/test.py",  # noqa: S108
                    "content": "import os  # noqa: F401\nx = 1\n",
                }
            ),
        }
        result = subprocess.run(
            [sys.executable, str(_HOOK_PATH)],
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert output["hookSpecificOutput"]["permissionDecision"] == "deny"

    @pytest.mark.unit
    def test_ignores_non_edit_write_tools(self) -> None:
        """Scenario: non-Edit/Write tools pass through."""
        env = {
            **os.environ,
            "CLAUDE_TOOL_NAME": "Bash",
            "CLAUDE_TOOL_INPUT": json.dumps(
                {
                    "command": "echo '# noqa'",
                }
            ),
        }
        result = subprocess.run(
            [sys.executable, str(_HOOK_PATH)],
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert output == {}

    @pytest.mark.unit
    def test_crash_proof_on_bad_input(self) -> None:
        """Scenario: malformed input fails open."""
        env = {
            **os.environ,
            "CLAUDE_TOOL_NAME": "Edit",
            "CLAUDE_TOOL_INPUT": "not-valid-json{{{",
        }
        result = subprocess.run(
            [sys.executable, str(_HOOK_PATH)],
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert output == {}
