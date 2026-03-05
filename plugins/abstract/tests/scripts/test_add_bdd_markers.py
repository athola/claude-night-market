"""Tests for the add_bdd_markers script.

Feature: BDD marker injection into test files
    As a developer
    I want BDD pattern detection and marker injection tested
    So that test files are correctly annotated
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from add_bdd_markers import (  # noqa: E402
    add_bdd_marker_to_file,
    is_bdd_test_function,
    needs_bdd_marker,
)


class TestIsBddTestFunction:
    """Feature: BDD pattern detection in test functions

    As a developer
    I want test functions checked for BDD patterns
    So that only genuine BDD tests get the marker
    """

    @pytest.mark.unit
    def test_detects_scenario_docstring(self) -> None:
        """Scenario: Function with Scenario docstring is BDD
        Given test lines containing a Scenario: docstring
        When is_bdd_test_function is called
        Then the result is True
        """
        lines = [
            "def test_something() -> None:\n",
            '    """Scenario: user logs in\n',
            "    Given a valid user\n",
            "    When they log in\n",
            "    Then they see the dashboard\n",
            '    """\n',
        ]
        assert is_bdd_test_function(lines, 0) is True

    @pytest.mark.unit
    def test_detects_given_keyword(self) -> None:
        """Scenario: Function with Given keyword in docstring is BDD
        Given test lines containing a Given clause
        When is_bdd_test_function is called
        Then the result is True
        """
        lines = [
            "def test_something() -> None:\n",
            '    """Given a valid config\n',
            "    When parsing\n",
            "    Then output is valid\n",
            '    """\n',
        ]
        assert is_bdd_test_function(lines, 0) is True

    @pytest.mark.unit
    def test_non_bdd_function_returns_false(self) -> None:
        """Scenario: Function without BDD patterns is not BDD
        Given test lines with no Scenario/Given/When/Then keywords
        When is_bdd_test_function is called
        Then the result is False
        """
        lines = [
            "def test_something() -> None:\n",
            '    """Check that the parser handles empty input."""\n',
            "    result = parse('')\n",
            "    assert result is None\n",
        ]
        assert is_bdd_test_function(lines, 0) is False

    @pytest.mark.unit
    def test_empty_function_returns_false(self) -> None:
        """Scenario: Function with no body beyond def line returns False
        Given only the def line in the slice
        When is_bdd_test_function is called
        Then the result is False
        """
        lines = ["def test_empty() -> None:\n"]
        assert is_bdd_test_function(lines, 0) is False

    @pytest.mark.unit
    def test_detects_when_keyword(self) -> None:
        """Scenario: Function with When keyword in docstring is BDD
        Given test lines containing a When clause
        When is_bdd_test_function is called
        Then the result is True
        """
        lines = [
            "def test_something() -> None:\n",
            '    """Test something.\n',
            "    When user submits form\n",
            '    """\n',
        ]
        assert is_bdd_test_function(lines, 0) is True


class TestNeedsBddMarker:
    """Feature: Checking whether a marker needs to be added

    As a developer
    I want to know if a test already has the BDD marker
    So that we do not add duplicate markers
    """

    @pytest.mark.unit
    def test_returns_true_when_no_existing_marker(self) -> None:
        """Scenario: No existing marker means one is needed
        Given lines where the test function has no decorators above it
        When needs_bdd_marker is called
        Then the result is True
        """
        lines = [
            "\n",
            "def test_something() -> None:\n",
        ]
        assert needs_bdd_marker(lines, 1) is True

    @pytest.mark.unit
    def test_returns_false_when_marker_exists(self) -> None:
        """Scenario: Existing @pytest.mark.bdd means no new marker needed
        Given lines where @pytest.mark.bdd already appears above the def
        When needs_bdd_marker is called with def at index >= 2
        Then the result is False
        """
        lines = [
            "class TestFoo:\n",
            "    @pytest.mark.bdd\n",
            "    def test_something() -> None:\n",
        ]
        assert needs_bdd_marker(lines, 2) is False

    @pytest.mark.unit
    def test_returns_true_when_different_marker_present(self) -> None:
        """Scenario: Different marker does not satisfy the BDD requirement
        Given lines where @pytest.mark.unit appears but not @pytest.mark.bdd
        When needs_bdd_marker is called
        Then the result is True
        """
        lines = [
            "@pytest.mark.unit\n",
            "def test_something() -> None:\n",
        ]
        assert needs_bdd_marker(lines, 1) is True

    @pytest.mark.unit
    def test_handles_start_of_file(self) -> None:
        """Scenario: Test function at the very first line
        Given the def line is at index 0
        When needs_bdd_marker is called
        Then no IndexError is raised and the result is True
        """
        lines = ["def test_something() -> None:\n"]
        assert needs_bdd_marker(lines, 0) is True


class TestAddBddMarkerToFile:
    """Feature: Adding BDD markers to test files

    As a developer
    I want BDD markers injected into test files
    So that pytest can filter BDD tests
    """

    @pytest.mark.unit
    def test_dry_run_does_not_modify_file(self, tmp_path: Path) -> None:
        """Scenario: Dry run leaves the file unchanged
        Given a test file with a BDD-style function and no marker
        When add_bdd_marker_to_file is called with dry_run=True
        Then the file on disk is not modified
        """
        test_file = tmp_path / "test_example.py"
        original_content = (
            "def test_something() -> None:\n"
            '    """Scenario: user logs in\n'
            "    Given a user\n"
            "    When they log in\n"
            "    Then they see the dashboard\n"
            '    """\n'
            "    assert True\n"
        )
        test_file.write_text(original_content)

        result = add_bdd_marker_to_file(test_file, dry_run=True)

        assert result is True
        assert test_file.read_text() == original_content

    @pytest.mark.unit
    def test_non_bdd_file_not_modified(self, tmp_path: Path) -> None:
        """Scenario: File without BDD patterns is left unchanged
        Given a test file with no BDD docstrings
        When add_bdd_marker_to_file is called
        Then the file is not modified and False is returned
        """
        test_file = tmp_path / "test_plain.py"
        content = (
            "def test_plain() -> None:\n"
            '    """Check that 1 + 1 equals 2."""\n'
            "    assert 1 + 1 == 2\n"
        )
        test_file.write_text(content)

        result = add_bdd_marker_to_file(test_file, dry_run=False)

        assert result is False
        assert test_file.read_text() == content

    @pytest.mark.unit
    def test_already_marked_file_not_modified(self, tmp_path: Path) -> None:
        """Scenario: File already marked is not modified
        Given a test file that already has @pytest.mark.bdd above the BDD test
        (with at least one preceding line so the decorator is visible in range)
        When add_bdd_marker_to_file is called
        Then the file is not changed and False is returned
        """
        test_file = tmp_path / "test_marked.py"
        content = (
            "import pytest\n"
            "@pytest.mark.bdd\n"
            "def test_something() -> None:\n"
            '    """Scenario: user logs in\n'
            "    Given a user\n"
            "    When they log in\n"
            "    Then they see the dashboard\n"
            '    """\n'
            "    assert True\n"
        )
        test_file.write_text(content)

        result = add_bdd_marker_to_file(test_file, dry_run=False)

        assert result is False

    @pytest.mark.unit
    def test_nonexistent_file_returns_false(self, tmp_path: Path) -> None:
        """Scenario: Missing file is handled gracefully
        Given a path that does not exist
        When add_bdd_marker_to_file is called
        Then False is returned without raising
        """
        missing = tmp_path / "nonexistent.py"
        result = add_bdd_marker_to_file(missing, dry_run=False)
        assert result is False

    @pytest.mark.unit
    def test_modifies_bdd_file_when_not_dry_run(self, tmp_path: Path) -> None:
        """Scenario: BDD file gets marker injected
        Given a test file with a BDD-style function and no marker
        When add_bdd_marker_to_file is called without dry_run
        Then the file on disk contains @pytest.mark.bdd and True is returned
        """
        test_file = tmp_path / "test_bdd.py"
        original_content = (
            "def test_something() -> None:\n"
            '    """Scenario: user logs in\n'
            "    Given a user\n"
            "    When they log in\n"
            "    Then they see the dashboard\n"
            '    """\n'
            "    assert True\n"
        )
        test_file.write_text(original_content)

        result = add_bdd_marker_to_file(test_file, dry_run=False)

        assert result is True
        assert "@pytest.mark.bdd" in test_file.read_text()
