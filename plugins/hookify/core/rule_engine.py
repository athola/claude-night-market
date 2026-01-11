"""Rule evaluation engine for hookify."""

import re
from dataclasses import dataclass
from typing import Any

from .config_loader import Condition, RuleConfig


@dataclass
class RuleResult:
    """Result of evaluating a rule."""

    matched: bool
    rule: RuleConfig
    action: str = "warn"
    message: str = ""

    def should_block(self) -> bool:
        """Check if this result should block the operation."""
        return self.matched and self.action == "block"

    def should_warn(self) -> bool:
        """Check if this result should show a warning."""
        return self.matched and self.action == "warn"


class RuleEngine:
    """Evaluate rules against tool inputs."""

    def __init__(self, rules: list[RuleConfig]) -> None:
        """Initialize rule engine.

        Args:
            rules: List of rule configurations to evaluate
        """
        self.rules = [r for r in rules if r.enabled]

    def evaluate_event(
        self, event_type: str, context: dict[str, Any]
    ) -> list[RuleResult]:
        """Evaluate all applicable rules for an event.

        Args:
            event_type: Type of event (bash, file, stop, prompt)
            context: Context data for the event

        Returns:
            List of rule results that matched
        """
        results = []

        for rule in self.rules:
            # Check if rule applies to this event type
            if rule.event != "all" and rule.event != event_type:
                continue

            # Evaluate the rule
            if self._evaluate_rule(rule, context):
                results.append(
                    RuleResult(
                        matched=True,
                        rule=rule,
                        action=rule.action,
                        message=rule.message,
                    )
                )

        return results

    def _evaluate_rule(self, rule: RuleConfig, context: dict[str, Any]) -> bool:
        """Evaluate a single rule against context.

        Args:
            rule: Rule configuration
            context: Context data

        Returns:
            True if rule matches
        """
        # Simple pattern matching
        if rule.pattern:
            return self._evaluate_pattern(rule.pattern, context)

        # Complex condition matching
        if rule.conditions:
            return self._evaluate_conditions(rule.conditions, context)

        return False

    def _evaluate_pattern(self, pattern: str, context: dict[str, Any]) -> bool:
        """Evaluate a simple pattern against context.

        Args:
            pattern: Regex pattern to match
            context: Context data

        Returns:
            True if pattern matches
        """
        # Default field depends on context
        text = self._get_default_field(context)

        if text is None:
            return False

        try:
            return bool(re.search(pattern, text, re.MULTILINE))
        except re.error:
            # Invalid regex - don't match
            return False

    def _evaluate_conditions(
        self, conditions: list[Condition], context: dict[str, Any]
    ) -> bool:
        """Evaluate multiple conditions (all must match).

        Args:
            conditions: List of conditions to evaluate
            context: Context data

        Returns:
            True if all conditions match
        """
        for condition in conditions:
            if not self._evaluate_condition(condition, context):
                return False
        return True

    def _evaluate_condition(
        self, condition: Condition, context: dict[str, Any]
    ) -> bool:
        """Evaluate a single condition.

        Args:
            condition: Condition to evaluate
            context: Context data

        Returns:
            True if condition matches
        """
        # Get field value from context
        field_value = context.get(condition.field, "")

        if not isinstance(field_value, str):
            field_value = str(field_value)

        # Apply operator
        operator = condition.operator
        pattern = condition.pattern

        if operator == "regex_match":
            try:
                return bool(re.search(pattern, field_value, re.MULTILINE))
            except re.error:
                return False
        elif operator == "contains":
            return pattern in field_value
        elif operator == "equals":
            return pattern == field_value
        elif operator == "not_contains":
            return pattern not in field_value
        elif operator == "starts_with":
            return field_value.startswith(pattern)
        elif operator == "ends_with":
            return field_value.endswith(pattern)

        return False

    def _get_default_field(self, context: dict[str, Any]) -> str | None:
        """Get the default field to match against based on context.

        Args:
            context: Context data

        Returns:
            Default field value or None
        """
        # Bash events: match against command
        if "command" in context:
            return str(context["command"]) if context["command"] is not None else None

        # File events: match against new_text by default
        if "new_text" in context:
            return str(context["new_text"]) if context["new_text"] is not None else None

        # File events: fallback to content
        if "content" in context:
            return str(context["content"]) if context["content"] is not None else None

        # Prompt events: match against user_prompt
        if "user_prompt" in context:
            return (
                str(context["user_prompt"])
                if context["user_prompt"] is not None
                else None
            )

        # Stop events: match against transcript or anything
        if "transcript" in context:
            return (
                str(context["transcript"])
                if context["transcript"] is not None
                else None
            )

        return None

    def has_blocking_results(self, results: list[RuleResult]) -> bool:
        """Check if any results should block the operation.

        Args:
            results: List of rule results

        Returns:
            True if any result should block
        """
        return any(r.should_block() for r in results)

    def format_messages(self, results: list[RuleResult]) -> str:
        """Format all matched rule messages.

        Args:
            results: List of rule results

        Returns:
            Formatted message string
        """
        if not results:
            return ""

        messages = []
        for result in results:
            header = f"{'🛑 BLOCKED' if result.should_block() else '⚠️  WARNING'}: {result.rule.name}"
            messages.append(f"{header}\n\n{result.message}")

        return "\n\n---\n\n".join(messages)
