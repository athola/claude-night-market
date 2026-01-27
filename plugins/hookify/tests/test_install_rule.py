"""Tests for hookify rule installation script.

Tests the install_rule.py module which manages copying rules from the
catalog to a project's .claude directory.
"""

import tempfile
from pathlib import Path

try:
    from scripts.install_rule import (
        get_available_rules,
        get_rule_path,
        install_category,
        install_rule,
        parse_rule_spec,
    )
except ImportError:
    import sys

    sys.path.insert(0, str(Path(__file__).parent.parent))
    from scripts.install_rule import (
        get_available_rules,
        get_rule_path,
        install_category,
        install_rule,
        parse_rule_spec,
    )


class TestParseRuleSpec:
    """Test rule specification parsing."""

    def test_parses_valid_spec(self):
        """Given 'git:block-force-push', returns (category, name) tuple."""
        result = parse_rule_spec("git:block-force-push")

        assert result == ("git", "block-force-push")

    def test_parses_spec_with_multiple_colons(self):
        """Given spec with extra colons, splits on first colon only."""
        result = parse_rule_spec("git:rule:with:colons")

        assert result == ("git", "rule:with:colons")

    def test_returns_none_for_missing_colon(self):
        """Given spec without colon, returns None."""
        result = parse_rule_spec("invalid-spec")

        assert result is None

    def test_returns_none_for_empty_string(self):
        """Given empty string, returns None."""
        result = parse_rule_spec("")

        assert result is None


class TestGetAvailableRules:
    """Test rule catalog discovery."""

    def test_returns_dict_of_categories(self):
        """Given a valid rules directory, returns category->rules mapping."""
        rules = get_available_rules()

        # Should be a dict (may be empty if no rules in catalog)
        assert isinstance(rules, dict)

    def test_category_values_are_lists(self):
        """Each category should contain a list of rule names."""
        rules = get_available_rules()

        for _category, rule_list in rules.items():
            assert isinstance(rule_list, list)
            for rule_name in rule_list:
                assert isinstance(rule_name, str)


class TestGetRulePath:
    """Test rule path resolution."""

    def test_returns_none_for_nonexistent_rule(self):
        """Given a rule that doesn't exist, returns None."""
        result = get_rule_path("nonexistent", "fake-rule")

        assert result is None

    def test_returns_path_when_rule_exists(self):
        """Given an existing rule, returns its Path."""
        # Get actual rules to test with
        rules = get_available_rules()
        if not rules:
            return  # Skip if no rules in catalog

        # Get first available rule
        category = next(iter(rules.keys()))
        rule_name = rules[category][0]

        result = get_rule_path(category, rule_name)

        assert result is not None
        assert result.exists()
        assert result.suffix == ".md"


class TestInstallRule:
    """Test single rule installation."""

    def test_installs_rule_to_target_dir(self):
        """Given a valid rule, copies it to target directory."""
        rules = get_available_rules()
        if not rules:
            return  # Skip if no rules

        category = next(iter(rules.keys()))
        rule_name = rules[category][0]

        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)

            result = install_rule(category, rule_name, target)

            assert result is True
            installed_file = target / f"hookify.{rule_name}.local.md"
            assert installed_file.exists()

    def test_returns_false_for_nonexistent_rule(self):
        """Given a rule that doesn't exist, returns False."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)

            result = install_rule("fake", "nonexistent", target)

            assert result is False

    def test_refuses_to_overwrite_without_force(self):
        """Given existing file and no --force, refuses to overwrite."""
        rules = get_available_rules()
        if not rules:
            return

        category = next(iter(rules.keys()))
        rule_name = rules[category][0]

        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)

            # First install
            install_rule(category, rule_name, target)

            # Second install without force should fail
            result = install_rule(category, rule_name, target, force=False)

            assert result is False

    def test_overwrites_with_force_flag(self):
        """Given existing file and --force, overwrites the file."""
        rules = get_available_rules()
        if not rules:
            return

        category = next(iter(rules.keys()))
        rule_name = rules[category][0]

        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)

            # First install
            install_rule(category, rule_name, target)

            # Second install with force should succeed
            result = install_rule(category, rule_name, target, force=True)

            assert result is True


class TestInstallCategory:
    """Test category-wide installation."""

    def test_returns_zero_for_nonexistent_category(self):
        """Given a category that doesn't exist, returns 0."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)

            count = install_category("nonexistent-category", target)

            assert count == 0

    def test_installs_all_rules_in_category(self):
        """Given a valid category, installs all its rules."""
        rules = get_available_rules()
        if not rules:
            return

        category = next(iter(rules.keys()))
        expected_count = len(rules[category])

        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)

            count = install_category(category, target)

            assert count == expected_count
            # Verify files exist
            for rule_name in rules[category]:
                assert (target / f"hookify.{rule_name}.local.md").exists()
