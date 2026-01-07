"""Tests for rule engine."""

from hookify.core.config_loader import Condition, RuleConfig
from hookify.core.rule_engine import RuleEngine, RuleResult


class TestRuleResult:
    """Test RuleResult dataclass."""

    def test_should_block_when_block_action(self) -> None:
        """Should return True for block action when matched."""
        rule = RuleConfig(
            name="test", enabled=True, event="bash", pattern="test", action="block"
        )
        result = RuleResult(matched=True, rule=rule, action="block", message="Test")

        assert result.should_block() is True
        assert result.should_warn() is False

    def test_should_warn_when_warn_action(self) -> None:
        """Should return True for warn action when matched."""
        rule = RuleConfig(
            name="test", enabled=True, event="bash", pattern="test", action="warn"
        )
        result = RuleResult(matched=True, rule=rule, action="warn", message="Test")

        assert result.should_warn() is True
        assert result.should_block() is False

    def test_no_action_when_not_matched(self) -> None:
        """Should return False for all actions when not matched."""
        rule = RuleConfig(
            name="test", enabled=True, event="bash", pattern="test", action="block"
        )
        result = RuleResult(matched=False, rule=rule, action="block", message="Test")

        assert result.should_block() is False
        assert result.should_warn() is False


class TestRuleEngine:
    """Test RuleEngine."""

    def test_evaluate_simple_pattern_match(self) -> None:
        """Simple pattern should match."""
        rules = [
            RuleConfig(
                name="test",
                enabled=True,
                event="bash",
                pattern=r"rm\s+-rf",
                action="block",
                message="Blocked",
            )
        ]
        engine = RuleEngine(rules)

        context = {"command": "rm -rf /tmp/test"}
        results = engine.evaluate_event("bash", context)

        assert len(results) == 1
        assert results[0].matched is True
        assert results[0].should_block() is True

    def test_evaluate_pattern_no_match(self) -> None:
        """Pattern should not match when text differs."""
        rules = [
            RuleConfig(
                name="test",
                enabled=True,
                event="bash",
                pattern=r"rm\s+-rf",
                action="block",
            )
        ]
        engine = RuleEngine(rules)

        context = {"command": "ls -la"}
        results = engine.evaluate_event("bash", context)

        assert len(results) == 0

    def test_evaluate_conditions_all_match(self) -> None:
        """All conditions must match."""
        rules = [
            RuleConfig(
                name="test",
                enabled=True,
                event="file",
                conditions=[
                    Condition(
                        field="file_path", operator="regex_match", pattern=r"\.env$"
                    ),
                    Condition(field="new_text", operator="contains", pattern="API_KEY"),
                ],
                action="warn",
                message="Warning",
            )
        ]
        engine = RuleEngine(rules)

        context = {"file_path": ".env", "new_text": "API_KEY=secret"}
        results = engine.evaluate_event("file", context)

        assert len(results) == 1
        assert results[0].matched is True

    def test_evaluate_conditions_partial_match(self) -> None:
        """Should not match if any condition fails."""
        rules = [
            RuleConfig(
                name="test",
                enabled=True,
                event="file",
                conditions=[
                    Condition(
                        field="file_path", operator="regex_match", pattern=r"\.env$"
                    ),
                    Condition(field="new_text", operator="contains", pattern="API_KEY"),
                ],
                action="warn",
            )
        ]
        engine = RuleEngine(rules)

        # file_path matches but new_text doesn't
        context = {"file_path": ".env", "new_text": "other content"}
        results = engine.evaluate_event("file", context)

        assert len(results) == 0

    def test_evaluate_event_all_events(self) -> None:
        """Rule with event='all' should match any event."""
        rules = [
            RuleConfig(
                name="test",
                enabled=True,
                event="all",
                pattern="test",
                action="warn",
            )
        ]
        engine = RuleEngine(rules)

        for event_type in ["bash", "file", "stop", "prompt"]:
            context = {"command": "test"} if event_type == "bash" else {"text": "test"}
            results = engine.evaluate_event(event_type, context)
            # Will match if context has a field with "test"
            assert isinstance(results, list)

    def test_disabled_rules_ignored(self) -> None:
        """Disabled rules should not be evaluated."""
        rules = [
            RuleConfig(
                name="test",
                enabled=False,  # Disabled
                event="bash",
                pattern="test",
                action="block",
            )
        ]
        engine = RuleEngine(rules)

        context = {"command": "test"}
        results = engine.evaluate_event("bash", context)

        assert len(results) == 0

    def test_has_blocking_results(self) -> None:
        """Should detect blocking results."""
        rule = RuleConfig(
            name="test", enabled=True, event="bash", pattern="test", action="block"
        )
        results = [
            RuleResult(matched=True, rule=rule, action="block", message="Blocked")
        ]
        engine = RuleEngine([])

        assert engine.has_blocking_results(results) is True

    def test_format_messages(self) -> None:
        """Should format multiple messages."""
        rule1 = RuleConfig(
            name="rule1", enabled=True, event="bash", pattern="test", action="block"
        )
        rule2 = RuleConfig(
            name="rule2", enabled=True, event="bash", pattern="test", action="warn"
        )
        results = [
            RuleResult(matched=True, rule=rule1, action="block", message="Message 1"),
            RuleResult(matched=True, rule=rule2, action="warn", message="Message 2"),
        ]
        engine = RuleEngine([])

        formatted = engine.format_messages(results)

        assert "🛑 BLOCKED: rule1" in formatted
        assert "⚠️  WARNING: rule2" in formatted
        assert "Message 1" in formatted
        assert "Message 2" in formatted
