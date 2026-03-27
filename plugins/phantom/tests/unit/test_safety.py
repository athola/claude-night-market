"""Tests for phantom.safety - confirmation callbacks and action filtering.

Feature: Safety Controls
    As an automation developer
    I want to require human confirmation before dangerous actions
    So that the agent doesn't accidentally click 'Delete' or submit forms
"""

from __future__ import annotations

from phantom.safety import (
    ActionFilter,
    ConfirmationGate,
    SafetyConfig,
    always_confirm,
    confirm_clicks_only,
    no_confirm,
)


class TestSafetyConfig:
    """Feature: Safety configuration."""

    def test_defaults(self):
        config = SafetyConfig()
        assert config.require_confirmation is False
        assert config.blocked_regions == []

    def test_custom_config(self):
        config = SafetyConfig(
            require_confirmation=True,
            blocked_regions=[(0, 0, 100, 50)],
        )
        assert config.require_confirmation is True
        assert len(config.blocked_regions) == 1


class TestActionFilter:
    """Feature: Block actions in forbidden screen regions."""

    def test_allow_action_outside_blocked_region(self):
        """
        Scenario: Click outside blocked region
        Given a blocked region at (0,0)-(100,50)
        When clicking at (200, 200)
        Then the action is allowed
        """
        f = ActionFilter(blocked_regions=[(0, 0, 100, 50)])
        assert f.is_allowed({"action": "left_click", "coordinate": [200, 200]}) is True

    def test_block_action_inside_blocked_region(self):
        """
        Scenario: Click inside blocked region
        Given a blocked region at (0,0)-(100,50)
        When clicking at (50, 25)
        Then the action is blocked
        """
        f = ActionFilter(blocked_regions=[(0, 0, 100, 50)])
        assert f.is_allowed({"action": "left_click", "coordinate": [50, 25]}) is False

    def test_non_coordinate_actions_always_allowed(self):
        """
        Scenario: Non-click actions
        Given a blocked region
        When a type or key action is checked
        Then it is always allowed
        """
        f = ActionFilter(blocked_regions=[(0, 0, 1920, 1080)])
        assert f.is_allowed({"action": "type", "text": "hello"}) is True
        assert f.is_allowed({"action": "key", "text": "ctrl+c"}) is True
        assert f.is_allowed({"action": "screenshot"}) is True

    def test_no_blocked_regions_allows_all(self):
        f = ActionFilter(blocked_regions=[])
        assert f.is_allowed({"action": "left_click", "coordinate": [0, 0]}) is True

    def test_edge_of_blocked_region(self):
        """Coordinates on the boundary are blocked (inclusive)."""
        f = ActionFilter(blocked_regions=[(0, 0, 100, 50)])
        assert f.is_allowed({"action": "left_click", "coordinate": [100, 50]}) is False
        assert f.is_allowed({"action": "left_click", "coordinate": [101, 51]}) is True


class TestConfirmationGate:
    """Feature: Human-in-the-loop confirmation before actions."""

    def test_auto_approve_with_no_confirm(self):
        """
        Scenario: No confirmation required
        Given no_confirm callback
        When any action is checked
        Then it is approved without prompting
        """
        gate = ConfirmationGate(callback=no_confirm)
        assert gate.check({"action": "left_click", "coordinate": [500, 500]}) is True

    def test_always_confirm_delegates_to_callback(self):
        """
        Scenario: Always confirm
        Given always_confirm callback (returns True)
        When an action is checked
        Then it delegates to the callback and returns True
        """
        gate = ConfirmationGate(callback=always_confirm)
        assert gate.check({"action": "left_click", "coordinate": [500, 500]}) is True

    def test_custom_callback_can_reject(self):
        """
        Scenario: Custom callback rejects
        Given a callback that always rejects
        When an action is checked
        Then it returns False
        """

        def reject_all(action):
            return False

        gate = ConfirmationGate(callback=reject_all)
        assert gate.check({"action": "left_click", "coordinate": [100, 200]}) is False

    def test_confirm_clicks_only_approves_non_clicks(self):
        """
        Scenario: Only confirm clicks
        Given confirm_clicks_only callback
        When a type action is checked
        Then it is approved (non-click)
        """
        gate = ConfirmationGate(callback=confirm_clicks_only)
        assert gate.check({"action": "type", "text": "hello"}) is True
        assert gate.check({"action": "screenshot"}) is True
        # Click actions return True (the default impl approves)
        assert gate.check({"action": "left_click", "coordinate": [1, 1]}) is True

    def test_rejection_count_tracked(self):
        """
        Scenario: Track rejections
        Given a callback that rejects
        When actions are checked
        Then rejection_count increments
        """

        def reject(action):
            return False

        gate = ConfirmationGate(callback=reject)
        gate.check({"action": "left_click", "coordinate": [1, 1]})
        gate.check({"action": "left_click", "coordinate": [2, 2]})
        assert gate.rejection_count == 2
