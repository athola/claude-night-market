"""Tests for TDD/BDD Gate hook enforcing test-first development.

This module tests the TDD/BDD gate hook that implements the Iron Law:
NO IMPLEMENTATION WITHOUT A FAILING TEST FIRST

The hook fires on PreToolUse for Write/Edit operations and checks whether
implementation files have corresponding test files.
"""

import json
from pathlib import Path

import pytest


class TestIsImplementationFile:
    """Feature: Identify implementation files that require tests.

    As a TDD enforcement system
    I want to identify implementation files
    So that I can enforce test-first development
    """

    @pytest.fixture
    def tdd_gate_module(self):
        """Import the tdd_bdd_gate module."""
        import importlib.util
        import sys

        hooks_path = Path(__file__).resolve().parent.parent.parent.parent / "hooks"
        module_path = hooks_path / "tdd_bdd_gate.py"

        spec = importlib.util.spec_from_file_location("tdd_bdd_gate", module_path)
        tdd_gate = importlib.util.module_from_spec(spec)
        sys.modules["tdd_bdd_gate"] = tdd_gate
        spec.loader.exec_module(tdd_gate)

        return tdd_gate

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_md_is_implementation_file(self, tdd_gate_module) -> None:
        """Scenario: SKILL.md files are identified as implementation files.

        Given a path to a SKILL.md file
        When checking if it's an implementation file
        Then it should return True with skill type.
        """
        is_impl, impl_type = tdd_gate_module.is_implementation_file(
            "/plugins/imbue/skills/proof-of-work/SKILL.md"
        )

        assert is_impl is True
        assert impl_type == tdd_gate_module.SKILL_FILE

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_markdown_module_is_not_implementation_file(self, tdd_gate_module) -> None:
        """Scenario: Markdown module files are NOT implementation files.

        Given a path to a .md file in modules/ directory
        When checking if it's an implementation file
        Then it should return False because markdown modules are agent
        instruction documents, not executable code testable by pytest.
        """
        is_impl, impl_type = tdd_gate_module.is_implementation_file(
            "/plugins/imbue/skills/proof-of-work/modules/iron-law-enforcement.md"
        )

        assert is_impl is False
        assert impl_type is None

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_python_module_is_implementation_file(self, tdd_gate_module) -> None:
        """Scenario: Python module files in modules/ ARE implementation files.

        Given a path to a .py file in modules/ directory
        When checking if it's an implementation file
        Then it should return True with python type.
        """
        is_impl, impl_type = tdd_gate_module.is_implementation_file(
            "/plugins/imbue/skills/proof-of-work/modules/validator.py"
        )

        assert is_impl is True
        assert impl_type == tdd_gate_module.PYTHON_FILE

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_md_still_triggers_gate(self, tdd_gate_module) -> None:
        """Scenario: SKILL.md files still trigger the TDD gate.

        Given a path to a SKILL.md file
        When checking if it's an implementation file
        Then it should return True (SKILL.md defines core behavior).
        """
        is_impl, impl_type = tdd_gate_module.is_implementation_file(
            "/plugins/attune/skills/war-room/SKILL.md"
        )

        assert is_impl is True
        assert impl_type == tdd_gate_module.SKILL_FILE

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_markdown_command_is_not_implementation_file(self, tdd_gate_module) -> None:
        """Scenario: Markdown command files are NOT implementation files.

        Given a path to a .md file in commands/ directory
        When checking if it's an implementation file
        Then it should return False because markdown commands are agent
        instruction documents, not executable code testable by pytest.
        """
        is_impl, impl_type = tdd_gate_module.is_implementation_file(
            "/plugins/attune/commands/war-room.md"
        )

        assert is_impl is False
        assert impl_type is None

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_python_implementation_is_implementation_file(
        self, tdd_gate_module
    ) -> None:
        """Scenario: Python files (not tests) are implementation files.

        Given a path to a Python implementation file
        When checking if it's an implementation file
        Then it should return True with python type.
        """
        is_impl, impl_type = tdd_gate_module.is_implementation_file(
            "/plugins/imbue/scripts/imbue_validator.py"
        )

        assert is_impl is True
        assert impl_type == tdd_gate_module.PYTHON_FILE

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_test_file_is_not_implementation(self, tdd_gate_module) -> None:
        """Scenario: Test files are not implementation files.

        Given a path to a test file
        When checking if it's an implementation file
        Then it should return False.
        """
        test_cases = [
            "/plugins/imbue/tests/unit/test_validator.py",
            "/plugins/imbue/tests/validator_test.py",
        ]

        for test_path in test_cases:
            is_impl, impl_type = tdd_gate_module.is_implementation_file(test_path)
            assert is_impl is False
            assert impl_type is None

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_conftest_is_not_implementation(self, tdd_gate_module) -> None:
        """Scenario: conftest.py files are not implementation files.

        Given a path to a conftest.py file
        When checking if it's an implementation file
        Then it should return False.
        """
        is_impl, impl_type = tdd_gate_module.is_implementation_file(
            "/plugins/imbue/tests/conftest.py"
        )

        assert is_impl is False
        assert impl_type is None

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_init_is_not_implementation(self, tdd_gate_module) -> None:
        """Scenario: __init__.py files are not implementation files.

        Given a path to an __init__.py file
        When checking if it's an implementation file
        Then it should return False.
        """
        is_impl, impl_type = tdd_gate_module.is_implementation_file(
            "/plugins/imbue/src/imbue/__init__.py"
        )

        assert is_impl is False
        assert impl_type is None

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_files_in_tests_dir_not_implementation(self, tdd_gate_module) -> None:
        """Scenario: Python files in tests directory are not implementation files.

        Given a path to a Python file inside tests/ directory
        When checking if it's an implementation file
        Then it should return False.
        """
        is_impl, impl_type = tdd_gate_module.is_implementation_file(
            "/plugins/imbue/tests/fixtures/sample_validator.py"
        )

        assert is_impl is False
        assert impl_type is None


class TestFindTestFile:
    """Feature: Find corresponding test file for implementation.

    As a TDD enforcement system
    I want to find the expected test file location
    So that I can check if tests exist before implementation
    """

    @pytest.fixture
    def tdd_gate_module(self):
        """Import the tdd_bdd_gate module."""
        import importlib.util
        import sys

        hooks_path = Path(__file__).resolve().parent.parent.parent.parent / "hooks"
        module_path = hooks_path / "tdd_bdd_gate.py"

        spec = importlib.util.spec_from_file_location("tdd_bdd_gate", module_path)
        tdd_gate = importlib.util.module_from_spec(spec)
        sys.modules["tdd_bdd_gate"] = tdd_gate
        spec.loader.exec_module(tdd_gate)

        return tdd_gate

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_find_test_for_skill(self, tdd_gate_module, tmp_path) -> None:
        """Scenario: Find test file for skill.

        Given a skill SKILL.md file path
        When finding the corresponding test file
        Then it should look in tests/unit/skills/ directory.
        """
        # Create mock plugin structure
        plugin_root = tmp_path / "plugins" / "imbue"
        plugin_root.mkdir(parents=True)
        (plugin_root / "pyproject.toml").touch()
        (plugin_root / "skills" / "proof-of-work").mkdir(parents=True)
        skill_path = plugin_root / "skills" / "proof-of-work" / "SKILL.md"
        skill_path.touch()

        test_path = tdd_gate_module.find_test_file(
            str(skill_path), tdd_gate_module.SKILL_FILE
        )

        assert test_path is not None
        assert "test_proof_of_work" in str(test_path)

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_find_test_for_python_impl(self, tdd_gate_module, tmp_path) -> None:
        """Scenario: Find test file for Python implementation.

        Given a Python implementation file path
        When finding the corresponding test file
        Then it should look in tests/unit/ directory.
        """
        # Create mock plugin structure
        plugin_root = tmp_path / "plugins" / "imbue"
        plugin_root.mkdir(parents=True)
        (plugin_root / "pyproject.toml").touch()
        (plugin_root / "scripts").mkdir(parents=True)
        impl_path = plugin_root / "scripts" / "validator.py"
        impl_path.touch()

        test_path = tdd_gate_module.find_test_file(
            str(impl_path), tdd_gate_module.PYTHON_FILE
        )

        assert test_path is not None
        assert "test_validator" in str(test_path)

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_hyphenated_names_convert_to_underscores(
        self, tdd_gate_module, tmp_path
    ) -> None:
        """Scenario: Hyphenated skill names convert to underscores in test path.

        Given a skill with hyphenated name (proof-of-work)
        When finding the corresponding test file
        Then the test filename should use underscores (test_proof_of_work.py).
        """
        # Create mock plugin structure
        plugin_root = tmp_path / "plugins" / "imbue"
        plugin_root.mkdir(parents=True)
        (plugin_root / "pyproject.toml").touch()
        (plugin_root / "skills" / "proof-of-work").mkdir(parents=True)
        skill_path = plugin_root / "skills" / "proof-of-work" / "SKILL.md"
        skill_path.touch()

        test_path = tdd_gate_module.find_test_file(
            str(skill_path), tdd_gate_module.SKILL_FILE
        )

        # Should convert hyphens to underscores
        assert "proof_of_work" in str(test_path)
        assert "proof-of-work" not in str(test_path)


class TestFormatTddBddReminder:
    """Feature: Format TDD/BDD reminder messages.

    As a TDD enforcement system
    I want to generate helpful reminder messages
    So that developers understand what tests to write
    """

    @pytest.fixture
    def tdd_gate_module(self):
        """Import the tdd_bdd_gate module."""
        import importlib.util
        import sys

        hooks_path = Path(__file__).resolve().parent.parent.parent.parent / "hooks"
        module_path = hooks_path / "tdd_bdd_gate.py"

        spec = importlib.util.spec_from_file_location("tdd_bdd_gate", module_path)
        tdd_gate = importlib.util.module_from_spec(spec)
        sys.modules["tdd_bdd_gate"] = tdd_gate
        spec.loader.exec_module(tdd_gate)

        return tdd_gate

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_reminder_includes_iron_law(self, tdd_gate_module, tmp_path) -> None:
        """Scenario: Reminder includes Iron Law statement.

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

        assert "Iron Law" in reminder
        assert "NO IMPLEMENTATION WITHOUT A FAILING TEST FIRST" in reminder

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_reminder_includes_expected_test_path(
        self, tdd_gate_module, tmp_path
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
    def test_reminder_includes_bdd_template_when_test_missing(
        self, tdd_gate_module, tmp_path
    ) -> None:
        """Scenario: Reminder includes BDD template when test doesn't exist.

        Given an implementation path with no existing test file
        When formatting the TDD/BDD reminder
        Then it should include a BDD test template.
        """
        test_path = tmp_path / "tests" / "test_skill.py"  # Does not exist

        reminder = tdd_gate_module.format_tdd_bdd_reminder(
            "/plugins/imbue/skills/example/SKILL.md",
            tdd_gate_module.SKILL_FILE,
            test_path,
        )

        assert "BDD Test Template" in reminder
        assert "Given" in reminder
        assert "When" in reminder
        assert "Then" in reminder
        assert "@pytest.mark" in reminder

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_reminder_shows_test_exists_status(self, tdd_gate_module, tmp_path) -> None:
        """Scenario: Reminder shows whether test file exists.

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

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_reminder_shows_write_tests_first_when_missing(
        self, tdd_gate_module, tmp_path
    ) -> None:
        """Scenario: Reminder emphasizes writing tests when test file missing.

        Given an implementation path with no test file
        When formatting the TDD/BDD reminder
        Then it should show "Write tests first!" status.
        """
        test_path = tmp_path / "tests" / "test_skill.py"  # Does not exist

        reminder = tdd_gate_module.format_tdd_bdd_reminder(
            "/plugins/imbue/skills/example/SKILL.md",
            tdd_gate_module.SKILL_FILE,
            test_path,
        )

        assert "Write tests first!" in reminder


class TestIsNewFile:
    """Feature: Detect new files vs modifications.

    As a TDD enforcement system
    I want to distinguish new files from modifications
    So that I can enforce stricter rules for new implementations
    """

    @pytest.fixture
    def tdd_gate_module(self):
        """Import the tdd_bdd_gate module."""
        import importlib.util
        import sys

        hooks_path = Path(__file__).resolve().parent.parent.parent.parent / "hooks"
        module_path = hooks_path / "tdd_bdd_gate.py"

        spec = importlib.util.spec_from_file_location("tdd_bdd_gate", module_path)
        tdd_gate = importlib.util.module_from_spec(spec)
        sys.modules["tdd_bdd_gate"] = tdd_gate
        spec.loader.exec_module(tdd_gate)

        return tdd_gate

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_nonexistent_file_is_new(self, tdd_gate_module, tmp_path) -> None:
        """Scenario: Non-existent file path is identified as new.

        Given a path to a non-existent file
        When checking if it's a new file
        Then it should return True.
        """
        nonexistent = tmp_path / "does_not_exist.py"

        assert tdd_gate_module.is_new_file(str(nonexistent)) is True

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_existing_file_is_not_new(self, tdd_gate_module, tmp_path) -> None:
        """Scenario: Existing file is not identified as new.

        Given a path to an existing file
        When checking if it's a new file
        Then it should return False.
        """
        existing = tmp_path / "existing.py"
        existing.touch()

        assert tdd_gate_module.is_new_file(str(existing)) is False


class TestMainEntryPoint:
    """Feature: Hook main entry point handles stdin/stdout correctly.

    As a Claude Code hook
    I want main() to process tool use events correctly
    So that I can enforce TDD/BDD discipline at the right times
    """

    @pytest.fixture
    def tdd_gate_module(self):
        """Import the tdd_bdd_gate module."""
        import importlib.util
        import sys

        hooks_path = Path(__file__).resolve().parent.parent.parent.parent / "hooks"
        module_path = hooks_path / "tdd_bdd_gate.py"

        spec = importlib.util.spec_from_file_location("tdd_bdd_gate", module_path)
        tdd_gate = importlib.util.module_from_spec(spec)
        sys.modules["tdd_bdd_gate"] = tdd_gate
        spec.loader.exec_module(tdd_gate)

        return tdd_gate

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_main_ignores_read_tool(self, tdd_gate_module, monkeypatch) -> None:
        """Scenario: main() ignores Read tool operations.

        Given a Read tool operation on stdin
        When running main
        Then it should exit 0 without output.
        """
        from io import StringIO

        input_data = json.dumps(
            {
                "tool_name": "Read",
                "tool_input": {"file_path": "/some/file.py"},
            }
        )
        monkeypatch.setattr("sys.stdin", StringIO(input_data))

        with pytest.raises(SystemExit) as exc_info:
            tdd_gate_module.main()

        assert exc_info.value.code == 0

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_main_ignores_bash_tool(self, tdd_gate_module, monkeypatch) -> None:
        """Scenario: main() ignores Bash tool operations.

        Given a Bash tool operation on stdin
        When running main
        Then it should exit 0 without output.
        """
        from io import StringIO

        input_data = json.dumps(
            {
                "tool_name": "Bash",
                "tool_input": {"command": "ls -la"},
            }
        )
        monkeypatch.setattr("sys.stdin", StringIO(input_data))

        with pytest.raises(SystemExit) as exc_info:
            tdd_gate_module.main()

        assert exc_info.value.code == 0

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_main_processes_write_tool(
        self, tdd_gate_module, monkeypatch, tmp_path
    ) -> None:
        """Scenario: main() processes Write tool operations.

        Given a Write tool operation for an implementation file
        When running main
        Then it should check for test file existence.
        """
        from io import StringIO

        # Create mock plugin structure
        plugin_root = tmp_path / "plugins" / "imbue"
        plugin_root.mkdir(parents=True)
        (plugin_root / "pyproject.toml").touch()
        skill_dir = plugin_root / "skills" / "example"
        skill_dir.mkdir(parents=True)

        skill_path = skill_dir / "SKILL.md"
        # File doesn't exist yet (new implementation)

        input_data = json.dumps(
            {
                "tool_name": "Write",
                "tool_input": {"file_path": str(skill_path)},
            }
        )
        monkeypatch.setattr("sys.stdin", StringIO(input_data))

        output_capture = StringIO()
        monkeypatch.setattr("sys.stdout", output_capture)

        with pytest.raises(SystemExit) as exc_info:
            tdd_gate_module.main()

        # Should exit with code 2 (continue but with warning)
        assert exc_info.value.code == 2
        output = output_capture.getvalue()
        assert "additionalContext" in output

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_main_handles_invalid_json(self, tdd_gate_module, monkeypatch) -> None:
        """Scenario: main() handles invalid JSON gracefully.

        Given invalid JSON on stdin
        When running main
        Then it should exit 0 without crashing.
        """
        from io import StringIO

        monkeypatch.setattr("sys.stdin", StringIO("not valid json"))

        with pytest.raises(SystemExit) as exc_info:
            tdd_gate_module.main()

        assert exc_info.value.code == 0

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_main_ignores_non_implementation_files(
        self, tdd_gate_module, monkeypatch, tmp_path
    ) -> None:
        """Scenario: main() ignores Write to non-implementation files.

        Given a Write tool operation for a README file
        When running main
        Then it should exit 0 (allow without warning).
        """
        from io import StringIO

        readme_path = tmp_path / "README.md"

        input_data = json.dumps(
            {
                "tool_name": "Write",
                "tool_input": {"file_path": str(readme_path)},
            }
        )
        monkeypatch.setattr("sys.stdin", StringIO(input_data))

        with pytest.raises(SystemExit) as exc_info:
            tdd_gate_module.main()

        assert exc_info.value.code == 0

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_main_processes_edit_tool(
        self, tdd_gate_module, monkeypatch, tmp_path
    ) -> None:
        """Scenario: main() processes Edit tool operations.

        Given an Edit tool operation for a new implementation file
        When running main
        Then it should enforce the TDD gate with exit code 2.
        """
        from io import StringIO

        # Create mock plugin structure
        plugin_root = tmp_path / "plugins" / "imbue"
        plugin_root.mkdir(parents=True)
        (plugin_root / "pyproject.toml").touch()
        skill_dir = plugin_root / "skills" / "example"
        skill_dir.mkdir(parents=True)

        skill_path = skill_dir / "SKILL.md"
        # File doesn't exist yet (new implementation)

        input_data = json.dumps(
            {
                "tool_name": "Edit",
                "tool_input": {"file_path": str(skill_path)},
            }
        )
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
    def test_main_processes_multiedit_tool(
        self, tdd_gate_module, monkeypatch, tmp_path
    ) -> None:
        """Scenario: main() processes MultiEdit tool operations.

        Given a MultiEdit tool operation for a new implementation file
        When running main
        Then it should enforce the TDD gate with exit code 2.
        """
        from io import StringIO

        # Create mock plugin structure
        plugin_root = tmp_path / "plugins" / "imbue"
        plugin_root.mkdir(parents=True)
        (plugin_root / "pyproject.toml").touch()
        skill_dir = plugin_root / "skills" / "example"
        skill_dir.mkdir(parents=True)

        skill_path = skill_dir / "SKILL.md"

        input_data = json.dumps(
            {
                "tool_name": "MultiEdit",
                "tool_input": {"file_path": str(skill_path)},
            }
        )
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
    def test_main_existing_file_without_tests_gives_short_reminder(
        self, tdd_gate_module, monkeypatch, tmp_path
    ) -> None:
        """Scenario: main() gives short reminder when modifying existing file without tests.

        Given a Write tool operation for an existing Python implementation file
        And no corresponding test file exists
        When running main
        Then it should exit with code 2 and a short reminder (not the full template).
        """
        from io import StringIO

        # Create mock plugin structure with existing implementation
        plugin_root = tmp_path / "plugins" / "imbue"
        plugin_root.mkdir(parents=True)
        (plugin_root / "pyproject.toml").touch()
        scripts_dir = plugin_root / "scripts"
        scripts_dir.mkdir(parents=True)

        impl_path = scripts_dir / "validator.py"
        impl_path.write_text("# existing implementation\n")

        input_data = json.dumps(
            {
                "tool_name": "Write",
                "tool_input": {"file_path": str(impl_path)},
            }
        )
        monkeypatch.setattr("sys.stdin", StringIO(input_data))

        output_capture = StringIO()
        monkeypatch.setattr("sys.stdout", output_capture)

        with pytest.raises(SystemExit) as exc_info:
            tdd_gate_module.main()

        assert exc_info.value.code == 2
        output = output_capture.getvalue()
        parsed = json.loads(output)
        context = parsed["hookSpecificOutput"]["additionalContext"]
        # Should be the short reminder, not the full Iron Law template
        assert "TDD/BDD Reminder" in context
        assert "Consider tests" in context


class TestFindPluginRoot:
    """Feature: Find plugin root directory.

    As a TDD enforcement system
    I want to find the plugin root
    So that I can locate the tests directory correctly
    """

    @pytest.fixture
    def tdd_gate_module(self):
        """Import the tdd_bdd_gate module."""
        import importlib.util
        import sys

        hooks_path = Path(__file__).resolve().parent.parent.parent.parent / "hooks"
        module_path = hooks_path / "tdd_bdd_gate.py"

        spec = importlib.util.spec_from_file_location("tdd_bdd_gate", module_path)
        tdd_gate = importlib.util.module_from_spec(spec)
        sys.modules["tdd_bdd_gate"] = tdd_gate
        spec.loader.exec_module(tdd_gate)

        return tdd_gate

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_find_plugin_root_by_pyproject(self, tdd_gate_module, tmp_path) -> None:
        """Scenario: Find plugin root by pyproject.toml.

        Given a file path inside a plugin with pyproject.toml
        When finding the plugin root
        Then it should return the directory containing pyproject.toml.
        """
        # Create mock plugin structure
        plugin_root = tmp_path / "plugins" / "imbue"
        plugin_root.mkdir(parents=True)
        (plugin_root / "pyproject.toml").touch()
        nested_path = plugin_root / "skills" / "example" / "SKILL.md"
        nested_path.parent.mkdir(parents=True)
        nested_path.touch()

        found_root = tdd_gate_module._find_plugin_root(nested_path)

        assert found_root == plugin_root

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_find_plugin_root_by_claude_plugin(self, tdd_gate_module, tmp_path) -> None:
        """Scenario: Find plugin root by .claude-plugin directory.

        Given a file path inside a plugin with .claude-plugin directory
        When finding the plugin root
        Then it should return the directory containing .claude-plugin.
        """
        # Create mock plugin structure
        plugin_root = tmp_path / "plugins" / "imbue"
        (plugin_root / ".claude-plugin").mkdir(parents=True)
        nested_path = plugin_root / "skills" / "example" / "SKILL.md"
        nested_path.parent.mkdir(parents=True)
        nested_path.touch()

        found_root = tdd_gate_module._find_plugin_root(nested_path)

        assert found_root == plugin_root

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_find_plugin_root_returns_none_without_markers(
        self, tdd_gate_module, tmp_path
    ) -> None:
        """Scenario: _find_plugin_root returns None when no marker is found.

        Given a file path with no pyproject.toml or .claude-plugin in any parent
        When finding the plugin root
        Then it should return None instead of traversing to filesystem root.
        """
        # Create directory structure without any plugin markers
        nested_dir = tmp_path / "some" / "deep" / "path"
        nested_dir.mkdir(parents=True)
        nested_file = nested_dir / "file.py"
        nested_file.touch()

        found_root = tdd_gate_module._find_plugin_root(nested_file)

        assert found_root is None
