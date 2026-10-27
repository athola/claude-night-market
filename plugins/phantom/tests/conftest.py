"""Shared fixtures for phantom tests."""

from __future__ import annotations

import subprocess
from types import SimpleNamespace

import pytest

from phantom import display as display_module
from phantom.display import DisplayConfig, DisplayToolkit


class RealDesktopInputError(AssertionError):
    """Raised when a test reaches the real xdotool/scrot subprocess."""


def _refuse_real_subprocess(cmd, **kwargs):
    raise RealDesktopInputError(f"test reached a real desktop command: {cmd}")


@pytest.fixture(autouse=True)
def _no_real_desktop_input(monkeypatch):
    """Keep every test away from the real mouse, keyboard and screen.

    ``phantom.display`` sends every action through ``subprocess.run``
    (xdotool, scrot). A test that forgets to patch ``_run`` would move
    the developer's mouse on any machine with xdotool and a display.
    The module's own ``subprocess`` name is replaced, not the global
    ``subprocess.run``, so loop tests that run ``bash -c`` still work.
    A test that patches ``phantom.display._run`` overrides this guard.
    """
    monkeypatch.setattr(
        display_module,
        "subprocess",
        SimpleNamespace(
            run=_refuse_real_subprocess,
            TimeoutExpired=subprocess.TimeoutExpired,
            CalledProcessError=subprocess.CalledProcessError,
        ),
    )
    # The settle delay, hold_key and wait sleep on the real clock. The
    # module's own ``time`` name is replaced so the global stays intact.
    monkeypatch.setattr(display_module, "time", SimpleNamespace(sleep=_no_sleep))


def _no_sleep(_seconds):
    return None


@pytest.fixture
def display_config():
    """Standard test display config."""
    return DisplayConfig(width=1024, height=768, display_number=1)


@pytest.fixture
def toolkit(display_config, monkeypatch):
    """DisplayToolkit with mocked system deps."""
    # Pretend all tools are available
    monkeypatch.setattr(
        "phantom.display._check_command",
        lambda name: True,
    )
    return DisplayToolkit(config=display_config)
