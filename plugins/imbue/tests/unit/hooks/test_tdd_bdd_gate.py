"""Tests for TDD/BDD Gate hook enforcing test-first development.

This module tests the TDD/BDD gate hook that implements the Iron Law:
NO IMPLEMENTATION WITHOUT A FAILING TEST FIRST

The hook fires on PreToolUse for Write/Edit operations and checks whether
implementation files have corresponding test files.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from io import StringIO
from pathlib import Path

import pytest


@pytest.fixture
def tdd_gate_module():
    """Import the tdd_bdd_gate module via importlib."""
    hooks_path = (
        Path(__file__).resolve().parent.parent.parent.parent / "hooks"
    )
    module_path = hooks_path / "tdd_bdd_gate.py"

    spec = importlib.util.spec_from_file_location(
        "tdd_bdd_gate", module_path,
    )
    tdd_gate = importlib.util.module_from_spec(spec)
    sys.modules["tdd_bdd_gate"] = tdd_gate
    spec.loader.exec_module(tdd_gate)

    return tdd_gate


class TestIsImplementationFile:
    """Feature: Identify implementation files that require tests.

    As a TDD enforcement system
    I want to identify implementation files
    So that I can enforce test-first development
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    @pytest.mark.parametrize(
        "file_path,expected_impl,expected_type_attr",
        [
            (
                "/plugins/imbue/skills/proof-of-work/SKILL.md",
                True,
                "SKILL_FILE",
            ),
            (
                "/plugins/attune/skills/war-room/SKILL.md",
                True,
                "SKILL_FILE",
            ),
            (
                "/plugins/imbue/skills/proof-of-work/modules/validator.py",
                True,
                "PYTHON_FILE",
            ),
            (
                "/plugins/imbue/scripts/imbue_validator.py",
                True,
                "PYTHON_FILE",
            ),
        ],
        ids=[
            "skill-md-is-impl",
            "skill-md-another-plugin",
            "python-module-is-impl",
            "python-script-is-impl",
        ],
    )
    def test_implementation_files_detected(
        self, tdd_gate_module, file_path,
        expected_impl, expected_type_attr,
    ) -> None:
        """Scenario: Implementation files are correctly identified.

        Given various implementation file paths
        When checking if each is an implementation file
        Then SKILL.md and .py source files return True
        And the correct implementation type is returned.
        """
        is_impl, impl_type = tdd_gate_module.is_implementation_file(
            file_path,
        )
        expected_type = getattr(tdd_gate_module, expected_type_attr)

        assert is_impl is True
        assert impl_type == expected_type

    @pytest.mark.bdd
    @pytest.mark.unit
    @pytest.mark.parametrize(
        "file_path",
        [
            "/plugins/imbue/skills/proof-of-work/modules/iron-law-enforcement.md",
            "/plugins/attune/commands/war-room.md",
            "/plugins/imbue/tests/unit/test_validator.py",
            "/plugins/imbue/tests/validator_test.py",
            "/plugins/imbue/tests/conftest.py",
            "/plugins/imbue/src/imbue/__init__.py",
            "/plugins/imbue/tests/fixtures/sample_validator.py",
        ],
        ids=[
            "md-module",
            "md-command",
            "test-prefix",
            "test-suffix",
            "conftest",
            "init-py",
            "tests-dir-file",
        ],
    )
    def test_non_implementation_files_excluded(
        self, tdd_gate_module, file_path,
    ) -> None:
        """Scenario: Non-implementation files are excluded.

        Given paths to tests, markdown modules, commands, and configs
        When checking if each is an implementation file
        Then all should return False with None type.
        """
        is_impl, impl_type = tdd_gate_module.is_implementation_file(
            file_path,
        )

        assert is_impl is False
        assert impl_type is None


class TestFindTestFile:
    """Feature: Find corresponding test file for implementation.

    As a TDD enforcement system
    I want to find the expected test file location
    So that I can check if tests exist before implementation
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    @pytest.mark.parametrize(
        "skill_name,impl_type_attr,expected_fragment",
        [
            ("proof-of-work", "SKILL_FILE", "test_proof_of_work"),
            ("proof-of-work", "SKILL_FILE", "proof_of_work"),
        ],
        ids=[
            "skill-test-file-location",
            "hyphen-to-underscore-conversion",
        ],
    )
    def test_find_test_for_skill(
        self, tdd_gate_module, tmp_path,
        skill_name, impl_type_attr, expected_fragment,
    ) -> None:
        """Scenario: Find test file for skill with name conversion.

        Given a skill SKILL.md file path
        When finding the corresponding test file
        Then it should look in tests/unit/skills/ directory
        And convert hyphens to underscores.
        """
        plugin_root = tmp_path / "plugins" / "imbue"
        plugin_root.mkdir(parents=True)
        (plugin_root / "pyproject.toml").touch()
        (plugin_root / "skills" / skill_name).mkdir(parents=True)
        skill_path = (
            plugin_root / "skills" / skill_name / "SKILL.md"
        )
        skill_path.touch()

        impl_type = getattr(tdd_gate_module, impl_type_attr)
        test_path = tdd_gate_module.find_test_file(
            str(skill_path), impl_type,
        )

        assert isinstance(test_path, (str, Path))
        assert expected_fragment in str(test_path)

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_find_test_for_python_impl(
        self, tdd_gate_module, tmp_path,
    ) -> None:
        """Scenario: Find test file for Python implementation.

        Given a Python implementation file path
        When finding the corresponding test file
        Then it should look in tests/unit/ directory.
        """
        plugin_root = tmp_path / "plugins" / "imbue"
        plugin_root.mkdir(parents=True)
        (plugin_root / "pyproject.toml").touch()
        (plugin_root / "scripts").mkdir(parents=True)
        impl_path = plugin_root / "scripts" / "validator.py"
        impl_path.touch()

        test_path = tdd_gate_module.find_test_file(
            str(impl_path), tdd_gate_module.PYTHON_FILE,
        )

        assert isinstance(test_path, (str, Path))
        assert "test_validator" in str(test_path)


class TestFormatTddBddReminder:
    """Feature: Format TDD/BDD reminder messages.

    As a TDD enforcement system
    I want to generate helpful reminder messages
    So that developers understand what tests to write
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    @pytest.mark.parametrize(
        "assertion_target",
        [
            "Iron Law",
            "NO IMPLEMENTATION WITHOUT A FAILING TEST FIRST",
        ],
        ids=["iron-law-label", "iron-law-statement"],
    )
    def test_reminder_content(
        self, tdd_gate_module, tmp_path, assertion_target,
    ) -> None:
        """Scenario: Reminder includes Iron Law content.

        Given an implementation path and type
        When formatting the TDD/BDD reminder
        Then it should include the Iron Law statement.
        """
        test_path = tmp_path / "tests" / "test_skill.py"

        reminder = tdd_gate_module.format_tdd_bdd_reminder(
            "/plugins/imbue/skills/example/SKILL.md",
            tdd_gate_module.SKILL_FILE,
            test_path,
        )

        assert assertion_target in reminder

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_reminder_includes_expected_test_path(
        self, tdd_gate_module, tmp_path,
    ) -> None:
        """Scenario: Reminder includes expected test file path.

        Given an implementation path and type
        When formatting the TDD/BDD reminder
        Then it should include the expected test file path.
        """
        test_path = tmp_path / "tests" / "test_skill.py"

        reminder = tdd_gate_module.format_tdd_bdd_reminder(
            "/plugins/imbue/skills/example/SKILL.md",
            tdd_gate_module.SKILL_FILE,
            test_path,
        )

        assert str(test_path) in reminder
        assert "Expected test file:" in reminder

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_reminder_bdd_template_when_test_missing(
        self, tdd_gate_module, tmp_path,
    ) -> None:
        """Scenario: Reminder includes BDD template when test missing.

        Given an implementation path with no existing test file
        When formatting the TDD/BDD reminder
        Then it should include a BDD test template with all markers.
        """
        test_path = tmp_path / "tests" / "test_skill.py"

        reminder = tdd_gate_module.format_tdd_bdd_reminder(
            "/plugins/imbue/skills/example/SKILL.md",
            tdd_gate_module.SKILL_FILE,
            test_path,
        )

        assert "BDD Test Template" in reminder
        for keyword in ["Given", "When", "Then", "@pytest.mark"]:
            assert keyword in reminder
        assert "Write tests first!" in reminder

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_reminder_shows_test_exists_status(
        self, tdd_gate_module, tmp_path,
    ) -> None:
        """Scenario: Reminder shows test file exists when present.

        Given an implementation path with existing test file
        When formatting the TDD/BDD reminder
        Then it should show that test file exists.
        """
        test_path = tmp_path / "tests" / "test_skill.py"
        test_path.parent.mkdir(parents=True)
        test_path.touch()

        reminder = tdd_gate_module.format_tdd_bdd_reminder(
            "/plugins/imbue/skills/example/SKILL.md",
            tdd_gate_module.SKILL_FILE,
            test_path,
        )

        assert "Test file exists: Yes" in reminder


class TestIsNewFile:
    """Feature: Detect new files vs modifications.

    As a TDD enforcement system
    I want to distinguish new files from modifications
    So that I can enforce stricter rules for new implementations
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    @pytest.mark.parametrize(
        "exists,expected",
        [(False, True), (True, False)],
        ids=["nonexistent-is-new", "existing-is-not-new"],
    )
    def test_new_file_detection(
        self, tdd_gate_module, tmp_path, exists, expected,
    ) -> None:
        """Scenario: File existence determines new-file status.

        Given a file path that may or may not exist
        When checking if it is a new file
        Then the result depends on existence.
        """
        file_path = tmp_path / "test_file.py"
        if exists:
            file_path.touch()

        assert tdd_gate_module.is_new_file(str(file_path)) is expected


class TestMainEntryPoint:
    """Feature: Hook main entry point handles stdin/stdout correctly.

    As a Claude Code hook
    I want main() to process tool use events correctly
    So that I can enforce TDD/BDD discipline at the right times
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    @pytest.mark.parametrize(
        "tool_name",
        ["Read", "Bash"],
        ids=["read-tool-ignored", "bash-tool-ignored"],
    )
    def test_main_ignores_non_write_tools(
        self, tdd_gate_module, monkeypatch, tool_name,
    ) -> None:
        """Scenario: main() ignores non-write tool operations.

        Given a non-write tool operation on stdin
        When running main
        Then it should exit 0 without output.
        """
        input_data = json.dumps({
            "tool_name": tool_name,
            "tool_input": {"file_path": "/some/file.py"},
        })
        monkeypatch.setattr("sys.stdin", StringIO(input_data))

        with pytest.raises(SystemExit) as exc_info:
            tdd_gate_module.main()

        assert exc_info.value.code == 0

    @pytest.mark.bdd
    @pytest.mark.unit
    @pytest.mark.parametrize(
        "tool_name",
        ["Write", "Edit", "MultiEdit"],
        ids=["write-tool", "edit-tool", "multiedit-tool"],
    )
    def test_main_processes_write_tools(
        self, tdd_gate_module, monkeypatch, tmp_path, tool_name,
    ) -> None:
        """Scenario: main() processes Write/Edit/MultiEdit tools.

        Given a write-family tool operation for new implementation
        When running main
        Then it should enforce the TDD gate with exit code 2.
        """
        plugin_root = tmp_path / "plugins" / "imbue"
        plugin_root.mkdir(parents=True)
        (plugin_root / "pyproject.toml").touch()
        skill_dir = plugin_root / "skills" / "example"
        skill_dir.mkdir(parents=True)
        skill_path = skill_dir / "SKILL.md"

        input_data = json.dumps({
            "tool_name": tool_name,
            "tool_input": {"file_path": str(skill_path)},
        })
        monkeypatch.setattr("sys.stdin", StringIO(input_data))

        output_capture = StringIO()
        monkeypatch.setattr("sys.stdout", output_capture)

        with pytest.raises(SystemExit) as exc_info:
            tdd_gate_module.main()

        assert exc_info.value.code == 2
        output = output_capture.getvalue()
        assert "additionalContext" in output

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_main_handles_invalid_json(
        self, tdd_gate_module, monkeypatch,
    ) -> None:
        """Scenario: main() handles invalid JSON gracefully.

        Given invalid JSON on stdin
        When running main
        Then it should exit 0 without crashing.
        """
        monkeypatch.setattr("sys.stdin", StringIO("not valid json"))

        with pytest.raises(SystemExit) as exc_info:
            tdd_gate_module.main()

        assert exc_info.value.code == 0

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_main_ignores_non_implementation_files(
        self, tdd_gate_module, monkeypatch, tmp_path,
    ) -> None:
        """Scenario: main() ignores Write to non-implementation files.

        Given a Write tool operation for a README file
        When running main
        Then it should exit 0 (allow without warning).
        """
        readme_path = tmp_path / "README.md"
        input_data = json.dumps({
            "tool_name": "Write",
            "tool_input": {"file_path": str(readme_path)},
        })
        monkeypatch.setattr("sys.stdin", StringIO(input_data))

        with pytest.raises(SystemExit) as exc_info:
            tdd_gate_module.main()

        assert exc_info.value.code == 0

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_main_existing_file_without_tests_gives_short_reminder(
        self, tdd_gate_module, monkeypatch, tmp_path,
    ) -> None:
        """Scenario: Existing file without tests gets short reminder.

        Given a Write for an existing Python file without tests
        When running main
        Then it should exit 2 with a short reminder (not full template).
        """
        plugin_root = tmp_path / "plugins" / "imbue"
        plugin_root.mkdir(parents=True)
        (plugin_root / "pyproject.toml").touch()
        scripts_dir = plugin_root / "scripts"
        scripts_dir.mkdir(parents=True)

        impl_path = scripts_dir / "validator.py"
        impl_path.write_text("# existing implementation\n")

        input_data = json.dumps({
            "tool_name": "Write",
            "tool_input": {"file_path": str(impl_path)},
        })
        monkeypatch.setattr("sys.stdin", StringIO(input_data))

        output_capture = StringIO()
        monkeypatch.setattr("sys.stdout", output_capture)

        with pytest.raises(SystemExit) as exc_info:
            tdd_gate_module.main()

        assert exc_info.value.code == 2
        output = output_capture.getvalue()
        parsed = json.loads(output)
        context = parsed["hookSpecificOutput"]["additionalContext"]
        assert "TDD/BDD Reminder" in context
        assert "Consider tests" in context


class TestFindPluginRoot:
    """Feature: Find plugin root directory.

    As a TDD enforcement system
    I want to find the plugin root
    So that I can locate the tests directory correctly
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    @pytest.mark.parametrize(
        "marker",
        ["pyproject.toml", ".claude-plugin"],
        ids=["by-pyproject-toml", "by-claude-plugin-dir"],
    )
    def test_find_plugin_root_by_marker(
        self, tdd_gate_module, tmp_path, marker,
    ) -> None:
        """Scenario: Find plugin root by filesystem marker.

        Given a file path inside a plugin with a marker file/dir
        When finding the plugin root
        Then it should return the directory containing the marker.
        """
        plugin_root = tmp_path / "plugins" / "imbue"
        if marker == ".claude-plugin":
            (plugin_root / marker).mkdir(parents=True)
        else:
            plugin_root.mkdir(parents=True)
            (plugin_root / marker).touch()

        nested_path = plugin_root / "skills" / "example" / "SKILL.md"
        nested_path.parent.mkdir(parents=True)
        nested_path.touch()

        found_root = tdd_gate_module._find_plugin_root(nested_path)
        assert found_root == plugin_root

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_find_plugin_root_returns_none_without_markers(
        self, tdd_gate_module, tmp_path,
    ) -> None:
        """Scenario: No marker found returns None.

        Given a file path with no plugin markers in any parent
        When finding the plugin root
        Then it should return None.
        """
        nested_dir = tmp_path / "some" / "deep" / "path"
        nested_dir.mkdir(parents=True)
        nested_file = nested_dir / "file.py"
        nested_file.touch()

        found_root = tdd_gate_module._find_plugin_root(nested_file)
        assert found_root is None
