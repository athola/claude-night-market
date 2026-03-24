"""Tests for phantom.stuck - screenshot diff-based stuck detection.

Feature: Stuck Detection
    As an automation developer
    I want to detect when the UI hasn't changed between iterations
    So that the agent loop can recover or abort instead of wasting iterations
"""

from __future__ import annotations

import base64

from phantom.stuck import ScreenshotTracker, StuckPolicy


class TestScreenshotTracker:
    """Feature: Track screenshot similarity across iterations."""

    def test_first_screenshot_is_never_stuck(self):
        """
        Scenario: First iteration
        Given no previous screenshots
        When the first screenshot is recorded
        Then is_stuck returns False
        """
        tracker = ScreenshotTracker()
        # A small 1x1 white PNG
        img = _make_png(b"\xff\xff\xff")
        assert tracker.record(img) is False

    def test_identical_screenshots_detected_as_stuck(self):
        """
        Scenario: Identical consecutive screenshots
        Given two identical screenshots
        When both are recorded
        Then the second is detected as stuck
        """
        tracker = ScreenshotTracker()
        img = _make_png(b"\xff\xff\xff")
        tracker.record(img)
        assert tracker.record(img) is True

    def test_different_screenshots_not_stuck(self):
        """
        Scenario: Different screenshots
        Given two different screenshots
        When both are recorded
        Then the second is NOT detected as stuck
        """
        tracker = ScreenshotTracker()
        tracker.record(_make_png(b"\xff\xff\xff"))
        assert tracker.record(_make_png(b"\x00\x00\x00")) is False

    def test_stuck_count_increments(self):
        """
        Scenario: Multiple identical screenshots
        Given three identical screenshots in a row
        When all are recorded
        Then stuck_count is 2 (second and third)
        """
        tracker = ScreenshotTracker()
        img = _make_png(b"\xff\xff\xff")
        tracker.record(img)
        tracker.record(img)
        tracker.record(img)
        assert tracker.stuck_count == 2

    def test_stuck_count_resets_on_change(self):
        """
        Scenario: UI changes after being stuck
        Given stuck_count is 2
        When a different screenshot is recorded
        Then stuck_count resets to 0
        """
        tracker = ScreenshotTracker()
        img_a = _make_png(b"\xff\xff\xff")
        img_b = _make_png(b"\x00\x00\x00")
        tracker.record(img_a)
        tracker.record(img_a)
        tracker.record(img_a)
        assert tracker.stuck_count == 2
        tracker.record(img_b)
        assert tracker.stuck_count == 0

    def test_history_limited(self):
        """
        Scenario: History size limit
        Given max_history=3
        When 5 screenshots are recorded
        Then only 3 hashes are kept
        """
        tracker = ScreenshotTracker(max_history=3)
        for i in range(5):
            tracker.record(_make_png(bytes([i, i, i])))
        assert len(tracker.hash_history) == 3


class TestStuckPolicy:
    """Feature: Policy for handling stuck state."""

    def test_default_policy(self):
        policy = StuckPolicy()
        assert policy.max_stuck == 3
        assert policy.recovery_action == "screenshot"

    def test_should_abort_when_exceeded(self):
        """
        Scenario: Stuck count exceeds threshold
        Given max_stuck=2 and stuck_count=3
        When should_abort is checked
        Then it returns True
        """
        policy = StuckPolicy(max_stuck=2)
        assert policy.should_abort(stuck_count=3) is True
        assert policy.should_abort(stuck_count=2) is False
        assert policy.should_abort(stuck_count=1) is False


def _make_png(pixel_bytes: bytes) -> str:
    """Create a minimal base64-encoded fake 'image' for testing.

    Not a real PNG - just deterministic bytes for hash comparison.
    """
    return base64.standard_b64encode(pixel_bytes).decode("ascii")
