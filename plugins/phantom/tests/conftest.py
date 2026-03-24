"""Shared fixtures for phantom tests."""

from __future__ import annotations

import pytest
from phantom.display import DisplayConfig, DisplayToolkit


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
