"""Regression tests from the API review."""

from __future__ import annotations

import dataclasses
import importlib
import sys
import warnings
from unittest.mock import patch

import pytest

from phantom import loop, safety
from phantom.display import DisplayConfig
from phantom.stuck import ScreenshotTracker, StuckPolicy


def test_loop_aborts_on_the_nth_identical_screenshot_for_max_stuck_n():
    tracker = ScreenshotTracker()
    policy = StuckPolicy(max_stuck=3)
    aborted_at = None
    for frame_number in range(1, 10):
        tracker.record("same-frame")
        if policy.should_abort(tracker.stuck_count):
            aborted_at = frame_number
            break
    assert aborted_at == 3


@pytest.mark.parametrize(
    "name",
    ["always_confirm", "confirm_clicks_only", "always_approve", "approve_clicks_only"],
)
def test_safety_module_exposes_no_always_true_confirmation_helpers(name):
    assert not hasattr(safety, name)


def test_display_config_has_no_unread_screenshot_format_knob():
    names = {f.name for f in dataclasses.fields(DisplayConfig)}
    assert "screenshot_format" not in names


def test_importing_main_module_does_not_run_the_cli():
    sys.modules.pop("phantom.__main__", None)
    with patch("phantom.cli.main") as cli_main:
        importlib.import_module("phantom.__main__")
    cli_main.assert_not_called()
    sys.modules.pop("phantom.__main__", None)


def test_loop_all_lists_only_public_api():
    assert set(loop.__all__) == {
        "LoopConfig",
        "LoopHooks",
        "LoopResult",
        "LoopSetup",
        "run_loop",
    }


@pytest.mark.parametrize(
    ("old", "new"),
    [
        ("ClientSetup", "_ClientSetup"),
        ("IterationConfig", "_IterationConfig"),
        ("IterationContext", "_IterationContext"),
    ],
)
def test_old_plumbing_names_resolve_with_deprecation_warning(old, new):
    with pytest.warns(DeprecationWarning, match=old):
        resolved = getattr(loop, old)
    assert resolved is getattr(loop, new)


def test_new_plumbing_names_resolve_without_warning():
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert loop._ClientSetup is not None


@pytest.mark.parametrize("old", ["ClientSetup", "IterationConfig", "IterationContext"])
def test_deprecation_warning_does_not_point_at_the_private_name(old):
    with pytest.warns(DeprecationWarning) as caught:
        getattr(loop, old)
    message = str(caught[0].message)
    assert f"_{old}" not in message
    assert "will be removed" in message
