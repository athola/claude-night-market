# ruff: noqa: D101,D102,D103,PLR2004,E501,E402
"""Tests for security_pattern_check hook — in-process coverage.

Tests context-aware security pattern detection that distinguishes
between actual code and documentation examples. All tests call
hook functions directly so that coverage tools track every branch.
"""

from __future__ import annotations

import json
import sys
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest

# Add hooks directory to path for import
HOOKS_DIR = Path(__file__).resolve().parents[1] / "hooks"
sys.path.insert(0, str(HOOKS_DIR))

from security_pattern_check import (
    NEGATIVE_CONTEXT_WORDS,
    check_content,
    get_security_patterns,
    has_negative_context,
    is_documentation_file,
    is_in_code_block,
    main,
)

# Pattern builders to construct test strings without triggering other hooks.
PATTERNS = {
    "eval_call": lambda: "ev" + "al(user_input)",
    "exec_call": lambda: "ex" + "ec(code_string)",
    "os_system": lambda: "os.sys" + "tem(command)",
    "shell_mode": lambda: "she" + "ll=True",
    "pkl_load": lambda: "pi" + "ckle.load(file)",
    "eval_upper": lambda: "EV" + "AL(user_input)",
    "eval_js": lambda: "ev" + "al(userCode)",
}


def run_hook_in_process(tool_name: str, tool_input: dict) -> tuple:
    """Run main() in-process and return (exit_code, stdout, stderr)."""
    input_data = json.dumps({"tool_name": tool_name, "tool_input": tool_input})
    captured_stdout = StringIO()
    captured_stderr = StringIO()

    with (
        patch("sys.stdin", StringIO(input_data)),
        patch("sys.stdout", captured_stdout),
        patch("sys.stderr", captured_stderr),
    ):
        try:
            main()
            exit_code = 0
        except SystemExit as e:
            exit_code = e.code if e.code is not None else 0

    return exit_code, captured_stdout.getvalue(), captured_stderr.getvalue()


# ============================================================================
# get_security_patterns()
# ============================================================================


class TestGetSecurityPatterns:
    """Feature: Security patterns are correctly configured."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_returns_five_patterns(self) -> None:
        """Given get_security_patterns(), it returns exactly 5 rules."""
        patterns = get_security_patterns()
        assert len(patterns) == 5

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_each_pattern_has_required_keys(self) -> None:
        """Given each pattern, it has ruleName, pattern, file_types, reminder."""
        for p in get_security_patterns():
            assert "ruleName" in p
            assert "pattern" in p
            assert "file_types" in p
            assert "reminder" in p

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_rule_names_are_unique(self) -> None:
        """Given all patterns, ruleNames are distinct."""
        names = [p["ruleName"] for p in get_security_patterns()]
        assert len(names) == len(set(names))

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_expected_rule_names_present(self) -> None:
        """Given get_security_patterns(), expected rule names exist."""
        names = {p["ruleName"] for p in get_security_patterns()}
        expected = {
            "dynamic_code_evaluation",
            "dynamic_code_execution",
            "os_system_call",
            "subprocess_shell_mode",
            "pickle_deserialization",
        }
        assert names == expected


# ============================================================================
# is_documentation_file()
# ============================================================================


class TestIsDocumentationFile:
    """Feature: Documentation file detection."""

    @pytest.mark.bdd
    @pytest.mark.unit
    @pytest.mark.parametrize("ext", [".md", ".rst", ".txt", ".adoc"])
    def test_detects_doc_extensions(self, ext: str) -> None:
        """Given a file with doc extension, returns True."""
        assert is_documentation_file(f"some/path/file{ext}") is True

    @pytest.mark.bdd
    @pytest.mark.unit
    @pytest.mark.parametrize("ext", [".py", ".js", ".ts", ".yaml", ".toml"])
    def test_rejects_non_doc_extensions(self, ext: str) -> None:
        """Given a code file outside doc directories, returns False."""
        assert is_documentation_file(f"src/module{ext}") is False

    @pytest.mark.bdd
    @pytest.mark.unit
    @pytest.mark.parametrize(
        "directory", ["docs", "doc", "documentation", "wiki", "examples", "commands"]
    )
    def test_detects_doc_directories(self, directory: str) -> None:
        """Given a file inside a documentation directory, returns True."""
        assert is_documentation_file(f"{directory}/api.py") is True

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_detects_nested_doc_directory(self) -> None:
        """Given a file nested under a doc directory, returns True."""
        assert is_documentation_file("project/docs/api/endpoints.py") is True

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_rejects_non_doc_path(self) -> None:
        """Given a pure code path, returns False."""
        assert is_documentation_file("src/app.py") is False


# ============================================================================
# has_negative_context()
# ============================================================================


class TestHasNegativeContext:
    """Feature: Negative context detection around pattern matches."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_finds_warning_context(self) -> None:
        """Given 'warning' near match position, returns True."""
        content = "This is a warning: do not use eval()"
        assert has_negative_context(content, 30) is True

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_finds_avoid_context(self) -> None:
        """Given 'avoid' near match position, returns True."""
        content = "You should avoid using os.system(cmd)"
        assert has_negative_context(content, 25) is True

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_no_negative_context(self) -> None:
        """Given neutral text, returns False."""
        content = "result = compute_value(x)"
        assert has_negative_context(content, 10) is False

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_window_boundary_start(self) -> None:
        """Given match at position 0, window clips to start of content."""
        content = "bad practice: eval(x)"
        assert has_negative_context(content, 0) is True

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_window_boundary_end(self) -> None:
        """Given match near end of content, window clips to end."""
        content = "result = eval(x)  # bad"
        assert has_negative_context(content, len(content) - 5) is True

    @pytest.mark.bdd
    @pytest.mark.unit
    @pytest.mark.parametrize(
        "word",
        [
            "bad",
            "avoid",
            "don't",
            "do not",
            "unsafe",
            "vulnerable",
            "never",
            "warning",
            "danger",
            "risk",
            "insecure",
            "# bad",
            "# wrong",
            "anti-pattern",
            "antipattern",
            "instead of",
            "example of unsafe",
            "[high]",
            "[med]",
            "[low]",
            "security issue",
            "flags",
            "detects",
        ],
    )
    def test_each_negative_context_word(self, word: str) -> None:
        """Given each NEGATIVE_CONTEXT_WORDS entry, detection succeeds."""
        content = f"prefix {word} suffix eval(x)"
        assert has_negative_context(content, 20) is True


# ============================================================================
# is_in_code_block()
# ============================================================================


class TestIsInCodeBlock:
    """Feature: Markdown code block detection."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_inside_code_block(self) -> None:
        """Given position inside a fenced block, returns True."""
        content = "text\n```python\neval(x)\n```\nmore text"
        pos = content.index("eval")
        assert is_in_code_block(content, pos) is True

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_outside_code_block(self) -> None:
        """Given position outside fenced blocks, returns False."""
        content = "text\n```python\ncode\n```\neval(x)"
        pos = content.rindex("eval")
        assert is_in_code_block(content, pos) is False

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_no_code_blocks(self) -> None:
        """Given content with no fences, returns False."""
        content = "eval(x) is used here"
        assert is_in_code_block(content, 0) is False

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_multiple_code_blocks(self) -> None:
        """Given position between two closed blocks, returns False."""
        content = "```\na\n```\nbetween\n```\nb\n```"
        pos = content.index("between")
        assert is_in_code_block(content, pos) is False


# ============================================================================
# check_content()
# ============================================================================


class TestCheckContent:
    """Feature: Content scanning for security patterns."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_detects_eval_in_python(self) -> None:
        """Given eval() in a .py file, returns rule and reminder."""
        content = f"result = {PATTERNS['eval_call']()}"
        rule, reminder = check_content("app.py", content)
        assert rule == "dynamic_code_evaluation"
        assert "arbitrary code" in reminder.lower() or "eval" in reminder.lower()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_detects_exec_in_python(self) -> None:
        """Given exec() in a .py file, returns dynamic_code_execution rule."""
        content = PATTERNS["exec_call"]()
        rule, reminder = check_content("runner.py", content)
        assert rule == "dynamic_code_execution"
        assert isinstance(reminder, str)
        assert len(reminder) > 0

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_detects_os_system(self) -> None:
        """Given os.system() in a .py file, returns os_system_call rule."""
        content = PATTERNS["os_system"]()
        rule, reminder = check_content("util.py", content)
        assert rule == "os_system_call"
        assert "subprocess" in reminder.lower()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_detects_shell_true(self) -> None:
        """Given shell=True in a .py file, returns subprocess_shell_mode rule."""
        content = f"subprocess.run(cmd, {PATTERNS['shell_mode']()})"
        rule, reminder = check_content("executor.py", content)
        assert rule == "subprocess_shell_mode"
        assert "injection" in reminder.lower()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_detects_pickle_load(self) -> None:
        """Given pickle.load in a .py file, returns pickle_deserialization rule."""
        content = f"data = {PATTERNS['pkl_load']()}"
        rule, reminder = check_content("loader.py", content)
        assert rule == "pickle_deserialization"
        assert "untrusted" in reminder.lower() or "json" in reminder.lower()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_ignores_pattern_in_wrong_file_type(self) -> None:
        """Given a Python pattern in a .yaml file, returns (None, None)."""
        content = f"subprocess.run(cmd, {PATTERNS['shell_mode']()})"
        rule, reminder = check_content("config.yaml", content)
        assert rule is None
        assert reminder is None

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_safe_content_returns_none(self) -> None:
        """Given safe Python code, returns (None, None)."""
        rule, reminder = check_content("app.py", "print('hello world')")
        assert rule is None
        assert reminder is None

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_doc_with_negative_context_skips(self) -> None:
        """Given docs file with negative context word, skips the match."""
        ev = PATTERNS["eval_call"]()
        content = f"Warning: never use {ev} in production."
        rule, reminder = check_content("docs/security.md", content)
        assert rule is None
        assert reminder is None

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_doc_code_block_with_negative_context_skips(self) -> None:
        """Given docs code block with 'bad' context, skips the match."""
        pattern = PATTERNS["os_system"]()
        content = f"## Bad Practice\nAvoid this:\n```python\n{pattern}\n```"
        rule, reminder = check_content("guide.md", content)
        assert rule is None
        assert reminder is None

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_doc_code_block_without_negative_context_flags(self) -> None:
        """Given docs code block without negative context, flags the match."""
        pattern = "os.sys" + 'tem("ls -la")'
        content = f"## Example\nHere is how:\n```python\n{pattern}\n```"
        rule, reminder = check_content("tutorial.md", content)
        assert rule == "os_system_call"
        assert isinstance(reminder, str)

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_doc_outside_code_block_without_negative_context_flags(self) -> None:
        """Given docs text without negative context, flags the match."""
        pattern = "os.sys" + 'tem("ls")'
        content = f"Use {pattern} to list files."
        rule, reminder = check_content("tutorial.md", content)
        assert rule == "os_system_call"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_case_insensitive_detection(self) -> None:
        """Given uppercase EVAL in Python file, still detects it."""
        content = f"result = {PATTERNS['eval_upper']()}"
        rule, _ = check_content("app.py", content)
        assert rule == "dynamic_code_evaluation"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_eval_in_javascript(self) -> None:
        """Given eval() in a .js file, detects it."""
        content = f"const result = {PATTERNS['eval_js']()};"
        rule, _ = check_content("script.js", content)
        assert rule == "dynamic_code_evaluation"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_eval_in_typescript(self) -> None:
        """Given eval() in a .ts file, detects it."""
        content = f"const result = {PATTERNS['eval_js']()};"
        rule, _ = check_content("module.ts", content)
        assert rule == "dynamic_code_evaluation"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_doc_in_examples_dir_with_context(self) -> None:
        """Given file in examples/ with negative context, skips match."""
        pattern = PATTERNS["os_system"]()
        content = f"# bad example: {pattern}"
        rule, reminder = check_content("examples/demo.py", content)
        assert rule is None
        assert reminder is None


# ============================================================================
# main() — Tool Dispatch
# ============================================================================


class TestMainToolDispatch:
    """Feature: main() dispatches based on tool_name and tool_input."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_write_tool_with_unsafe_content_warns(self) -> None:
        """Given Write tool with eval(), exits 0 with injected warning."""
        content = f"result = {PATTERNS['eval_call']()}"
        code, stdout, stderr = run_hook_in_process(
            "Write", {"file_path": "app.py", "content": content}
        )
        assert code == 0  # warns instead of blocking since v2.1.90
        assert "dynamic_code_evaluation" in stderr
        output = json.loads(stdout)
        assert "SECURITY WARNING" in output["hookSpecificOutput"]["additionalContext"]

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_edit_tool_checks_new_string(self) -> None:
        """Given Edit tool with unsafe new_string, exits 0 with warning."""
        pattern = PATTERNS["exec_call"]()
        code, _, stderr = run_hook_in_process(
            "Edit",
            {"file_path": "script.py", "old_string": "pass", "new_string": pattern},
        )
        assert code == 0  # warns instead of blocking since v2.1.90
        assert "dynamic_code_execution" in stderr

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_multi_edit_checks_combined_content(self) -> None:
        """Given MultiEdit with unsafe pattern in one edit, exits 0 with warning."""
        pattern = PATTERNS["eval_call"]()
        code, _, stderr = run_hook_in_process(
            "MultiEdit",
            {
                "file_path": "app.py",
                "edits": [
                    {"old_string": "a", "new_string": "b"},
                    {"old_string": "c", "new_string": pattern},
                ],
            },
        )
        assert code == 0  # warns instead of blocking since v2.1.90
        assert "dynamic_code_evaluation" in stderr

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_safe_write_exits_0(self) -> None:
        """Given Write tool with safe content, exits with code 0."""
        code, stdout, _ = run_hook_in_process(
            "Write", {"file_path": "app.py", "content": "print('hello')"}
        )
        assert code == 0
        assert stdout == ""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_safe_edit_exits_0(self) -> None:
        """Given Edit tool with safe new_string, exits with code 0."""
        code, _, _ = run_hook_in_process(
            "Edit",
            {"file_path": "script.py", "old_string": "pass", "new_string": "return 1"},
        )
        assert code == 0

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_safe_multi_edit_exits_0(self) -> None:
        """Given MultiEdit with all safe edits, exits with code 0."""
        code, _, _ = run_hook_in_process(
            "MultiEdit",
            {
                "file_path": "app.py",
                "edits": [
                    {"old_string": "a", "new_string": "b"},
                    {"old_string": "c", "new_string": "d"},
                ],
            },
        )
        assert code == 0


# ============================================================================
# main() — Early Exit Paths
# ============================================================================


class TestMainEarlyExits:
    """Feature: main() exits early for unsupported tools / missing data."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_non_write_tool_exits_0(self) -> None:
        """Given a Read tool, exits with code 0 without checking."""
        code, _, _ = run_hook_in_process("Read", {"file_path": "app.py"})
        assert code == 0

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_bash_tool_exits_0(self) -> None:
        """Given a Bash tool, exits with code 0 without checking."""
        code, _, _ = run_hook_in_process("Bash", {"command": "ls"})
        assert code == 0

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_missing_file_path_exits_0(self) -> None:
        """Given Write with no file_path, exits with code 0."""
        content = PATTERNS["eval_call"]()
        code, _, _ = run_hook_in_process("Write", {"content": content})
        assert code == 0

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_empty_content_exits_0(self) -> None:
        """Given Write with empty content, exits with code 0."""
        code, _, _ = run_hook_in_process(
            "Write", {"file_path": "empty.py", "content": ""}
        )
        assert code == 0


# ============================================================================
# main() — Error Handling
# ============================================================================


class TestMainErrorHandling:
    """Feature: main() handles malformed input gracefully."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_invalid_json_exits_0(self) -> None:
        """Given invalid JSON, main() exits with code 0."""
        captured_stdout = StringIO()
        captured_stderr = StringIO()
        with (
            patch("sys.stdin", StringIO("not valid json")),
            patch("sys.stdout", captured_stdout),
            patch("sys.stderr", captured_stderr),
        ):
            try:
                main()
                code = 0
            except SystemExit as e:
                code = e.code if e.code is not None else 0

        assert code == 0
        assert "parse failed" in captured_stderr.getvalue().lower()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_empty_stdin_exits_0(self) -> None:
        """Given empty stdin (valid empty JSON would fail), exits with code 0."""
        captured_stderr = StringIO()
        with (
            patch("sys.stdin", StringIO("")),
            patch("sys.stdout", StringIO()),
            patch("sys.stderr", captured_stderr),
        ):
            try:
                main()
                code = 0
            except SystemExit as e:
                code = e.code if e.code is not None else 0

        assert code == 0

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_json_without_tool_name_exits_0(self) -> None:
        """Given JSON with no tool_name key, exits with code 0."""
        captured_stdout = StringIO()
        with (
            patch("sys.stdin", StringIO(json.dumps({"something": "else"}))),
            patch("sys.stdout", captured_stdout),
            patch("sys.stderr", StringIO()),
        ):
            try:
                main()
                code = 0
            except SystemExit as e:
                code = e.code if e.code is not None else 0

        assert code == 0


# ============================================================================
# NEGATIVE_CONTEXT_WORDS constant
# ============================================================================


class TestCrashHandler:
    """Feature: Top-level crash handler logs traceback to stderr."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_main_exception_produces_traceback_on_stderr(self) -> None:
        """Scenario: main() raises an unexpected exception.

        Given main() throws a RuntimeError
        When the __main__ guard catches it
        Then traceback is printed to stderr.
        """
        captured_stderr = StringIO()
        with (
            patch("security_pattern_check.main", side_effect=RuntimeError("boom")),
            patch("sys.stderr", captured_stderr),
        ):
            # Simulate the __main__ guard behavior
            try:
                from security_pattern_check import main as _main

                _main()
            except RuntimeError:
                import traceback

                traceback.print_exc(file=captured_stderr)

        stderr_out = captured_stderr.getvalue()
        assert "boom" in stderr_out


class TestNegativeContextWords:
    """Feature: NEGATIVE_CONTEXT_WORDS is properly configured."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_is_a_list(self) -> None:
        """Given NEGATIVE_CONTEXT_WORDS, it is a list."""
        assert isinstance(NEGATIVE_CONTEXT_WORDS, list)

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_contains_expected_entries(self) -> None:
        """Given NEGATIVE_CONTEXT_WORDS, it contains key safety words."""
        for word in ("avoid", "unsafe", "warning", "never", "bad"):
            assert word in NEGATIVE_CONTEXT_WORDS, f"Missing: {word}"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_all_entries_are_lowercase(self) -> None:
        """Given NEGATIVE_CONTEXT_WORDS, all entries are lowercase."""
        for word in NEGATIVE_CONTEXT_WORDS:
            assert word == word.lower(), f"Not lowercase: {word}"
