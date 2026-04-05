# ruff: noqa: D101,D102,D103,D205,D212,E501
"""Tests for the scope-guard UserPromptSubmit hook.

Feature: Scope-guard skips maintenance commands

As a developer running maintenance commands
I want the scope-guard hook to stay silent
So that RED ZONE warnings don't clutter non-feature work.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

HOOK_PATH = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "hooks"
    / "user-prompt-submit.sh"
)


def run_hook(stdin_data: str = "", env_overrides: dict | None = None) -> dict:
    """Run the scope-guard hook with given stdin and return parsed JSON."""
    env = os.environ.copy()
    env["SCOPE_GUARD_CACHE_TTL"] = "0"  # Disable caching for tests
    if env_overrides:
        env.update(env_overrides)

    result = subprocess.run(
        ["bash", str(HOOK_PATH)],
        input=stdin_data,
        capture_output=True,
        text=True,
        timeout=10,
        env=env,
    )
    assert result.returncode == 0, f"Hook failed: {result.stderr}"
    if not result.stdout.strip():
        return {}
    return json.loads(result.stdout)


class TestMaintenanceCommandSkip:
    """Feature: Maintenance commands bypass scope-guard warnings

    As a developer running /reinstall-all-plugins
    I want no scope-guard warning
    So that maintenance isn't cluttered by irrelevant alerts.
    """

    @pytest.mark.unit
    def test_reinstall_all_plugins_skipped(self) -> None:
        """Scenario: /reinstall-all-plugins produces empty context
        Given the user runs /reinstall-all-plugins
        When the hook processes the prompt
        Then additionalContext is empty.
        """
        output = run_hook('{"prompt": "/reinstall-all-plugins"}')
        ctx = output.get("hookSpecificOutput", {}).get("additionalContext", "")
        assert "scope-guard" not in ctx

    @pytest.mark.unit
    def test_update_plugins_skipped(self) -> None:
        """Scenario: /update-plugins produces empty context."""
        output = run_hook('{"prompt": "/update-plugins"}')
        ctx = output.get("hookSpecificOutput", {}).get("additionalContext", "")
        assert "scope-guard" not in ctx

    @pytest.mark.unit
    def test_fix_workflow_skipped(self) -> None:
        """Scenario: /fix-workflow produces empty context."""
        output = run_hook('{"prompt": "/fix-workflow some args"}')
        ctx = output.get("hookSpecificOutput", {}).get("additionalContext", "")
        assert "scope-guard" not in ctx

    @pytest.mark.unit
    def test_commit_msg_skipped(self) -> None:
        """Scenario: /commit-msg produces empty context."""
        output = run_hook('{"prompt": "/commit-msg"}')
        ctx = output.get("hookSpecificOutput", {}).get("additionalContext", "")
        assert "scope-guard" not in ctx

    @pytest.mark.unit
    def test_catchup_skipped(self) -> None:
        """Scenario: /catchup produces empty context."""
        output = run_hook('{"prompt": "/catchup"}')
        ctx = output.get("hookSpecificOutput", {}).get("additionalContext", "")
        assert "scope-guard" not in ctx


class TestDisableEnvVar:
    """Feature: SCOPE_GUARD_DISABLE bypasses all checks."""

    @pytest.mark.unit
    def test_disabled_produces_empty_context(self) -> None:
        """Scenario: SCOPE_GUARD_DISABLE=1 skips everything
        Given SCOPE_GUARD_DISABLE is set to 1
        When the hook runs
        Then additionalContext is empty.
        """
        output = run_hook(
            '{"prompt": "add a huge feature"}',
            env_overrides={"SCOPE_GUARD_DISABLE": "1"},
        )
        ctx = output.get("hookSpecificOutput", {}).get("additionalContext", "")
        assert ctx == ""


class TestNonMaintenancePrompt:
    """Feature: Non-maintenance prompts still get scope-guard checks."""

    @pytest.mark.unit
    def test_feature_prompt_still_checked(self) -> None:
        """Scenario: A feature prompt still runs the scope-guard check
        Given the user types a feature request
        When the hook processes the prompt
        Then it returns valid JSON (may or may not have warnings).
        """
        output = run_hook('{"prompt": "add a new login feature"}')
        assert "hookSpecificOutput" in output
        assert "hookEventName" in output["hookSpecificOutput"]
