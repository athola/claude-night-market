"""Tests for rule engine.

Covers RuleResult, RuleEngine.evaluate_event, and all private
methods: _evaluate_pattern, _evaluate_conditions,
_evaluate_condition (all 6 operators), _get_default_field,
has_blocking_results, and format_messages.
"""

from __future__ import annotations

import pytest

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

        assert "[BLOCKED]: rule1" in formatted
        assert "[WARNING]: rule2" in formatted
        assert "Message 1" in formatted
        assert "Message 2" in formatted


class TestEvaluatePattern:
    """Test RuleEngine._evaluate_pattern (via evaluate_event)."""

    def test_invalid_regex_does_not_match(self) -> None:
        """Invalid regex pattern returns no match instead of raising."""
        rules = [
            RuleConfig(
                name="bad-regex",
                enabled=True,
                event="bash",
                pattern=r"[unclosed",
                action="block",
            )
        ]
        engine = RuleEngine(rules)
        results = engine.evaluate_event("bash", {"command": "anything"})
        assert len(results) == 0

    def test_none_command_field_does_not_match(self) -> None:
        """Context with None command value produces no match."""
        rules = [
            RuleConfig(
                name="test",
                enabled=True,
                event="bash",
                pattern="test",
                action="warn",
            )
        ]
        engine = RuleEngine(rules)
        results = engine.evaluate_event("bash", {"command": None})
        assert len(results) == 0

    def test_empty_context_does_not_match(self) -> None:
        """Empty context dict produces no match."""
        rules = [
            RuleConfig(
                name="test",
                enabled=True,
                event="bash",
                pattern="test",
                action="warn",
            )
        ]
        engine = RuleEngine(rules)
        results = engine.evaluate_event("bash", {})
        assert len(results) == 0

    def test_rule_without_pattern_or_conditions_does_not_match(self) -> None:
        """Rule with neither pattern nor conditions returns False.

        We build the RuleConfig manually to bypass __post_init__
        validation.
        """
        rule = RuleConfig.__new__(RuleConfig)
        rule.name = "empty"
        rule.enabled = True
        rule.event = "bash"
        rule.action = "warn"
        rule.pattern = None
        rule.conditions = []
        rule.message = ""
        rule.file_path = None
        rule.source = "user"

        engine = RuleEngine([rule])
        results = engine.evaluate_event("bash", {"command": "anything"})
        assert len(results) == 0


class TestGetDefaultField:
    """Test RuleEngine._get_default_field priority ordering."""

    def _make_engine_with_pattern(self) -> RuleEngine:
        """Create an engine with a single catch-all pattern rule."""
        rules = [
            RuleConfig(
                name="catchall",
                enabled=True,
                event="all",
                pattern=r".+",
                action="warn",
            )
        ]
        return RuleEngine(rules)

    def test_command_field_takes_priority(self) -> None:
        """When command is present, it is the default field."""
        engine = self._make_engine_with_pattern()
        context = {"command": "test-cmd", "new_text": "text"}
        results = engine.evaluate_event("bash", context)
        assert len(results) == 1

    def test_new_text_field_used_for_file_events(self) -> None:
        """new_text is the default field for file events."""
        engine = self._make_engine_with_pattern()
        results = engine.evaluate_event(
            "file", {"new_text": "some content"}
        )
        assert len(results) == 1

    def test_content_field_used_when_no_new_text(self) -> None:
        """content is used as fallback for file events."""
        engine = self._make_engine_with_pattern()
        results = engine.evaluate_event(
            "file", {"content": "body text"}
        )
        assert len(results) == 1

    def test_user_prompt_field(self) -> None:
        """user_prompt is the default field for prompt events."""
        engine = self._make_engine_with_pattern()
        results = engine.evaluate_event(
            "prompt", {"user_prompt": "hello"}
        )
        assert len(results) == 1

    def test_transcript_field(self) -> None:
        """transcript is the default field for stop events."""
        engine = self._make_engine_with_pattern()
        results = engine.evaluate_event(
            "stop", {"transcript": "session log"}
        )
        assert len(results) == 1

    def test_none_new_text_returns_no_match(self) -> None:
        """None new_text value produces no match."""
        engine = self._make_engine_with_pattern()
        results = engine.evaluate_event(
            "file", {"new_text": None}
        )
        assert len(results) == 0

    def test_none_user_prompt_returns_no_match(self) -> None:
        """None user_prompt value produces no match."""
        engine = self._make_engine_with_pattern()
        results = engine.evaluate_event(
            "prompt", {"user_prompt": None}
        )
        assert len(results) == 0

    def test_none_transcript_returns_no_match(self) -> None:
        """None transcript value produces no match."""
        engine = self._make_engine_with_pattern()
        results = engine.evaluate_event(
            "stop", {"transcript": None}
        )
        assert len(results) == 0

    def test_none_content_returns_no_match(self) -> None:
        """None content value produces no match."""
        engine = self._make_engine_with_pattern()
        results = engine.evaluate_event(
            "file", {"content": None}
        )
        assert len(results) == 0


class TestEvaluateConditionOperators:
    """Test all 6 condition operators via _evaluate_condition."""

    def _make_engine_with_condition(
        self, field: str, operator: str, pattern: str
    ) -> RuleEngine:
        """Build an engine with a single condition-based rule."""
        rules = [
            RuleConfig(
                name="op-test",
                enabled=True,
                event="bash",
                conditions=[
                    Condition(
                        field=field,
                        operator=operator,
                        pattern=pattern,
                    )
                ],
                action="warn",
                message="matched",
            )
        ]
        return RuleEngine(rules)

    def test_equals_match(self) -> None:
        """equals operator matches identical strings."""
        engine = self._make_engine_with_condition(
            "command", "equals", "git status"
        )
        results = engine.evaluate_event(
            "bash", {"command": "git status"}
        )
        assert len(results) == 1

    def test_equals_no_match(self) -> None:
        """equals operator rejects different strings."""
        engine = self._make_engine_with_condition(
            "command", "equals", "git status"
        )
        results = engine.evaluate_event(
            "bash", {"command": "git diff"}
        )
        assert len(results) == 0

    def test_contains_match(self) -> None:
        """contains operator finds substring."""
        engine = self._make_engine_with_condition(
            "command", "contains", "rm"
        )
        results = engine.evaluate_event(
            "bash", {"command": "rm -rf /tmp"}
        )
        assert len(results) == 1

    def test_contains_no_match(self) -> None:
        """contains operator rejects absent substring."""
        engine = self._make_engine_with_condition(
            "command", "contains", "rm"
        )
        results = engine.evaluate_event(
            "bash", {"command": "ls -la"}
        )
        assert len(results) == 0

    def test_not_contains_match(self) -> None:
        """not_contains operator matches when substring is absent."""
        engine = self._make_engine_with_condition(
            "command", "not_contains", "dangerous"
        )
        results = engine.evaluate_event(
            "bash", {"command": "ls -la"}
        )
        assert len(results) == 1

    def test_not_contains_no_match(self) -> None:
        """not_contains operator rejects when substring is present."""
        engine = self._make_engine_with_condition(
            "command", "not_contains", "ls"
        )
        results = engine.evaluate_event(
            "bash", {"command": "ls -la"}
        )
        assert len(results) == 0

    def test_starts_with_match(self) -> None:
        """starts_with operator matches prefix."""
        engine = self._make_engine_with_condition(
            "command", "starts_with", "git"
        )
        results = engine.evaluate_event(
            "bash", {"command": "git push origin"}
        )
        assert len(results) == 1

    def test_starts_with_no_match(self) -> None:
        """starts_with operator rejects non-prefix."""
        engine = self._make_engine_with_condition(
            "command", "starts_with", "git"
        )
        results = engine.evaluate_event(
            "bash", {"command": "npm run git"}
        )
        assert len(results) == 0

    def test_ends_with_match(self) -> None:
        """ends_with operator matches suffix."""
        engine = self._make_engine_with_condition(
            "command", "ends_with", ".py"
        )
        results = engine.evaluate_event(
            "bash", {"command": "python test.py"}
        )
        assert len(results) == 1

    def test_ends_with_no_match(self) -> None:
        """ends_with operator rejects non-suffix."""
        engine = self._make_engine_with_condition(
            "command", "ends_with", ".py"
        )
        results = engine.evaluate_event(
            "bash", {"command": "python test.js"}
        )
        assert len(results) == 0

    def test_regex_match_match(self) -> None:
        """regex_match operator matches regex."""
        engine = self._make_engine_with_condition(
            "command", "regex_match", r"\d{3,}"
        )
        results = engine.evaluate_event(
            "bash", {"command": "echo 12345"}
        )
        assert len(results) == 1

    def test_regex_match_no_match(self) -> None:
        """regex_match operator rejects non-matching text."""
        engine = self._make_engine_with_condition(
            "command", "regex_match", r"\d{3,}"
        )
        results = engine.evaluate_event(
            "bash", {"command": "echo ab"}
        )
        assert len(results) == 0

    def test_regex_match_invalid_regex(self) -> None:
        """regex_match with invalid regex returns no match."""
        engine = self._make_engine_with_condition(
            "command", "regex_match", r"[bad"
        )
        results = engine.evaluate_event(
            "bash", {"command": "anything"}
        )
        assert len(results) == 0

    def test_non_string_field_value_converted(self) -> None:
        """Non-string context values are coerced to strings."""
        engine = self._make_engine_with_condition(
            "command", "contains", "42"
        )
        results = engine.evaluate_event(
            "bash", {"command": 42}
        )
        assert len(results) == 1

    def test_missing_field_uses_empty_string(self) -> None:
        """Missing field defaults to empty string."""
        engine = self._make_engine_with_condition(
            "nonexistent", "equals", ""
        )
        results = engine.evaluate_event(
            "bash", {"command": "test"}
        )
        assert len(results) == 1


class TestEvaluateConditionsEdgeCases:
    """Test _evaluate_conditions edge cases."""

    def test_empty_conditions_list_does_not_match(self) -> None:
        """Empty conditions list is falsy, so _evaluate_rule returns False.

        We bypass __post_init__ to create this state.
        """
        rule = RuleConfig.__new__(RuleConfig)
        rule.name = "empty-conds"
        rule.enabled = True
        rule.event = "bash"
        rule.action = "warn"
        rule.pattern = None
        rule.conditions = []
        rule.message = "empty"
        rule.file_path = None
        rule.source = "user"

        engine = RuleEngine([rule])
        # _evaluate_rule sees no pattern, checks `if rule.conditions:`
        # which is falsy for empty list, falls through to return False
        results = engine.evaluate_event("bash", {"command": "test"})
        assert len(results) == 0

    def test_multiple_conditions_all_must_match(self) -> None:
        """All conditions must match for a rule to fire."""
        rules = [
            RuleConfig(
                name="multi",
                enabled=True,
                event="bash",
                conditions=[
                    Condition(
                        field="command",
                        operator="starts_with",
                        pattern="git",
                    ),
                    Condition(
                        field="command",
                        operator="ends_with",
                        pattern="--force",
                    ),
                ],
                action="block",
                message="blocked",
            )
        ]
        engine = RuleEngine(rules)

        assert len(
            engine.evaluate_event(
                "bash", {"command": "git push --force"}
            )
        ) == 1
        assert len(
            engine.evaluate_event(
                "bash", {"command": "git push --soft"}
            )
        ) == 0


class TestHasBlockingResultsEdge:
    """Additional tests for has_blocking_results."""

    def test_empty_results(self) -> None:
        """Empty list has no blocking results."""
        engine = RuleEngine([])
        assert engine.has_blocking_results([]) is False

    def test_warn_only_results(self) -> None:
        """Warn-only results do not block."""
        rule = RuleConfig(
            name="w",
            enabled=True,
            event="bash",
            pattern="t",
            action="warn",
        )
        results = [
            RuleResult(
                matched=True, rule=rule, action="warn", message="w"
            )
        ]
        engine = RuleEngine([])
        assert engine.has_blocking_results(results) is False

    def test_mixed_results_detects_block(self) -> None:
        """Mixed warn/block list returns True."""
        warn_rule = RuleConfig(
            name="w",
            enabled=True,
            event="bash",
            pattern="t",
            action="warn",
        )
        block_rule = RuleConfig(
            name="b",
            enabled=True,
            event="bash",
            pattern="t",
            action="block",
        )
        results = [
            RuleResult(
                matched=True, rule=warn_rule, action="warn", message="w"
            ),
            RuleResult(
                matched=True,
                rule=block_rule,
                action="block",
                message="b",
            ),
        ]
        engine = RuleEngine([])
        assert engine.has_blocking_results(results) is True


class TestFormatMessagesEdge:
    """Additional tests for format_messages."""

    def test_empty_results_returns_empty_string(self) -> None:
        """No results produces empty string."""
        engine = RuleEngine([])
        assert engine.format_messages([]) == ""

    def test_single_warning_format(self) -> None:
        """Single warning result is formatted correctly."""
        rule = RuleConfig(
            name="single-warn",
            enabled=True,
            event="bash",
            pattern="t",
            action="warn",
        )
        results = [
            RuleResult(
                matched=True,
                rule=rule,
                action="warn",
                message="Watch out",
            )
        ]
        engine = RuleEngine([])
        formatted = engine.format_messages(results)
        assert formatted == "[WARNING]: single-warn\n\nWatch out"

    def test_single_block_format(self) -> None:
        """Single block result is formatted correctly."""
        rule = RuleConfig(
            name="single-block",
            enabled=True,
            event="bash",
            pattern="t",
            action="block",
        )
        results = [
            RuleResult(
                matched=True,
                rule=rule,
                action="block",
                message="Stopped",
            )
        ]
        engine = RuleEngine([])
        formatted = engine.format_messages(results)
        assert formatted == "[BLOCKED]: single-block\n\nStopped"

    def test_separator_between_messages(self) -> None:
        """Multiple messages are joined by '---' separator."""
        rule = RuleConfig(
            name="r",
            enabled=True,
            event="bash",
            pattern="t",
            action="warn",
        )
        results = [
            RuleResult(
                matched=True, rule=rule, action="warn", message="A"
            ),
            RuleResult(
                matched=True, rule=rule, action="warn", message="B"
            ),
        ]
        engine = RuleEngine([])
        formatted = engine.format_messages(results)
        assert "\n\n---\n\n" in formatted


class TestEventTypeFiltering:
    """Test that rules only fire for matching event types."""

    @pytest.mark.parametrize(
        ("rule_event", "trigger_event", "should_match"),
        [
            ("bash", "bash", True),
            ("bash", "file", False),
            ("file", "file", True),
            ("file", "bash", False),
            ("all", "bash", True),
            ("all", "file", True),
            ("all", "stop", True),
            ("all", "prompt", True),
        ],
    )
    def test_event_filtering(
        self,
        rule_event: str,
        trigger_event: str,
        should_match: bool,
    ) -> None:
        """Rule only fires when event types align."""
        rules = [
            RuleConfig(
                name="filter-test",
                enabled=True,
                event=rule_event,
                pattern="target",
                action="warn",
            )
        ]
        engine = RuleEngine(rules)
        context = {"command": "target"}
        results = engine.evaluate_event(trigger_event, context)
        if should_match:
            assert len(results) == 1
        else:
            assert len(results) == 0
