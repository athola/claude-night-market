"""Pytest plugin for capturing content assertion results.

Automatically captures test results from classes whose names end
with "Content" or tests marked with L1/L2/L3 markers, and optionally
publishes them to the ERC-8004 Reputation Registry at session end.

Usage in conftest.py:
    pytest_plugins = ["leyline.erc8004.pytest_plugin"]

Or via pyproject.toml:
    [tool.pytest.ini_options]
    # Set these to enable on-chain publishing:
    # ERC8004_PUBLISH=1 (env var)

Markers:
    @pytest.mark.l1 - Structural assertion
    @pytest.mark.l2 - Semantic assertion
    @pytest.mark.l3 - Behavioral assertion
"""

from __future__ import annotations

import logging
import os
import subprocess
import time
from typing import Any

from leyline.erc8004.reputation import AssertionResult

logger = logging.getLogger(__name__)

# Module-level storage for captured assertions
_captured_assertions: list[AssertionResult] = []

# Level marker names
LEVEL_MARKERS = {"l1": "L1", "l2": "L2", "l3": "L3"}


def _detect_level(item: Any) -> str | None:
    """Detect assertion level from test markers or class name.

    Checks for explicit l1/l2/l3 markers first, then falls back
    to inferring from the test class name.

    Args:
        item: The pytest test item.

    Returns:
        Level string ("L1", "L2", "L3") or None if not a
        content assertion test.

    """
    # Check explicit markers first
    for marker_name, level in LEVEL_MARKERS.items():
        if item.get_closest_marker(marker_name):
            return level

    # Fall back to class name convention: classes ending with "Content"
    if hasattr(item, "cls") and item.cls is not None:
        cls_name = item.cls.__name__
        if cls_name.endswith("Content"):
            return "L1"

    return None


def _get_git_commit_hash() -> str:
    """Get current git commit hash.

    Returns:
        Short commit hash, or "unknown" if git is unavailable.

    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.SubprocessError, FileNotFoundError):
        pass
    return "unknown"


def pytest_configure(config: Any) -> None:
    """Register custom markers for assertion levels."""
    config.addinivalue_line("markers", "l1: L1 structural assertion")
    config.addinivalue_line("markers", "l2: L2 semantic assertion")
    config.addinivalue_line("markers", "l3: L3 behavioral assertion")


def pytest_runtest_logreport(report: Any) -> None:
    """Capture test results for content assertion classes.

    Only captures results from the "call" phase (not setup/teardown)
    for tests identified as content assertions.

    """
    if report.when != "call":
        return

    level = _detect_level(report)
    if level is None:
        return

    status = "pass" if report.passed else ("fail" if report.failed else "skip")

    _captured_assertions.append(
        AssertionResult(
            test_name=report.nodeid,
            level=level,
            status=status,
            timestamp=int(time.time()),
        ),
    )
    logger.debug(
        "Captured %s assertion: %s -> %s",
        level,
        report.nodeid,
        status,
    )


def pytest_sessionfinish(session: Any, exitstatus: int) -> None:
    """Publish captured assertions at session end if configured.

    Set ERC8004_PUBLISH=1 environment variable to enable publishing.
    Also requires ERC8004_PRIVATE_KEY and registry addresses.

    """
    if not _captured_assertions:
        logger.debug("No content assertions captured, skipping publish")
        return

    logger.info("Captured %d content assertions", len(_captured_assertions))

    # Only publish if explicitly enabled
    if not os.environ.get("ERC8004_PUBLISH"):
        logger.debug(
            "ERC8004_PUBLISH not set, skipping on-chain publish. "
            "Set ERC8004_PUBLISH=1 to enable."
        )
        return

    try:
        from leyline.erc8004.client import ERC8004Client  # noqa: PLC0415

        client = ERC8004Client.from_env()
        token_id = os.environ.get("ERC8004_PLUGIN_TOKEN_ID", "")
        if not token_id:
            logger.warning("ERC8004_PLUGIN_TOKEN_ID not set, cannot publish assertions")
            return

        commit_hash = _get_git_commit_hash()
        tx_hash = client.reputation.publish_assertions(
            token_id, commit_hash, list(_captured_assertions)
        )
        logger.info("Published assertions on-chain: %s", tx_hash)
    except Exception:
        logger.exception("Failed to publish assertions on-chain")
    finally:
        _captured_assertions.clear()
