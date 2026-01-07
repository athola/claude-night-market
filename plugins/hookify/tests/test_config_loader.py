"""Tests for config loader."""

from pathlib import Path

import pytest

from hookify.core.config_loader import Condition, ConfigLoader, RuleConfig


class TestCondition:
    """Test Condition dataclass."""

    def test_valid_condition(self) -> None:
        """Valid condition should initialize."""
        condition = Condition(
            field="command", operator="regex_match", pattern=r"rm\s+-rf"
        )
        assert condition.field == "command"
        assert condition.operator == "regex_match"
        assert condition.pattern == r"rm\s+-rf"

    def test_invalid_operator(self) -> None:
        """Invalid operator should raise ValueError."""
        with pytest.raises(ValueError, match="Invalid operator"):
            Condition(field="command", operator="invalid", pattern="test")


class TestRuleConfig:
    """Test RuleConfig dataclass."""

    def test_valid_rule_with_pattern(self) -> None:
        """Valid rule with pattern should initialize."""
        rule = RuleConfig(
            name="test-rule",
            enabled=True,
            event="bash",
            pattern=r"rm\s+-rf",
            action="block",
        )
        assert rule.name == "test-rule"
        assert rule.enabled is True
        assert rule.event == "bash"
        assert rule.pattern == r"rm\s+-rf"
        assert rule.action == "block"

    def test_valid_rule_with_conditions(self) -> None:
        """Valid rule with conditions should initialize."""
        conditions = [
            Condition(field="file_path", operator="regex_match", pattern=r"\.env$")
        ]
        rule = RuleConfig(
            name="test-rule",
            enabled=True,
            event="file",
            conditions=conditions,
            action="warn",
        )
        assert rule.conditions == conditions
        assert rule.pattern is None

    def test_invalid_event(self) -> None:
        """Invalid event should raise ValueError."""
        with pytest.raises(ValueError, match="Invalid event"):
            RuleConfig(
                name="test",
                enabled=True,
                event="invalid",
                pattern="test",
            )

    def test_invalid_action(self) -> None:
        """Invalid action should raise ValueError."""
        with pytest.raises(ValueError, match="Invalid action"):
            RuleConfig(
                name="test",
                enabled=True,
                event="bash",
                pattern="test",
                action="invalid",
            )

    def test_missing_pattern_and_conditions(self) -> None:
        """Rule without pattern or conditions should raise ValueError."""
        with pytest.raises(ValueError, match="either 'pattern' or 'conditions'"):
            RuleConfig(
                name="test",
                enabled=True,
                event="bash",
            )


class TestConfigLoader:
    """Test ConfigLoader."""

    def test_parse_markdown_valid(self) -> None:
        """Valid markdown should parse correctly."""
        content = """---
name: test-rule
enabled: true
event: bash
pattern: test
---

Test message
"""
        loader = ConfigLoader()
        frontmatter, message = loader._parse_markdown(content)

        assert frontmatter["name"] == "test-rule"
        assert frontmatter["enabled"] is True
        assert frontmatter["event"] == "bash"
        assert frontmatter["pattern"] == "test"
        assert message.strip() == "Test message"

    def test_parse_markdown_no_frontmatter(self) -> None:
        """Markdown without frontmatter should raise ValueError."""
        content = "No frontmatter here"
        loader = ConfigLoader()

        with pytest.raises(ValueError, match="No valid YAML frontmatter"):
            loader._parse_markdown(content)

    def test_parse_markdown_invalid_yaml(self) -> None:
        """Invalid YAML should raise ValueError."""
        content = """---
invalid: yaml: here:
---
Message
"""
        loader = ConfigLoader()

        with pytest.raises(ValueError, match="Invalid YAML"):
            loader._parse_markdown(content)

    def test_parse_markdown_missing_required(self) -> None:
        """Missing required fields should raise ValueError."""
        content = """---
name: test
---
Message
"""
        loader = ConfigLoader()

        with pytest.raises(ValueError, match="Missing required fields"):
            loader._parse_markdown(content)

    def test_get_rule_path(self) -> None:
        """Should generate correct rule path."""
        loader = ConfigLoader(user_rules_dir=Path("/tmp/.claude"))
        path = loader.get_rule_path("test-rule")

        assert path == Path("/tmp/.claude/hookify.test-rule.local.md")

    def test_loads_bundled_rules_by_default(self) -> None:
        """Should load bundled rules when include_bundled is True (default)."""
        loader = ConfigLoader(include_bundled=True)
        rules = loader.load_all_rules()

        # Should have bundled rules
        bundled_rules = [r for r in rules if r.source == "bundled"]
        assert len(bundled_rules) > 0

        # Check for expected bundled rule names
        bundled_names = {r.name for r in bundled_rules}
        assert "block-force-push" in bundled_names

    def test_skip_bundled_rules(self) -> None:
        """Should skip bundled rules when include_bundled is False."""
        loader = ConfigLoader(include_bundled=False)
        rules = loader.load_all_rules()

        # Should have no bundled rules
        bundled_rules = [r for r in rules if r.source == "bundled"]
        assert len(bundled_rules) == 0

    def test_user_rules_override_bundled(self, tmp_path: Path) -> None:
        """User rules should override bundled rules with same name."""
        # Create a user rule that overrides a bundled rule
        user_rules_dir = tmp_path / ".claude"
        user_rules_dir.mkdir()

        user_rule = user_rules_dir / "hookify.block-force-push.local.md"
        user_rule.write_text("""---
name: block-force-push
enabled: false
event: bash
pattern: git push --force
action: warn
---

User override - disabled
""")

        loader = ConfigLoader(user_rules_dir=user_rules_dir, include_bundled=True)
        rules = loader.load_all_rules()

        # Find the block-force-push rule
        force_push_rules = [r for r in rules if r.name == "block-force-push"]
        assert len(force_push_rules) == 1

        rule = force_push_rules[0]
        # Should be the user's version (disabled, warn)
        assert rule.source == "user"
        assert rule.enabled is False
        assert rule.action == "warn"

    def test_get_bundled_rule_names(self) -> None:
        """Should return names of all bundled rules."""
        loader = ConfigLoader()
        names = loader.get_bundled_rule_names()

        assert "block-force-push" in names
        assert "warn-print-statements" in names
        assert len(names) >= 8  # We have 8 bundled rules

    def test_get_rule_status(self) -> None:
        """Should return status of all rules."""
        loader = ConfigLoader()
        status = loader.get_rule_status()

        assert "block-force-push" in status
        assert status["block-force-push"]["source"] == "bundled"
        assert status["block-force-push"]["category"] == "git"
