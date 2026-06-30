"""Regression tests for the make plugin-check dogfooding harness.

Feature: The dogfooding harness must not silently hang or mask failures

As a maintainer
I want plugin-check to surface real defects instead of hiding them
So that a green run is trustworthy

These are invariant-encoding tests (test-updates Phase 2.5). Each one
encodes a fix from the 2026-06-28 dogfooding pass, distilled in
docs/quality-gates.md ("Dogfooding Harness Lessons"). They would have
failed against the pre-fix code and now pass. If one fails, someone
reverted a fix: read that section before changing the assertion.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def _read(rel: str) -> str:
    return (REPO / rel).read_text()


def test_conserve_makefile_has_no_stale_conservation_refs() -> None:
    """
    GIVEN plugins/conserve (the directory is named conserve)
    WHEN the Makefile references sibling plugin paths
    THEN it must use ../conserve/, never the stale ../conservation/
    """
    assert "../conservation/" not in _read("plugins/conserve/Makefile"), (
        "stale ../conservation/ reference reintroduced (finding F-A)"
    )


def test_parseltongue_demo_lint_targets_real_source() -> None:
    """
    GIVEN parseltongue source lives under src/parseltongue/
    WHEN demo-lint runs ruff
    THEN it must target src/parseltongue/, not the missing parseltongue/
    """
    assert "check src/parseltongue/" in _read("plugins/parseltongue/Makefile"), (
        "demo-lint no longer targets src/parseltongue/ (finding F-B)"
    )


def test_scry_playwright_probe_does_not_hang_offline() -> None:
    """
    GIVEN scry checks playwright availability in its dependency probe
    WHEN the probe runs via npx
    THEN it must use --no-install so an absent package fails fast,
    not a bare npx fetch that hangs offline
    """
    text = _read("plugins/scry/Makefile")
    assert "npx --no-install playwright" in text, (
        "npx --no-install dropped from scry playwright probe (finding F-G)"
    )


def test_root_plugin_check_bounds_each_plugin() -> None:
    """
    GIVEN make plugin-check iterates every plugin in sequence
    WHEN one plugin's check hangs
    THEN a per-plugin timeout must bound it so the run cannot stall
    """
    # Assert the invariant (each per-plugin check is time-bounded), not the
    # specific number: ``timeout 240`` would still satisfy it. The pattern
    # binds the timeout to the per-plugin make invocation in the loop.
    assert re.search(
        r"timeout \d+ \$\(MAKE\) -C \$\$plugin plugin-check", _read("Makefile")
    ), "per-plugin timeout removed from root plugin-check loop (finding F-G)"


def test_scribe_test_does_not_mask_pytest_failures() -> None:
    """
    GIVEN scribe has a real test suite
    WHEN make test runs pytest
    THEN a failure must propagate, not be hidden as "No tests found"
    """
    assert "No tests found" not in _read("plugins/scribe/Makefile"), (
        "scribe test target masks pytest failures again (finding F-C)"
    )
